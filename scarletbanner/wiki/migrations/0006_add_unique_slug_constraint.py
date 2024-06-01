from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('wiki', '0005_alter_page_options_historicalpage_polymorphic_ctype_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql="CREATE UNIQUE INDEX unique_slug ON wiki_page (slug)",
            reverse_sql="DROP INDEX unique_slug"
        ),
    ]
