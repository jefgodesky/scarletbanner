from django.db import models


class WikiPage(models.Model):
    @property
    def latest(self):
        return self.revisions.order_by('-timestamp').first()

    @property
    def title(self):
        return self.latest.title

    def __str__(self):
        return self.latest.title

    def update(self, title):
        Revision.objects.create(title=title, page=self)

    @classmethod
    def create(cls, title):
        page = cls.objects.create()
        Revision.objects.create(page=page, title=title)
        return page


class Revision(models.Model):
    title = models.CharField(max_length=255)
    page = models.ForeignKey(WikiPage, related_name="revisions", on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
