from django.core.management.base import BaseCommand
from superapp.apps.email.services.delivery import EmailDeliveryService
from superapp.apps.email.models import Email


class Command(BaseCommand):
    help = 'Deliver pending outgoing emails'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email-id',
            type=str,
            help='UUID of the email to deliver (optional)'
        )
        parser.add_argument(
            '--retry-errors',
            action='store_true',
            help='Retry emails in error state'
        )

    def handle(self, *args, **options):
        email_id = options.get('email_id')
        retry_errors = options.get('retry_errors', False)
        
        if email_id:
            try:
                email_obj = Email.objects.get(id=email_id)
                self.stdout.write(f"Delivering email {email_id}...")
                service = EmailDeliveryService(
                    email_id=email_id,
                    force_tls=options.get('force_tls', False),
                    force_ssl=options.get('force_ssl', False)
                )
                service.deliver_pending_emails(retry_errors=retry_errors)
                self.stdout.write(self.style.SUCCESS(f"Successfully delivered email {email_id}"))
            except Email.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Email with ID {email_id} does not exist"))
        else:
            if retry_errors:
                self.stdout.write("Delivering all pending emails and retrying failed emails...")
            else:
                self.stdout.write("Delivering all pending emails...")
            
            service = EmailDeliveryService()
            service.deliver_pending_emails(retry_errors=retry_errors)
            
            if retry_errors:
                self.stdout.write(self.style.SUCCESS("Successfully processed all pending and failed emails"))
            else:
                self.stdout.write(self.style.SUCCESS("Successfully delivered all pending emails"))
