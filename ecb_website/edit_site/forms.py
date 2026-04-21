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


class ImageSettingsForm(forms.ModelForm):
    value = forms.ImageField(required=True)
    class Meta:
        model = SiteSettings
        fields = ['name', 'value', 'type']
        labels = {
            'name': 'Name',
            'value': 'Value',
            'type': 'Type',
        }