from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import HttpResponse
from django.conf import settings
from .models import SiteSetting, AboutPage
from .forms import SiteSettingForm, ServiceForm, AboutPageForm
from client_view.models import Service
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
    site_settings = {s.name: s.get_value() for s in site_settings_model}

    header_forms = []
    home_forms = []
    for setting in site_settings_model:
        form = SiteSettingForm(instance=setting)
        form.mediaType = setting.file
        if setting.name.startswith('header_'):
            header_forms.append(form)
        elif setting.name.startswith('home_'):
            home_forms.append(form)

    about, _ = AboutPage.objects.get_or_create(pk=1)
    about_form = AboutPageForm(instance=about)

    return render(request, "edit_site/site_changes.html", {
        'admin_site': True,
        'site_settings': site_settings,
        'header_forms': header_forms,
        'home_forms': home_forms,
        'about_form': about_form,
        'about': about,
    })


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


@staff_member_required(login_url='login')
def about_edit(request):
    about, _ = AboutPage.objects.get_or_create(pk=1)
    if request.method == 'POST':
        form = AboutPageForm(request.POST, request.FILES, instance=about)
        if form.is_valid():
            form.save()
            messages.success(request, 'About page has been updated.')
            return redirect('edit_site:site_changes')
    else:
        form = AboutPageForm(instance=about)
    return render(request, 'edit_site/about_form.html', {'form': form, 'about': about})


@staff_member_required(login_url='login')
def service_list(request):
    services = Service.objects.all().order_by('display_order', 'title')
    return render(request, 'edit_site/service_list.html', {'services': services})


@staff_member_required(login_url='login')
def service_add(request):
    if request.method == 'POST':
        form = ServiceForm(request.POST, request.FILES)
        if form.is_valid():
            service = form.save()
            messages.success(request, f'"{service.title}" has been added.')
            return redirect('edit_site:service_list')
    else:
        form = ServiceForm()
    return render(request, 'edit_site/service_form.html', {
        'form': form,
        'action': 'Add New Service',
    })


@staff_member_required(login_url='login')
def service_edit(request, pk):
    service = get_object_or_404(Service, pk=pk)
    if request.method == 'POST':
        form = ServiceForm(request.POST, request.FILES, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, f'"{service.title}" has been updated.')
            return redirect('edit_site:service_list')
    else:
        form = ServiceForm(instance=service)
    return render(request, 'edit_site/service_form.html', {
        'form': form,
        'service': service,
        'action': f'Edit — {service.title}',
    })


@staff_member_required(login_url='login')
def service_delete(request, pk):
    service = get_object_or_404(Service, pk=pk)
    if request.method == 'POST':
        title = service.title
        service.delete()
        messages.success(request, f'"{title}" has been removed.')
        return redirect('edit_site:service_list')
    return render(request, 'edit_site/service_confirm_delete.html', {'service': service})