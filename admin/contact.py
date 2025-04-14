from django.contrib import admin
from superapp.apps.admin_portal.admin import SuperAppModelAdmin
from superapp.apps.admin_portal.sites import superapp_admin_site
from superapp.apps.email.models import Contact


@admin.register(Contact, site=superapp_admin_site)
class ContactAdmin(SuperAppModelAdmin):
    list_display = ['email', 'name', 'company', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['email', 'name', 'company']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        (None, {
            'fields': ('email', 'name', 'is_active')
        }),
        ('Additional Information', {
            'fields': ('company', 'job_title', 'phone_number', 'notes')
        }),
        ('Metadata', {
            'fields': ('metadata',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
