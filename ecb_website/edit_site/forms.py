from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import SiteSetting, AboutPage
from client_view.models import Service, TeamMember


class PortalUserForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ['username', 'password1', 'password2']


class PortalUserPermissionForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ['role', 'can_edit_site', 'can_edit_fleet', 'can_edit_blog', 'can_edit_services', 'can_edit_team']
        labels = {
            'role': 'Role',
            'can_edit_site': 'Edit Site Settings',
            'can_edit_fleet': 'Edit Fleet / Vehicles',
            'can_edit_blog': 'Edit Blog',
            'can_edit_services': 'Edit Services',
            'can_edit_team': 'Edit Team',
        }
        help_texts = {
            'role': 'Admins have full access regardless of individual permissions.',
        }


class TeamMemberForm(forms.ModelForm):
    class Meta:
        model = TeamMember
        fields = ['name', 'role', 'bio', 'photo', 'display_order', 'is_active']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }
        help_texts = {
            'display_order': 'Lower numbers appear first in the team section.',
            'is_active': 'Uncheck to hide this member without deleting them.',
        }


class AboutPageForm(forms.ModelForm):
    class Meta:
        model = AboutPage
        fields = ['title', 'image', 'body']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 20}),
        }
        help_texts = {
            'body': 'Separate paragraphs with a blank line. HTML is not supported.',
        }


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['title', 'label', 'description', 'image', 'display_order', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }
        help_texts = {
            'label': 'Optional category label shown alongside the service.',
            'display_order': 'Lower numbers appear first on the services page.',
            'is_active': 'Uncheck to hide this service from the public site.',
        }


class SiteSettingForm(forms.ModelForm):
    mediaType = None
    class Meta:
        model = SiteSetting
        fields = ['name', 'file_value', 'text_value']
        labels = {
            'name': 'Name',
            'file_value': 'File Value',
            'text_value': 'Text Value',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['text_value'].required = False
        self.fields['file_value'].required = False
