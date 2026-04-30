from django.shortcuts import render, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from django.conf import settings
from .models import SiteSetting
from .forms import SiteSettingForm
from django.urls import resolve


# Create your views here.
@staff_member_required(login_url='login')
def site_changes(request, name = None):
    
    form = None
    if request.method == 'POST' and name is not None:
        setting = get_object_or_404(SiteSetting, name=name)
        form    = SiteSettingForm(request.POST, request.FILES, instance=setting)

        if (form.is_valid()):
            instance = form.save()
            print('saved')
            if instance.file:
                return HttpResponse("{};{}".format(settings.MEDIA_URL, instance.file_value))
            else:
                return HttpResponse(instance.text_value)
        return HttpResponse("Invalid", status=400)



    # Load settings
    site_settings_model = SiteSetting.objects.all()
    site_settings = {s.name : s.get_value() for s in site_settings_model}

    settings_form = []
    for setting in site_settings_model:
        form = SiteSettingForm(instance=setting)
        settings_form.append(form)
        if setting.file:
            form.mediaType = True
        else:
            form.mediaType = False

    return render(request, "edit_site/site_changes.html", {'admin_site':True, 'site_settings': site_settings, 'settings_form': settings_form})


@staff_member_required(login_url='login')
def admin_view(request):
    site_settings_model = SiteSetting.objects.all()
    site_settings = {s.name : s.get_value() for s in site_settings_model}

    
    settings_form = {}
    for setting in site_settings_model:
        form = SiteSettingForm(instance=setting)
        settings_form[setting.name]= form;
        if setting.file:
            form.mediaType = True
        else:
            form.mediaType = False

    view = resolve(request.GET.get('s', '/'))
    file = view.app_name + '/' + (view.url_name if view.url_name else 'client_view') + '.html'

    return render(request, file, {'admin_site': True, 'site_settings': site_settings, 'settings_form': settings_form})