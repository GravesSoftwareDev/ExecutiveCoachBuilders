from .models import SiteSetting
from .palettes import PALETTES, DEFAULT_PALETTE


def site_settings(request):
    all_settings = {s.name: s.get_value() for s in SiteSetting.objects.all()}

    palette_key = all_settings.get('theme_palette', DEFAULT_PALETTE)
    if palette_key not in PALETTES:
        palette_key = DEFAULT_PALETTE

    return {
        'site_settings': all_settings,
        'theme': PALETTES[palette_key],
        'theme_key': palette_key,
    }
