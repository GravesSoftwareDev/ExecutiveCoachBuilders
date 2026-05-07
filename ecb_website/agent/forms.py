"""Per-provider form for the AgentSettings singleton.

We intentionally edit one provider at a time. This keeps the UI small and
removes the "which field do I fill?" noise.
"""

from django import forms

from agent.models import AgentSettings


class QuotaForm(forms.Form):
    """Admin-editable per-user daily LLM call budget.

    Tiny standalone form so the settings template can render it in its
    own panel, separate from provider keys.
    """

    daily_llm_calls_per_user = forms.IntegerField(
        min_value=0,
        required=True,
        label='Daily LLM calls per user',
        help_text=(
            'Max LLM calls per non-staff user per UTC day. '
            '0 = unlimited. Staff bypass this limit.'
        ),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
    )

    def __init__(self, *args, settings_row: AgentSettings, **kwargs):
        super().__init__(*args, **kwargs)
        self.settings_row = settings_row
        if not self.is_bound:
            self.fields['daily_llm_calls_per_user'].initial = (
                settings_row.daily_llm_calls_per_user
            )

    def save(self) -> AgentSettings:
        row = self.settings_row
        row.daily_llm_calls_per_user = int(
            self.cleaned_data['daily_llm_calls_per_user']
        )
        row.save()
        return row


class ProviderForm(forms.Form):
    """Edits one provider's {model, api_key} on the AgentSettings singleton.

    - `provider` is 'openai' or 'gemini' (fixed per form instance, not a field).
    - Blank api_key means "keep the existing one".
    - A separate POST action='revoke' clears the key (see the view).
    """

    model = forms.CharField(
        max_length=64,
        required=False,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Model name, for example deepseek-v4-flash',
            }
        ),
    )
    api_key = forms.CharField(
        max_length=256,
        required=False,
        widget=forms.PasswordInput(
            render_value=False,
            attrs={
                'autocomplete': 'new-password',
                'class': 'form-control',
                'placeholder': 'Paste a new key (leave blank to keep existing)',
            },
        ),
    )

    def __init__(self, *args, provider: str, settings_row: AgentSettings, **kwargs):
        super().__init__(*args, **kwargs)
        assert provider in {'openai', 'gemini', 'deepseek', 'openrouter'}
        self.provider = provider
        self.settings_row = settings_row
        model_field = f'{provider}_model'
        if not self.is_bound:
            self.fields['model'].initial = getattr(settings_row, model_field, '')

    def save(self) -> AgentSettings:
        row = self.settings_row
        model_field = f'{self.provider}_model'
        key_field = f'{self.provider}_api_key'
        setattr(row, model_field, (self.cleaned_data.get('model') or '').strip())
        new_key = (self.cleaned_data.get('api_key') or '').strip()
        if new_key:
            setattr(row, key_field, new_key)
        row.save()
        return row
