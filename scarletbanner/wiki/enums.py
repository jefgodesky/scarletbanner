from enum import Enum


class PermissionLevel(Enum):
    PUBLIC = "public"
    MEMBERS_ONLY = "members"
    EDITORS_ONLY = "editors"
    ADMIN_ONLY = "admin"

    @staticmethod
    def get_choices():
        return [
            (PermissionLevel.PUBLIC.value, "Public"),
            (PermissionLevel.MEMBERS_ONLY.value, "Members"),
            (PermissionLevel.EDITORS_ONLY.value, "Editors"),
            (PermissionLevel.ADMIN_ONLY.value, "Admin"),
        ]
