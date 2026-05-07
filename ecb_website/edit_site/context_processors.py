from .models import SiteSetting


def site_settings(request):
    return {
        'site_settings': {s.name: s.get_value() for s in SiteSetting.objects.all()}
    }
