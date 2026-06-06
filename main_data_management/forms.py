from django import forms

from .services.registry import import_ordered


def _importable_model_choices():
    """Return (model_label, human_name) pairs for all import-enabled registry entries."""
    # Human-readable labels for known model labels
    _labels = {
        "app_brand_standard.Brand": "Brand",
        "app_brand_standard.BrandStandardsCatalog": "Brand Standards Catalog Entry",
        "app_hospitality_core.Property": "Property",
        "app_hospitality_core.Building": "Building",
        "app_hospitality_core.PropertyConfiguration": "Property Configuration",
        "app_hospitality_core.Guestroom": "Guestroom (subtype)",
        "app_hospitality_core.FnBOutlet": "F&B Outlet (subtype)",
        "app_hospitality_core.PublicArea": "Public Area (subtype)",
        "app_hospitality_core.BOHUnit": "BOH Unit (subtype)",
        "app_hospitality_core.AdministrativeOffice": "Administrative Office (subtype)",
        "app_brand_standard.PropertyStandardsCatalog": "Property Standards Catalog Entry",
        "app_brand_standard.PropertyStandardsCatalogFile": "Property Standards Catalog File",
    }
    choices = [("", "--- Select entity type (required for single file upload) ---")]
    for entry in import_ordered():
        label = _labels.get(entry.model_label, entry.model_label)
        choices.append((entry.model_label, label))
    return choices


class ExportForm(forms.Form):
    SCOPE_CHOICES = [
        ("all", "All data"),
        ("property", "By Property"),
        ("brand", "By Brand"),
    ]
    scope = forms.ChoiceField(
        choices=SCOPE_CHOICES,
        initial="all",
        widget=forms.Select(attrs={"class": "form-select", "id": "export-scope"}),
    )
    scope_id = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput(attrs={"id": "export-scope-id"}),
    )


class ImportForm(forms.Form):
    MODE_CHOICES = [
        ("append", "Append (add new records)"),
        ("replace", "Replace (delete all first — DANGEROUS)"),
    ]
    folder_name = forms.CharField(
        max_length=200,
        required=False,
        help_text="Name of the folder inside data/imports/ containing the files to import.",
    )
    mode = forms.ChoiceField(choices=MODE_CHOICES, initial="append")


class ImportUploadForm(forms.Form):
    MODE_CHOICES = ImportForm.MODE_CHOICES

    upload_file = forms.FileField(
        required=True,
        help_text="Upload a .zip package containing multiple tables, or a single .csv/.xlsx file.",
        widget=forms.FileInput(
            attrs={
                "accept": ".zip,.csv,.xlsx",
                "class": "form-control",
            }
        ),
    )
    model_label = forms.ChoiceField(
        choices=[],  # populated in __init__ to avoid import-time registry access
        required=False,
        widget=forms.Select(attrs={"class": "form-select", "id": "import-model-label"}),
        help_text="Select the entity type when uploading a single .csv/.xlsx file. Not needed for ZIP uploads.",
    )
    mode = forms.ChoiceField(
        choices=MODE_CHOICES,
        initial="append",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["model_label"].choices = _importable_model_choices()
