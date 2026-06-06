from django.urls import path

from . import views

app_name = "data_management"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("export/", views.ExportView.as_view(), name="export"),
    path("import/", views.ImportView.as_view(), name="import"),
    path("import/<uuid:job_uuid>/validate/", views.ValidateJobView.as_view(), name="validate_job"),
    path("import/<uuid:job_uuid>/commit/", views.CommitJobView.as_view(), name="commit_job"),
    path("jobs/import/<uuid:job_uuid>/", views.ImportJobDetailView.as_view(), name="import_job_detail"),
    path("jobs/import/<uuid:job_uuid>/errors.csv", views.ErrorReportDownloadView.as_view(), name="error_report"),
    path("template/<str:model_label>/", views.TemplateDownloadView.as_view(), name="template_download"),
]
