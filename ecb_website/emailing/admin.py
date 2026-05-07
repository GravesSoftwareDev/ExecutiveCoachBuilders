from django.contrib import admin

from .models import EmailSettings, IncomingEmail


@admin.register(EmailSettings)
class EmailSettingsAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'from_address', 'smtp_enabled', 'imap_enabled', 'last_poll_at')


@admin.register(IncomingEmail)
class IncomingEmailAdmin(admin.ModelAdmin):
    list_display = ('from_email', 'subject', 'status', 'received_at', 'lead')
    list_filter = ('status',)
    search_fields = ('from_email', 'subject', 'message_id')
    readonly_fields = ('message_id', 'created_at', 'raw_headers')
