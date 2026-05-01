from django.contrib import admin
from .models import Contact
from .models import Service

# Register your models here.
@admin.register(Contact)
class contactAdmin(admin.ModelAdmin):
    list_display = ['firstname', 'lastname', 'email']
    search_fields = ['firstname', 'lastname', 'email', 'message']

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['title', 'label', 'display_order', 'is_active']
    search_fields = ['title', 'label']
    ordering = ['display_order']