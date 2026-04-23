from django import forms
from .models import Article


class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['title', 'slug', 'image', 'video', 'body', 'tags', 'status', 'publish']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'fleet-input',
                'placeholder': 'Article headline',
            }),
            'slug': forms.TextInput(attrs={
                'class': 'fleet-input',
                'placeholder': 'url-friendly-slug',
            }),
            'body': forms.HiddenInput(attrs={'id': 'id_body'}),
            'status': forms.Select(attrs={'class': 'fleet-input'}),
            'publish': forms.DateTimeInput(
                attrs={'class': 'fleet-input', 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
            'tags': forms.TextInput(attrs={
                'class': 'fleet-input',
                'placeholder': 'luxury, custom build, motorcoach',
            }),
        }
        help_texts = {
            'slug': 'Auto-filled from the title. Only change for a custom URL.',
            'tags': 'Comma-separated list of tags.',
            'publish': 'Defaults to now. Set a future date to schedule.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].widget.attrs.update({'class': 'fleet-file-input'})
        self.fields['image'].required = False
        self.fields['video'].widget.attrs.update({'class': 'fleet-file-input'})
        self.fields['video'].required = False
        self.fields['publish'].input_formats = ['%Y-%m-%dT%H:%M']
        # Render taggit tags as a plain comma string
        if self.instance.pk:
            self.initial['tags'] = ', '.join(
                t.name for t in self.instance.tags.all()
            )
