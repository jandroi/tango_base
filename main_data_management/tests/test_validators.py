from django.test import TestCase

from app_brand_standard.models import Brand, PropertyStandardsCatalog
from app_hospitality_core.models import Property
from main_data_management.services.validators import validate_rows


class ValidatorErrorCodeTest(TestCase):
    def test_required_and_fk_errors_include_expected_codes_and_row_numbers(self):
        result = validate_rows(
            "app_hospitality_core.Property",
            [
                {
                    "property_code": "",
                    "property_name": "",
                    "brand": "999999",
                }
            ],
        )

        self.assertFalse(result.is_valid)
        self.assertEqual({err.row_number for err in result.errors}, {2})
        error_codes = {err.error_code for err in result.errors}
        self.assertIn("REQUIRED_FIELD_MISSING", error_codes)
        self.assertIn("FK_NOT_FOUND", error_codes)

    def test_invalid_fk_value_returns_fk_invalid_value(self):
        result = validate_rows(
            "app_hospitality_core.Property",
            [
                {
                    "property_code": "P-1",
                    "property_name": "Hotel",
                    "brand": "not-a-number",
                }
            ],
        )

        self.assertFalse(result.is_valid)
        self.assertTrue(any(err.error_code == "FK_INVALID_VALUE" for err in result.errors))


class ValidatorCharPrimaryKeyTest(TestCase):
    def test_standardfile_fk_accepts_char_pk_standard_id(self):
        brand = Brand.objects.create(brand_name="Brand", brand_code="B-CHAR")
        property_obj = Property.objects.create(
            property_code="PK-CHAR",
            property_name="PK Hotel",
            brand=brand,
        )
        standard = PropertyStandardsCatalog.objects.create(
            brand=brand,
            property=property_obj,
            product_name="Desk Lamp",
        )

        result = validate_rows(
            "app_brand_standard.PropertyStandardsCatalogFile",
            [
                {
                    "property_standards_catalog_entry": standard.property_standards_catalog_id,
                    "title": "Spec Sheet",
                    "file": "docs/spec.pdf",
                    "file_type": "SUBMITTAL",
                }
            ],
        )

        self.assertTrue(result.is_valid, msg=[e.error_message for e in result.errors])
