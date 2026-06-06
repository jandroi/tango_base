"""
Validators — row-level validation before DB write.
"""
from dataclasses import dataclass, field
from typing import Any

from django.apps import apps

from .registry import RegistryEntry, get_entry
from .resolvers import resolve_rows


@dataclass
class RowError:
    row_number: int
    field_name: str | None
    error_code: str
    error_message: str
    payload: dict | None = None


@dataclass
class ValidationResult:
    model_label: str
    errors: list[RowError] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def add(self, row_number: int, field_name: str | None, code: str, message: str,
            payload: dict | None = None):
        self.errors.append(RowError(
            row_number=row_number,
            field_name=field_name,
            error_code=code,
            error_message=message,
            payload=payload,
        ))


def validate_rows(model_label: str, rows: list[dict], mode: str = "append") -> ValidationResult:
    """
    Perform row-level validation for all rows destined for a given model.

    Steps:
    1. Resolve natural-key columns to FK PKs (if fk_natural_keys defined)
    2. Check required fields
    3. Check FK existence
    4. Check uniqueness (within batch always; against DB only in append mode)

    mode: "append" or "replace". In replace mode, existing records are deleted
    before commit, so DB conflict checks are skipped.

    Returns a ValidationResult containing all errors found (does not abort early).
    """
    entry: RegistryEntry = get_entry(model_label)
    result = ValidationResult(model_label=model_label)

    model_class = apps.get_model(*model_label.split("."))

    # Step 1: Resolve natural keys
    # Keep a copy of original rows (with user-typed NK columns) for readable error messages.
    original_rows = rows
    if entry.fk_natural_keys:
        rows, nk_errors = resolve_rows(entry, rows)
        for err in nk_errors:
            result.add(
                row_number=err["row_number"],
                field_name=err["field_name"],
                code=err["error_code"],
                message=err["error_message"],
            )

    for row_idx, row in enumerate(rows):
        row_number = row_idx + 2  # 1-based header + 1

        # --- Required field checks ---
        for fname in entry.required_fields:
            val = row.get(fname)
            if val is None or str(val).strip() == "":
                result.add(
                    row_number=row_number,
                    field_name=fname,
                    code="REQUIRED_FIELD_MISSING",
                    message=f"Row {row_number}: '{fname}' is required but empty.",
                    payload={"row": row},
                )

        # --- FK existence checks ---
        for fk_field, related_label in entry.fk_fields.items():
            raw_value = row.get(fk_field)
            if raw_value is None:
                continue
            try:
                related_model = apps.get_model(*related_label.split("."))
                pk_val = _coerce_pk(raw_value, related_model)
                if not related_model.objects.filter(pk=pk_val).exists():
                    result.add(
                        row_number=row_number,
                        field_name=fk_field,
                        code="FK_NOT_FOUND",
                        message=(
                            f"Row {row_number}: No {related_label.split('.')[-1]} found "
                            f"with ID {pk_val!r}. Check that the parent record exists."
                        ),
                        payload={"value": raw_value},
                    )
            except (ValueError, TypeError) as exc:
                result.add(
                    row_number=row_number,
                    field_name=fk_field,
                    code="FK_INVALID_VALUE",
                    message=(
                        f"Row {row_number}: The value in '{fk_field}' is not a valid ID format."
                    ),
                    payload={"value": raw_value},
                )

    # Step 4: Uniqueness checks
    if entry.natural_key_fields:
        _check_uniqueness(entry, rows, model_class, result, check_db=(mode == "append"),
                          original_rows=original_rows)

    return result


def _display_key(entry: RegistryEntry, nk_fields: tuple, original_row: dict) -> str:
    """
    Build a human-readable description of a natural key using the original (pre-resolution)
    row so users see the column names they actually typed, not resolved PK integers.

    For FK fields that were supplied as natural-key columns (e.g. building_code + property_code
    instead of building=1), we show those original column names and values.
    For non-FK fields we show the field name and value directly.
    """
    parts = []
    for fname in nk_fields:
        if fname in entry.fk_natural_keys:
            # Show the NK columns the user typed for this FK, e.g. building_code=B01, property_code=HZC
            for csv_col in entry.fk_natural_keys[fname].values():
                val = original_row.get(csv_col)
                if val is not None:
                    parts.append(f"{csv_col}={val}")
        else:
            val = original_row.get(fname)
            if val is not None:
                parts.append(f"{fname}={val}")
    return ", ".join(parts) if parts else str(tuple(original_row.get(f) for f in nk_fields))


def _check_uniqueness(
    entry: RegistryEntry,
    rows: list[dict],
    model_class,
    result: ValidationResult,
    check_db: bool = True,
    original_rows: list[dict] | None = None,
) -> None:
    """
    Check for duplicate natural-key combinations within the uploaded batch and,
    when check_db=True, against existing DB records.

    check_db should be False in replace mode since existing records will be
    upserted — a DB conflict is not actually a conflict.

    original_rows: the rows before NK resolution, used for readable error messages.
    """
    nk_fields = entry.natural_key_fields
    if original_rows is None:
        original_rows = rows

    # Build a list of (row_number, key_tuple, display_str) for rows that have all NK values present.
    keyed_rows: list[tuple[int, tuple, str]] = []
    for row_idx, row in enumerate(rows):
        row_number = row_idx + 2
        key_parts = []
        for fname in nk_fields:
            val = row.get(fname)
            if val is None:
                key_parts = None
                break
            # FK fields after resolution hold the PK value — normalise to str for comparison
            key_parts.append(str(val))
        if key_parts is not None:
            orig = original_rows[row_idx] if row_idx < len(original_rows) else row
            keyed_rows.append((row_number, tuple(key_parts), _display_key(entry, nk_fields, orig)))

    # Within-batch duplicate detection
    seen: dict[tuple, tuple[int, str]] = {}  # key_tuple → (first row_number, display)
    for row_number, key, display in keyed_rows:
        if key in seen:
            first_row, first_display = seen[key]
            result.add(
                row_number=row_number,
                field_name=None,
                code="DUPLICATE_IN_FILE",
                message=(
                    f"Row {row_number}: Duplicate — another row in this file has the same "
                    f"values ({first_display}), first seen on row {first_row}."
                ),
            )
        else:
            seen[key] = (row_number, display)

    # DB conflict detection — skipped in replace mode
    if not check_db:
        return

    # DB conflict detection — only for unique keys not already flagged as within-batch dupes
    duped_keys = {key for key, count in (
        (k, sum(1 for _, kk, _ in keyed_rows if kk == k))
        for k in {kk for _, kk, _ in keyed_rows}
    ) if count > 1}
    unique_keys = {key for _, key, _ in keyed_rows} - duped_keys

    if not unique_keys:
        return

    # Build OR-filter to check all unique keys in one query.
    # We use the FK id lookup for FK fields (e.g. building → building_id).
    from django.db.models import Q
    q = Q()
    for key in unique_keys:
        kwargs = {}
        for fname, val in zip(nk_fields, key):
            field_obj = model_class._meta.get_field(fname)
            if field_obj.is_relation:
                kwargs[f"{fname}_id"] = val
            else:
                kwargs[fname] = val
        q |= Q(**kwargs)

    existing = model_class.objects.filter(q)
    if not existing.exists():
        return

    # Map existing records back to their key tuples
    existing_keys: set[tuple] = set()
    for obj in existing:
        parts = []
        for fname in nk_fields:
            field_obj = model_class._meta.get_field(fname)
            if field_obj.is_relation:
                parts.append(str(getattr(obj, f"{fname}_id")))
            else:
                parts.append(str(getattr(obj, fname)))
        existing_keys.add(tuple(parts))

    for row_number, key, display in keyed_rows:
        if key in existing_keys:
            result.add(
                row_number=row_number,
                field_name=None,
                code="DUPLICATE_IN_DB",
                message=(
                    f"Row {row_number}: A record with these values already exists in the database "
                    f"({display}). Use Replace mode to overwrite, or remove duplicate rows."
                ),
            )


def _coerce_pk(raw_value: Any, model_class) -> Any:
    pk_field = model_class._meta.pk
    if pk_field is None:
        return raw_value
    if hasattr(pk_field, "max_length"):
        return str(raw_value).strip()
    return int(float(str(raw_value)))
