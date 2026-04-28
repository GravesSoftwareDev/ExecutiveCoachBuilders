from django.contrib import admin
from .models import SiteSetting

# Register your models here.
@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
        
    model = SiteSetting
    list_display = ['name', 'file_value', 'text_value', 'file']
    list_display_links = None
    search_fields = ['name', 'file_value', 'text_value', 'file']
    list_editable = ['name', 'file_value', 'text_value', 'file']