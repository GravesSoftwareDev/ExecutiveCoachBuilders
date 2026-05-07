"""Settings forms for SMTP / IMAP (blank password keeps existing)."""

from __future__ import annotations

from django import forms

from emailing.models import EmailSettings

_PASSWORD_WIDGET = forms.PasswordInput(
    render_value=False,
    attrs={
        'autocomplete': 'new-password',
        'placeholder': 'Leave blank to keep existing',
        'class': 'form-control',
    },
)


class SmtpForm(forms.Form):
    smtp_enabled = forms.BooleanField(required=False)
    smtp_host = forms.CharField(max_length=255, required=False)
    smtp_port = forms.IntegerField(required=False, min_value=1, max_value=65535)
    smtp_username = forms.CharField(max_length=255, required=False)
    smtp_password = forms.CharField(max_length=255, required=False, widget=_PASSWORD_WIDGET)
    smtp_use_tls = forms.BooleanField(required=False)
    from_address = forms.EmailField(required=False)
    from_name = forms.CharField(max_length=120, required=False)
    signature = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
    )

    def __init__(self, *args, settings_row: EmailSettings, **kwargs):
        super().__init__(*args, **kwargs)
        self.settings_row = settings_row
        if not self.is_bound:
            for name in (
                'smtp_enabled', 'smtp_host', 'smtp_port', 'smtp_username',
                'smtp_use_tls', 'from_address', 'from_name', 'signature',
            ):
                self.fields[name].initial = getattr(settings_row, name)
            for fn in self.fields:
                w = self.fields[fn].widget.attrs.get('class')
                if fn not in ('signature', 'smtp_password') and isinstance(
                    self.fields[fn].widget, (forms.TextInput, forms.EmailInput, forms.NumberInput),
                ):
                    self.fields[fn].widget.attrs.setdefault('class', 'form-control')

    def save(self) -> EmailSettings:
        row = self.settings_row
        row.smtp_enabled = bool(self.cleaned_data.get('smtp_enabled'))
        row.smtp_host = (self.cleaned_data.get('smtp_host') or '').strip()
        row.smtp_port = self.cleaned_data.get('smtp_port') or None
        row.smtp_username = (self.cleaned_data.get('smtp_username') or '').strip()
        new_pwd = (self.cleaned_data.get('smtp_password') or '').strip()
        if new_pwd:
            row.smtp_password = new_pwd
        row.smtp_use_tls = bool(self.cleaned_data.get('smtp_use_tls'))
        row.from_address = (self.cleaned_data.get('from_address') or '').strip()
        row.from_name = (self.cleaned_data.get('from_name') or '').strip()
        row.signature = (self.cleaned_data.get('signature') or '').rstrip()
        row.save()
        return row


class ImapForm(forms.Form):
    imap_enabled = forms.BooleanField(required=False)
    imap_host = forms.CharField(max_length=255, required=False)
    imap_port = forms.IntegerField(required=False, min_value=1, max_value=65535)
    imap_username = forms.CharField(max_length=255, required=False)
    imap_password = forms.CharField(max_length=255, required=False, widget=_PASSWORD_WIDGET)
    imap_use_ssl = forms.BooleanField(required=False)
    imap_folder = forms.CharField(max_length=120, required=False)
    internal_domains = forms.CharField(
        max_length=500,
        required=False,
        help_text='Comma-separated (e.g. ecblimo.com)',
    )

    def __init__(self, *args, settings_row: EmailSettings, **kwargs):
        super().__init__(*args, **kwargs)
        self.settings_row = settings_row
        if not self.is_bound:
            for name in (
                'imap_enabled', 'imap_host', 'imap_port', 'imap_username',
                'imap_use_ssl', 'imap_folder', 'internal_domains',
            ):
                self.fields[name].initial = getattr(settings_row, name)
        for fname in ('imap_host', 'imap_port', 'imap_username', 'imap_folder', 'internal_domains'):
            self.fields[fname].widget.attrs.setdefault('class', 'form-control')

    def save(self) -> EmailSettings:
        row = self.settings_row
        row.imap_enabled = bool(self.cleaned_data.get('imap_enabled'))
        row.imap_host = (self.cleaned_data.get('imap_host') or '').strip()
        row.imap_port = self.cleaned_data.get('imap_port') or None
        row.imap_username = (self.cleaned_data.get('imap_username') or '').strip()
        new_pwd = (self.cleaned_data.get('imap_password') or '').strip()
        if new_pwd:
            row.imap_password = new_pwd
        row.imap_use_ssl = bool(self.cleaned_data.get('imap_use_ssl'))
        folder = (self.cleaned_data.get('imap_folder') or '').strip()
        row.imap_folder = folder or 'INBOX'
        row.internal_domains = (self.cleaned_data.get('internal_domains') or '').strip()
        row.save()
        return row
