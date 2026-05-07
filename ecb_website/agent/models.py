"""
Singleton row for runtime-configurable agent settings.

Why singleton: there is exactly one active LLM configuration for the whole
portal. Admins edit it in the UI; regular users just consume the result.

Priority rules (see agent/config.py):
    DB value (this model) > environment variable > hard-coded default
"""

from django.conf import settings
from django.db import models


class AgentSettings(models.Model):
    class Provider(models.TextChoices):
        OPENAI = 'openai', 'OpenAI'
        GEMINI = 'gemini', 'Google Gemini'
        DEEPSEEK = 'deepseek', 'DeepSeek'
        OPENROUTER = 'openrouter', 'OpenRouter'

    llm_provider = models.CharField(
        max_length=16,
        choices=Provider.choices,
        blank=True,
        default='',
        help_text='If empty, falls back to LLM_PROVIDER env var.',
    )

    openai_api_key = models.CharField(max_length=256, blank=True, default='')
    openai_model = models.CharField(max_length=64, blank=True, default='')

    gemini_api_key = models.CharField(max_length=256, blank=True, default='')
    gemini_model = models.CharField(max_length=64, blank=True, default='')

    deepseek_api_key = models.CharField(max_length=256, blank=True, default='')
    deepseek_model = models.CharField(max_length=64, blank=True, default='')

    openrouter_api_key = models.CharField(max_length=256, blank=True, default='')
    openrouter_model = models.CharField(max_length=64, blank=True, default='')

    daily_llm_calls_per_user = models.PositiveIntegerField(
        default=0,
        help_text=(
            'Max LLM calls per user per UTC day. 0 = unlimited. '
            'Applies to user-initiated calls (chat Q&A, manual triage, '
            'connection test). Staff users bypass the limit.'
        ),
    )

    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
    )

    class Meta:
        verbose_name = 'Agent settings'
        verbose_name_plural = 'Agent settings'

    def __str__(self) -> str:
        return f'AgentSettings(provider={self.llm_provider or "(env)"})'

    def save(self, *args, **kwargs):
        # Enforce singleton by pinning pk=1.
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls) -> 'AgentSettings':
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class LLMCall(models.Model):
    """One row per outbound LLM request, for observability."""

    class Purpose(models.TextChoices):
        ENRICHMENT = 'enrichment', 'Lead enrichment'
        QA = 'qa', 'Portal lead chat'
        WEBSITE_CHAT = 'website_chat', 'Website visitor chat'
        EMAIL_TRIAGE = 'email_triage', 'Email triage'
        BLOG_DRAFT = 'blog_draft', 'Blog draft helper'
        TEST = 'test', 'Connection test'

    provider = models.CharField(max_length=16)
    model = models.CharField(max_length=64)
    purpose = models.CharField(max_length=16, choices=Purpose.choices, default=Purpose.QA)
    prompt_tokens = models.IntegerField(default=0)
    completion_tokens = models.IntegerField(default=0)
    total_tokens = models.IntegerField(default=0)
    latency_ms = models.IntegerField(default=0)
    success = models.BooleanField(default=True)
    error_kind = models.CharField(max_length=64, blank=True, default='')
    lead_id = models.IntegerField(null=True, blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='llm_calls',
        help_text='The user whose action triggered this call, if any.',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['provider', '-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self) -> str:
        return f'LLMCall({self.provider}/{self.model}, {self.purpose})'
