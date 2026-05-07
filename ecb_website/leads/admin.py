from django.contrib import admin

from .models import Lead, LeadChatSession, LeadMessage


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'interest', 'pipeline_stage', 'priority', 'created_at')
    list_filter = ('interest', 'pipeline_stage', 'priority', 'is_hot')
    search_fields = ('first_name', 'last_name', 'email', 'company', 'message')
    readonly_fields = ('created_at', 'updated_at', 'ai_structured_updated_at')


@admin.register(LeadChatSession)
class LeadChatSessionAdmin(admin.ModelAdmin):
    list_display = ('lead', 'title', 'started_by', 'last_activity_at', 'is_archived')
    list_filter = ('is_archived',)
    search_fields = ('title', 'lead__email', 'lead__first_name', 'lead__last_name')


@admin.register(LeadMessage)
class LeadMessageAdmin(admin.ModelAdmin):
    list_display = ('lead', 'direction', 'channel', 'status', 'is_ai_generated', 'created_at')
    list_filter = ('direction', 'channel', 'status', 'is_ai_generated')
    search_fields = ('lead__email', 'subject', 'body', 'from_email', 'to_email')
