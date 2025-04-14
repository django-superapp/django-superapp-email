from celery import shared_task
from superapp.apps.email.services.sync import EmailSyncService
from superapp.apps.email.services.delivery import EmailDeliveryService


@shared_task
def sync_all_email_accounts():
    """
    Synchronize all email accounts
    """
    service = EmailSyncService()
    service.sync_all_accounts()


@shared_task
def sync_email_account(email_address_id):
    """
    Synchronize a specific email account
    
    Args:
        email_address_id: UUID of the email address to sync
    """
    service = EmailSyncService(email_address_id=email_address_id)
    service.sync_all_accounts()


@shared_task
def deliver_pending_emails():
    """
    Deliver all pending outgoing emails
    """
    service = EmailDeliveryService()
    service.deliver_pending_emails()


@shared_task
def deliver_email(email_id):
    """
    Deliver a specific email
    
    Args:
        email_id: UUID of the email to deliver
    """
    service = EmailDeliveryService(email_id=email_id)
    service.deliver_pending_emails()
