from django.core.management.base import BaseCommand
from superapp.apps.email.services.sync import EmailSyncService
from superapp.apps.email.models import EmailAddress


class Command(BaseCommand):
    help = 'Synchronize emails from IMAP servers'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email-address-id',
            type=str,
            help='UUID of the email address to sync (optional)'
        )

    def handle(self, *args, **options):
        email_address_id = options.get('email_address_id')
        
        if email_address_id:
            try:
                email_address = EmailAddress.objects.get(id=email_address_id)
                self.stdout.write(f"Syncing emails for {email_address.email}...")
                service = EmailSyncService(
                    email_address_id=email_address_id,
                    force_tls=options.get('force_tls', False),
                    force_ssl=options.get('force_ssl', False)
                )
                service.sync_all_accounts()
                self.stdout.write(self.style.SUCCESS(f"Successfully synced emails for {email_address.email}"))
            except EmailAddress.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Email address with ID {email_address_id} does not exist"))
        else:
            self.stdout.write("Syncing emails for all active email addresses...")
            service = EmailSyncService()
            service.sync_all_accounts()
            self.stdout.write(self.style.SUCCESS("Successfully synced emails for all active email addresses"))
