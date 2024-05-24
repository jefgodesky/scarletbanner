import datetime

from django.conf import settings
from django.db import models
from django.db.models import F, Max, Q
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from slugify import slugify

from scarletbanner.users.models import User
from wiki.permission_levels import PermissionLevel


class WikiPage(models.Model):
    def __str__(self) -> str:
        return self.latest.title

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
    def slug(self) -> str:
        return self.latest.slug

    @property
    def unique_slug_element(self) -> str:
        parts = [part for part in self.slug.split("/")]
        return parts[-1]

    @property
    def body(self) -> str:
        return self.latest.body

    @property
    def owner(self) -> User or None:
        return self.latest.owner

    @property
    def parent(self) -> "WikiPage" or None:
        return self.latest.parent

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

    @property
    def children(self) -> list["WikiPage"]:
        latest_revisions = (
            Revision.objects.filter(parent=self)
            .annotate(latest_timestamp=Max("page__revisions__timestamp"))
            .filter(timestamp=F("latest_timestamp"))
        )
        return [rev.page for rev in latest_revisions]

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

    def update(
        self,
        title: str,
        body: str,
        editor: User,
        read: PermissionLevel,
        write: PermissionLevel,
        message: str,
        slug: str or None = None,
        parent: "WikiPage" = None,
        owner: User or None = None,
    ) -> None:
        if not self.can_write(write.value, editor):
            return

        slug = slugify(title) if slug is None else slug
        Revision.objects.create(
            title=title,
            slug=slug,
            body=body,
            page=self,
            editor=editor,
            read=read.value,
            write=write.value,
            message=message,
            owner=owner,
            parent=parent,
        )

    def patch(
        self,
        editor: User,
        message: str,
        title: str = None,
        slug: str = None,
        body: str = None,
        parent: "WikiPage" = None,
        owner: User or None = None,
        read: PermissionLevel = None,
        write: PermissionLevel = None,
    ) -> None:
        patch_title = self.title if title is None else title
        patch_slug = self.slug if slug is None else slug
        patch_body = self.body if body is None else body
        patch_parent = self.parent if parent is None else parent
        patch_owner = self.owner if owner is None else owner
        patch_read = self.read if read is None else read.value
        patch_write = self.write if write is None else write.value

        if not self.can_write(patch_write, editor):
            return

        Revision.objects.create(
            title=patch_title,
            slug=patch_slug,
            body=patch_body,
            parent=patch_parent,
            owner=patch_owner,
            page=self,
            editor=editor,
            read=patch_read,
            write=patch_write,
        )

    def reparent(self, editor: User, deleted: str, new_parent: "WikiPage" or None = None) -> None:
        none_message = "Reparenting to root"
        new_message = f"Reparenting to {new_parent}"
        message = none_message if new_parent is None else new_message
        slug = WikiPage.reslug_without_parent(self.slug, deleted)

        self.patch(
            editor=editor,
            message=message,
            parent=new_parent,
            slug=slug
        )

        for child in self.children:
            child.reparent(editor, deleted, new_parent=self)

    def destroy(self, editor: User) -> None:
        for child in self.children:
            child.reparent(editor, deleted=self.slug, new_parent=self.parent)
        super().delete()

    @classmethod
    def create(
        cls,
        title: str,
        body: str,
        editor: User,
        message: str = "Initial text",
        read: PermissionLevel = PermissionLevel.PUBLIC,
        write: PermissionLevel = PermissionLevel.PUBLIC,
        slug: str = None,
        parent: "WikiPage" or None = None,
        owner: User or None = None,
    ) -> "WikiPage":
        page = cls.objects.create()
        slug = slugify(title) if slug is None else slug
        Revision.objects.create(
            page=page,
            title=title,
            slug=slug,
            body=body,
            message=message,
            editor=editor,
            read=read.value,
            write=write.value,
            parent=parent,
            owner=owner,
        )
        return page

    @staticmethod
    def reslug_without_parent(slug: str, parent_slug: str) -> str:
        parent_parts = [part for part in parent_slug.split("/")]
        parent_unique = parent_parts[-1]
        parts = [part for part in slug.split("/")]
        parts = filter(lambda p: p != parent_unique, parts)
        return "/".join(parts)


class Revision(models.Model):
    SECURITY_CHOICES = [
        (PermissionLevel.PUBLIC.value, "Public"),
        (PermissionLevel.MEMBERS_ONLY.value, "Members only"),
        (PermissionLevel.EDITORS_ONLY.value, "Editors only"),
        (PermissionLevel.OWNER_ONLY.value, "Owner only"),
        (PermissionLevel.ADMIN_ONLY.value, "Admins only"),
    ]

    title = models.CharField(max_length=255)
    slug = models.CharField(max_length=255)
    body = models.TextField(null=True, blank=True)
    message = models.TextField(max_length=255)
    page = models.ForeignKey(WikiPage, related_name="revisions", on_delete=models.CASCADE)
    editor = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="revisions", on_delete=models.CASCADE)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="owned_pages", on_delete=models.CASCADE, null=True, blank=True
    )
    read = models.CharField(max_length=20, choices=SECURITY_CHOICES, default=PermissionLevel.PUBLIC.value)
    write = models.CharField(max_length=20, choices=SECURITY_CHOICES, default=PermissionLevel.PUBLIC.value)
    timestamp = models.DateTimeField(auto_now=True)
    parent = models.ForeignKey(WikiPage, on_delete=models.SET_NULL, null=True, blank=True)
    is_latest = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["slug"], condition=Q(is_latest=True), name="unique_page_slug")
        ]

    def __str__(self) -> str:
        return self.slug

    def save(self, *args, **kwargs):
        self.set_slug(self.slug)
        super().save(*args, **kwargs)

        if self.is_latest:
            self.page.revisions.exclude(pk=self.pk).update(is_latest=False)

    def set_slug(self, slug: str or None = None):
        root = self.title if slug is None else slug
        parts = [slugify(part) for part in root.split("/")]
        slug = "/".join(parts)

        if self.parent is not None:
            slug = f"{self.parent.slug}/{slug}"

        self.slug = slug


@receiver(pre_save, sender=Revision)
def set_latest_revision(sender, instance, **kwargs):
    if instance.pk is None:
        instance.is_latest = True


@receiver(post_save, sender=Revision)
def update_latest_revision(sender, instance, created, **kwargs):
    if created:
        Revision.objects.filter(page=instance.page).exclude(pk=instance.pk).update(is_latest=False)
