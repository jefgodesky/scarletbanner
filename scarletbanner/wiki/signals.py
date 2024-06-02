from django.db.models.signals import pre_save
from django.dispatch import receiver

from scarletbanner.wiki.models import Page


@receiver(pre_save, sender=Page)
def validate_unique_slug(sender, instance, **kwargs):
    if Page.objects.filter(slug=instance.slug).exclude(pk=instance.pk).exists():
        raise ValueError("Slug must be unique.")
