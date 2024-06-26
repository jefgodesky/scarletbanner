import ast
import mimetypes
import re
from typing import Any

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.db import models
from polymorphic.models import PolymorphicModel
from simple_history.models import HistoricalRecords
from simple_history.utils import update_change_reason
from slugify import slugify
from tree_queries.models import TreeNode

from scarletbanner.wiki.enums import PermissionLevel

User = get_user_model()


class Page(PolymorphicModel):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=1024, unique=True)
    body = models.TextField()
    parent = models.ForeignKey("Page", related_name="children", on_delete=models.SET_NULL, null=True, blank=True)
    read = models.IntegerField(default=PermissionLevel.PUBLIC, choices=PermissionLevel.get_choices())
    write = models.IntegerField(default=PermissionLevel.PUBLIC, choices=PermissionLevel.get_choices())
    history = HistoricalRecords(inherit=True)

    def __str__(self):
        return self.title

    @property
    def editors(self):
        ids = self.history.exclude(history_user=None).values_list("history_user", flat=True).distinct()
        return User.objects.filter(id__in=ids)

    @property
    def unique_slug_element(self) -> str:
        parts = [part for part in self.slug.split("/")]
        return parts[-1]

    def set_slug(self, slug: str or None = None):
        slug = slugify(self.title) if slug is None else slugify(self.unique_slug_element)
        if self.parent is not None:
            slug = f"{self.parent.slug}/{slug}"

        self.slug = slug

    def save(self, *args, **kwargs):
        self.set_slug(self.slug)
        if Page.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
            raise ValueError("Slug must be unique.")
        super().save(*args, **kwargs)

    def evaluate_permission(self, permission: PermissionLevel, user: User = None) -> bool:
        if user is not None and user.is_staff:
            return True

        match PermissionLevel(permission):
            case PermissionLevel.PUBLIC:
                return True
            case PermissionLevel.MEMBERS_ONLY:
                return user is not None and not user.is_anonymous
            case PermissionLevel.EDITORS_ONLY:
                return user in self.editors
            case _:
                return False

    def can_read(self, user: User = None) -> bool:
        return self.evaluate_permission(PermissionLevel(self.read), user)

    def can_write(self, to: PermissionLevel, user: User = None) -> bool:
        can_read = self.can_read(user)
        can_write_before = self.evaluate_permission(PermissionLevel(self.write), user)
        can_write_after = self.evaluate_permission(to, user)
        editor_exception = user is not None and to == PermissionLevel.EDITORS_ONLY
        no_write_lockout = can_write_after or editor_exception
        no_read_lockout = to.value <= self.read or editor_exception
        return can_read and can_write_before and no_write_lockout and no_read_lockout

    def update(
        self,
        editor: User,
        message: str,
        title: str = None,
        body: str = None,
        slug: str = None,
        parent: "Page" = None,
        read: PermissionLevel = None,
        write: PermissionLevel = None,
    ):
        read = PermissionLevel(self.write) if read is None else read
        write = PermissionLevel(self.write) if write is None else write
        will_read = self.evaluate_permission(read, editor) or read == PermissionLevel.EDITORS_ONLY

        if not self.can_write(write, editor) or not will_read:
            return

        self.title = self.title if title is None else title
        self.body = self.body if body is None else body
        self.slug = self.slug if slug is None else slug
        self.parent = self.parent if parent is None else parent
        self.read = read.value
        self.write = write.value
        self.stamp_revision(editor, message)

    def reparent(self, editor: User, new_parent: "Page" or None = None) -> None:
        message = f"Reparenting to {'root' if new_parent is None else new_parent.slug}"

        self.parent = None
        self.update(
            editor=editor,
            message=message,
            parent=new_parent,
        )

        for child in self.children.all():
            child.reparent(editor, new_parent=self)

    def destroy(self, editor: User) -> None:
        children = list(self.children.all())
        new_parent = self.parent

        super().delete()

        for child in children:
            child.reparent(editor, new_parent=new_parent)

    def stamp_revision(self, editor: User, message: str):
        self.save()
        latest = self.history.first()
        latest.history_user = editor
        latest.save()
        update_change_reason(self, message)

    @classmethod
    def create(
        cls,
        editor: User,
        title: str,
        body: str,
        message: str = "Initial text",
        slug: str = None,
        parent: "Page" = None,
        read: PermissionLevel = PermissionLevel.PUBLIC,
        write: PermissionLevel = PermissionLevel.PUBLIC,
    ):
        slug = slugify(title) if slug is None else slug
        page = cls(title=title, body=body, slug=slug, parent=parent, read=read.value, write=write.value)
        page.save()
        page.stamp_revision(editor, message)
        return page


class OwnedPage(Page):
    owner = models.ForeignKey(User, related_name="pages", on_delete=models.SET_NULL, null=True, blank=True)

    def evaluate_permission(self, permission: PermissionLevel, user: User = None) -> bool:
        is_owner = self.owner == user
        is_admin = user is not None and user.is_staff

        if permission == PermissionLevel.OWNER_ONLY:
            return is_owner or is_admin
        elif permission == PermissionLevel.EDITORS_ONLY and is_owner:
            return True
        else:
            return super().evaluate_permission(permission, user)

    @classmethod
    def create(
        cls,
        editor: User,
        title: str,
        body: str,
        message: str = "Initial text",
        slug: str = None,
        parent: "Page" = None,
        owner: User = None,
        read: PermissionLevel = PermissionLevel.PUBLIC,
        write: PermissionLevel = PermissionLevel.PUBLIC,
    ):
        slug = slugify(title) if slug is None else slug
        page = cls(title=title, body=body, slug=slug, parent=parent, owner=owner, read=read.value, write=write.value)
        page.save()
        page.stamp_revision(editor, message)
        return page


class Character(OwnedPage):
    @property
    def player(self):
        return self.owner


class Template(Page):
    pass


class File(Page):
    attachment = models.FileField(upload_to="uploads/")
    content_type = models.CharField(max_length=255, blank=True)

    @property
    def size(self):
        return File.get_human_readable_size(self.attachment.size)

    def save(self, *args, **kwargs):
        if self.attachment and not self.content_type:
            content_type, _ = mimetypes.guess_type(self.attachment.name)
            self.content_type = content_type or "application/octet-stream"
        super().save(*args, **kwargs)

    @classmethod
    def create(
        cls,
        editor: User,
        title: str,
        body: str,
        message: str = "Initial text",
        slug: str = None,
        parent: Page = None,
        attachment: UploadedFile = None,
        read: PermissionLevel = PermissionLevel.PUBLIC,
        write: PermissionLevel = PermissionLevel.PUBLIC,
    ):
        slug = slugify(title) if slug is None else slug
        page = cls(
            title=title, body=body, slug=slug, parent=parent, attachment=attachment, read=read.value, write=write.value
        )
        page.save()
        page.stamp_revision(editor, message)
        return page

    @staticmethod
    def get_human_readable_size(size: int) -> str:
        if size > 1024**3:
            return f"{size / 1024 ** 3:.1f} GB"
        elif size > 1024**2:
            return f"{size / 1024 ** 2:.1f} MB"
        elif size > 1024:
            return f"{size / 1024:.1f} kB"
        else:
            return f"{size} B"


class Image(File):
    def clean(self):
        super().clean()
        if self.attachment:
            content_type = self.attachment.file.content_type
            if not content_type.startswith("image/"):
                raise ValidationError("Attachment is not an image.")

    @classmethod
    def create(
        cls,
        editor: User,
        title: str,
        body: str,
        message: str = "Initial text",
        slug: str = None,
        parent: Page = None,
        attachment: UploadedFile = None,
        read: PermissionLevel = PermissionLevel.PUBLIC,
        write: PermissionLevel = PermissionLevel.PUBLIC,
    ):
        if attachment:
            if not attachment.content_type.startswith("image/"):
                raise ValidationError("Attachment is not an image.")
        return super().create(editor, title, body, message, slug, parent, attachment, read, write)


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
    known_to = models.ManyToManyField(Character, related_name="secrets_known", blank=True)

    def __str__(self):
        return self.key

    def knows(self, character: Character) -> bool:
        return self.known_to.filter(pk=character.pk).exists()

    @staticmethod
    def evaluate(expression: str, character: Character, secrets: Any = None) -> bool:
        secrets = Secret.objects.all() if secrets is None else secrets
        return SecretEvaluator(character, secrets).eval(expression)


class SecretEvaluator(ast.NodeVisitor):
    def __init__(self, character: Character, secrets: Any = None):
        secrets = Secret.objects.all() if secrets is None else secrets
        self.character = character
        self.secrets = {
            SecretEvaluator.variablize(secret.key): (secret.key, secret.knows(character)) for secret in secrets
        }

    def eval(self, expression: str) -> bool:
        for variable, (key, _) in self.secrets.items():
            expression = expression.replace(f"[{key}]", variable)
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
