from enum import Enum


class PermissionLevel(Enum):
    PUBLIC = 100
    MEMBERS_ONLY = 300
    EDITORS_ONLY = 600
    OWNER_ONLY = 900
    ADMIN_ONLY = 999

    @staticmethod
    def get_choices():
        return [
            (PermissionLevel.PUBLIC.value, "Public"),
            (PermissionLevel.MEMBERS_ONLY.value, "Members only"),
            (PermissionLevel.EDITORS_ONLY.value, "Editors only"),
            (PermissionLevel.OWNER_ONLY.value, "Owners only"),
            (PermissionLevel.ADMIN_ONLY.value, "Administrator only"),
        ]
