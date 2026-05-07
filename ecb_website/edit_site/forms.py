from django import forms
from .models import SiteSetting, AboutPage
from client_view.models import Service


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
        