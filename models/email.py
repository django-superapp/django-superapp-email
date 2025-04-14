import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


class Email(models.Model):
    """
    Email model for storing sent and received emails
    """
    DIRECTION_CHOICES = (
        ('incoming', _('Incoming')),
        ('outgoing', _('Outgoing')),
    )
    
    STATUS_CHOICES = (
        ('draft', _('Draft')),
        ('sending', _('Sending')),
        ('sent', _('Sent')),
        ('delivered', _('Delivered')),
        ('failed', _('Failed')),
        ('received', _('Received')),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)
    
    email_address = models.ForeignKey(
        'email.EmailAddress',
        on_delete=models.CASCADE,
        related_name='emails',
        verbose_name=_("email address")
    )
    
    # Thread reference
    thread = models.ForeignKey(
        'email.Thread',
        on_delete=models.CASCADE,
        related_name='emails',
        null=True,
        blank=True,
        verbose_name=_("thread")
    )
    
    direction = models.CharField(
        _("direction"),
        max_length=10,
        choices=DIRECTION_CHOICES,
        default='outgoing'
    )
    
    status = models.CharField(
        _("status"),
        max_length=10,
        choices=STATUS_CHOICES,
        default='draft'
    )
    
    message_id = models.CharField(_("message ID"), max_length=255, blank=True)
    in_reply_to = models.CharField(_("in reply to"), max_length=255, blank=True)
    references = models.TextField(_("references"), blank=True)
    
    # Sender and recipients
    from_email = models.EmailField(_("from email"))
    from_name = models.CharField(_("from name"), max_length=255, blank=True)
    to_emails = models.JSONField(_("to emails"), default=list)  # List of email addresses
    cc_emails = models.JSONField(_("cc emails"), default=list, blank=True)  # List of email addresses
    bcc_emails = models.JSONField(_("bcc emails"), default=list, blank=True)  # List of email addresses
    
    # Content
    subject = models.CharField(_("subject"), max_length=255)
    body_text = models.TextField(_("body text"), blank=True)
    body_html = models.TextField(_("body HTML"), blank=True)
    
    # Attachments can be handled through a separate model or file field
    attachments = models.JSONField(_("attachments"), default=list, blank=True)  # List of attachment metadata
    
    # Metadata
    headers = models.JSONField(_("headers"), default=dict, blank=True)
    metadata = models.JSONField(_("metadata"), default=dict, blank=True)
    
    # Timestamps
    sent_at = models.DateTimeField(_("sent at"), null=True, blank=True)
    delivered_at = models.DateTimeField(_("delivered at"), null=True, blank=True)
    
    # Error handling
    error_message = models.TextField(_("error message"), blank=True)
    error_code = models.CharField(_("error code"), max_length=50, blank=True)
    
    # For incoming emails, reference to the contact
    contact = models.ForeignKey(
        'email.Contact',
        on_delete=models.SET_NULL,
        related_name='emails',
        null=True,
        blank=True,
        verbose_name=_("contact")
    )
    
    # Raw email data
    raw_message = models.TextField(_("raw message"), blank=True)
    
    class Meta:
        verbose_name = _("email")
        verbose_name_plural = _("emails")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.subject} ({self.get_direction_display()})"
    
    def save(self, *args, **kwargs):
        # If this is a new outgoing email without a thread, create one
        if not self.pk and self.direction == 'outgoing' and not self.thread:
            from superapp.apps.email.models import Thread
            
            # Create a new thread
            thread = Thread.objects.create(
                subject=self.subject,
                participants=self.to_emails + ([self.from_email] if self.from_email else []),
                email_address=self.email_address,
                contact=self.contact,
                last_message_at=timezone.now()
            )
            self.thread = thread
        
        # If this is a new email with a thread, update the thread's last_message_at
        elif self.thread:
            self.thread.last_message_at = timezone.now()
            self.thread.save(update_fields=['last_message_at', 'updated_at'])
        
        super().save(*args, **kwargs)
