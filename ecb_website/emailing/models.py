"""
Email integration models.

* EmailSettings — singleton row for SMTP (outbound) and IMAP (inbound) credentials.
* IncomingEmail — one audit row per fetched message (dedup by Message-ID).
"""

from __future__ import annotations

from django.conf import settings as dj_settings
from django.db import models


class EmailSettings(models.Model):
    smtp_enabled = models.BooleanField(default=False)
    smtp_host = models.CharField(max_length=255, blank=True, default='')
    smtp_port = models.PositiveIntegerField(null=True, blank=True)
    smtp_username = models.CharField(max_length=255, blank=True, default='')
    smtp_password = models.CharField(max_length=255, blank=True, default='')
    smtp_use_tls = models.BooleanField(default=True)
    from_address = models.EmailField(blank=True, default='')
    from_name = models.CharField(max_length=120, blank=True, default='')
    signature = models.TextField(
        blank=True,
        default='',
        help_text='Auto-appended to outbound mail (two blank lines above signature).',
    )

    imap_enabled = models.BooleanField(default=False)
    imap_host = models.CharField(max_length=255, blank=True, default='')
    imap_port = models.PositiveIntegerField(null=True, blank=True)
    imap_username = models.CharField(max_length=255, blank=True, default='')
    imap_password = models.CharField(max_length=255, blank=True, default='')
    imap_use_ssl = models.BooleanField(default=True)
    imap_folder = models.CharField(max_length=120, blank=True, default='')

    internal_domains = models.CharField(
        max_length=500,
        blank=True,
        default='',
        help_text='Comma-separated domains we treat as internal (e.g. ecblimo.com).',
    )

    last_poll_at = models.DateTimeField(null=True, blank=True)
    last_poll_status = models.CharField(max_length=255, blank=True, default='')

    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        dj_settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
    )

    class Meta:
        verbose_name = 'Email settings'
        verbose_name_plural = 'Email settings'

    def __str__(self) -> str:
        return f'EmailSettings(smtp={self.smtp_enabled}, imap={self.imap_enabled})'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls) -> 'EmailSettings':
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def internal_domain_list(self) -> list[str]:
        return [d.strip().lower() for d in self.internal_domains.split(',') if d.strip()]


class IncomingEmail(models.Model):
    """Audit row for every IMAP-fetched message before/after linking to a Lead."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending (unmatched)'
        LINKED = 'linked', 'Linked to lead'
        INTERNAL_REPLY = 'internal_reply', 'Internal reply'
        FILTERED = 'filtered', 'Filtered (headers/heuristics)'

    message_id = models.CharField(max_length=998, unique=True)
    in_reply_to = models.CharField(max_length=998, blank=True, default='', db_index=True)
    references = models.TextField(blank=True, default='')

    from_email = models.EmailField()
    from_name = models.CharField(max_length=255, blank=True, default='')
    to_email = models.EmailField(blank=True, default='')
    subject = models.CharField(max_length=998, blank=True, default='')
    body_text = models.TextField(blank=True, default='')
    body_html = models.TextField(blank=True, default='')

    raw_headers = models.JSONField(default=dict, blank=True)
    attachment_names = models.JSONField(default=list, blank=True)

    received_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    status = models.CharField(
        max_length=24,
        choices=Status.choices,
        default=Status.PENDING,
    )
    filter_reason = models.CharField(max_length=120, blank=True, default='')

    lead = models.ForeignKey(
        'leads.Lead',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='incoming_emails',
    )
    linked_message = models.ForeignKey(
        'leads.LeadMessage',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )

    class Meta:
        ordering = ['-received_at']
        indexes = [
            models.Index(fields=['status', '-received_at']),
            models.Index(fields=['from_email']),
        ]

    def __str__(self) -> str:
        return f'IncomingEmail<{self.from_email} "{self.subject[:40]}">'
