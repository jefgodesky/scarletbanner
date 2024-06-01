from enum import Enum


class PermissionLevel(Enum):
    PUBLIC = 100
    MEMBERS_ONLY = 300
    EDITORS_ONLY = 600
    ADMIN_ONLY = 999

    @staticmethod
    def get_choices():
        return [
            (PermissionLevel.PUBLIC.value, 100),
            (PermissionLevel.MEMBERS_ONLY.value, 300),
            (PermissionLevel.EDITORS_ONLY.value, 600),
            (PermissionLevel.ADMIN_ONLY.value, 999),
        ]
