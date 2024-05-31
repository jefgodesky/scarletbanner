from django.db import models
from simple_history.models import HistoricalRecords


class AbstractPage(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    body = models.TextField()
    history = HistoricalRecords(inherit=True)

    class Meta:
        abstract = True


class Page(AbstractPage):
    pass
