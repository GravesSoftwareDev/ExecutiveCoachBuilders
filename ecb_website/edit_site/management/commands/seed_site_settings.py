from django.core.management.base import BaseCommand
from edit_site.models import SiteSetting

SETTINGS = [
    # (name, file, text_value)
    ('header_logo',        True,  ''),
    ('header_title',       False, 'Executive Coach Builders'),
    ('header_tagline',     False, '50 Years of Excellence'),
    ('home_video',         True,  ''),
    ('home_video_caption', False, ''),
]


class Command(BaseCommand):
    help = 'Create default SiteSetting records if they do not already exist.'

    def handle(self, *args, **options):
        for name, is_file, default_text in SETTINGS:
            _, created = SiteSetting.objects.get_or_create(
                name=name,
                defaults={'file': is_file, 'text_value': default_text},
            )
            status = 'created' if created else 'already exists'
            self.stdout.write(f'  {name}: {status}')
        self.stdout.write(self.style.SUCCESS('Done.'))
