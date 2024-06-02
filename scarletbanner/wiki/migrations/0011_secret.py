# Generated by Django 5.0.6 on 2024-06-02 00:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wiki", "0010_secretcategory"),
    ]

    operations = [
        migrations.CreateModel(
            name="Secret",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("key", models.CharField(max_length=255, unique=True)),
                ("description", models.TextField(blank=True, null=True)),
                ("categories", models.ManyToManyField(related_name="secrets", to="wiki.secretcategory")),
                ("known_to", models.ManyToManyField(blank=True, related_name="secrets_known", to="wiki.character")),
            ],
        ),
    ]
