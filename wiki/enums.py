from enum import Enum


class PageType(Enum):
    PAGE = "page"
    CHARACTER = "character"


class PermissionLevel(Enum):
    PUBLIC = "public"
    MEMBERS_ONLY = "members"
    EDITORS_ONLY = "editors"
    OWNER_ONLY = "owner"
    ADMIN_ONLY = "admin"
