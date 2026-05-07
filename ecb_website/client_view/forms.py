from django import forms

from leads.models import Lead


class ContactForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = [
            'first_name',
            'last_name',
            'email',
            'phone_number',
            'company',
            'budget',
            'interest',
            'passenger_count',
            'timeline',
            'use_case',
            'source',
            'source_url',
            'message',
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'given-name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'family-name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'autocomplete': 'email'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'tel'}),
            'company': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'organization'}),
            'budget': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'step': 1}),
            'interest': forms.Select(attrs={'class': 'form-select'}),
            'passenger_count': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 14 passengers, 45 passengers, flexible',
            }),
            'timeline': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. ASAP, 3-6 months, Q3 2026',
            }),
            'use_case': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. charter, hotel shuttle, livery, corporate travel',
            }),
            'source': forms.HiddenInput(),
            'source_url': forms.HiddenInput(),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Tell us about the vehicle, timeline, and any custom requirements.',
            }),
        }
        labels = {
            'first_name': 'First name',
            'last_name': 'Last name',
            'phone_number': 'Phone',
            'passenger_count': 'Passenger count',
            'use_case': 'Use case',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['interest'].choices = [('', 'Select one')] + list(Lead.Interest.choices)
        self.fields['interest'].required = True
        for field_name in ('phone_number', 'company', 'budget', 'passenger_count', 'timeline', 'use_case', 'source', 'source_url'):
            self.fields[field_name].required = False
