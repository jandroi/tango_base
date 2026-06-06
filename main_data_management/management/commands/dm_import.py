"""
Management command: dm_import

Two-phase import: validate then (optionally) commit.

Usage:
    python manage.py dm_import <folder_name>
    python manage.py dm_import <folder_name> --mode replace
    python manage.py dm_import <folder_name> --dry-run      (validate only, no commit)
    python manage.py dm_import /absolute/path/to/folder
"""
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from main_data_management.models import DataImportJob
from main_data_management.services.importer import commit_job, validate_job
from main_data_management.services.registry import import_ordered


class Command(BaseCommand):
    help = "Import CSV/Excel files into the database using the registry contract."

    def add_arguments(self, parser):
        parser.add_argument(
            "folder",
            help=(
                "Folder name inside DATA_ROOT/imports/, or an absolute path "
                "to the directory containing the import files."
            ),
        )
        parser.add_argument(
            "--mode",
            choices=["append", "replace"],
            default="append",
            help="Import mode (default: append). replace deletes existing rows first.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate only — do not commit any rows to the database.",
        )
        parser.add_argument(
            "--no-confirm",
            action="store_true",
            help="Skip the replace-mode confirmation prompt.",
        )

    def handle(self, *args, **options):
        mode = options["mode"]
        dry_run = options["dry_run"]
        folder_arg = options["folder"]

        data_root = getattr(settings, "MAIN_DATA_MANAGEMENT_ROOT", None)

        # Resolve input folder
        candidate = Path(folder_arg)
        if candidate.is_absolute():
            input_folder = candidate
        else:
            if data_root is None:
                raise CommandError("MAIN_DATA_MANAGEMENT_ROOT is not set in settings.")
            input_folder = Path(data_root) / "imports" / folder_arg

        if not input_folder.exists():
            raise CommandError(f"Input folder does not exist: {input_folder}")

        # Confirm replace mode
        if mode == "replace" and not dry_run and not options["no_confirm"]:
            self.stdout.write(
                self.style.WARNING(
                    f"\n⚠  Replace mode will DELETE ALL DATA for each exported model!"
                    f"\nFolder: {input_folder}"
                )
            )
            answer = input("Type 'yes' to continue: ").strip().lower()
            if answer != "yes":
                self.stdout.write("Import cancelled.")
                return

        job = DataImportJob.objects.create(
            mode=mode,
            input_folder=str(input_folder),
            started_at=timezone.now(),
        )

        self.stdout.write(f"Import job created: {job.job_uuid}")
        self.stdout.write(f"Mode: {mode.upper()}  |  Dry-run: {dry_run}")
        self.stdout.write(f"Input: {input_folder}")
        self.stdout.write("-" * 60)

        # Phase 1 — validate
        self.stdout.write("Phase 1: Validating...")
        try:
            summary = validate_job(job, input_folder)
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"Validation error: {exc}"))
            raise

        total_errors = summary.get("total_errors", 0)
        if total_errors:
            self.stderr.write(
                self.style.ERROR(f"Validation found {total_errors} error(s):")
            )
            for label, info in summary.get("models", {}).items():
                if info.get("errors"):
                    self.stderr.write(f"  {label}: {info['errors']} error(s)")
            self.stderr.write("Run without --dry-run only when errors are resolved.")
            job.finished_at = timezone.now()
            job.save(update_fields=["finished_at"])
            return

        self.stdout.write(self.style.SUCCESS("Validation passed."))
        for label, info in summary.get("models", {}).items():
            status = info.get("status", "")
            rows = info.get("row_count", "-")
            self.stdout.write(f"  {label}: {rows} rows [{status}]")

        if dry_run:
            self.stdout.write(self.style.WARNING("[DRY RUN] Skipping commit phase."))
            job.status = "cancelled"
            job.finished_at = timezone.now()
            job.save(update_fields=["status", "finished_at"])
            return

        # Phase 2 — commit
        self.stdout.write("Phase 2: Committing...")
        try:
            commit_summary = commit_job(job, input_folder)
            job.finished_at = timezone.now()
            job.save(update_fields=["finished_at"])

            matched_files = int(commit_summary.get("matched_files", 0))
            total_imported = int(commit_summary.get("total_imported", 0))
            if matched_files == 0:
                expected = ", ".join(f"{entry.table_name}.csv/.xlsx" for entry in import_ordered())
                self.stdout.write(self.style.WARNING(
                    "No matching import files found. "
                    f"Expected filenames: {expected}"
                ))
            else:
                self.stdout.write(self.style.SUCCESS(
                    f"Import complete. {total_imported} rows imported."
                ))
            for label, info in commit_summary.get("models", {}).items():
                self.stdout.write(f"  {label}: {info.get('row_count', 0)} rows")

        except Exception as exc:
            job.finished_at = timezone.now()
            job.save(update_fields=["finished_at"])
            self.stderr.write(self.style.ERROR(f"Commit failed: {exc}"))
            raise
