"""
Importer tests.

Verifies:
1. validate phase writes DataRowError records without DB mutation.
2. commit phase writes rows in dependency order.
3. FK violations are captured as DataRowError records.
4. replace mode is correctly applied.
"""
import csv
import tempfile
from pathlib import Path

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.db.models.deletion import ProtectedError
from django.test import TestCase

from app_brand_standard.models import Brand, PropertyStandardsCatalog
from app_hospitality_core.models import Building, Property
from main_data_management.models import DataImportJob, DataRowError
from main_data_management.services.importer import validate_job, commit_job


def _write_csv(folder: Path, filename: str, rows: list[dict]) -> None:
    path = folder / filename
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


class ImporterValidatePhaseTest(TestCase):
    def _make_job(self, folder, mode="append"):
        return DataImportJob.objects.create(mode=mode, input_folder=str(folder))

    def test_validate_with_valid_brand_rows_creates_no_errors(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir)
            _write_csv(folder, "app_brand_standard_brand.csv", [
                {"brand_id": "1", "brand_code": "BX", "brand_name": "Brand X",
                 "brand_description": "", "brand_logo": ""},
            ])
            job = self._make_job(folder)
            summary = validate_job(job, folder)
            self.assertEqual(summary["total_errors"], 0)
            self.assertTrue(summary["valid"])
            self.assertEqual(DataRowError.objects.filter(import_job=job).count(), 0)

    def test_validate_missing_required_field_creates_row_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir)
            # brand_name is required but missing value
            _write_csv(folder, "app_brand_standard_brand.csv", [
                {"brand_id": "1", "brand_code": "BX", "brand_name": ""},
            ])
            job = self._make_job(folder)
            summary = validate_job(job, folder)
            self.assertFalse(summary["valid"])
            self.assertGreater(summary["total_errors"], 0)
            self.assertGreater(
                DataRowError.objects.filter(import_job=job).count(), 0
            )

    def test_validate_does_not_mutate_db(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir)
            _write_csv(folder, "app_brand_standard_brand.csv", [
                {"brand_id": "99", "brand_code": "NEW", "brand_name": "New Brand",
                 "brand_description": "", "brand_logo": ""},
            ])
            job = self._make_job(folder)
            brand_count_before = Brand.objects.count()
            validate_job(job, folder)
            self.assertEqual(Brand.objects.count(), brand_count_before,
                             "validate_job must not write brand rows to the DB")

    def test_validate_fk_violation_creates_row_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir)
            # Property references brand_id=9999 which doesn't exist
            _write_csv(folder, "app_hospitality_core_property.csv", [
                {
                    "property_id": "1", "brand": "9999",
                    "property_code": "P1", "property_name": "Hotel One",
                },
            ])
            job = self._make_job(folder)
            validate_job(job, folder)
            fk_errors = DataRowError.objects.filter(
                import_job=job, error_code="FK_NOT_FOUND"
            )
            self.assertGreater(fk_errors.count(), 0)

    def test_validate_empty_csv_is_parse_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir)
            (folder / "app_brand_standard_brand.csv").write_text("", encoding="utf-8")

            job = self._make_job(folder)
            summary = validate_job(job, folder)

            self.assertFalse(summary["valid"])
            self.assertEqual(summary["total_errors"], 1)
            self.assertEqual(
                summary["models"]["app_brand_standard.Brand"]["status"],
                "parse_error",
            )

    def test_validate_missing_required_column_records_schema_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir)
            _write_csv(folder, "app_brand_standard_brand.csv", [
                {"brand_code": "SCHEMA-ONLY"},
            ])

            job = self._make_job(folder)
            summary = validate_job(job, folder)

            self.assertFalse(summary["valid"])
            errors = DataRowError.objects.filter(
                import_job=job,
                model_label="app_brand_standard.Brand",
                error_code="SCHEMA_ERROR",
            )
            self.assertEqual(errors.count(), 1)
            self.assertEqual(errors.first().row_number, 0)
            self.assertEqual(
                summary["models"]["app_brand_standard.Brand"]["status"],
                "schema_error",
            )


class ImporterCommitPhaseTest(TestCase):
    def _make_job(self, folder, mode="append"):
        return DataImportJob.objects.create(mode=mode, input_folder=str(folder))

    def test_commit_creates_brand_rows(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir)
            _write_csv(folder, "app_brand_standard_brand.csv", [
                {"brand_id": "", "brand_code": "CB", "brand_name": "Commit Brand",
                 "brand_description": "", "brand_logo": ""},
            ])
            job = self._make_job(folder)
            validate_job(job, folder)
            job.status = "validated"
            job.save(update_fields=["status"])

            before = Brand.objects.count()
            commit_job(job, folder)
            self.assertEqual(Brand.objects.count(), before + 1)
            self.assertTrue(Brand.objects.filter(brand_code="CB").exists())

    def test_commit_dependency_order(self):
        """Brand must exist before Property can be committed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir)
            _write_csv(folder, "app_brand_standard_brand.csv", [
                {"brand_id": "", "brand_code": "ORD", "brand_name": "Order Brand",
                 "brand_description": "", "brand_logo": ""},
            ])
            job = self._make_job(folder)
            validate_job(job, folder)
            job.status = "validated"
            job.save(update_fields=["status"])
            commit_job(job, folder)

            brand = Brand.objects.get(brand_code="ORD")
            # Now import a property referencing that brand
            with tempfile.TemporaryDirectory() as tmpdir2:
                folder2 = Path(tmpdir2)
                _write_csv(folder2, "app_hospitality_core_property.csv", [
                    {
                        "property_id": "", "brand": str(brand.brand_id),
                        "property_code": "P-ORD", "property_name": "Ordered Hotel",
                        "property_image": "", "address": "", "postal_code": "",
                        "city": "", "country": "", "phone": "", "email": "",
                        "operator_company": "",
                    },
                ])
                job2 = self._make_job(folder2)
                validate_job(job2, folder2)
                job2.status = "validated"
                job2.save(update_fields=["status"])
                commit_job(job2, folder2)
                self.assertTrue(Property.objects.filter(property_code="P-ORD").exists())

    def test_commit_status_set_to_completed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir)
            _write_csv(folder, "app_brand_standard_brand.csv", [
                {"brand_id": "", "brand_code": "STC", "brand_name": "Status Check",
                 "brand_description": "", "brand_logo": ""},
            ])
            job = self._make_job(folder)
            validate_job(job, folder)
            job.status = "validated"
            job.save(update_fields=["status"])
            commit_job(job, folder)
            job.refresh_from_db()
            self.assertEqual(job.status, "completed")

    def test_commit_creates_standard_rows_with_current_model_fields(self):
        brand = Brand.objects.create(brand_code="STD", brand_name="PropertyStandardsCatalog Brand")
        property_obj = Property.objects.create(
            brand=brand,
            property_code="STD-PROP",
            property_name="Standards Hotel",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir)
            _write_csv(folder, "app_brand_standard_propertystandardscatalog.csv", [
                {
                    "brand": str(brand.brand_id),
                    "property": str(property_obj.property_id),
                    "manufacturer_code": "MFG-101",
                    "room_category": "Guestroom",
                    "subcategory": "Dinnerware",
                    "group_code": "D01",
                    "hotel_unit_type": "Restaurant",
                    "hotel_unit_code": "REST-01",
                    "product_name": "DM Import Plate",
                    "product_specifications": "Porcelain dinner plate",
                    "quantity_per_unit": "12",
                    "unit_of_measure": "pcs",
                    "product_placement": "Service shelf",
                    "product_photo": "",
                    "suggested_supplier": "Metalisteria Pylsa",
                    "brand_name": "Churchill",
                    "brand_model": "Profile WHVP651",
                    "estimated_cost": "14.50",
                    "status": "active",
                    "purchase_date": "",
                    "installation_date": "",
                    "comments": "Imported from data management",
                },
            ])
            job = self._make_job(folder)
            validate_job(job, folder)
            job.status = "validated"
            job.save(update_fields=["status"])

            commit_job(job, folder)

            standard = PropertyStandardsCatalog.objects.get(product_name="DM Import Plate")
            self.assertEqual(standard.group_code, "D01")
            self.assertEqual(standard.hotel_unit_type, "Restaurant")
            self.assertEqual(standard.hotel_unit_code, "REST-01")
            self.assertEqual(standard.brand_name, "Churchill")
            self.assertEqual(standard.brand_model, "Profile WHVP651")

    def test_commit_ignores_readonly_audit_columns_from_input(self):
        user = get_user_model().objects.create_user(
            email="audit-import@test.com",
            password="pass123",
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir)
            _write_csv(folder, "app_hospitality_core_property.csv", [
                {
                    "property_id": "",
                    "brand": "",
                    "property_code": "AUD-01",
                    "property_name": "Audit Import Hotel",
                    "created_at": "2000-01-01T00:00:00+00:00",
                    "updated_at": "2000-01-01T00:00:00+00:00",
                    "created_by": str(user.pk),
                    "updated_by": str(user.pk),
                },
            ])
            job = self._make_job(folder)
            validate_job(job, folder)
            job.status = "validated"
            job.save(update_fields=["status"])
            commit_job(job, folder)

            prop = Property.objects.get(property_code="AUD-01")
            self.assertIsNone(prop.created_by)
            self.assertIsNone(prop.updated_by)
            self.assertNotEqual(prop.created_at.year, 2000)
            self.assertNotEqual(prop.updated_at.year, 2000)

    def test_commit_with_no_matching_registry_files_marks_job_no_data(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir)
            _write_csv(folder, "not_a_registry_table.csv", [
                {"col_a": "x"},
            ])
            job = self._make_job(folder)
            validate_job(job, folder)
            job.status = "validated"
            job.save(update_fields=["status"])

            summary = commit_job(job, folder)
            job.refresh_from_db()

            self.assertEqual(summary["matched_files"], 0)
            self.assertEqual(summary["total_imported"], 0)
            self.assertEqual(job.status, "no_data")
            self.assertEqual(summary["severity"], "error")
            self.assertIn("no matching files found", summary["message"])
            self.assertTrue(
                DataRowError.objects.filter(
                    import_job=job,
                    error_code="NO_ROWS_IMPORTED",
                ).exists()
            )

    def test_commit_replace_mode_deletes_existing_rows_for_model(self):
        Brand.objects.create(brand_code="OLD", brand_name="Old Brand")

        with tempfile.TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir)
            _write_csv(folder, "app_brand_standard_brand.csv", [
                {
                    "brand_id": "",
                    "brand_code": "NEW",
                    "brand_name": "New Brand",
                    "brand_description": "",
                    "brand_logo": "",
                },
            ])
            job = self._make_job(folder, mode="replace")
            validate_job(job, folder)
            job.status = "validated"
            job.save(update_fields=["status"])

            commit_job(job, folder)

            self.assertTrue(Brand.objects.filter(brand_code="NEW").exists())
            self.assertFalse(Brand.objects.filter(brand_code="OLD").exists())
            self.assertEqual(Brand.objects.count(), 1)

    def test_commit_failure_marks_job_failed_and_rolls_back(self):
        Brand.objects.create(brand_code="DUP", brand_name="Existing Duplicate")

        with tempfile.TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir)
            _write_csv(folder, "app_brand_standard_brand.csv", [
                {
                    "brand_id": "",
                    "brand_code": "DUP",
                    "brand_name": "Conflicting",
                    "brand_description": "",
                    "brand_logo": "",
                },
                {
                    "brand_id": "",
                    "brand_code": "NEWC",
                    "brand_name": "Should Roll Back",
                    "brand_description": "",
                    "brand_logo": "",
                },
            ])
            job = self._make_job(folder)
            validate_job(job, folder)
            job.status = "validated"
            job.save(update_fields=["status"])

            with self.assertRaises(IntegrityError):
                commit_job(job, folder)

            job.refresh_from_db()
            self.assertEqual(job.status, "failed")
            self.assertIn("error", job.summary_json)
            self.assertIn("duplicate", job.summary_json.get("message", "").lower())
            self.assertFalse(Brand.objects.filter(brand_code="NEWC").exists())

    def test_commit_replace_with_protected_dependencies_has_user_friendly_message(self):
        prop = Property.objects.create(
            property_code="H01",
            property_name="Hotel Main",
        )
        Building.objects.create(
            property=prop,
            building_code="MAIN",
            building_name="Main",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir)
            _write_csv(folder, "app_hospitality_core_property.csv", [
                {
                    "property_id": "",
                    "brand": "",
                    "property_code": "H02",
                    "property_name": "Hotel Two",
                },
            ])
            job = self._make_job(folder, mode="replace")
            validate_job(job, folder)
            job.status = "validated"
            job.save(update_fields=["status"])

            with self.assertRaises(ProtectedError):
                commit_job(job, folder)

            job.refresh_from_db()
            self.assertEqual(job.status, "failed")
            self.assertIn("Replace mode cannot delete Property records", job.summary_json.get("message", ""))
            self.assertIn("Building", job.summary_json.get("message", ""))
