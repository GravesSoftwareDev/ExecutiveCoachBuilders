from django import forms

from .models import Lead


class LeadForm(forms.ModelForm):
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
            'pipeline_stage',
            'priority',
            'is_hot',
            'hot_reason',
            'assigned_to',
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'company': forms.TextInput(attrs={'class': 'form-control'}),
            'budget': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'step': 1}),
            'interest': forms.Select(attrs={'class': 'form-select'}),
            'passenger_count': forms.TextInput(attrs={'class': 'form-control'}),
            'timeline': forms.TextInput(attrs={'class': 'form-control'}),
            'use_case': forms.TextInput(attrs={'class': 'form-control'}),
            'source': forms.TextInput(attrs={'class': 'form-control'}),
            'source_url': forms.TextInput(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'pipeline_stage': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'hot_reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_to'].queryset = self.fields['assigned_to'].queryset.filter(is_staff=True)
        self.fields['assigned_to'].required = False
        self.fields['pipeline_stage'].initial = Lead.PipelineStage.NEW
        self.fields['pipeline_stage'].required = False
        self.fields['priority'].initial = Lead.Priority.NORMAL
        self.fields['priority'].required = False
        for field_name in (
            'phone_number',
            'company',
            'budget',
            'passenger_count',
            'timeline',
            'use_case',
            'source',
            'source_url',
            'message',
            'hot_reason',
        ):
            self.fields[field_name].required = False
