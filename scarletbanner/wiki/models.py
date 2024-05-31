from django.db import models
from simple_history.models import HistoricalRecords

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


class Page(AbstractPage):
    pass
