from django import forms
from .models import Contact

class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['firstname', 'lastname', 'email', 'message']
        labels = {
            'firstname': 'First Name',
            'lastname': 'Last Name',
            'email': 'Email',
            'message': 'Message',
        }
        widgets = {
            'message': forms.Textarea(attrs={'rows': 5}),
        }
        help_texts = {
            'email': 'We will use this email to contact you back.',
            'message': 'Enter your message or inquiry here.',
        }