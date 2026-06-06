"""
Explicit permission names for data management actions.

Grant these via Django's permission system (Group or user-level).
"""

CAN_EXPORT_DATA = "main_data_management.can_export_data"
CAN_IMPORT_VALIDATE = "main_data_management.can_import_validate"
CAN_IMPORT_COMMIT = "main_data_management.can_import_commit"
CAN_IMPORT_REPLACE = "main_data_management.can_import_replace"


def user_can_export(user) -> bool:
    return user.is_authenticated and user.has_perm(CAN_EXPORT_DATA)


def user_can_validate(user) -> bool:
    return user.is_authenticated and user.has_perm(CAN_IMPORT_VALIDATE)


def user_can_commit(user) -> bool:
    return user.is_authenticated and user.has_perm(CAN_IMPORT_COMMIT)


def user_can_replace(user) -> bool:
    return user.is_authenticated and user.has_perm(CAN_IMPORT_REPLACE)
