from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from .models import SiteSettings
from .forms import SiteSettingsForm, MediaSettingsForm


# Create your views here.
@staff_member_required(login_url='login')
def site_changes(request):
    # should only be the first object
    # settings = SiteSettings.objects.get()
    # form = SiteSettingsForm(request.POST, request.FILES, instance=settings)

    # if request.method == 'POST':
    #     if form.is_valid():
    #         form.save()

    # Load settings
    site_settings_model = SiteSettings.objects.all()
    site_settings = {s.name : s.get_value() for s in site_settings_model}

    settings_form = []
    for setting in site_settings_model:
        if setting.media_type():
            settings_form.append(MediaSettingsForm(instance=setting))
        else:
            settings_form.append(SiteSettingsForm(instance=setting))

    return render(request, "edit_site/site_changes.html", {'admin_site':True, 'site_settings': site_settings, 'settings_form': settings_form})


@staff_member_required(login_url='login')
def admin_view(request):
    site_settings_model = SiteSettings.objects.all()
    site_settings = {s.name : s.get_value() for s in site_settings_model}


    return render(request, request.GET.get('s', 'client_view/'), {'admin_site': True, 'site_settings': site_settings})