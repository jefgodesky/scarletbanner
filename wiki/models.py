from django.conf import settings
from django.db import models


class WikiPage(models.Model):
    @property
    def latest(self):
        return self.revisions.order_by('-timestamp', '-id').first()

    @property
    def original(self):
        return self.revisions.order_by('timestamp', 'id').first()

    @property
    def title(self):
        return self.latest.title

    @property
    def updated(self):
        return self.latest.timestamp

    @property
    def created(self):
        return self.original.timestamp

    def __str__(self):
        return self.latest.title

    def update(self, title, editor):
        Revision.objects.create(title=title, page=self, editor=editor)

    @classmethod
    def create(cls, title, editor):
        page = cls.objects.create()
        Revision.objects.create(page=page, title=title, editor=editor)
        return page


class Revision(models.Model):
    title = models.CharField(max_length=255)
    page = models.ForeignKey(WikiPage, related_name="revisions", on_delete=models.CASCADE)
    editor = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="revisions", on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
