# main_data_management

Bulk import/export app with validation, job tracking, and permission gates.

## Entry Points

- UI: `/data_management/`
- Commands:
  - `python manage.py dm_export --format csv|excel|both`
  - `python manage.py dm_import <folder_or_absolute_path> --mode append|replace [--dry-run]`

## Workflow

- Import is two-phase: validate, then commit.
- UI import with file upload can auto-run validate and commit if the user has commit permission.
- Export writes files plus a manifest and can stream a zip download.

## Permissions

- `main_data_management.can_export_data`
- `main_data_management.can_import_validate`
- `main_data_management.can_import_commit`
- `main_data_management.can_import_replace`

## Registry Contract

Source of truth: `main_data_management/services/registry.py`.

Current registry includes:

- `app_brand_standard.Brand`
- `app_hospitality_core.Property`
- `app_hospitality_core.Building` (export)
- `app_hospitality_core.PropertyConfiguration` (export)
- `app_hospitality_core.Guestroom` (export)
- `app_hospitality_core.FnBOutlet` (export)
- `app_hospitality_core.PublicArea` (export)
- `app_hospitality_core.BOHUnit` (export)
- `app_hospitality_core.AdministrativeOffice` (export)
- `app_brand_standard.BrandStandardsCatalog`
- `app_brand_standard.PropertyStandardsCatalog`
- `app_brand_standard.PropertyStandardsCatalogFile`

## Model rename (2026-04)

The hospitality and brand-standards models were renamed to match the new
"catalog" vocabulary. Bulk import/export callers, saved CSV templates, and
scripts that referenced the old names must be updated.

| Old name                          | New name                                    |
|-----------------------------------|---------------------------------------------|
| `app_hospitality_core.HotelUnit`  | `app_hospitality_core.PropertyConfiguration`|
| `app_brand_standard.BrandStandard`| `app_brand_standard.BrandStandardsCatalog`  |
| `app_brand_standard.Standard`     | `app_brand_standard.PropertyStandardsCatalog`|
| `app_brand_standard.StandardFile` | `app_brand_standard.PropertyStandardsCatalogFile`|

Table / CSV filename renames that follow from the above:

- `app_hospitality_core_hotelunit.csv` → `app_hospitality_core_propertyconfiguration.csv`
- `app_brand_standard_brandstandard.csv` → `app_brand_standard_brandstandardscatalog.csv`
- `app_brand_standard_standard.csv` → `app_brand_standard_propertystandardscatalog.csv`
- `app_brand_standard_standardfile.csv` → `app_brand_standard_propertystandardscatalogfile.csv`

## Data Folders

Under `main_data_management/data/`:

- `imports/`
- `exports/`
- `manifests/`
- `templates/`
