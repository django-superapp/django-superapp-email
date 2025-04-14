import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _


class Contact(models.Model):
    """
    Contact model for storing details of external email contacts
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)
    
    email = models.EmailField(_("email address"), unique=True)
    name = models.CharField(_("name"), max_length=255, blank=True)
    
    # Additional contact information
    company = models.CharField(_("company"), max_length=255, blank=True)
    job_title = models.CharField(_("job title"), max_length=255, blank=True)
    phone_number = models.CharField(_("phone number"), max_length=50, blank=True)
    
    # Metadata
    notes = models.TextField(_("notes"), blank=True)
    metadata = models.JSONField(_("metadata"), default=dict, blank=True)
    
    # Status
    is_active = models.BooleanField(_("is active"), default=True)
    
    class Meta:
        verbose_name = _("contact")
        verbose_name_plural = _("contacts")
        ordering = ['name', 'email']
    
    def __str__(self):
        return f"{self.name} <{self.email}>" if self.name else self.email
