from django import forms
from .models import SiteSettings

class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = ['primaryCenterVideo']
        labels = {
            'primaryCenterVideo': 'Primary Center Video'
        }