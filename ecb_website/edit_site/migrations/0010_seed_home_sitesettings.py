from django.db import migrations


def seed_home_settings(apps, schema_editor):
    SiteSetting = apps.get_model('edit_site', 'SiteSetting')
    SiteSetting.objects.get_or_create(
        name='home_video',
        defaults={'file': True, 'text_value': '_'},
    )
    SiteSetting.objects.get_or_create(
        name='home_video_caption',
        defaults={'file': False, 'text_value': '', 'file_value': '_'},
    )


class Migration(migrations.Migration):

    dependencies = [
        ('edit_site', '0009_aboutpage'),
    ]

    operations = [
        migrations.RunPython(seed_home_settings, migrations.RunPython.noop),
    ]
