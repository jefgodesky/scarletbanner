# Generated by Django 5.0.6 on 2024-05-21 23:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wiki", "0005_revision_editor"),
    ]

    operations = [
        migrations.AddField(
            model_name="revision",
            name="body",
            field=models.TextField(blank=True, null=True),
        ),
    ]