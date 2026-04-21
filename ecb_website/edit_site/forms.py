from django import forms
from .models import SiteSettings

class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = ['name', 'value', 'type']
        labels = {
            'name': 'Name',
            'value': 'Value',
            'type': 'Type',
        }


class MediaSettingsForm(forms.ModelForm):
    value = forms.FileField(required=True)
    class Meta:
        model = SiteSettings
        fields = ['name', 'value']
        labels = {
            'name': 'Name',
            'value': 'Value',
        }