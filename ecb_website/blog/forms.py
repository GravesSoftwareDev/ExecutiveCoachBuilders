from django import forms
from .models import Article


class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['title', 'slug', 'summary', 'image', 'video', 'body', 'status', 'publish']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'fleet-input',
                'placeholder': 'Article headline',
            }),
            'slug': forms.TextInput(attrs={
                'class': 'fleet-input',
                'placeholder': 'url-friendly-slug',
            }),
            'summary': forms.Textarea(attrs={
                'class': 'fleet-input',
                'rows': 3,
                'placeholder': '1-2 sentence excerpt for the news list.',
            }),
            'body': forms.HiddenInput(attrs={'id': 'id_body'}),
            'status': forms.Select(attrs={'class': 'fleet-input'}),
            'publish': forms.DateTimeInput(
                attrs={'class': 'fleet-input', 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
        }
        help_texts = {
            'slug': 'Auto-filled from the title. Only change for a custom URL.',
            'summary': 'Optional but recommended. Keep it concise.',
            'publish': 'Defaults to now. Set a future date to schedule.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].widget.attrs.update({'class': 'fleet-file-input'})
        self.fields['image'].required = False
        self.fields['video'].widget.attrs.update({'class': 'fleet-file-input'})
        self.fields['video'].required = False
        self.fields['publish'].input_formats = ['%Y-%m-%dT%H:%M']
