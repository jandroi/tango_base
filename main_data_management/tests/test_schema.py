"""
Schema validation tests.

Verifies:
1. Valid file columns pass validation.
2. Missing required columns fail with explicit errors.
3. Extra columns produce warnings.
4. Missing optional columns produce warnings but don't fail.
"""
from django.test import TestCase

from main_data_management.services.schema import validate_columns, get_expected_columns
from main_data_management.services.registry import get_entry


class SchemaValidateColumnsTest(TestCase):
    MODEL = "app_brand_standard.Brand"

    def _required_cols(self):
        return list(get_entry(self.MODEL).required_fields)

    def _writable_cols(self):
        return list(get_entry(self.MODEL).writable_fields)

    def test_all_writable_columns_pass(self):
        result = validate_columns(self.MODEL, self._writable_cols())
        self.assertTrue(result.is_valid)
        self.assertEqual(result.missing_required, [])
        self.assertEqual(result.extra_columns, [])

    def test_required_columns_only_pass(self):
        result = validate_columns(self.MODEL, self._required_cols())
        self.assertTrue(result.is_valid)

    def test_missing_required_column_fails(self):
        cols = [c for c in self._writable_cols() if c != "brand_name"]
        result = validate_columns(self.MODEL, cols)
        self.assertFalse(result.is_valid)
        self.assertIn("brand_name", result.missing_required)
        self.assertTrue(len(result.errors()) > 0)

    def test_extra_column_produces_warning(self):
        cols = self._writable_cols() + ["made_up_column"]
        result = validate_columns(self.MODEL, cols)
        self.assertIn("made_up_column", result.extra_columns)
        self.assertTrue(any("made_up_column" in w for w in result.warnings()))

    def test_missing_optional_column_produces_warning(self):
        entry = get_entry(self.MODEL)
        optional = [
            c for c in entry.writable_fields
            if c not in entry.required_fields
        ]
        if not optional:
            self.skipTest("No optional columns for this model")
        cols = list(entry.required_fields)
        result = validate_columns(self.MODEL, cols)
        self.assertTrue(result.is_valid)
        self.assertTrue(len(result.missing_writable) > 0)
        self.assertTrue(len(result.warnings()) > 0)

    def test_empty_columns_fails_if_required(self):
        result = validate_columns(self.MODEL, [])
        self.assertFalse(result.is_valid)
        for req in get_entry(self.MODEL).required_fields:
            self.assertIn(req, result.missing_required)


class SchemaGetExpectedColumnsTest(TestCase):
    def test_returns_writable_fields(self):
        cols = get_expected_columns("app_brand_standard.Brand")
        entry = get_entry("app_brand_standard.Brand")
        self.assertEqual(cols, list(entry.writable_fields))

    def test_unknown_label_raises(self):
        with self.assertRaises(KeyError):
            get_expected_columns("nonexistent.Model")


class SchemaPropertyTest(TestCase):
    MODEL = "app_hospitality_core.Property"

    def test_fk_columns_treated_as_known(self):
        entry = get_entry(self.MODEL)
        cols = list(entry.writable_fields)
        result = validate_columns(self.MODEL, cols)
        self.assertTrue(result.is_valid)
        # 'brand' should not be in extra_columns since it's in writable_fields
        self.assertNotIn("brand", result.extra_columns)


class SchemaStandardContractTest(TestCase):
    def test_standard_expected_columns_include_hesb_and_brand_fields(self):
        cols = get_expected_columns("app_brand_standard.PropertyStandardsCatalog")
        for field_name in (
            "group_code",
            "hotel_unit_type",
            "hotel_unit_code",
            "brand_name",
            "brand_model",
        ):
            with self.subTest(field=field_name):
                self.assertIn(field_name, cols)
