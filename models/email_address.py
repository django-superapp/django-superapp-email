import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _


class EmailAddress(models.Model):
    """
    Email Address model for storing SMTP credentials and configuration
    """
    # Connection type choices
    PLAIN = 'plain'
    SSL = 'ssl'
    TLS = 'tls'
    CONNECTION_CHOICES = [
        (PLAIN, _('Plain (no encryption)')),
        (SSL, _('SSL')),
        (TLS, _('TLS/STARTTLS')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)
    
    email = models.EmailField(_("email address"), unique=True)
    name = models.CharField(_("display name"), max_length=255, blank=True)
    
    # SMTP Configuration
    smtp_connection_type = models.CharField(
        _("SMTP connection type"), 
        max_length=10, 
        choices=CONNECTION_CHOICES,
        default=SSL
    )
    smtp_server = models.CharField(_("SMTP server"), max_length=255)
    smtp_port = models.PositiveIntegerField(_("SMTP port"), default=465)
    smtp_username = models.CharField(_("SMTP username"), max_length=255)
    smtp_password = models.CharField(_("SMTP password"), max_length=255)
    
    # IMAP Configuration for receiving emails
    imap_connection_type = models.CharField(
        _("IMAP connection type"), 
        max_length=10, 
        choices=CONNECTION_CHOICES,
        default=SSL
    )
    imap_server = models.CharField(_("IMAP server"), max_length=255, blank=True)
    imap_port = models.PositiveIntegerField(_("IMAP port"), default=993)
    imap_username = models.CharField(_("IMAP username"), max_length=255, blank=True)
    imap_password = models.CharField(_("IMAP password"), max_length=255, blank=True)
    
    is_active = models.BooleanField(_("is active"), default=True)
    use_idle = models.BooleanField(_("use IDLE for real-time sync"), default=False, 
                                  help_text=_("Enable real-time synchronization using IMAP IDLE"))
    idle_folder = models.CharField(_("IDLE folder"), max_length=255, default="INBOX", 
                                  help_text=_("IMAP folder to monitor with IDLE"))
    
    class Meta:
        verbose_name = _("email address")
        verbose_name_plural = _("email addresses")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} <{self.email}>" if self.name else self.email
