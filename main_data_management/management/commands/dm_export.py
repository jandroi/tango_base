"""
Management command: dm_export

Exports all registry-approved models to the configured data root.

Usage:
    python manage.py dm_export
    python manage.py dm_export --format csv
    python manage.py dm_export --format excel
    python manage.py dm_export --format both       (default)
    python manage.py dm_export --output-folder /custom/path
"""
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from main_data_management.models import DataExportJob
from main_data_management.services.exporter import run_export


class Command(BaseCommand):
    help = "Export all registry-approved models to CSV/Excel files."

    def add_arguments(self, parser):
        parser.add_argument(
            "--format",
            choices=["csv", "excel", "both"],
            default="both",
            help="Output format (default: both)",
        )
        parser.add_argument(
            "--output-folder",
            default=None,
            help="Override output folder path (default: DATA_ROOT/exports/TIMESTAMP)",
        )

    def handle(self, *args, **options):
        fmt = options["format"]
        data_root = getattr(settings, "MAIN_DATA_MANAGEMENT_ROOT", None)
        if data_root is None:
            self.stderr.write(
                self.style.ERROR(
                    "MAIN_DATA_MANAGEMENT_ROOT is not set in settings."
                )
            )
            return

        if options["output_folder"]:
            output_folder = Path(options["output_folder"])
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_folder = Path(data_root) / "exports" / timestamp

        job = DataExportJob.objects.create(
            format=fmt,
            output_folder=str(output_folder),
            started_at=timezone.now(),
        )

        self.stdout.write(f"Starting export job {job.job_uuid}...")
        self.stdout.write(f"Output: {output_folder}")

        try:
            summary = run_export(job, output_folder, fmt=fmt)
            job.finished_at = timezone.now()
            job.save(update_fields=["finished_at"])

            self.stdout.write(self.style.SUCCESS(
                f"Export complete. {summary['total_rows']} rows exported."
            ))
            for label, info in summary.get("models", {}).items():
                self.stdout.write(f"  {label}: {info.get('row_count', 0)} rows")
            self.stdout.write(f"Manifest: {summary.get('manifest', 'N/A')}")

        except Exception as exc:
            job.finished_at = timezone.now()
            job.save(update_fields=["finished_at"])
            self.stderr.write(self.style.ERROR(f"Export failed: {exc}"))
            raise
