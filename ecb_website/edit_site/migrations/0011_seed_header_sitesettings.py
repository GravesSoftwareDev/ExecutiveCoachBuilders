from django.db import migrations


def seed_header_settings(apps, schema_editor):
    SiteSetting = apps.get_model('edit_site', 'SiteSetting')
    SiteSetting.objects.get_or_create(
        name='header_logo',
        defaults={'file': True, 'text_value': '_'},
    )
    SiteSetting.objects.get_or_create(
        name='header_title',
        defaults={'file': False, 'text_value': 'Executive Coach Builders', 'file_value': '_'},
    )
    SiteSetting.objects.get_or_create(
        name='header_tagline',
        defaults={'file': False, 'text_value': '50 Years of Excellence', 'file_value': '_'},
    )


class Migration(migrations.Migration):

    dependencies = [
        ('edit_site', '0010_seed_home_sitesettings'),
    ]

    operations = [
        migrations.RunPython(seed_header_settings, migrations.RunPython.noop),
    ]
