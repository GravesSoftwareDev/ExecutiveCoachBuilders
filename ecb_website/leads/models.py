from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models

phone_regex = RegexValidator(
    regex=r'^\+?\(?\d{1,4}\)?[\s\-\.\d]{5,20}$',
    message='Please enter a valid phone number.',
)


class Lead(models.Model):
    class Interest(models.TextChoices):
        BUS = 'BUS', 'Bus'
        COACH = 'COACH', 'Coach'
        SPRINTER = 'SPRINTER', 'Sprinter Van'
        CUSTOM = 'CUSTOM', 'Custom'

    class PipelineStage(models.TextChoices):
        NEW = 'new', 'New'
        IN_PROGRESS = 'in_progress', 'In progress'
        CLOSED = 'closed', 'Closed'

    class Priority(models.TextChoices):
        NORMAL = 'normal', 'Normal'
        HIGH = 'high', 'High'

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    phone_number = models.CharField(max_length=25, blank=True, validators=[phone_regex])
    company = models.CharField(blank=True, null=True, max_length=255)
    budget = models.IntegerField(blank=True, null=True)
    interest = models.CharField(max_length=20, choices=Interest.choices, default=Interest.CUSTOM)
    passenger_count = models.CharField(max_length=60, blank=True, default='')
    timeline = models.CharField(max_length=120, blank=True, default='')
    use_case = models.CharField(max_length=160, blank=True, default='')
    source = models.CharField(max_length=80, blank=True, default='')
    source_url = models.CharField(max_length=255, blank=True, default='')
    message = models.TextField(blank=True, default='')

    pipeline_stage = models.CharField(
        max_length=32,
        choices=PipelineStage.choices,
        default=PipelineStage.NEW,
    )
    priority = models.CharField(
        max_length=16,
        choices=Priority.choices,
        default=Priority.NORMAL,
    )

    is_hot = models.BooleanField(default=False)
    hot_reason = models.TextField(blank=True, default='')

    ai_structured = models.JSONField(default=dict, blank=True)
    ai_structured_updated_at = models.DateTimeField(null=True, blank=True)

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_leads',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.first_name} {self.last_name} <{self.email}>'


class LeadChatSession(models.Model):
    """
    A single threaded AI-assistant conversation about a Lead.
    One session groups multiple LeadMessage rows (channel=chat) so we can
    render, title, archive, or summarize conversations as units.
    """
    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        related_name='chat_sessions',
    )
    title = models.CharField(max_length=200, blank=True, default='')
    started_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='chat_sessions',
    )
    is_archived = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    last_activity_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-last_activity_at']
        indexes = [
            models.Index(fields=['lead', '-last_activity_at']),
        ]

    def __str__(self) -> str:
        return f'ChatSession #{self.pk} for Lead {self.lead_id}'

    @property
    def display_title(self) -> str:
        return self.title or 'Untitled conversation'


class LeadMessage(models.Model):
    """
    A single row on a Lead's timeline. Covers form submissions, inbound/outbound
    emails (including AI drafts awaiting human send), notes, and system events.
    Shape is intentionally uniform across sources; differences live in
    direction/channel/status.
    """

    class Direction(models.TextChoices):
        IN = 'in', 'Inbound'
        OUT = 'out', 'Outbound'
        INTERNAL = 'internal', 'Internal'

    class Channel(models.TextChoices):
        FORM = 'form', 'Website form'
        EMAIL = 'email', 'Email'
        NOTE = 'note', 'Note'
        SYSTEM = 'system', 'System'
        CHAT = 'chat', 'Assistant chat'

    class Status(models.TextChoices):
        RECEIVED = 'received', 'Received'
        DRAFT = 'draft', 'Draft'
        SENT = 'sent', 'Sent'
        LOGGED = 'logged', 'Logged'

    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        related_name='messages',
    )
    direction = models.CharField(max_length=16, choices=Direction.choices)
    channel = models.CharField(max_length=16, choices=Channel.choices)
    status = models.CharField(max_length=16, choices=Status.choices)

    subject = models.CharField(max_length=998, blank=True, default='')
    body = models.TextField(blank=True, default='')

    # Email threading: for outbound we generate this when actually sent; for
    # inbound it comes from the provider's parsed headers. Unused for form/note.
    message_id = models.CharField(max_length=998, blank=True, default='')
    in_reply_to = models.CharField(max_length=998, blank=True, default='')

    # Real addresses seen on the wire (may differ from Lead.email when a
    # contact writes from a secondary address).
    from_email = models.EmailField(blank=True, default='')
    to_email = models.EmailField(blank=True, default='')

    is_ai_generated = models.BooleanField(default=False)

    metadata = models.JSONField(default=dict, blank=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lead_messages',
        help_text='Employee who created or sent this message, if any.',
    )
    chat_session = models.ForeignKey(
        'LeadChatSession',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='messages',
        help_text='Set only for channel=chat messages.',
    )

    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['lead', 'created_at']),
            models.Index(fields=['direction', 'channel']),
            models.Index(fields=['chat_session', 'created_at']),
            models.Index(fields=['message_id']),
            models.Index(fields=['in_reply_to']),
        ]

    def __str__(self) -> str:
        return f'{self.direction}/{self.channel} @ {self.created_at:%Y-%m-%d %H:%M}'
