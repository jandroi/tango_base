"""
Exporter tests.

Verifies:
1. Only allowlisted (export_enabled) models are exported.
2. Generated CSV files and manifest exist after export.
3. Row counts in the manifest match the DB.
4. Scope filtering works for property and brand.
"""
import csv
import json
import tempfile
from pathlib import Path

from django.test import TestCase

from app_brand_standard.models import Brand, PropertyStandardsCatalog
from app_hospitality_core.models import Property
from main_data_management.services.exporter import run_export
from main_data_management.services.registry import export_enabled_entries


class ExporterFileOutputTest(TestCase):
    def setUp(self):
        self.brand = Brand.objects.create(brand_name="Test Brand", brand_code="TB")

    def test_manifest_created(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_folder = Path(tmpdir)
            run_export(output_folder)
            manifest_path = output_folder / "manifest.json"
            self.assertTrue(manifest_path.exists(), "manifest.json was not created")

    def test_csv_files_created_for_all_export_enabled_models(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_folder = Path(tmpdir)
            run_export(output_folder)
            for entry in export_enabled_entries():
                csv_path = output_folder / f"{entry.table_name}.csv"
                self.assertTrue(
                    csv_path.exists(),
                    f"Expected CSV file not found: {csv_path.name}",
                )

    def test_no_excel_files_created(self):
        """Export always produces CSV only — no XLSX files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_folder = Path(tmpdir)
            run_export(output_folder)
            for entry in export_enabled_entries():
                self.assertFalse((output_folder / f"{entry.table_name}.xlsx").exists())


class ExporterRowCountTest(TestCase):
    def setUp(self):
        self.brand1 = Brand.objects.create(brand_name="Alpha", brand_code="AL")
        self.brand2 = Brand.objects.create(brand_name="Beta", brand_code="BE")

    def test_manifest_row_count_matches_db(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_folder = Path(tmpdir)
            run_export(output_folder)

            brand_count_db = Brand.objects.count()
            manifest_path = output_folder / "manifest.json"
            manifest = json.loads(manifest_path.read_text())

            brand_entry_label = "app_brand_standard.Brand"
            self.assertIn(brand_entry_label, manifest["models"])
            self.assertEqual(
                manifest["models"][brand_entry_label]["row_count"],
                brand_count_db,
            )


class ExporterScopeFilterTest(TestCase):
    def setUp(self):
        self.brand = Brand.objects.create(brand_name="Filter Brand", brand_code="FB")
        self.property = Property.objects.create(
            property_code="FB-01",
            property_name="Filter Hotel",
            brand=self.brand,
        )

    def test_export_by_property_filters_property_rows(self):
        other_brand = Brand.objects.create(brand_name="Other Brand", brand_code="OB")
        Property.objects.create(property_code="OB-01", property_name="Other Hotel", brand=other_brand)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_folder = Path(tmpdir)
            run_export(output_folder, scope="property", scope_id=self.property.property_id)

            property_csv = output_folder / "app_hospitality_core_property.csv"
            with property_csv.open(newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))

            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["property_code"], "FB-01")

    def test_export_by_brand_filters_brand_rows(self):
        other_brand = Brand.objects.create(brand_name="Another Brand", brand_code="AB")

        with tempfile.TemporaryDirectory() as tmpdir:
            output_folder = Path(tmpdir)
            run_export(output_folder, scope="brand", scope_id=self.brand.brand_id)

            brand_csv = output_folder / "app_brand_standard_brand.csv"
            with brand_csv.open(newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))

            codes = [r["brand_code"] for r in rows]
            self.assertIn("FB", codes)
            self.assertNotIn("AB", codes)


class ExporterSerializationTest(TestCase):
    def test_property_fk_and_audit_fields_excluded(self):
        brand = Brand.objects.create(brand_name="Serialize Brand", brand_code="SB")
        Property.objects.create(
            property_code="SER-01",
            property_name="Serialize Hotel",
            brand=brand,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_folder = Path(tmpdir)
            run_export(output_folder)

            property_csv = output_folder / "app_hospitality_core_property.csv"
            with property_csv.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))

            self.assertEqual(len(rows), 1)
            row = rows[0]
            self.assertEqual(row["brand"], str(brand.brand_id))
            self.assertNotIn("created_at", row)
            self.assertNotIn("updated_at", row)
            self.assertNotIn("created_by", row)
            self.assertNotIn("updated_by", row)

    def test_standard_export_includes_hesb_and_brand_fields(self):
        brand = Brand.objects.create(brand_name="PropertyStandardsCatalog Export Brand", brand_code="SEB")
        property_obj = Property.objects.create(
            property_code="SER-STD",
            property_name="PropertyStandardsCatalog Export Hotel",
            brand=brand,
        )
        PropertyStandardsCatalog.objects.create(
            brand=brand,
            property=property_obj,
            group_code="D01",
            hotel_unit_type="Restaurant",
            hotel_unit_code="REST-01",
            product_name="DM Export Plate",
            brand_name="Churchill",
            brand_model="Profile WHVP651",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_folder = Path(tmpdir)
            run_export(output_folder)

            standard_csv = output_folder / "app_brand_standard_propertystandardscatalog.csv"
            with standard_csv.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))

            row = next(row for row in rows if row["product_name"] == "DM Export Plate")
            self.assertEqual(row["group_code"], "D01")
            self.assertEqual(row["hotel_unit_type"], "Restaurant")
            self.assertEqual(row["hotel_unit_code"], "REST-01")
            self.assertEqual(row["brand_name"], "Churchill")
            self.assertEqual(row["brand_model"], "Profile WHVP651")
