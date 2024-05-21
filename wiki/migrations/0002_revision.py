# Generated by Django 5.0.6 on 2024-05-21 18:44

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wiki", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Revision",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                (
                    "page",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="revisions", to="wiki.wikipage"
                    ),
                ),
            ],
        ),
    ]
