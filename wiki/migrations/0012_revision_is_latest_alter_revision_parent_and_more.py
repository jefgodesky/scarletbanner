# Generated by Django 5.0.6 on 2024-05-24 20:08

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wiki", "0011_revision_message_alter_revision_parent"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="revision",
            name="is_latest",
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name="revision",
            name="parent",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="wiki.wikipage"
            ),
        ),
        migrations.AlterField(
            model_name="revision",
            name="slug",
            field=models.CharField(max_length=255),
        ),
        migrations.AddConstraint(
            model_name="revision",
            constraint=models.UniqueConstraint(
                condition=models.Q(("is_latest", True)), fields=("slug",), name="unique_page_slug"
            ),
        ),
    ]
