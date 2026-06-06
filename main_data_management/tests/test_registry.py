"""
Registry contract tests.

Verifies:
1. Every registry entry resolves to a valid Django model.
2. import_order values are unique and deterministic.
3. All declared writable/required fields exist on the model.
4. FK fields point to valid related models.
5. Helpers (get_entry, get_entry_by_table, import_ordered, export_enabled_entries) work correctly.
"""
from django.apps import apps
from django.test import TestCase

from main_data_management.services.registry import (
    REGISTRY,
    get_entry,
    get_entry_by_table,
    import_ordered,
    export_enabled_entries,
    all_model_labels,
)


class RegistryResolvesModelsTest(TestCase):
    def test_all_model_labels_resolve(self):
        """Each registry entry's model_label must point to a real Django model."""
        for entry in REGISTRY:
            with self.subTest(model=entry.model_label):
                app_label, model_name = entry.model_label.split(".")
                model_class = apps.get_model(app_label, model_name)
                self.assertIsNotNone(model_class)

    def test_all_table_names_match_meta(self):
        """Declared table_name must match model._meta.db_table."""
        for entry in REGISTRY:
            with self.subTest(model=entry.model_label):
                app_label, model_name = entry.model_label.split(".")
                model_class = apps.get_model(app_label, model_name)
                self.assertEqual(
                    entry.table_name,
                    model_class._meta.db_table,
                    f"table_name mismatch for {entry.model_label}",
                )


class RegistryImportOrderTest(TestCase):
    def test_import_order_is_unique(self):
        """No two entries should share the same import_order."""
        orders = [e.import_order for e in REGISTRY]
        self.assertEqual(len(orders), len(set(orders)), "Duplicate import_order values found")

    def test_import_ordered_returns_sorted(self):
        """import_ordered() must return entries in ascending import_order."""
        entries = import_ordered()
        orders = [e.import_order for e in entries]
        self.assertEqual(orders, sorted(orders))

    def test_export_enabled_entries_sorted(self):
        entries = export_enabled_entries()
        orders = [e.import_order for e in entries]
        self.assertEqual(orders, sorted(orders))


class RegistryFieldsExistOnModelTest(TestCase):
    def _get_model_field_names(self, model_label: str) -> set:
        app_label, model_name = model_label.split(".")
        model_class = apps.get_model(app_label, model_name)
        return {
            f.name
            for f in model_class._meta.get_fields()
            if not f.many_to_many and not f.one_to_many
        }

    def test_required_fields_exist(self):
        for entry in REGISTRY:
            model_fields = self._get_model_field_names(entry.model_label)
            for fname in entry.required_fields:
                with self.subTest(model=entry.model_label, field=fname):
                    self.assertIn(
                        fname,
                        model_fields,
                        f"Required field '{fname}' not found on {entry.model_label}",
                    )

    def test_writable_fields_exist(self):
        for entry in REGISTRY:
            model_fields = self._get_model_field_names(entry.model_label)
            for fname in entry.writable_fields:
                with self.subTest(model=entry.model_label, field=fname):
                    self.assertIn(
                        fname,
                        model_fields,
                        f"Writable field '{fname}' not found on {entry.model_label}",
                    )

    def test_readonly_fields_exist(self):
        for entry in REGISTRY:
            model_fields = self._get_model_field_names(entry.model_label)
            for fname in entry.readonly_fields:
                with self.subTest(model=entry.model_label, field=fname):
                    self.assertIn(
                        fname,
                        model_fields,
                        f"Readonly field '{fname}' not found on {entry.model_label}",
                    )


class RegistryFKFieldsTest(TestCase):
    def test_fk_fields_point_to_valid_models(self):
        for entry in REGISTRY:
            for fk_field, related_label in entry.fk_fields.items():
                with self.subTest(model=entry.model_label, fk=fk_field):
                    app_label, model_name = related_label.split(".")
                    related_model = apps.get_model(app_label, model_name)
                    self.assertIsNotNone(related_model)


class RegistryHelperTest(TestCase):
    def test_get_entry_known_label(self):
        entry = get_entry("app_brand_standard.Brand")
        self.assertEqual(entry.model_label, "app_brand_standard.Brand")

    def test_get_entry_unknown_label_raises(self):
        with self.assertRaises(KeyError):
            get_entry("nonexistent.Model")

    def test_get_entry_by_table(self):
        entry = get_entry_by_table("app_brand_standard_brand")
        self.assertEqual(entry.model_label, "app_brand_standard.Brand")

    def test_get_entry_by_table_unknown_raises(self):
        with self.assertRaises(KeyError):
            get_entry_by_table("no_such_table")

    def test_all_model_labels_returns_all(self):
        labels = all_model_labels()
        self.assertEqual(len(labels), len(REGISTRY))
        self.assertIn("app_brand_standard.Brand", labels)

    def test_main_users_not_in_registry(self):
        """main_users.MainUser must never be in the registry for safety."""
        labels = all_model_labels()
        self.assertNotIn("main_users.MainUser", labels)

    def test_hospitality_core_models_are_export_enabled(self):
        expected = {
            "app_hospitality_core.Property",
            "app_hospitality_core.Building",
            "app_hospitality_core.PropertyConfiguration",
            "app_hospitality_core.Guestroom",
            "app_hospitality_core.FnBOutlet",
            "app_hospitality_core.PublicArea",
            "app_hospitality_core.BOHUnit",
            "app_hospitality_core.AdministrativeOffice",
        }
        exported_labels = {entry.model_label for entry in export_enabled_entries()}
        self.assertTrue(expected.issubset(exported_labels))

    def test_standard_registry_includes_current_hesb_fields(self):
        entry = get_entry("app_brand_standard.PropertyStandardsCatalog")
        expected_fields = {
            "group_code",
            "hotel_unit_type",
            "hotel_unit_code",
            "brand_name",
            "brand_model",
        }
        self.assertTrue(expected_fields.issubset(set(entry.writable_fields)))
