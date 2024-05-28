import ast
import datetime
import re

from django.conf import settings
from django.db import models
from django.db.models import F, Max, Q
from django.db.models.query import QuerySet
from django.db.models.signals import post_save, pre_save
from django.db.utils import IntegrityError
from django.dispatch import receiver
from slugify import slugify
from tree_queries.models import TreeNode

from scarletbanner.users.models import User
from wiki.enums import PageType, PermissionLevel


def get_unique_slug_element(slug: str) -> str:
    parts = [part for part in slug.split("/")]
    return parts[-1]


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
    def page_type(self) -> PageType:
        return PageType(self.latest.page_type)

    @property
    def title(self) -> str:
        return self.latest.title

    @property
    def slug(self) -> str:
        return self.latest.slug

    @property
    def unique_slug_element(self) -> str:
        return get_unique_slug_element(self.slug)

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
    def read(self) -> PermissionLevel:
        return PermissionLevel(self.latest.read)

    @property
    def write(self) -> PermissionLevel:
        return PermissionLevel(self.latest.write)

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
        return [revision.editor for revision in self.revisions.order_by("timestamp", "id")]

    @property
    def children(self) -> list["WikiPage"]:
        latest_revisions = (
            Revision.objects.filter(parent=self)
            .annotate(latest_timestamp=Max("page__revisions__timestamp"))
            .filter(timestamp=F("latest_timestamp"))
        )
        return [rev.page for rev in latest_revisions]

    def evaluate_permission(self, permission: PermissionLevel, user: User = None) -> bool:
        is_admin = user is not None and user.is_staff
        is_owner = self.owner == user
        is_editor = user in self.editors

        match permission:
            case PermissionLevel.PUBLIC:
                return True
            case PermissionLevel.MEMBERS_ONLY:
                return user is not None
            case PermissionLevel.EDITORS_ONLY:
                return is_editor or is_admin or is_owner
            case PermissionLevel.OWNER_ONLY:
                return is_admin or is_owner
            case _:
                return is_admin

    def can_read(self, user: User = None) -> bool:
        return self.evaluate_permission(self.read, user)

    def can_write(self, to: PermissionLevel, user: User = None) -> bool:
        can_read = self.can_read(user)
        can_write_before = self.evaluate_permission(self.write, user)
        can_write_after = self.evaluate_permission(to, user)
        return can_read and can_write_before and can_write_after

    def update(
        self,
        page_type: PageType,
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
        if not self.can_write(write, editor):
            return

        slug = slugify(title) if slug is None else slug
        Revision.objects.create(
            page_type=page_type.value,
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
        page_type: PageType = None,
        title: str = None,
        slug: str = None,
        body: str = None,
        parent: "WikiPage" = None,
        owner: User or None = None,
        read: PermissionLevel = None,
        write: PermissionLevel = None,
    ) -> None:
        patch_type = self.page_type if page_type is None else page_type
        patch_title = self.title if title is None else title
        patch_slug = self.slug if slug is None else slug
        patch_body = self.body if body is None else body
        patch_parent = self.parent if parent is None else parent
        patch_owner = self.owner if owner is None else owner
        patch_read = self.read if read is None else read
        patch_write = self.write if write is None else write

        if not self.can_write(patch_write, editor):
            return

        Revision.objects.create(
            page_type=patch_type.value,
            title=patch_title,
            slug=patch_slug,
            body=patch_body,
            parent=patch_parent,
            owner=patch_owner,
            page=self,
            editor=editor,
            read=patch_read.value,
            write=patch_write.value,
            message=message,
        )

    def reparent(self, editor: User, new_parent: "WikiPage" or None = None) -> None:
        none_message = "Reparenting to root"
        new_message = f"Reparenting to {new_parent}"
        message = none_message if new_parent is None else new_message

        self.update(
            page_type=self.page_type,
            title=self.title,
            body=self.body,
            editor=editor,
            read=self.read,
            write=self.write,
            message=message,
            slug=self.unique_slug_element,
            parent=new_parent,
            owner=self.owner,
        )

        for child in self.children:
            child.reparent(editor, new_parent=self)

    def destroy(self, editor: User) -> None:
        for child in self.children:
            child.reparent(editor, new_parent=self.parent)

        super().delete()

    @classmethod
    def create(
        cls,
        title: str,
        body: str,
        editor: User,
        message: str = "Initial text",
        page_type: PageType = PageType.PAGE,
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
            page_type=page_type.value,
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

    @classmethod
    def get_type(cls, page_type: PageType, owner: User or None = None) -> QuerySet["WikiPage"]:
        latest = Q(revisions__is_latest=True, revisions__page_type=page_type.value)

        if owner is None:
            return cls.objects.filter(latest).distinct()

        return cls.objects.filter(latest, revisions__owner=owner).distinct()


class Revision(models.Model):
    PAGE_TYPES = [(PageType.PAGE.value, "Page"), (PageType.CHARACTER.value, "Character")]
    SECURITY_CHOICES = [
        (PermissionLevel.PUBLIC.value, "Public"),
        (PermissionLevel.MEMBERS_ONLY.value, "Members only"),
        (PermissionLevel.EDITORS_ONLY.value, "Editors only"),
        (PermissionLevel.OWNER_ONLY.value, "Owner only"),
        (PermissionLevel.ADMIN_ONLY.value, "Admins only"),
    ]

    page_type = models.CharField(max_length=20, choices=PAGE_TYPES, default=PageType.PAGE.value)
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
            models.UniqueConstraint(fields=["slug", "page"], condition=Q(is_latest=True), name="unique_page_slug")
        ]

    def __str__(self) -> str:
        return self.slug

    def save(self, *args, **kwargs):
        if self.is_latest:
            Revision.objects.filter(page=self.page, is_latest=True).exclude(pk=self.pk).update(is_latest=False)

        if Revision.objects.filter(slug=self.slug, is_latest=True).exclude(page=self.page).exists():
            raise IntegrityError(f"A page with the slug '{self.slug}' already exists.")

        self.set_slug(self.slug)
        super().save(*args, **kwargs)

    def set_slug(self, slug: str or None = None):
        slug = slugify(self.title) if slug is None else slugify(get_unique_slug_element(slug))
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


class SecretCategory(TreeNode):
    name = models.CharField(max_length=255)

    class Meta:
        verbose_name = "Secret category"
        verbose_name_plural = "Secret categories"

    def __str__(self):
        return self.name


class Secret(models.Model):
    key = models.CharField(max_length=255, unique=True)
    description = models.TextField(null=True, blank=True)
    categories = models.ManyToManyField(SecretCategory, related_name="secrets")
    known_to = models.ManyToManyField(WikiPage, related_name="secrets_known", blank=True)

    def __str__(self):
        return self.key

    def knows(self, character: WikiPage) -> bool:
        return self.known_to.filter(pk=character.pk).exists()

    @staticmethod
    def evaluate(expression: str, character: WikiPage) -> bool:
        return SecretEvaluator(character).eval(expression)


class SecretEvaluator(ast.NodeVisitor):
    def __init__(self, character: WikiPage):
        self.character = character
        self.secrets = {
            SecretEvaluator.variablize(secret.key): (secret.key, secret.knows(character))
            for secret in Secret.objects.all()
        }

    def eval(self, expression: str) -> bool:
        for variable, (key, _) in self.secrets.items():
            expression = expression.replace(f"<{key}>", variable)
        tree = ast.parse(expression, mode="eval")
        return self.visit(tree.body)

    def visit_BoolOp(self, node):
        fn = all if isinstance(node.op, ast.And) else any
        return fn(self.visit(value) for value in node.values)

    def visit_UnaryOp(self, node):
        if isinstance(node.op, ast.Not):
            return not self.visit(node.operand)

    def visit_Name(self, node):
        variable = node.id
        if variable in self.secrets:
            return self.secrets[variable][1]
        raise ValueError(f"Unknown secret key: {self.secrets[variable][0]}")

    def visit_Expr(self, node):
        return self.visit(node.value)

    def visit_Module(self, node):
        return all(self.visit(body) for body in node.body)

    @staticmethod
    def variablize(key: str) -> str:
        return re.sub(r"\W|^(?=\d)", "_", key)
