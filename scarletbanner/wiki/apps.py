from django.apps import AppConfig


class WikiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "scarletbanner.wiki"
    verbose_name = "Wiki"

    def ready(self):
        import scarletbanner.wiki.signals  # noqa: F401
