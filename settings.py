from django.utils.translation import gettext_lazy as _
from django.urls import reverse_lazy


def extend_superapp_settings(main_settings):
    """
    Extend the main settings with email app specific settings
    """
    main_settings['INSTALLED_APPS'] += ['superapp.apps.email']
    
    # Add Celery beat schedule for email tasks
    if 'CELERY_BEAT_SCHEDULE' not in main_settings:
        main_settings['CELERY_BEAT_SCHEDULE'] = {}
    
    main_settings['CELERY_BEAT_SCHEDULE'].update({
        'sync_all_email_accounts': {
            'task': 'superapp.apps.email.tasks.sync_all_email_accounts',
            'schedule': 300.0,  # Every 5 minutes
        },
        'deliver_pending_emails': {
            'task': 'superapp.apps.email.tasks.deliver_pending_emails',
            'schedule': 60.0,  # Every minute
        },
    })
    
    # Add admin navigation for the email app
    main_settings['UNFOLD']['SIDEBAR']['navigation'] = main_settings['UNFOLD']['SIDEBAR'].get('navigation', []) + [
        {
            "title": _("Email"),
            "icon": "email",
            "items": [
                {
                    "title": lambda request: _("Email Addresses"),
                    "icon": "alternate_email",
                    "link": reverse_lazy("admin:email_emailaddress_changelist"),
                    "permission": lambda request: request.user.has_perm("email.view_emailaddress"),
                },
                {
                    "title": lambda request: _("Threads"),
                    "icon": "forum",
                    "link": reverse_lazy("admin:email_thread_changelist"),
                    "permission": lambda request: request.user.has_perm("email.view_thread"),
                },
                {
                    "title": lambda request: _("Emails"),
                    "icon": "mail",
                    "link": reverse_lazy("admin:email_email_changelist"),
                    "permission": lambda request: request.user.has_perm("email.view_email"),
                },
                {
                    "title": lambda request: _("Contacts"),
                    "icon": "contacts",
                    "link": reverse_lazy("admin:email_contact_changelist"),
                    "permission": lambda request: request.user.has_perm("email.view_contact"),
                },
            ]
        },
    ]

