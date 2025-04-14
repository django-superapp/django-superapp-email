from django.contrib import admin
from superapp.apps.admin_portal.admin import SuperAppModelAdmin
from superapp.apps.admin_portal.sites import superapp_admin_site
from superapp.apps.email.models import Thread


@admin.register(Thread, site=superapp_admin_site)
class ThreadAdmin(SuperAppModelAdmin):
    list_display = ['subject', 'email_address', 'contact', 'is_active', 'is_archived', 'last_message_at', 'created_at']
    list_filter = ['is_active', 'is_archived']
    search_fields = ['subject', 'participants']
    readonly_fields = ['created_at', 'updated_at', 'last_message_at']
    autocomplete_fields = ['email_address', 'contact']
    fieldsets = (
        (None, {
            'fields': ('subject', 'email_address', 'contact', 'is_active', 'is_archived')
        }),
        ('Participants', {
            'fields': ('participants',)
        }),
        ('Metadata', {
            'fields': ('metadata',)
        }),
        ('Timestamps', {
            'fields': ('last_message_at', 'created_at', 'updated_at')
        }),
    )
