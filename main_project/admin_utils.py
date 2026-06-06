class ShowAllFieldsAdminMixin:
    """
    Render every concrete and many-to-many model field in the admin form.

    Non-editable model fields are surfaced as readonly automatically so newly
    added schema fields do not disappear behind stale `fieldsets` definitions.
    """

    def _all_model_field_names(self):
        concrete_fields = [field.name for field in self.model._meta.concrete_fields]
        many_to_many_fields = [field.name for field in self.model._meta.many_to_many]
        return concrete_fields + many_to_many_fields

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        for field in self.model._meta.concrete_fields:
            if not field.editable and field.name not in readonly_fields:
                readonly_fields.append(field.name)
        return tuple(readonly_fields)

    def get_fields(self, request, obj=None):
        fields = list(self._all_model_field_names())
        for field_name in self.get_readonly_fields(request, obj):
            if field_name not in fields:
                fields.append(field_name)
        return tuple(fields)

    def get_fieldsets(self, request, obj=None):
        return ((None, {"fields": self.get_fields(request, obj)}),)
