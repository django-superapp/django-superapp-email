from django.contrib import admin
from django.utils.html import format_html
from superapp.apps.admin_portal.admin import SuperAppModelAdmin
from superapp.apps.admin_portal.sites import superapp_admin_site
from superapp.apps.email.models import Email


@admin.register(Email, site=superapp_admin_site)
class EmailAdmin(SuperAppModelAdmin):
    list_display = ['subject', 'from_email', 'direction', 'status', 'created_at']
    list_filter = ['direction', 'status']
    search_fields = ['subject', 'from_email', 'from_name', 'to_emails']
    readonly_fields = ['created_at', 'updated_at', 'sent_at', 'delivered_at', 'message_id', 
                      'in_reply_to', 'references', 'raw_message', 'body_text', 'html_preview']
    autocomplete_fields = ['email_address', 'contact', 'thread']
    fieldsets = (
        (None, {
            'fields': ('email_address', 'thread', 'direction', 'status')
        }),
        ('Sender & Recipients', {
            'fields': ('from_email', 'from_name', 'to_emails', 'cc_emails', 'bcc_emails', 'contact')
        }),
        ('Content', {
            'fields': ('subject', 'body_html', 'html_preview', 'attachments')
        }),
        ('Metadata', {
            'fields': ('message_id', 'in_reply_to', 'references', 'headers', 'metadata')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'sent_at', 'delivered_at')
        }),
        ('Error Information', {
            'fields': ('error_code', 'error_message')
        }),
        ('Raw Data', {
            'fields': ('raw_message',),
            'classes': ('collapse',)
        }),
    )
    
    def html_preview(self, obj):
        """Display HTML preview with proper styling"""
        if not obj.body_html:
            return "-"
        
        return format_html(
            '<div style="max-width:800px; max-height:400px; overflow:auto; '
            'border:1px solid #ccc; padding:10px; background-color:#fff;">{}</div>',
            obj.body_html
        )
    
    html_preview.short_description = "HTML Preview"
