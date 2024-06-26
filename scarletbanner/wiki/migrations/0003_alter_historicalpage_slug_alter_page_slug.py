# Generated by Django 5.0.6 on 2024-05-31 21:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wiki", "0002_historicalpage_read_historicalpage_write_page_read_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="historicalpage",
            name="slug",
            field=models.SlugField(max_length=1024),
        ),
        migrations.AlterField(
            model_name="page",
            name="slug",
            field=models.SlugField(max_length=1024, unique=True),
        ),
    ]
