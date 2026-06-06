"""
Registry — canonical definition of all models allowed for bulk import/export.

Every data-model change that affects bulk I/O MUST update this file.
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class RegistryEntry:
    model_label: str           # e.g. "app_brand_standard.Brand"
    table_name: str            # physical DB table name
    import_order: int          # lower number imports first (dependency order)
    import_enabled: bool
    export_enabled: bool
    writable_fields: tuple     # fields written on import (excluding auto fields)
    required_fields: tuple     # fields that must be non-null on every row
    readonly_fields: tuple     # fields never written on import
    fk_fields: dict            # {field_name: "app_label.ModelName"}
    natural_key_fields: tuple = field(default_factory=tuple)  # for dedupe/upsert
    fk_natural_keys: dict = field(default_factory=dict, hash=False, compare=False)  # {fk_field: {django_lookup: csv_col}}


# ---------------------------------------------------------------------------
# Registry — ordered by import dependency
# ---------------------------------------------------------------------------

REGISTRY: tuple[RegistryEntry, ...] = (
    RegistryEntry(
        model_label="app_brand_standard.Brand",
        table_name="app_brand_standard_brand",
        import_order=1,
        import_enabled=True,
        export_enabled=True,
        writable_fields=(
            "brand_id",
            "brand_code",
            "brand_name",
            "brand_description",
            "brand_logo",
        ),
        required_fields=("brand_code", "brand_name"),
        readonly_fields=(),
        fk_fields={},
        natural_key_fields=("brand_code",),
        fk_natural_keys={},
    ),
    RegistryEntry(
        model_label="app_brand_standard.BrandStandardsCatalog",
        table_name="app_brand_standard_brandstandardscatalog",
        import_order=2,
        import_enabled=True,
        export_enabled=True,
        writable_fields=(
            # unit_type, unit_category, quantity_per_unit dropped in migration 0035;
            # assignment + quantity now live in BrandStandardApplicability rows
            # keyed by (BSC, BrandHotelUnitType). Old CSVs carrying these columns
            # are flagged as `extra_columns` by schema.validate_columns() and
            # produce a "Unknown column: '<name>' (will be ignored)" warning.
            "brand",
            "group_code",
            "hotel_unit_type",
            "hotel_unit_code",
            "product_name",
            "product_specifications",
            "unit_of_measure",
            "product_placement",
            "product_photo",
            "suggested_supplier",
            "brand_name",
            "brand_model",
            "estimated_cost",
        ),
        required_fields=("brand", "product_name"),
        readonly_fields=("brand_standards_catalog_id", "created_at", "updated_at", "created_by", "updated_by"),
        fk_fields={"brand": "app_brand_standard.Brand"},
        natural_key_fields=(),
        fk_natural_keys={"brand": {"brand_code": "brand_code"}},
    ),
    RegistryEntry(
        model_label="app_hospitality_core.Property",
        table_name="app_hospitality_core_property",
        import_order=3,
        import_enabled=True,
        export_enabled=True,
        writable_fields=(
            "property_id",
            "brand",
            "property_code",
            "property_name",
            "property_image",
        ),
        required_fields=("property_code", "property_name"),
        readonly_fields=("created_at", "updated_at", "created_by", "updated_by"),
        fk_fields={"brand": "app_brand_standard.Brand"},
        natural_key_fields=("property_code",),
        fk_natural_keys={"brand": {"brand_code": "brand_code"}},
    ),
    RegistryEntry(
        model_label="app_hospitality_core.Building",
        table_name="app_hospitality_core_building",
        import_order=4,
        import_enabled=True,
        export_enabled=True,
        writable_fields=(
            "building_id",
            "property",
            "building_code",
            "building_name",
        ),
        required_fields=("property", "building_code", "building_name"),
        readonly_fields=("created_at", "updated_at", "created_by", "updated_by"),
        fk_fields={"property": "app_hospitality_core.Property"},
        natural_key_fields=("property", "building_code"),
        fk_natural_keys={"property": {"property_code": "property_code"}},
    ),
    RegistryEntry(
        model_label="app_hospitality_core.PropertyConfiguration",
        table_name="app_hospitality_core_propertyconfiguration",
        import_order=5,
        import_enabled=True,
        export_enabled=True,
        writable_fields=(
            "property_configuration_id",
            "building",
            "hotel_unit_category",
            "unit_category",
            "display_name",
            "floor_number",
            "notes",
        ),
        required_fields=("building", "hotel_unit_category", "unit_category"),
        readonly_fields=("created_at", "updated_at", "created_by", "updated_by"),
        fk_fields={
            "building": "app_hospitality_core.Building",
            "hotel_unit_category": "app_hospitality_core.HotelUnitCategory",
        },
        natural_key_fields=("building", "unit_category"),
        fk_natural_keys={
            "building": {"building_code": "building_code", "property__property_code": "property_code"},
            "hotel_unit_category": {"slug": "slug"},
        },
    ),
    RegistryEntry(
        model_label="app_hospitality_core.Guestroom",
        table_name="app_hospitality_core_guestroom",
        import_order=6,
        import_enabled=True,
        export_enabled=True,
        writable_fields=(
            "property_configuration",
            "room_description",
            "bed_type",
            "orientation",
        ),
        required_fields=("property_configuration", "room_description", "bed_type", "orientation"),
        readonly_fields=("created_at", "updated_at", "created_by", "updated_by"),
        fk_fields={"property_configuration": "app_hospitality_core.PropertyConfiguration"},
        natural_key_fields=("property_configuration",),
        fk_natural_keys={},
    ),
    RegistryEntry(
        model_label="app_hospitality_core.FnBOutlet",
        table_name="app_hospitality_core_fnboutlet",
        import_order=7,
        import_enabled=True,
        export_enabled=True,
        writable_fields=(
            "property_configuration",
            "outlet_type",
            "standard_name",
            "branded_name",
        ),
        required_fields=("property_configuration", "outlet_type", "standard_name"),
        readonly_fields=("created_at", "updated_at", "created_by", "updated_by"),
        fk_fields={"property_configuration": "app_hospitality_core.PropertyConfiguration"},
        natural_key_fields=("property_configuration",),
        fk_natural_keys={},
    ),
    RegistryEntry(
        model_label="app_hospitality_core.PublicArea",
        table_name="app_hospitality_core_publicarea",
        import_order=8,
        import_enabled=True,
        export_enabled=True,
        writable_fields=(
            "property_configuration",
            "public_area_type",
        ),
        required_fields=("property_configuration", "public_area_type"),
        readonly_fields=("created_at", "updated_at", "created_by", "updated_by"),
        fk_fields={"property_configuration": "app_hospitality_core.PropertyConfiguration"},
        natural_key_fields=("property_configuration",),
        fk_natural_keys={},
    ),
    RegistryEntry(
        model_label="app_hospitality_core.BOHUnit",
        table_name="app_hospitality_core_bohunit",
        import_order=9,
        import_enabled=True,
        export_enabled=True,
        writable_fields=(
            "property_configuration",
            "boh_type",
        ),
        required_fields=("property_configuration", "boh_type"),
        readonly_fields=("created_at", "updated_at", "created_by", "updated_by"),
        fk_fields={"property_configuration": "app_hospitality_core.PropertyConfiguration"},
        natural_key_fields=("property_configuration",),
        fk_natural_keys={},
    ),
    RegistryEntry(
        model_label="app_hospitality_core.AdministrativeOffice",
        table_name="app_hospitality_core_administrativeoffice",
        import_order=10,
        import_enabled=True,
        export_enabled=True,
        writable_fields=(
            "property_configuration",
            "office_type",
        ),
        required_fields=("property_configuration", "office_type"),
        readonly_fields=("created_at", "updated_at", "created_by", "updated_by"),
        fk_fields={"property_configuration": "app_hospitality_core.PropertyConfiguration"},
        natural_key_fields=("property_configuration",),
        fk_natural_keys={},
    ),
    RegistryEntry(
        model_label="app_brand_standard.PropertyStandardsCatalog",
        table_name="app_brand_standard_propertystandardscatalog",
        import_order=11,
        import_enabled=True,
        export_enabled=True,
        writable_fields=(
            # property_standards_catalog_id is auto-generated; omit from writable on import.
            # unit_type, unit_category, quantity_per_unit dropped in migration 0042;
            # assignment + quantity now live on PropertyStandardApplicability rows keyed
            # by (PSC, BrandHotelUnitType). Old CSVs carrying these columns are flagged
            # as `extra_columns` by schema.validate_columns() and produce a
            # "Unknown column: '<name>' (will be ignored)" warning.
            "brand",
            "property",
            "brand_standards_catalog_entry",
            "group_code",
            "hotel_unit_type",
            "hotel_unit_code",
            "product_name",
            "product_specifications",
            "unit_of_measure",
            "product_placement",
            "product_photo",
            "suggested_supplier",
            "brand_name",
            "brand_model",
            "estimated_cost",
            "status",
            "comments",
        ),
        required_fields=("brand", "property", "product_name"),
        readonly_fields=("property_standards_catalog_id", "created_at", "updated_at", "created_by", "updated_by"),
        fk_fields={
            "brand": "app_brand_standard.Brand",
            "property": "app_hospitality_core.Property",
            "brand_standards_catalog_entry": "app_brand_standard.BrandStandardsCatalog",
        },
        natural_key_fields=(),
        fk_natural_keys={
            "brand": {"brand_code": "brand_code"},
            "property": {"property_code": "property_code"},
        },
    ),
    RegistryEntry(
        model_label="app_brand_standard.PropertyStandardsCatalogFile",
        table_name="app_brand_standard_propertystandardscatalogfile",
        import_order=12,
        import_enabled=True,
        export_enabled=True,
        writable_fields=(
            "standard_file_id",
            "property_standards_catalog_entry",
            "file_type",
            "title",
            "file",
            "description",
        ),
        required_fields=("property_standards_catalog_entry", "title", "file"),
        readonly_fields=("uploaded_at", "uploaded_by"),
        fk_fields={"property_standards_catalog_entry": "app_brand_standard.PropertyStandardsCatalog"},
        natural_key_fields=(),
        fk_natural_keys={},
    ),
)

# main_users.MainUser is intentionally excluded from default export/import.

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_by_label: dict[str, RegistryEntry] = {e.model_label: e for e in REGISTRY}
_by_table: dict[str, RegistryEntry] = {e.table_name: e for e in REGISTRY}


def get_entry(model_label: str) -> RegistryEntry:
    """Return registry entry by dot-notation model label. Raises KeyError if not found."""
    if model_label not in _by_label:
        raise KeyError(f"Model '{model_label}' is not in the data-management registry.")
    return _by_label[model_label]


def get_entry_by_table(table_name: str) -> RegistryEntry:
    """Return registry entry by DB table name."""
    if table_name not in _by_table:
        raise KeyError(f"Table '{table_name}' is not in the data-management registry.")
    return _by_table[table_name]


def import_ordered() -> tuple[RegistryEntry, ...]:
    """Return all import-enabled entries sorted by import_order."""
    return tuple(sorted(
        (e for e in REGISTRY if e.import_enabled),
        key=lambda e: e.import_order,
    ))


def export_enabled_entries() -> tuple[RegistryEntry, ...]:
    """Return all export-enabled entries sorted by import_order."""
    return tuple(sorted(
        (e for e in REGISTRY if e.export_enabled),
        key=lambda e: e.import_order,
    ))


def all_model_labels() -> tuple[str, ...]:
    return tuple(e.model_label for e in REGISTRY)
