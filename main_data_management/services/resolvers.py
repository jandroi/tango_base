"""
Resolvers — convert natural-key CSV columns to FK PKs before validation/commit.

For each FK field in entry.fk_natural_keys, the resolver reads user-provided
natural key columns (e.g. property_code=HZC) and resolves them to the actual
PK value the model expects.

Error codes:
  NK_NOT_FOUND  — no record found for the given natural key values
  NK_AMBIGUOUS  — more than one record matches (should not normally happen)
"""
from __future__ import annotations

from django.apps import apps

from .registry import RegistryEntry, get_entry


def resolve_rows(entry: RegistryEntry, rows: list[dict]) -> tuple[list[dict], list[dict]]:
    """
    Batch-resolve natural key columns for all rows destined for `entry`.

    Returns:
        resolved_rows: list of row dicts with FK columns replaced by resolved PKs.
        errors: list of error dicts with keys row_number, field_name, error_code, error_message.

    Backward compat: if no NK columns are present in the row and the raw FK column IS present,
    resolution is skipped and the raw value passes through.
    """
    if not entry.fk_natural_keys:
        return rows, []

    # Build a per-FK cache so same NK value across rows = 1 DB query.
    # cache[fk_field][frozenset(lookup_items)] = pk_value | "NOT_FOUND" | "AMBIGUOUS"
    cache: dict[str, dict] = {fk_field: {} for fk_field in entry.fk_natural_keys}

    resolved_rows = []
    errors = []

    for row_idx, row in enumerate(rows):
        row_number = row_idx + 2  # 1-based, row 1 is header
        new_row = dict(row)

        for fk_field, lookup_map in entry.fk_natural_keys.items():
            # lookup_map: {django_lookup: csv_column_name}
            # e.g. {"property_code": "property_code"}
            # e.g. {"building_code": "building_code", "property__property_code": "property_code"}

            # Check which NK columns are present in the row
            nk_columns_present = any(
                csv_col in row and row[csv_col] is not None
                for csv_col in lookup_map.values()
            )

            if not nk_columns_present:
                # Fall through: use raw FK if present (backward compat)
                continue

            # Gather the lookup kwargs
            filter_kwargs = {}
            missing_nk = False
            for django_lookup, csv_col in lookup_map.items():
                val = row.get(csv_col)
                if val is None:
                    missing_nk = True
                    break
                filter_kwargs[django_lookup] = val

            if missing_nk:
                errors.append({
                    "row_number": row_number,
                    "field_name": fk_field,
                    "error_code": "NK_NOT_FOUND",
                    "error_message": (
                        f"Row {row_number}: Could not resolve '{fk_field}' — "
                        f"one or more required identifier columns are empty."
                    ),
                })
                continue

            # Cache key is the frozenset of filter items
            cache_key = frozenset(filter_kwargs.items())

            if cache_key not in cache[fk_field]:
                # Resolve via DB
                related_label = entry.fk_fields[fk_field]
                related_model = apps.get_model(*related_label.split("."))
                try:
                    qs = related_model.objects.filter(**filter_kwargs)
                    count = qs.count()
                    if count == 0:
                        cache[fk_field][cache_key] = ("NOT_FOUND", filter_kwargs)
                    elif count > 1:
                        cache[fk_field][cache_key] = ("AMBIGUOUS", filter_kwargs)
                    else:
                        pk_val = qs.values_list("pk", flat=True).first()
                        cache[fk_field][cache_key] = ("OK", pk_val)
                except Exception as exc:
                    cache[fk_field][cache_key] = ("ERROR", str(exc))

            status, payload = cache[fk_field][cache_key]

            if status == "OK":
                new_row[fk_field] = payload
                # Remove the NK columns from the row so they don't interfere with writable_fields
                for csv_col in lookup_map.values():
                    new_row.pop(csv_col, None)
            elif status == "NOT_FOUND":
                related_label = entry.fk_fields[fk_field]
                human_desc = ", ".join(f"{k}={v!r}" for k, v in payload.items())
                errors.append({
                    "row_number": row_number,
                    "field_name": fk_field,
                    "error_code": "NK_NOT_FOUND",
                    "error_message": (
                        f"Row {row_number}: No {related_label.split('.')[-1]} found with "
                        f"{human_desc}. Check that this record exists."
                    ),
                })
            elif status == "AMBIGUOUS":
                related_label = entry.fk_fields[fk_field]
                human_desc = ", ".join(f"{k}={v!r}" for k, v in payload.items())
                errors.append({
                    "row_number": row_number,
                    "field_name": fk_field,
                    "error_code": "NK_AMBIGUOUS",
                    "error_message": (
                        f"Row {row_number}: Multiple {related_label.split('.')[-1]} records match "
                        f"{human_desc}. The identifier must be unique."
                    ),
                })
            else:
                errors.append({
                    "row_number": row_number,
                    "field_name": fk_field,
                    "error_code": "NK_NOT_FOUND",
                    "error_message": (
                        f"Row {row_number}: Could not resolve '{fk_field}': {payload}"
                    ),
                })

        resolved_rows.append(new_row)

    return resolved_rows, errors


def resolve_row(entry: RegistryEntry, row: dict) -> tuple[dict, list[dict]]:
    """Single-row convenience wrapper around resolve_rows."""
    resolved, errors = resolve_rows(entry, [row])
    return resolved[0] if resolved else row, errors
