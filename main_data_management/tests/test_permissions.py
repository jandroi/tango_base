"""
Permission tests.

Verifies:
1. Unauthenticated users cannot access export/import endpoints.
2. Authenticated users without permissions are blocked.
3. Permission helpers correctly reflect user permissions.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from main_data_management.permissions import (
    CAN_EXPORT_DATA,
    CAN_IMPORT_VALIDATE,
    CAN_IMPORT_COMMIT,
    CAN_IMPORT_REPLACE,
    user_can_export,
    user_can_validate,
    user_can_commit,
    user_can_replace,
)

User = get_user_model()


class PermissionHelperTest(TestCase):
    def setUp(self):
        self.plain_user = User.objects.create_user(
            email="plain@test.com", password="pass123"
        )

    def test_anonymous_user_cannot_export(self):
        class AnonUser:
            is_authenticated = False
            def has_perm(self, perm): return False

        self.assertFalse(user_can_export(AnonUser()))

    def test_plain_user_lacks_permissions(self):
        self.assertFalse(user_can_export(self.plain_user))
        self.assertFalse(user_can_validate(self.plain_user))
        self.assertFalse(user_can_commit(self.plain_user))
        self.assertFalse(user_can_replace(self.plain_user))

    def test_superuser_has_all_permissions(self):
        su = User.objects.create_superuser(
            email="super@test.com", password="pass123"
        )
        self.assertTrue(user_can_export(su))
        self.assertTrue(user_can_validate(su))
        self.assertTrue(user_can_commit(su))
        self.assertTrue(user_can_replace(su))


class ViewAuthenticationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.plain_user = User.objects.create_user(
            email="view@test.com", password="pass123"
        )

    def test_unauthenticated_dashboard_redirects_to_login(self):
        url = reverse("data_management:dashboard")
        response = self.client.get(url)
        self.assertIn(response.status_code, [302, 301])
        self.assertIn("/users/login/", response["Location"])

    def test_authenticated_no_permission_export_returns_403(self):
        self.client.login(email="view@test.com", password="pass123")
        url = reverse("data_management:export")
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)

    def test_authenticated_no_permission_import_returns_403(self):
        self.client.login(email="view@test.com", password="pass123")
        url = reverse("data_management:import")
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
