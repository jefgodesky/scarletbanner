from django.contrib.auth import get_user_model
from django.db import models
from polymorphic.models import PolymorphicModel
from simple_history.models import HistoricalRecords
from simple_history.utils import update_change_reason
from slugify import slugify

from scarletbanner.wiki.enums import PermissionLevel

User = get_user_model()


class Page(PolymorphicModel):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=1024, unique=True)
    body = models.TextField()
    read = models.IntegerField(default=PermissionLevel.PUBLIC, choices=PermissionLevel.get_choices())
    write = models.IntegerField(default=PermissionLevel.PUBLIC, choices=PermissionLevel.get_choices())
    history = HistoricalRecords(inherit=True)

    @property
    def editors(self):
        ids = self.history.exclude(history_user=None).values_list("history_user", flat=True).distinct()
        return User.objects.filter(id__in=ids)

    def evaluate_permission(self, permission: PermissionLevel, user: User = None) -> bool:
        if user is not None and user.is_staff:
            return True

        match PermissionLevel(permission):
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
        editor_exception = user is not None and to == PermissionLevel.EDITORS_ONLY
        no_write_lockout = can_write_after or editor_exception
        no_read_lockout = to.value <= self.read or editor_exception
        return can_read and can_write_before and no_write_lockout and no_read_lockout

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
        read = PermissionLevel(self.write) if read is None else read
        write = PermissionLevel(self.write) if write is None else write
        will_read = self.evaluate_permission(read, editor) or read == PermissionLevel.EDITORS_ONLY

        if not self.can_write(write, editor) or not will_read:
            return

        self.title = title
        self.body = body
        self.slug = slugify(title) if slug is None else slug
        self.read = self.read if read is None else read.value
        self.write = write.value
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
