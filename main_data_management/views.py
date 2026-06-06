"""
Data-management views.

Provides a simple dashboard UI with:
- Drag/drop upload for imports
- One-click export download (CSV, filterable by property or brand)
- Template CSV downloads for each importable model
"""
from __future__ import annotations

import csv
import io
import json
import shutil
import uuid
import zipfile
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import FileResponse, HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView, TemplateView

from .forms import ExportForm, ImportUploadForm
from .models import DataImportJob
from .permissions import (
    user_can_commit,
    user_can_export,
    user_can_replace,
    user_can_validate,
)
from .services import exporter, importer
from .services.registry import get_entry, import_ordered
from .services.schema import get_expected_columns, get_template_columns, get_column_metadata


DATA_ROOT = Path(
    getattr(
        settings,
        "MAIN_DATA_MANAGEMENT_ROOT",
        Path(settings.BASE_DIR) / "main_data_management" / "data",
    )
)


def _ensure_data_root() -> Path:
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    for folder in ("imports", "exports", "templates", "manifests"):
        (DATA_ROOT / folder).mkdir(parents=True, exist_ok=True)
    return DATA_ROOT


def _wants_json(request) -> bool:
    accept = request.headers.get("Accept", "").lower()
    return "application/json" in accept or request.headers.get("X-Requested-With") == "XMLHttpRequest"


def _safe_extract_zip(uploaded_file, destination: Path) -> None:
    with zipfile.ZipFile(uploaded_file) as archive:
        for member in archive.infolist():
            if member.is_dir():
                continue

            member_path = Path(member.filename)
            if member_path.is_absolute() or ".." in member_path.parts:
                raise ValueError("Invalid archive path detected in uploaded zip file.")

            target_path = destination / member_path
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member) as source, target_path.open("wb") as target:
                shutil.copyfileobj(source, target)


def _store_upload(uploaded_file, input_folder: Path) -> None:
    suffix = Path(uploaded_file.name).suffix.lower()
    if suffix not in {".zip", ".csv", ".xlsx"}:
        raise ValueError("Unsupported upload type. Use .zip, .csv, or .xlsx.")

    if suffix == ".zip":
        _safe_extract_zip(uploaded_file, input_folder)
        return

    target_path = input_folder / Path(uploaded_file.name).name
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with target_path.open("wb") as output:
        for chunk in uploaded_file.chunks():
            output.write(chunk)


def _build_export_archive(output_folder: Path) -> Path:
    archive_base = output_folder.parent / output_folder.name
    archive_path = shutil.make_archive(str(archive_base), "zip", root_dir=output_folder)
    return Path(archive_path)


def _flash_summary_message(request, summary: dict | None) -> None:
    if not summary:
        return
    message = summary.get("message")
    if not message:
        return

    severity = summary.get("severity", "info")
    if severity == "success":
        messages.success(request, message)
    elif severity == "warning":
        messages.warning(request, message)
    elif severity == "error":
        messages.error(request, message)
    else:
        messages.info(request, message)


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "main_data_management/dashboard.html"

    def get_context_data(self, **kwargs):
        from django.apps import apps

        ctx = super().get_context_data(**kwargs)
        ctx["recent_imports"] = DataImportJob.objects.order_by("-created_at")[:10]
        ctx["export_form"] = ExportForm()
        ctx["import_form"] = ImportUploadForm()
        ctx["can_export"] = user_can_export(self.request.user)
        ctx["can_validate"] = user_can_validate(self.request.user)
        ctx["can_replace"] = user_can_replace(self.request.user)
        ctx["importable_entries"] = list(import_ordered())

        # Populate scope pickers for the export form
        try:
            Property = apps.get_model("app_hospitality_core", "Property")
            ctx["properties"] = Property.objects.order_by("property_name").values(
                "property_id", "property_name", "property_code"
            )
        except LookupError:
            ctx["properties"] = []

        try:
            Brand = apps.get_model("app_brand_standard", "Brand")
            ctx["brands"] = Brand.objects.order_by("brand_name").values(
                "brand_id", "brand_name", "brand_code"
            )
        except LookupError:
            ctx["brands"] = []

        return ctx


class ExportView(LoginRequiredMixin, View):
    def post(self, request):
        if not user_can_export(request.user):
            return HttpResponseForbidden("Missing permission: can_export_data")

        data_root = _ensure_data_root()
        form = ExportForm(request.POST)

        scope = "all"
        scope_id = None
        if form.is_valid():
            scope = form.cleaned_data.get("scope", "all")
            scope_id = form.cleaned_data.get("scope_id") or None
            if scope == "all":
                scope_id = None

        timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
        output_folder = data_root / "exports" / timestamp

        try:
            exporter.run_export(output_folder, scope=scope, scope_id=scope_id)
        except Exception as exc:
            if _wants_json(request):
                return JsonResponse({"error": str(exc)}, status=500)
            messages.error(request, f"Export failed: {exc}")
            return redirect("data_management:dashboard")

        if _wants_json(request):
            return JsonResponse({"status": "completed", "scope": scope, "scope_id": scope_id})

        archive_path = _build_export_archive(output_folder)
        filename = f"data_export_{timestamp}.zip"
        return FileResponse(archive_path.open("rb"), as_attachment=True, filename=filename)


class ImportView(LoginRequiredMixin, View):
    def post(self, request):
        if not user_can_validate(request.user):
            return HttpResponseForbidden("Missing permission: can_import_validate")

        data_root = _ensure_data_root()
        mode = request.POST.get("mode", "append")
        if mode not in ("append", "replace"):
            mode = "append"
        if mode == "replace" and not user_can_replace(request.user):
            return HttpResponseForbidden("Missing permission: can_import_replace")

        uploaded_file = request.FILES.get("upload_file")
        if uploaded_file:
            folder_name = f"{timezone.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
            input_folder = data_root / "imports" / folder_name
            input_folder.mkdir(parents=True, exist_ok=True)

            try:
                _store_upload(uploaded_file, input_folder)
            except ValueError as exc:
                if _wants_json(request):
                    return JsonResponse({"error": str(exc)}, status=400)
                messages.error(request, str(exc))
                return redirect("data_management:dashboard")

            # When the user selected an entity type (single-file upload), write a sidecar
            # so the importer can map the file to the correct model without relying on filename.
            model_label = request.POST.get("model_label", "").strip()
            if model_label:
                try:
                    get_entry(model_label)  # validate the label exists in registry
                    sidecar = {
                        "model_label": model_label,
                        "filename": Path(uploaded_file.name).name,
                    }
                    (input_folder / "_model_override.json").write_text(
                        json.dumps(sidecar), encoding="utf-8"
                    )
                except KeyError:
                    pass  # unknown label; fall through to filename-based detection

            job = DataImportJob.objects.create(
                requested_by=request.user,
                mode=mode,
                input_folder=str(input_folder),
                started_at=timezone.now(),
            )

            validate_summary = {}

            try:
                validate_summary = importer.validate_job(job, input_folder)
                if validate_summary.get("valid"):
                    messages.success(
                        request,
                        "File validated successfully — review the summary below and confirm to import."
                    )
                else:
                    _flash_summary_message(request, validate_summary)
            except Exception as exc:
                job.refresh_from_db()
                if job.summary_json and job.summary_json.get("message"):
                    _flash_summary_message(request, job.summary_json)
                else:
                    messages.error(request, f"Import failed: {exc}")
                    job.summary_json = {"severity": "error", "message": f"Import failed: {exc}"}
                    job.save(update_fields=["summary_json"])
                if _wants_json(request):
                    return JsonResponse(
                        {
                            "job_uuid": str(job.job_uuid),
                            "status": job.status,
                            "error": str(exc),
                            "user_message": job.summary_json.get("message", f"Import failed: {exc}"),
                        },
                        status=500,
                    )
            finally:
                job.finished_at = timezone.now()
                job.save(update_fields=["finished_at"])

            if _wants_json(request):
                return JsonResponse(
                    {
                        "job_uuid": str(job.job_uuid),
                        "status": job.status,
                        "validate_summary": validate_summary,
                    }
                )
            return redirect("data_management:import_job_detail", job_uuid=job.job_uuid)

        # Backward-compatible folder-based mode for existing integrations.
        folder_name = request.POST.get("folder_name", "").strip()
        if not folder_name:
            if _wants_json(request):
                return JsonResponse({"error": "Missing upload_file or folder_name."}, status=400)
            messages.error(request, "Provide a file upload or a folder_name.")
            return redirect("data_management:dashboard")

        input_folder = data_root / "imports" / folder_name
        job = DataImportJob.objects.create(
            requested_by=request.user,
            mode=mode,
            input_folder=str(input_folder),
            started_at=timezone.now(),
        )

        if _wants_json(request):
            return JsonResponse({"job_uuid": str(job.job_uuid), "status": job.status})

        messages.info(request, "Import job created. Use validate/commit endpoints to execute it.")
        return redirect("data_management:import_job_detail", job_uuid=job.job_uuid)


class ValidateJobView(LoginRequiredMixin, View):
    def post(self, request, job_uuid):
        if not user_can_validate(request.user):
            return HttpResponseForbidden("Missing permission: can_import_validate")

        job = get_object_or_404(DataImportJob, job_uuid=job_uuid)
        input_folder = Path(job.input_folder)

        try:
            summary = importer.validate_job(job, input_folder)
        except Exception as exc:
            return JsonResponse({"error": str(exc)}, status=500)

        return JsonResponse({"job_uuid": str(job.job_uuid), "summary": summary})


class CommitJobView(LoginRequiredMixin, View):
    def post(self, request, job_uuid):
        if not user_can_commit(request.user):
            return HttpResponseForbidden("Missing permission: can_import_commit")

        job = get_object_or_404(DataImportJob, job_uuid=job_uuid)
        if job.mode == "replace" and not user_can_replace(request.user):
            return HttpResponseForbidden("Missing permission: can_import_replace")

        input_folder = Path(job.input_folder)

        try:
            summary = importer.commit_job(job, input_folder, committed_by=request.user)
        except Exception as exc:
            if _wants_json(request):
                return JsonResponse({"error": str(exc)}, status=500)
            messages.error(request, f"Import failed: {exc}")
            return redirect("data_management:import_job_detail", job_uuid=job.job_uuid)
        finally:
            job.finished_at = timezone.now()
            job.save(update_fields=["finished_at"])

        if _wants_json(request):
            return JsonResponse({"job_uuid": str(job.job_uuid), "summary": summary})

        _flash_summary_message(request, summary)
        return redirect("data_management:import_job_detail", job_uuid=job.job_uuid)


class ImportJobDetailView(LoginRequiredMixin, DetailView):
    model = DataImportJob
    template_name = "main_data_management/import_job_detail.html"
    slug_field = "job_uuid"
    slug_url_kwarg = "job_uuid"
    context_object_name = "job"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        job = self.object
        ctx["errors"] = job.row_errors.order_by("row_number")
        ctx["can_commit"] = user_can_commit(self.request.user)
        ctx["is_confirmable"] = (
            job.status == "validated"
            and bool(job.summary_json)
            and job.summary_json.get("valid", False)
        )
        ctx["has_errors"] = job.row_errors.exists()

        model_counts = []
        if job.summary_json and "models" in job.summary_json:
            from .services.registry import get_entry
            for label, model_data in job.summary_json["models"].items():
                if model_data.get("status") == "valid" and model_data.get("row_count", 0) > 0:
                    try:
                        entry = get_entry(label)
                        short_name = label.split(".")[-1]
                        model_counts.append({
                            "label": label,
                            "name": short_name,
                            "row_count": model_data["row_count"],
                        })
                    except KeyError:
                        pass
        ctx["model_counts"] = model_counts
        return ctx


class ErrorReportDownloadView(LoginRequiredMixin, View):
    """Download a CSV of all row errors for an import job."""

    def get(self, request, job_uuid):
        job = get_object_or_404(DataImportJob, job_uuid=job_uuid)
        errors = job.row_errors.order_by("row_number")

        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["row", "model", "field", "error_code", "message"])
        for err in errors:
            writer.writerow([
                err.row_number,
                err.model_label,
                err.field_name or "",
                err.error_code,
                err.error_message,
            ])
        buf.seek(0)

        response = HttpResponse(buf.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="import_errors_{job_uuid}.csv"'
        return response


class TemplateDownloadView(LoginRequiredMixin, View):
    """Return a pre-headered CSV template for a given importable model."""

    def get(self, request, model_label):
        # model_label uses dots; URL receives it as a path segment with dots replaced by slashes
        # We reconstruct the label from the URL kwargs — dots are passed URL-encoded or directly.
        try:
            entry = get_entry(model_label)
        except KeyError:
            from django.http import Http404
            raise Http404(f"No registry entry for '{model_label}'")

        columns = get_template_columns(model_label)
        metadata = get_column_metadata(model_label)

        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(columns)  # header row
        # Description row (prefixed with # so reader skips it)
        desc_row = []
        for col in columns:
            col_meta = metadata.get(col, {})
            desc = col_meta.get("description", "")
            desc_row.append(f"# {desc}" if desc else "#")
        writer.writerow(desc_row)
        buf.seek(0)

        response = HttpResponse(buf.getvalue(), content_type="text/csv")
        filename = f"{entry.table_name}_template.csv"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
