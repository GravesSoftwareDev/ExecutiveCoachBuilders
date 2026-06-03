from django.db import migrations

SETTINGS = [
    # (name, file, text_value)
    ('header_logo',        True,  ''),
    ('header_title',       False, 'Executive Coach Builders'),
    ('header_tagline',     False, '50 Years of Excellence'),
    ('home_video',         True,  ''),
    ('home_video_caption', False, ''),
]


def seed_site_settings(apps, schema_editor):
    SiteSetting = apps.get_model('edit_site', 'SiteSetting')
    for name, is_file, default_text in SETTINGS:
        SiteSetting.objects.get_or_create(
            name=name,
            defaults={'file': is_file, 'text_value': default_text},
        )


class Migration(migrations.Migration):

    dependencies = [
        ('edit_site', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_site_settings, migrations.RunPython.noop),
    ]
