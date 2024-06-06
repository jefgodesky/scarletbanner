# Generated by Django 5.0.6 on 2024-06-02 23:39

import django.db.models.deletion
import scarletbanner.wiki.enums
import simple_history.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("wiki", "0012_template_historicaltemplate"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="File",
            fields=[
                (
                    "page_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="wiki.page",
                    ),
                ),
                ("attachment", models.FileField(upload_to="uploads/")),
                ("content_type", models.CharField(blank=True, max_length=255)),
            ],
            options={
                "abstract": False,
                "base_manager_name": "objects",
            },
            bases=("wiki.page",),
        ),
        migrations.CreateModel(
            name="HistoricalFile",
            fields=[
                (
                    "page_ptr",
                    models.ForeignKey(
                        auto_created=True,
                        blank=True,
                        db_constraint=False,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        parent_link=True,
                        related_name="+",
                        to="wiki.page",
                    ),
                ),
                ("id", models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                ("slug", models.SlugField(max_length=1024)),
                ("body", models.TextField()),
                (
                    "read",
                    models.IntegerField(
                        choices=[
                            (100, "Public"),
                            (300, "Members only"),
                            (600, "Editors only"),
                            (900, "Owners only"),
                            (999, "Administrator only"),
                        ],
                        default=scarletbanner.wiki.enums.PermissionLevel["PUBLIC"],
                    ),
                ),
                (
                    "write",
                    models.IntegerField(
                        choices=[
                            (100, "Public"),
                            (300, "Members only"),
                            (600, "Editors only"),
                            (900, "Owners only"),
                            (999, "Administrator only"),
                        ],
                        default=scarletbanner.wiki.enums.PermissionLevel["PUBLIC"],
                    ),
                ),
                ("attachment", models.TextField(max_length=100)),
                ("content_type", models.CharField(blank=True, max_length=255)),
                ("history_id", models.AutoField(primary_key=True, serialize=False)),
                ("history_date", models.DateTimeField(db_index=True)),
                ("history_change_reason", models.CharField(max_length=100, null=True)),
                (
                    "history_type",
                    models.CharField(choices=[("+", "Created"), ("~", "Changed"), ("-", "Deleted")], max_length=1),
                ),
                (
                    "history_user",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "parent",
                    models.ForeignKey(
                        blank=True,
                        db_constraint=False,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="+",
                        to="wiki.page",
                    ),
                ),
                (
                    "polymorphic_ctype",
                    models.ForeignKey(
                        blank=True,
                        db_constraint=False,
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="+",
                        to="contenttypes.contenttype",
                    ),
                ),
            ],
            options={
                "verbose_name": "historical file",
                "verbose_name_plural": "historical files",
                "ordering": ("-history_date", "-history_id"),
                "get_latest_by": ("history_date", "history_id"),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
    ]