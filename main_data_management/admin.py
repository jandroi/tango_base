from django.contrib import admin

from .models import (
    DataSchemaVersion,
    DataImportJob,
    DataJobFile,
    DataRowError,
)


@admin.register(DataSchemaVersion)
class DataSchemaVersionAdmin(admin.ModelAdmin):
    list_display = ("schema_version_id", "module_version", "registry_checksum", "created_at")
    readonly_fields = ("schema_version_id", "created_at")
    fieldsets = (
        (None, {
            'fields': ('schema_version_id', 'module_version', 'registry_checksum', 'created_at'),
        }),
    )


class DataRowErrorInline(admin.TabularInline):
    model = DataRowError
    extra = 0
    readonly_fields = (
        "model_label", "row_number", "field_name",
        "error_code", "error_message", "payload_json", "created_at",
    )
    can_delete = False


class DataJobFileInline(admin.TabularInline):
    model = DataJobFile
    extra = 0
    readonly_fields = (
        "file_role", "relative_path", "checksum_sha256", "row_count", "created_at",
    )
    can_delete = False


@admin.register(DataImportJob)
class DataImportJobAdmin(admin.ModelAdmin):
    list_display = (
        "import_job_id", "job_uuid", "status", "mode",
        "requested_by", "input_folder", "created_at",
    )
    list_filter = ("status", "mode")
    readonly_fields = ("import_job_id", "job_uuid", "created_at")
    inlines = [DataJobFileInline, DataRowErrorInline]
    fieldsets = (
        (None, {
            'fields': (
                'import_job_id', 'job_uuid', 'status', 'mode',
                'requested_by', 'input_folder', 'summary_json',
                'started_at', 'finished_at', 'created_at',
            ),
        }),
    )


@admin.register(DataJobFile)
class DataJobFileAdmin(admin.ModelAdmin):
    list_display = (
        "data_job_file_id", "import_job", "file_role", "relative_path",
        "checksum_sha256", "row_count", "created_at",
    )
    list_filter = ("file_role",)
    readonly_fields = ("data_job_file_id", "created_at")
    fieldsets = (
        (None, {
            'fields': (
                'data_job_file_id', 'import_job', 'file_role',
                'relative_path', 'checksum_sha256', 'row_count', 'created_at',
            ),
        }),
    )


@admin.register(DataRowError)
class DataRowErrorAdmin(admin.ModelAdmin):
    list_display = (
        "data_row_error_id", "import_job", "model_label",
        "row_number", "field_name", "error_code", "created_at",
    )
    list_filter = ("error_code", "model_label")
    readonly_fields = ("data_row_error_id", "created_at")
    fieldsets = (
        (None, {
            'fields': (
                'data_row_error_id', 'import_job', 'model_label',
                'row_number', 'field_name', 'error_code',
                'error_message', 'payload_json', 'created_at',
            ),
        }),
    )
