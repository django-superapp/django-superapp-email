import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _


class Thread(models.Model):
    """
    Thread model for grouping related emails in a conversation
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)
    
    subject = models.CharField(_("subject"), max_length=255)
    participants = models.JSONField(_("participants"), default=list)  # List of email addresses
    
    # Reference to the email address that owns this thread
    email_address = models.ForeignKey(
        'email.EmailAddress',
        on_delete=models.CASCADE,
        related_name='threads',
        verbose_name=_("email address")
    )
    
    # Optional reference to a contact
    contact = models.ForeignKey(
        'email.Contact',
        on_delete=models.SET_NULL,
        related_name='threads',
        null=True,
        blank=True,
        verbose_name=_("primary contact")
    )
    
    # Metadata
    metadata = models.JSONField(_("metadata"), default=dict, blank=True)
    
    # Status
    is_active = models.BooleanField(_("is active"), default=True)
    is_archived = models.BooleanField(_("is archived"), default=False)
    
    # Last message timestamp
    last_message_at = models.DateTimeField(_("last message at"), null=True, blank=True)
    
    class Meta:
        verbose_name = _("thread")
        verbose_name_plural = _("threads")
        ordering = ['-last_message_at', '-created_at']
    
    def __str__(self):
        return self.subject
