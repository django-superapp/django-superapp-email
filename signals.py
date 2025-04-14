from django.db.models.signals import post_save
from django.dispatch import receiver
from superapp.apps.email.models import Email
from superapp.apps.email.tasks import deliver_email


@receiver(post_save, sender=Email)
def handle_email_post_save(sender, instance, created, **kwargs):
    """
    Handle post-save signal for Email model
    
    If a new outgoing email is created with status 'draft', queue it for delivery
    """
    if created and instance.direction == 'outgoing' and instance.status == 'draft':
        # Queue the email for delivery
        deliver_email.delay(str(instance.id))
