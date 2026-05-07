from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Employee


@admin.register(Employee)
class EmployeeAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Portal Permissions', {
            'fields': ('role', 'can_edit_site', 'can_edit_fleet', 'can_edit_blog', 'can_edit_services', 'can_edit_team'),
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Portal Permissions', {
            'fields': ('role', 'can_edit_site', 'can_edit_fleet', 'can_edit_blog', 'can_edit_services', 'can_edit_team'),
        }),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff', 'is_active')
    list_filter = UserAdmin.list_filter + ('role',)
