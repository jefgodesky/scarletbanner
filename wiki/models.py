from django.db import models


class WikiPage(models.Model):
    title = models.CharField(max_length=255)

    @property
    def latest(self):
        return self.revisions.order_by('-timestamp').first()

    def __str__(self):
        return self.title


class Revision(models.Model):
    title = models.CharField(max_length=255)
    page = models.ForeignKey(WikiPage, related_name="revisions", on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
