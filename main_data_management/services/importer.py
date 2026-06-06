"""
Importer — two-phase import: validate then commit.

Phase 1 (validate): Parse + validate rows, persist DataRowError records. No DB mutation
                    on business data.
Phase 2 (commit):   Transactional write in registry dependency order.
"""
import hashlib
import json
import re
import uuid
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.db import transaction

from .registry import import_ordered, RegistryEntry
from .schema import validate_columns
from .serializers import read_file, normalize_dataframe
from .validators import validate_rows


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def validate_job(import_job, input_folder: Path) -> dict:
    """
    Phase 1: parse every file in input_folder, run schema + row validation,
    persist DataRowError records, update job status.

    Returns summary dict.
    """
    from main_data_management.models import DataRowError  # local import avoids circular

    summary = {
        "models": {},
        "total_errors": 0,
        "valid": True,
        "severity": "success",
        "message": "Validation passed.",
    }
    has_fk_not_found = False

    import_job.status = "validating"
    import_job.save(update_fields=["status"])

    override_map = _load_override_map(input_folder)

    for entry in import_ordered():
        file_path = _find_file(input_folder, entry.table_name, override_map)
        if file_path is None:
            summary["models"][entry.model_label] = {"status": "skipped", "errors": 0}
            continue

        try:
            df = read_file(file_path)
        except Exception as exc:
            summary["models"][entry.model_label] = {
                "status": "parse_error",
                "error": str(exc),
                "errors": 1,
            }
            summary["total_errors"] += 1
            summary["valid"] = False
            continue

        # Schema validation
        schema_result = validate_columns(entry.model_label, list(df.columns))
        if not schema_result.is_valid:
            for msg in schema_result.errors():
                DataRowError.objects.create(
                    import_job=import_job,
                    model_label=entry.model_label,
                    row_number=0,
                    field_name=None,
                    error_code="SCHEMA_ERROR",
                    error_message=msg,
                )
            summary["models"][entry.model_label] = {
                "status": "schema_error",
                "errors": len(schema_result.missing_required),
            }
            summary["total_errors"] += len(schema_result.missing_required)
            summary["valid"] = False
            continue

        # Row validation
        rows = normalize_dataframe(df)
        val_result = validate_rows(entry.model_label, rows, mode=import_job.mode)
        for err in val_result.errors:
            if err.error_code == "FK_NOT_FOUND":
                has_fk_not_found = True
            DataRowError.objects.create(
                import_job=import_job,
                model_label=entry.model_label,
                row_number=err.row_number,
                field_name=err.field_name,
                error_code=err.error_code,
                error_message=err.error_message,
                payload_json=err.payload,
            )

        model_valid = val_result.is_valid
        summary["models"][entry.model_label] = {
            "status": "valid" if model_valid else "invalid",
            "row_count": len(rows),
            "errors": len(val_result.errors),
        }
        if not model_valid:
            summary["valid"] = False
        summary["total_errors"] += len(val_result.errors)

    import_job.status = "validated"
    if summary["total_errors"] > 0:
        summary["severity"] = "error"
        summary["message"] = f"Import validation found {summary['total_errors']} error(s)."
        if has_fk_not_found:
            summary["message"] += " Some referenced IDs do not exist (for example, Brand ID)."
    import_job.summary_json = summary
    import_job.save(update_fields=["status", "summary_json"])

    return summary


def commit_job(import_job, input_folder: Path, committed_by=None) -> dict:
    """
    Phase 2: transactional write of all valid files in dependency order.

    Replace mode deletes matched models in REVERSE import_order (children first,
    parents last) to avoid FK PROTECT constraint violations.

    committed_by: a MainUser instance whose identity is stamped on created_by /
                  updated_by for all AuditMixin models.
    """
    import_job.status = "committing"
    import_job.save(update_fields=["status"])

    summary = {
        "models": {},
        "total_imported": 0,
        "matched_files": 0,
        "severity": "success",
        "message": "",
    }

    try:
        from main_data_management.models import DataRowError  # local import avoids circular

        override_map = _load_override_map(input_folder)

        # Collect registry entries that have a matching file, in import_order.
        present_entries = [
            (entry, file_path)
            for entry in import_ordered()
            if (file_path := _find_file(input_folder, entry.table_name, override_map)) is not None
        ]

        with transaction.atomic():
            from .resolvers import resolve_rows as _resolve_rows

            # Replace mode — models WITHOUT natural_key_fields have no dedup key, so they are
            # deleted globally and re-inserted (in reverse dependency order to avoid FK errors).
            if import_job.mode == "replace":
                for entry, _ in reversed(present_entries):
                    if not entry.natural_key_fields:
                        model_class = apps.get_model(*entry.model_label.split("."))
                        model_class.objects.all().delete()

            # Write in forward dependency order.
            # Models WITH natural_key_fields are upserted (update-or-create), which preserves
            # their PKs so that child records keep their FK relationships intact.
            resolved_rows_cache: dict[str, list[dict]] = {}
            for entry, file_path in present_entries:
                summary["matched_files"] += 1
                df = read_file(file_path)
                rows = normalize_dataframe(df)
                rows, _ = _resolve_rows(entry, rows)
                resolved_rows_cache[entry.model_label] = rows

                count = _write_rows(entry, rows, committed_by=committed_by, mode=import_job.mode)
                summary["models"][entry.model_label] = {
                    "status": "imported",
                    "row_count": count,
                }
                summary["total_imported"] += count

            # Replace mode — delete records NOT covered by the upload (stragglers).
            # Done in reverse dependency order so children are removed before parents.
            if import_job.mode == "replace":
                for entry, _ in reversed(present_entries):
                    if entry.natural_key_fields:
                        _delete_stragglers(entry, resolved_rows_cache.get(entry.model_label, []))

        DataRowError.objects.filter(
            import_job=import_job,
            error_code="NO_ROWS_IMPORTED",
        ).delete()

        if summary["total_imported"] == 0:
            summary["severity"] = "warning"
            summary["expected_filenames"] = [
                f"{entry.table_name}.csv/.xlsx" for entry in import_ordered()
            ]
            if summary["matched_files"] == 0:
                summary["severity"] = "error"
                summary["message"] = (
                    "Import failed: no matching files found. "
                    "Select the entity type when uploading a single file, "
                    "or name ZIP contents after the template filenames."
                )
            else:
                summary["message"] = (
                    "No rows were imported. "
                    "Check required fields and referenced IDs (for example, Brand ID)."
                )

            DataRowError.objects.create(
                import_job=import_job,
                model_label="main_data_management.DataImportJob",
                row_number=0,
                field_name=None,
                error_code="NO_ROWS_IMPORTED",
                error_message=summary["message"],
                payload_json={
                    "matched_files": summary["matched_files"],
                    "total_imported": summary["total_imported"],
                    "expected_filenames": summary.get("expected_filenames", []),
                },
            )
            import_job.status = "no_data"
        else:
            summary["message"] = f"Import completed. {summary['total_imported']} rows imported."
            import_job.status = "completed"
    except Exception as exc:
        import_job.status = "failed"
        summary["severity"] = "error"
        summary["message"] = _friendly_import_exception_message(exc)
        summary["error"] = str(exc)
        raise
    finally:
        import_job.summary_json = summary
        import_job.save(update_fields=["status", "summary_json"])

    return summary


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_override_map(input_folder: Path) -> dict:
    """
    Load the optional model-label override sidecar written by ImportView when the
    user uploads a single file and selects the entity type in the form.

    Returns a dict mapping table_name → Path, or an empty dict if no sidecar exists.
    """
    from .registry import get_entry
    sidecar = input_folder / "_model_override.json"
    if not sidecar.exists():
        return {}
    try:
        data = json.loads(sidecar.read_text())
        model_label = data.get("model_label", "")
        filename = data.get("filename", "")
        if not model_label or not filename:
            return {}
        entry = get_entry(model_label)
        candidate = input_folder / filename
        if candidate.exists():
            return {entry.table_name: candidate}
    except Exception:
        pass
    return {}


def _find_file(folder: Path, table_name: str, override_map: dict | None = None) -> Path | None:
    if override_map and table_name in override_map:
        return override_map[table_name]
    for suffix in (".xlsx", ".csv"):
        candidate = folder / f"{table_name}{suffix}"
        if candidate.exists():
            return candidate
    return None


def _write_rows(entry: RegistryEntry, rows: list[dict], committed_by=None, mode: str = "append") -> int:
    """
    Build and write model instances from normalized rows.

    In append mode: bulk_create (existing behavior).
    In replace mode with natural_key_fields: update_or_create by natural key,
        preserving PKs so child FK relationships (e.g. HotelUnit → Building) survive.
    In replace mode without natural_key_fields: bulk_create (caller already deleted old rows).
    """
    model_class = apps.get_model(*entry.model_label.split("."))
    # Safety: never write readonly fields even if they exist in input files.
    writable = set(entry.writable_fields) - set(entry.readonly_fields)
    pk_field_name = model_class._meta.pk.name if model_class._meta.pk else None
    use_upsert = mode == "replace" and bool(entry.natural_key_fields)

    objects = []
    count = 0

    for row in rows:
        kwargs = {}
        for field_name in writable:
            if field_name not in row:
                continue
            val = row[field_name]
            if val is None:
                continue

            # Resolve FK fields
            if field_name in entry.fk_fields:
                related_label = entry.fk_fields[field_name]
                related_model = apps.get_model(*related_label.split("."))
                pk_val = _coerce_pk_for(val, related_model)
                try:
                    kwargs[field_name] = related_model.objects.get(pk=pk_val)
                except related_model.DoesNotExist:
                    # validation should have caught this; skip silently
                    continue
            else:
                kwargs[field_name] = val

        # For PropertyStandardsCatalog / BrandStandardsCatalog, do NOT set the ID — let the model auto-generate
        if entry.model_label == "app_brand_standard.PropertyStandardsCatalog":
            kwargs.pop("property_standards_catalog_id", None)
        elif entry.model_label == "app_brand_standard.BrandStandardsCatalog":
            kwargs.pop("brand_standards_catalog_id", None)

        # For PropertyConfiguration, derive property from the resolved building
        if entry.model_label == "app_hospitality_core.PropertyConfiguration" and "building" in kwargs:
            kwargs["property"] = kwargs["building"].property

        if use_upsert:
            # Upsert: update existing record in-place (preserving PK) or create new.
            # Never set the PK explicitly — let the DB assign it on create.
            kwargs.pop(pk_field_name, None)
            lookup = {f: kwargs.pop(f) for f in entry.natural_key_fields if f in kwargs}
            if not lookup:
                continue  # can't upsert without a key — skip row
            obj, created = model_class.objects.update_or_create(defaults=kwargs, **lookup)
            if committed_by is not None:
                audit_updates = []
                if created and hasattr(obj, "created_by_id"):
                    obj.created_by = committed_by
                    audit_updates.append("created_by")
                if hasattr(obj, "updated_by_id"):
                    obj.updated_by = committed_by
                    audit_updates.append("updated_by")
                if audit_updates:
                    obj.save(update_fields=audit_updates)
            count += 1
        else:
            obj = model_class(**kwargs)
            if committed_by is not None and hasattr(obj, "created_by_id"):
                obj.created_by = committed_by
                obj.updated_by = committed_by
            objects.append(obj)

    if objects:
        model_class.objects.bulk_create(objects, batch_size=500)
        count = len(objects)

    return count


def _delete_stragglers(entry: RegistryEntry, rows: list[dict]) -> None:
    """
    In replace mode: delete records whose natural key is NOT in the uploaded rows.
    Records that were upserted keep their PKs; records absent from the file are removed.
    """
    from django.db.models import Q
    model_class = apps.get_model(*entry.model_label.split("."))
    uploaded_q = Q()
    for row in rows:
        kwargs: dict = {}
        valid = True
        for fname in entry.natural_key_fields:
            val = row.get(fname)
            if val is None:
                valid = False
                break
            try:
                field_obj = model_class._meta.get_field(fname)
                kwargs[f"{fname}_id" if field_obj.is_relation else fname] = val
            except Exception:
                valid = False
                break
        if valid and kwargs:
            uploaded_q |= Q(**kwargs)

    if uploaded_q:
        model_class.objects.exclude(uploaded_q).delete()
    else:
        model_class.objects.all().delete()


def _coerce_pk_for(raw_value, model_class) -> object:
    pk_field = model_class._meta.pk
    if pk_field is None:
        return raw_value
    if hasattr(pk_field, "max_length"):
        return str(raw_value).strip()
    return int(float(str(raw_value)))


def _friendly_import_exception_message(exc: Exception) -> str:
    raw = str(exc)

    # SQLite / Django IntegrityError common shape:
    # "UNIQUE constraint failed: app_hospitality_core_property.property_id"
    if "UNIQUE constraint failed:" in raw:
        cols_part = raw.split("UNIQUE constraint failed:", 1)[1].strip()
        cols = [c.strip() for c in cols_part.split(",") if c.strip()]
        fields = [c.split(".")[-1] for c in cols]
        if len(fields) == 1:
            field_label = fields[0].replace("_", " ")
            return (
                f"Import failed: duplicate {field_label}. "
                "That value already exists. Leave ID blank for new records or use Replace mode."
            )
        return (
            "Import failed: duplicate values were found for a unique field. "
            "Leave ID/code columns blank for new records or use Replace mode."
        )

    if "Cannot delete some instances of model" in raw and "protected foreign keys" in raw:
        model_match = re.search(r"model '([^']+)'", raw)
        model_name = model_match.group(1) if model_match else "record"
        relation_matches = re.findall(r"'([A-Za-z0-9_]+\.[A-Za-z0-9_]+)'", raw)
        if relation_matches:
            rel_model, rel_field = relation_matches[0].split(".", 1)
            return (
                f"Import failed: Replace mode cannot delete {model_name} records because "
                f"they are referenced by {rel_model} records (field '{rel_field}'). "
                "Use Append mode, or delete/update dependent records first."
            )
        return (
            f"Import failed: Replace mode cannot delete {model_name} records because "
            "they are still referenced by other records. "
            "Use Append mode, or delete/update dependent records first."
        )

    if "FOREIGN KEY constraint failed" in raw:
        return (
            "Import failed: one or more referenced IDs do not exist. "
            "Import parent records first (for example, Brand before Property)."
        )

    if "NOT NULL constraint failed:" in raw:
        col = raw.split("NOT NULL constraint failed:", 1)[1].strip()
        field_label = col.split(".")[-1].replace("_", " ")
        return (
            f"Import failed: required value missing for {field_label}. "
            "Fill all required columns and try again."
        )

    return f"Import failed: {raw}"
