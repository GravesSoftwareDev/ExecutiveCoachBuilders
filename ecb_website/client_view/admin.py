from django.contrib import admin
from .models import Contact

# Register your models here.
@admin.register(Contact)
class contactAdmin(admin.ModelAdmin):
    list_display = ['firstname', 'lastname', 'email']
    search_fields = ['firstname', 'lastname', 'email', 'message']