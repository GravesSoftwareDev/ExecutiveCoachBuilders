from django.contrib import admin

from agent.models import AgentSettings


@admin.register(AgentSettings)
class AgentSettingsAdmin(admin.ModelAdmin):
    list_display = ('id', 'llm_provider', 'openai_model', 'gemini_model', 'updated_at', 'updated_by')
    readonly_fields = ('updated_at',)

    def has_add_permission(self, request):
        return not AgentSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
