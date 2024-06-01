from django.contrib.auth import get_user_model
from django.db import models
from simple_history.models import HistoricalRecords
from simple_history.utils import update_change_reason
from slugify import slugify

from scarletbanner.wiki.enums import PermissionLevel

User = get_user_model()


class AbstractPage(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=1024, unique=True)
    body = models.TextField()
    read = models.CharField(max_length=20, choices=PermissionLevel.get_choices(), default=PermissionLevel.PUBLIC.value)
    write = models.CharField(
        max_length=20, choices=PermissionLevel.get_choices(), default=PermissionLevel.PUBLIC.value
    )
    history = HistoricalRecords(inherit=True)

    class Meta:
        abstract = True

    @property
    def editors(self):
        ids = self.history.exclude(history_user=None).values_list("history_user", flat=True).distinct()
        return User.objects.filter(id__in=ids)

    def evaluate_permission(self, permission: PermissionLevel, user: User = None) -> bool:
        if user is not None and user.is_staff:
            return True

        match permission:
            case PermissionLevel.PUBLIC:
                return True
            case PermissionLevel.MEMBERS_ONLY:
                return user is not None
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
        return can_read and can_write_before and can_write_after

    def update(
        self,
        editor: User,
        title: str,
        body: str,
        message: str,
        slug: str = None,
        read: PermissionLevel = None,
        write: PermissionLevel = None,
    ):
        self.title = title
        self.body = body
        self.slug = slugify(title) if slug is None else slug
        self.read = self.read if read is None else read
        self.write = self.write if write is None else write
        self.stamp_revision(editor, message)

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
        read: PermissionLevel = PermissionLevel.PUBLIC,
        write: PermissionLevel = PermissionLevel.PUBLIC,
    ):
        slug = slugify(title) if slug is None else slug
        page = cls(title=title, body=body, slug=slug, read=read.value, write=write.value)
        page.save()
        page.stamp_revision(editor, message)
        return page


class Page(AbstractPage):
    pass
