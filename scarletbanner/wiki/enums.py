from enum import Enum


class PageType(Enum):
    PAGE = "page"
    TEMPLATE = "template"
    CHARACTER = "character"

    @staticmethod
    def get_choices():
        return [
            (PageType.PAGE.value, "Page"),
            (PageType.TEMPLATE.value, "Template"),
            (PageType.CHARACTER.value, "Character"),
        ]


class PermissionLevel(Enum):
    PUBLIC = "public"
    MEMBERS_ONLY = "members"
    EDITORS_ONLY = "editors"
    OWNER_ONLY = "owner"
    ADMIN_ONLY = "admin"

    @staticmethod
    def get_choices():
        return [
            (PermissionLevel.PUBLIC.value, "Public"),
            (PermissionLevel.MEMBERS_ONLY.value, "Members"),
            (PermissionLevel.EDITORS_ONLY.value, "Editors"),
            (PermissionLevel.OWNER_ONLY.value, "Owner"),
            (PermissionLevel.ADMIN_ONLY.value, "Admin"),
        ]
