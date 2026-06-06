"""
Schema service — validates incoming file columns against registry expectations.
"""
from dataclasses import dataclass

from django.apps import apps

from .registry import RegistryEntry, get_entry


@dataclass
class SchemaValidationResult:
    model_label: str
    missing_required: list[str]       # required fields absent from file
    missing_writable: list[str]       # writable (non-required) fields absent
    extra_columns: list[str]          # columns in file not in registry
    type_warnings: list[str]          # e.g. expected decimal, got str
    is_valid: bool                    # False if missing_required is non-empty

    def errors(self) -> list[str]:
        msgs = []
        for f in self.missing_required:
            msgs.append(f"Missing required column: '{f}'")
        return msgs

    def warnings(self) -> list[str]:
        msgs = []
        for f in self.missing_writable:
            msgs.append(f"Missing optional column: '{f}' (will be skipped)")
        for f in self.extra_columns:
            msgs.append(f"Unknown column: '{f}' (will be ignored)")
        for w in self.type_warnings:
            msgs.append(w)
        return msgs


def _nk_columns_for_entry(entry: RegistryEntry) -> set[str]:
    """Return all natural-key CSV column names defined for this entry."""
    nk_cols = set()
    for lookup_map in entry.fk_natural_keys.values():
        for csv_col in lookup_map.values():
            nk_cols.add(csv_col)
    return nk_cols


def validate_columns(model_label: str, file_columns: list[str]) -> SchemaValidationResult:
    """
    Compare the columns found in an uploaded file against the registry contract
    for the given model. Accepts natural-key columns as alternatives to raw FK columns.
    """
    entry: RegistryEntry = get_entry(model_label)
    file_col_set = set(file_columns)

    # Collect all NK columns defined in the registry
    nk_cols = _nk_columns_for_entry(entry)

    # For required FK fields: if NK columns are present instead of raw FK, treat as satisfied
    effective_required = set()
    for fname in entry.required_fields:
        if fname in entry.fk_natural_keys:
            lookup_map = entry.fk_natural_keys[fname]
            nk_col_names = set(lookup_map.values())
            if nk_col_names & file_col_set:
                # NK columns present — treat raw FK as satisfied
                continue
        effective_required.add(fname)

    writable = set(entry.writable_fields)
    known = writable | set(entry.readonly_fields) | nk_cols

    # FK fields that have NK alternatives present: remove them from writable known
    # so they don't cause "missing_writable" complaints
    for fk_field, lookup_map in entry.fk_natural_keys.items():
        nk_col_names = set(lookup_map.values())
        if nk_col_names & file_col_set:
            # NK present: raw FK field is optional
            writable.discard(fk_field)
            effective_required.discard(fk_field)

    missing_required = sorted(effective_required - file_col_set)
    missing_writable = sorted((writable - set(entry.required_fields)) - file_col_set)
    extra_columns = sorted(file_col_set - known)

    return SchemaValidationResult(
        model_label=model_label,
        missing_required=missing_required,
        missing_writable=missing_writable,
        extra_columns=extra_columns,
        type_warnings=[],
        is_valid=len(missing_required) == 0,
    )


def get_expected_columns(model_label: str) -> list[str]:
    """Return the ordered list of writable columns for a model (template generation).
    Legacy function — returns raw writable_fields including FK columns and PKs."""
    entry: RegistryEntry = get_entry(model_label)
    return list(entry.writable_fields)


def get_template_columns(model_label: str) -> list[str]:
    """
    Return user-facing columns for template download:
    - Excludes PK fields (auto-generated IDs like building_id, property_id)
    - Excludes audit fields (readonly_fields)
    - Replaces raw FK fields with natural-key columns when fk_natural_keys is set
    """
    entry: RegistryEntry = get_entry(model_label)

    from django.apps import apps as django_apps
    try:
        model_class = django_apps.get_model(*model_label.split("."))
        pk_field_name = model_class._meta.pk.name if model_class._meta.pk else None
    except Exception:
        pk_field_name = None

    readonly = set(entry.readonly_fields)
    columns = []

    for fname in entry.writable_fields:
        # Skip the model PK field
        if fname == pk_field_name:
            continue
        # Skip audit/readonly fields
        if fname in readonly:
            continue
        # Replace raw FK field with NK columns if available
        if fname in entry.fk_natural_keys:
            for csv_col in entry.fk_natural_keys[fname].values():
                if csv_col not in columns:
                    columns.append(csv_col)
        else:
            columns.append(fname)

    return columns


def get_column_metadata(model_label: str) -> dict[str, dict]:
    """
    Return per-column metadata for template generation.
    Keys are column names, values are dicts with: required (bool), description, example_value.
    """
    entry: RegistryEntry = get_entry(model_label)
    template_cols = get_template_columns(model_label)

    # Build a set of which original required fields map to which template columns
    # A template column is required if it comes from a required field
    required_nk_cols = set()
    for fname in entry.required_fields:
        if fname in entry.fk_natural_keys:
            for csv_col in entry.fk_natural_keys[fname].values():
                required_nk_cols.add(csv_col)

    required_raw = set(entry.required_fields) - set(entry.fk_natural_keys.keys())

    meta = {}
    for col in template_cols:
        is_required = col in required_raw or col in required_nk_cols
        meta[col] = {
            "required": is_required,
            "description": "Required" if is_required else "Optional",
            "example_value": "",
        }
    return meta
