from django.db import models
from simple_history.models import HistoricalRecords
from simple_history.utils import update_change_reason
from slugify import slugify

from scarletbanner.wiki.enums import PermissionLevel


class AbstractPage(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    body = models.TextField()
    read = models.CharField(max_length=20, choices=PermissionLevel.get_choices(), default=PermissionLevel.PUBLIC.value)
    write = models.CharField(
        max_length=20, choices=PermissionLevel.get_choices(), default=PermissionLevel.PUBLIC.value
    )
    history = HistoricalRecords(inherit=True)

    class Meta:
        abstract = True

    @classmethod
    def create(cls, title: str, body: str, message: str = "Initial text", slug: str = None, read: PermissionLevel = PermissionLevel.PUBLIC, write: PermissionLevel = PermissionLevel.PUBLIC):
        slug = slugify(title) if slug is None else slug
        page = cls(title=title, body=body, slug=slug, read=read.value, write=write.value)
        page.save()
        update_change_reason(page, message)
        return page


class Page(AbstractPage):
    pass
