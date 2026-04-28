from django import forms
from .models import SiteSetting

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
        