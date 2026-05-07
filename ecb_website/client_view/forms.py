from django import forms
from account.models import Lead


class ContactForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'company', 'interest', 'budget', 'message']
        labels = {
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'email': 'Email',
            'phone_number': 'Phone Number',
            'company': 'Company',
            'interest': 'I\'m interested in',
            'budget': 'Budget ($)',
            'message': 'Message',
        }
        widgets = {
            'message': forms.Textarea(attrs={'rows': 5}),
        }
        help_texts = {
            'phone_number': '',
            'company': '',
            'budget': 'Optional — helps us recommend the right options.',
        }
