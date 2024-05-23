import datetime

from django.conf import settings
from django.db import models

from scarletbanner.users.models import User
from wiki.permission_levels import PermissionLevel


class WikiPage(models.Model):
    @property
    def latest(self) -> "Revision":
        return self.revisions.order_by("-timestamp", "-id").first()

    @property
    def original(self) -> "Revision":
        return self.revisions.order_by("timestamp", "id").first()

    @property
    def title(self) -> str:
        return self.latest.title

    @property
    def body(self) -> str:
        return self.latest.body

    @property
    def owner(self) -> User or None:
        return self.latest.owner

    @property
    def read(self) -> str:
        return self.latest.read

    @property
    def write(self) -> str:
        return self.latest.write

    @property
    def updated(self) -> datetime:
        return self.latest.timestamp

    @property
    def created(self) -> datetime:
        return self.original.timestamp

    @property
    def created_by(self) -> User:
        return self.original.editor

    @property
    def editors(self) -> list[User]:
        return [revision.editor for revision in self.revisions.all()]

    def __str__(self) -> str:
        return self.latest.title

    def evaluate_permission(self, permission: str, user: User = None) -> bool:
        is_admin = user is not None and user.is_staff
        is_owner = self.owner == user
        is_editor = user in self.editors

        match permission:
            case PermissionLevel.PUBLIC.value:
                return True
            case PermissionLevel.MEMBERS_ONLY.value:
                return user is not None
            case PermissionLevel.EDITORS_ONLY.value:
                return is_editor or is_admin or is_owner
            case PermissionLevel.OWNER_ONLY.value:
                return is_admin or is_owner
            case _:
                return is_admin

    def can_read(self, user: User = None) -> bool:
        return self.evaluate_permission(self.read, user)

    def can_write(self, to: str, user: User = None) -> bool:
        can_read = self.can_read(user)
        can_write_before = self.evaluate_permission(self.write, user)
        can_write_after = self.evaluate_permission(to, user)
        return can_read and can_write_before and can_write_after

    def update(self, title, body, editor, read: PermissionLevel, write: PermissionLevel, owner=None) -> None:
        if not self.can_write(write.value, editor):
            return

        Revision.objects.create(
            title=title, body=body, page=self, editor=editor, read=read.value, write=write.value, owner=owner
        )

    def patch(
        self, editor, title=None, body=None, read: PermissionLevel = None, write: PermissionLevel = None, owner=None
    ) -> None:
        patch_title = self.title if title is None else title
        patch_body = self.body if body is None else body
        patch_owner = self.owner if owner is None else owner
        patch_read = self.read if read is None else read.value
        patch_write = self.write if write is None else write.value

        if not self.can_write(patch_write, editor):
            return

        Revision.objects.create(
            title=patch_title,
            body=patch_body,
            page=self,
            editor=editor,
            read=patch_read,
            write=patch_write,
            owner=patch_owner,
        )

    @classmethod
    def create(
        cls,
        title,
        body,
        editor,
        read: PermissionLevel = PermissionLevel.PUBLIC,
        write: PermissionLevel = PermissionLevel.PUBLIC,
        owner=None,
    ) -> "WikiPage":
        page = cls.objects.create()
        Revision.objects.create(
            page=page,
            title=title,
            body=body,
            editor=editor,
            read=read.value,
            write=write.value,
            owner=owner,
        )
        return page


class Revision(models.Model):
    SECURITY_CHOICES = [
        (PermissionLevel.PUBLIC.value, "Public"),
        (PermissionLevel.MEMBERS_ONLY.value, "Members only"),
        (PermissionLevel.EDITORS_ONLY.value, "Editors only"),
        (PermissionLevel.OWNER_ONLY.value, "Owner only"),
        (PermissionLevel.ADMIN_ONLY.value, "Admins only"),
    ]

    title = models.CharField(max_length=255)
    body = models.TextField(null=True, blank=True)
    page = models.ForeignKey(WikiPage, related_name="revisions", on_delete=models.CASCADE)
    editor = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="revisions", on_delete=models.CASCADE)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="owned_pages", on_delete=models.CASCADE, null=True, blank=True
    )
    read = models.CharField(max_length=20, choices=SECURITY_CHOICES, default=PermissionLevel.PUBLIC.value)
    write = models.CharField(max_length=20, choices=SECURITY_CHOICES, default=PermissionLevel.PUBLIC.value)
    timestamp = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.title
