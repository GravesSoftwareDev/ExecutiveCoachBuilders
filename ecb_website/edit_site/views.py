from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import HttpResponse
from django.conf import settings
from .models import SiteSetting, AboutPage
from .forms import SiteSettingForm, ServiceForm, AboutPageForm, TeamMemberForm, PortalUserForm, PortalUserPermissionForm
from django.contrib.auth import get_user_model
from .palettes import PALETTES, DEFAULT_PALETTE
from client_view.models import Service, TeamMember
from django.urls import Resolver404, resolve
from account.decorators import portal_section_required, portal_admin_required


# Create your views here.
@portal_section_required('can_edit_site')
def site_changes(request, name = None):

    form = None
    if request.method == 'POST' and name is not None:
        if not name.strip():
            return HttpResponse("Invalid setting", status=400)
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
    site_settings_model = SiteSetting.objects.exclude(name='')
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

    theme_setting = SiteSetting.objects.filter(name='theme_palette').first()
    theme_key = theme_setting.text_value if theme_setting and theme_setting.text_value else DEFAULT_PALETTE
    if theme_key not in PALETTES:
        theme_key = DEFAULT_PALETTE

    return render(request, "edit_site/site_changes.html", {
        'admin_site': True,
        'site_settings': site_settings,
        'header_forms': header_forms,
        'home_forms': home_forms,
        'about_form': about_form,
        'about': about,
        'palettes': PALETTES,
        'theme': PALETTES[theme_key],
        'theme_key': theme_key,
    })


@portal_section_required('can_edit_site')
def admin_view(request):
    site_settings_model = SiteSetting.objects.exclude(name='')
    site_settings = {s.name : s.get_value() for s in site_settings_model}

    settings_form = {}
    for setting in site_settings_model:
        form = SiteSettingForm(instance=setting)
        settings_form[setting.name]= form;
        if setting.file:
            form.mediaType = True
        else:
            form.mediaType = False

    target = request.GET.get('s') or '/'
    try:
        view = resolve(target)
    except Resolver404:
        return HttpResponse("Invalid page", status=400)
    file = view.app_name + '/' + (view.url_name if view.url_name else 'client_view') + '.html'

    return render(request, file, {'admin_site': True, 'site_settings': site_settings, 'settings_form': settings_form})


@portal_section_required('can_edit_site')
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


@portal_section_required('can_edit_services')
def service_list(request):
    services = Service.objects.all().order_by('display_order', 'title')
    return render(request, 'edit_site/service_list.html', {'services': services})


@portal_section_required('can_edit_services')
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


@portal_section_required('can_edit_services')
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


@portal_section_required('can_edit_services')
def service_delete(request, pk):
    service = get_object_or_404(Service, pk=pk)
    if request.method == 'POST':
        title = service.title
        service.delete()
        messages.success(request, f'"{title}" has been removed.')
        return redirect('edit_site:service_list')
    return render(request, 'edit_site/service_confirm_delete.html', {'service': service})


@portal_section_required('can_edit_team')
def team_member_list(request):
    members = TeamMember.objects.all()
    return render(request, 'edit_site/team_member_list.html', {'members': members})


@portal_section_required('can_edit_team')
def team_member_add(request):
    if request.method == 'POST':
        form = TeamMemberForm(request.POST, request.FILES)
        if form.is_valid():
            member = form.save()
            messages.success(request, f'"{member.name}" has been added to the team.')
            return redirect('team:team_member_list')
    else:
        form = TeamMemberForm()
    return render(request, 'edit_site/team_member_form.html', {
        'form': form,
        'action': 'Add Team Member',
    })


@portal_section_required('can_edit_team')
def team_member_edit(request, pk):
    member = get_object_or_404(TeamMember, pk=pk)
    if request.method == 'POST':
        form = TeamMemberForm(request.POST, request.FILES, instance=member)
        if form.is_valid():
            form.save()
            messages.success(request, f'"{member.name}" has been updated.')
            return redirect('team:team_member_list')
    else:
        form = TeamMemberForm(instance=member)
    return render(request, 'edit_site/team_member_form.html', {
        'form': form,
        'member': member,
        'action': f'Edit — {member.name}',
    })


@portal_section_required('can_edit_team')
def team_member_delete(request, pk):
    member = get_object_or_404(TeamMember, pk=pk)
    if request.method == 'POST':
        name = member.name
        member.delete()
        messages.success(request, f'"{name}" has been removed from the team.')
        return redirect('team:team_member_list')
    return render(request, 'edit_site/team_member_confirm_delete.html', {'member': member})


@portal_admin_required
def portal_user_list(request):
    users = get_user_model().objects.filter(is_staff=True).order_by('username')
    return render(request, 'edit_site/portal_user_list.html', {'portal_users': users})


@portal_admin_required
def portal_user_add(request):
    if request.method == 'POST':
        form = PortalUserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_staff = True
            user.save()
            messages.success(request, f'Account "{user.username}" has been created.')
            return redirect('team:portal_user_list')
    else:
        form = PortalUserForm()
    return render(request, 'edit_site/portal_user_form.html', {'form': form})


@portal_admin_required
def portal_user_edit(request, pk):
    portal_user = get_object_or_404(get_user_model(), pk=pk, is_staff=True)
    if request.method == 'POST':
        form = PortalUserPermissionForm(request.POST, instance=portal_user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Permissions updated for "{portal_user.username}".')
            return redirect('team:portal_user_list')
    else:
        form = PortalUserPermissionForm(instance=portal_user)
    return render(request, 'edit_site/portal_user_edit.html', {
        'form': form,
        'portal_user': portal_user,
    })


@portal_admin_required
def portal_user_delete(request, pk):
    portal_user = get_object_or_404(get_user_model(), pk=pk, is_staff=True)
    if portal_user == request.user:
        messages.error(request, "You cannot delete your own account.")
        return redirect('team:portal_user_list')
    if request.method == 'POST':
        username = portal_user.username
        portal_user.delete()
        messages.success(request, f'Account "{username}" has been removed.')
        return redirect('team:portal_user_list')
    return render(request, 'edit_site/portal_user_confirm_delete.html', {'portal_user': portal_user})


@portal_section_required('can_edit_site')
def theme_save(request):
    if request.method == 'POST':
        palette_key = request.POST.get('palette', DEFAULT_PALETTE)
        if palette_key not in PALETTES:
            palette_key = DEFAULT_PALETTE
        SiteSetting.objects.update_or_create(
            name='theme_palette',
            defaults={'text_value': palette_key, 'file': False},
        )
        messages.success(request, f'Color scheme changed to {PALETTES[palette_key]["label"]}.')
    return redirect('edit_site:site_changes')
