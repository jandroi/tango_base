"""
Exporter — writes one CSV per registry-approved model into an output folder,
then emits a JSON manifest with row counts.

Exports are always CSV. Scope can be "all", "property", or "brand".
"""
import json
from datetime import datetime, timezone
from pathlib import Path

from django.apps import apps
from django.db.models.fields.files import FieldFile

from .registry import export_enabled_entries, RegistryEntry
from .serializers import write_csv


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_export(output_folder: Path, scope: str = "all", scope_id: int | None = None) -> dict:
    """
    Export registry-approved models to output_folder as CSV files.

    Args:
        output_folder: destination directory
        scope: "all" | "property" | "brand"
        scope_id: PK of the selected Property or Brand (ignored when scope="all")

    Returns:
        summary dict with row counts per model and manifest path.
    """
    output_folder.mkdir(parents=True, exist_ok=True)

    summary = {"models": {}, "scope": scope, "scope_id": scope_id, "total_rows": 0}

    for entry in export_enabled_entries():
        rows, count = _extract_rows(entry, scope=scope, scope_id=scope_id)

        csv_path = output_folder / f"{entry.table_name}.csv"
        write_csv(rows, csv_path)

        summary["models"][entry.model_label] = {
            "table": entry.table_name,
            "row_count": count,
        }
        summary["total_rows"] += count

    # Write manifest
    manifest_path = output_folder / "manifest.json"
    manifest = _build_manifest(summary, output_folder)
    manifest_path.write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    summary["manifest"] = str(manifest_path)

    return summary


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _extract_rows(entry: RegistryEntry, scope: str = "all", scope_id: int | None = None) -> tuple[list[dict], int]:
    """Extract model queryset as a list of plain dicts, applying scope filter."""
    model_class = apps.get_model(*entry.model_label.split("."))
    qs = model_class.objects.all()

    if scope_id is not None:
        if scope == "property":
            # The Property model itself — filter to the single selected property
            if entry.model_label == "app_hospitality_core.Property":
                qs = qs.filter(pk=scope_id)
            # Models with a direct property FK
            elif "property" in entry.fk_fields:
                qs = qs.filter(property_id=scope_id)
            # Models with an indirect property link via building
            elif _model_has_field(model_class, "building"):
                qs = qs.filter(building__property_id=scope_id)
            # Models with indirect link via property_configuration → building → property
            elif _model_has_field(model_class, "property_configuration"):
                qs = qs.filter(property_configuration__building__property_id=scope_id)
            # Brand and BrandStandardsCatalog are not filtered when exporting by property

        elif scope == "brand":
            # The Brand model itself — filter to the single selected brand
            if entry.model_label == "app_brand_standard.Brand":
                qs = qs.filter(pk=scope_id)
            elif "brand" in entry.fk_fields:
                qs = qs.filter(brand_id=scope_id)
            elif "property" in entry.fk_fields:
                qs = qs.filter(property__brand_id=scope_id)
            elif _model_has_field(model_class, "building"):
                qs = qs.filter(building__property__brand_id=scope_id)
            elif _model_has_field(model_class, "property_configuration"):
                qs = qs.filter(property_configuration__building__property__brand_id=scope_id)

    export_fields = list(entry.writable_fields)

    rows = []
    for obj in qs:
        row = {}
        for fname in export_fields:
            try:
                val = getattr(obj, fname)
                if hasattr(val, "pk") and not isinstance(val, (str, int, float, bool)):
                    val = val.pk
                elif isinstance(val, FieldFile):
                    val = val.name if val.name else None
                elif hasattr(val, "isoformat"):
                    val = val.isoformat()
            except AttributeError:
                val = None
            row[fname] = val
        rows.append(row)

    return rows, len(rows)


def _model_has_field(model_class, field_name: str) -> bool:
    return any(f.name == field_name for f in model_class._meta.get_fields())


def _build_manifest(summary: dict, output_folder: Path) -> dict:
    return {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "format": "csv",
        "scope": summary.get("scope", "all"),
        "scope_id": summary.get("scope_id"),
        "models": summary["models"],
        "total_rows": summary["total_rows"],
        "output_folder": str(output_folder),
    }
