import uuid

from django.conf import settings
from django.db import models


class DataSchemaVersion(models.Model):
    schema_version_id = models.BigAutoField(primary_key=True)
    module_version = models.CharField(max_length=50, unique=True)
    registry_checksum = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"SchemaVersion {self.module_version}"


class DataImportJob(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("validating", "Validating"),
        ("validated", "Validated"),
        ("committing", "Committing"),
        ("completed", "Completed"),
        ("no_data", "No Data Imported"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    ]
    MODE_CHOICES = [
        ("append", "Append"),
        ("replace", "Replace"),
    ]

    import_job_id = models.BigAutoField(primary_key=True)
    job_uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    mode = models.CharField(max_length=10, choices=MODE_CHOICES, default="append")
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="import_jobs",
    )
    input_folder = models.CharField(max_length=500)
    summary_json = models.JSONField(default=dict, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"ImportJob {self.job_uuid} [{self.status}]"


class DataJobFile(models.Model):
    ROLE_CHOICES = [
        ("input", "Input"),
        ("output", "Output"),
        ("manifest", "Manifest"),
        ("error_report", "Error Report"),
    ]

    data_job_file_id = models.BigAutoField(primary_key=True)
    import_job = models.ForeignKey(
        DataImportJob,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="files",
    )
    file_role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    relative_path = models.CharField(max_length=500)
    checksum_sha256 = models.CharField(max_length=64)
    row_count = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"JobFile {self.relative_path} [{self.file_role}]"


class DataRowError(models.Model):
    data_row_error_id = models.BigAutoField(primary_key=True)
    import_job = models.ForeignKey(
        DataImportJob,
        on_delete=models.CASCADE,
        related_name="row_errors",
    )
    model_label = models.CharField(max_length=200)
    row_number = models.IntegerField()
    field_name = models.CharField(max_length=100, null=True, blank=True)
    error_code = models.CharField(max_length=50)
    error_message = models.TextField()
    payload_json = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["import_job", "row_number"]

    def __str__(self):
        return (
            f"RowError row={self.row_number} "
            f"field={self.field_name} [{self.error_code}]"
        )
