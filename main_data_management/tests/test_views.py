import io
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from main_data_management.models import DataImportJob

User = get_user_model()


class DataManagementViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="dm@test.com",
            password="pass123",
        )
        self.client.login(email="dm@test.com", password="pass123")

    def _grant_permission(self, codename: str, model_class) -> None:
        content_type = ContentType.objects.get_for_model(model_class)
        perm, _ = Permission.objects.get_or_create(
            codename=codename,
            content_type=content_type,
            defaults={"name": codename.replace("_", " ").title()},
        )
        self.user.user_permissions.add(perm)

    def test_export_json_success_when_user_has_export_permission(self):
        self._grant_permission("can_export_data", DataImportJob)
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("main_data_management.views.DATA_ROOT", Path(tmpdir)):
                response = self.client.post(
                    reverse("data_management:export"),
                    data={"scope": "all"},
                    HTTP_ACCEPT="application/json",
                )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("status", payload)
        self.assertEqual(payload["status"], "completed")

    def test_import_rejects_unsupported_upload_extension(self):
        self._grant_permission("can_import_validate", DataImportJob)
        bad_file = SimpleUploadedFile("bad.txt", b"not supported", content_type="text/plain")

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("main_data_management.views.DATA_ROOT", Path(tmpdir)):
                response = self.client.post(
                    reverse("data_management:import"),
                    data={"upload_file": bad_file, "mode": "append"},
                    HTTP_ACCEPT="application/json",
                )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Unsupported upload type", response.json()["error"])

    def test_import_replace_mode_requires_replace_permission(self):
        self._grant_permission("can_import_validate", DataImportJob)

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("main_data_management.views.DATA_ROOT", Path(tmpdir)):
                response = self.client.post(
                    reverse("data_management:import"),
                    data={"mode": "replace"},
                )

        self.assertEqual(response.status_code, 403)
        self.assertIn("can_import_replace", response.content.decode("utf-8"))

    def test_import_json_does_not_commit_when_user_lacks_commit_permission(self):
        self._grant_permission("can_import_validate", DataImportJob)
        csv_file = SimpleUploadedFile(
            "app_brand_standard_brand.csv",
            b"brand_code,brand_name\nNOCOMMIT,No Commit Brand\n",
            content_type="text/csv",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("main_data_management.views.DATA_ROOT", Path(tmpdir)):
                with patch(
                    "main_data_management.views.importer.validate_job",
                    return_value={"valid": True, "total_errors": 0},
                ):
                    with patch("main_data_management.views.importer.commit_job") as commit_mock:
                        response = self.client.post(
                            reverse("data_management:import"),
                            data={"upload_file": csv_file, "mode": "append"},
                            HTTP_ACCEPT="application/json",
                        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("commit_summary", response.json())
        commit_mock.assert_not_called()

    def test_import_json_returns_validate_summary_without_auto_commit(self):
        self._grant_permission("can_import_validate", DataImportJob)
        self._grant_permission("can_import_commit", DataImportJob)
        csv_file = SimpleUploadedFile(
            "app_brand_standard_brand.csv",
            b"brand_code,brand_name\nYESCOMMIT,Yes Commit Brand\n",
            content_type="text/csv",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("main_data_management.views.DATA_ROOT", Path(tmpdir)):
                with patch(
                    "main_data_management.views.importer.validate_job",
                    return_value={"valid": True, "total_errors": 0},
                ):
                    with patch(
                        "main_data_management.views.importer.commit_job",
                    ) as commit_mock:
                        response = self.client.post(
                            reverse("data_management:import"),
                            data={"upload_file": csv_file, "mode": "append"},
                            HTTP_ACCEPT="application/json",
                        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("validate_summary", response.json())
        commit_mock.assert_not_called()

    def test_import_ui_redirects_to_job_detail_after_validate(self):
        self._grant_permission("can_import_validate", DataImportJob)
        self._grant_permission("can_import_commit", DataImportJob)
        csv_file = SimpleUploadedFile(
            "not_a_registry_table.csv",
            b"col_a\nvalue\n",
            content_type="text/csv",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("main_data_management.views.DATA_ROOT", Path(tmpdir)):
                response = self.client.post(
                    reverse("data_management:import"),
                    data={"upload_file": csv_file, "mode": "append"},
                )

        self.assertEqual(response.status_code, 302)
        job = DataImportJob.objects.latest("created_at")
        self.assertIn(str(job.job_uuid), response["Location"])

    def test_import_zip_rejects_path_traversal(self):
        self._grant_permission("can_import_validate", DataImportJob)

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, mode="w") as archive:
            archive.writestr("../escape.csv", "brand_code,brand_name\nX,Escape\n")
        upload = SimpleUploadedFile(
            "payload.zip",
            buffer.getvalue(),
            content_type="application/zip",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("main_data_management.views.DATA_ROOT", Path(tmpdir)):
                response = self.client.post(
                    reverse("data_management:import"),
                    data={"upload_file": upload, "mode": "append"},
                    HTTP_ACCEPT="application/json",
                )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid archive path", response.json()["error"])
        self.assertEqual(DataImportJob.objects.count(), 0)

    def test_commit_endpoint_requires_replace_permission_for_replace_jobs(self):
        self._grant_permission("can_import_commit", DataImportJob)
        job = DataImportJob.objects.create(
            mode="replace",
            input_folder="C:/tmp/does-not-matter",
        )

        response = self.client.post(
            reverse("data_management:commit_job", kwargs={"job_uuid": job.job_uuid})
        )
        self.assertEqual(response.status_code, 403)
        self.assertIn("can_import_replace", response.content.decode("utf-8"))
