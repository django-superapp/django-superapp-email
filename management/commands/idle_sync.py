import time
import signal
import sys
import logging
from django.core.management.base import BaseCommand
from superapp.apps.email.services.idle_sync import IdleSyncManager
from superapp.apps.email.models import EmailAddress

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Start real-time IMAP synchronization using IDLE'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email-address-id',
            type=str,
            help='UUID of the email address to monitor (optional)'
        )
        parser.add_argument(
            '--reconnect-interval',
            type=int,
            default=300,  # 5 minutes
            help='Interval in seconds to check and reconnect idle clients'
        )
        parser.add_argument(
            '--max-failures',
            type=int,
            default=10,
            help='Maximum number of consecutive failures before giving up on an account'
        )

    def handle(self, *args, **options):
        email_address_id = options.get('email_address_id')
        reconnect_interval = options.get('reconnect_interval')
        max_failures = options.get('max_failures')
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.handle_exit)
        signal.signal(signal.SIGTERM, self.handle_exit)
        
        self.manager = IdleSyncManager()
        self.running = True
        self.failure_counts = {}  # Track consecutive failures by email address
        
        if email_address_id:
            try:
                email_address = EmailAddress.objects.get(id=email_address_id)
                if not email_address.use_idle:
                    self.stdout.write(self.style.WARNING(
                        f"IDLE is not enabled for {email_address.email}. Enable it in the admin interface."
                    ))
                    return
                
                self.stdout.write(f"Starting IDLE sync for {email_address.email}...")
                self.manager.start_client(email_address_id)
                
                # Keep the command running with connection monitoring
                last_check = time.time()
                while self.running:
                    current_time = time.time()
                    
                    # Check connections periodically
                    if current_time - last_check > reconnect_interval:
                        self.check_and_restart_client(email_address_id, max_failures)
                        last_check = current_time
                    
                    time.sleep(1)
                
            except EmailAddress.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Email address with ID {email_address_id} does not exist"))
        else:
            self.stdout.write("Starting IDLE sync for all email addresses with IDLE enabled...")
            self.manager.start()
            
            # Keep the command running with connection monitoring for all clients
            last_check = time.time()
            while self.running:
                current_time = time.time()
                
                # Check all connections periodically
                if current_time - last_check > reconnect_interval:
                    self.check_and_restart_all_clients(max_failures)
                    last_check = current_time
                
                time.sleep(1)
    
    def check_and_restart_client(self, email_address_id, max_failures):
        """Check if a client is still connected and restart if needed"""
        client = self.manager.clients.get(email_address_id)
        
        if not client:
            # Client not found, try to start it
            self.stdout.write(self.style.WARNING(f"Client for {email_address_id} not found, restarting..."))
            self.manager.start_client(email_address_id)
            return
        
        if not client.running or not client.client or not client.idle_thread or not client.idle_thread.is_alive():
            # Client is not running properly
            failure_count = self.failure_counts.get(email_address_id, 0) + 1
            self.failure_counts[email_address_id] = failure_count
            
            if failure_count > max_failures:
                self.stdout.write(self.style.ERROR(
                    f"Too many consecutive failures ({failure_count}) for {client.email_address.email}, giving up"
                ))
                # Remove from active clients but don't try to restart anymore
                self.manager.stop_client(email_address_id)
                return
            
            self.stdout.write(self.style.WARNING(
                f"Client for {client.email_address.email} is not running properly (attempt {failure_count}/{max_failures}), restarting..."
            ))
            
            # Stop and restart the client
            self.manager.stop_client(email_address_id)
            time.sleep(2)  # Give it a moment before restarting
            self.manager.start_client(email_address_id)
        else:
            # Client is running, reset failure count
            if email_address_id in self.failure_counts:
                del self.failure_counts[email_address_id]
    
    def check_and_restart_all_clients(self, max_failures):
        """Check all clients and restart any that are not connected"""
        # Get a list of all email addresses with IDLE enabled
        email_addresses = EmailAddress.objects.filter(is_active=True, use_idle=True)
        active_ids = set(str(email.id) for email in email_addresses)
        
        # Check existing clients
        for email_address_id in list(self.manager.clients.keys()):
            if email_address_id not in active_ids:
                # Email address no longer active or IDLE disabled
                self.stdout.write(f"Email address {email_address_id} no longer active or IDLE disabled, stopping client")
                self.manager.stop_client(email_address_id)
            else:
                # Check and restart if needed
                self.check_and_restart_client(email_address_id, max_failures)
        
        # Start clients for any new email addresses
        for email_address in email_addresses:
            email_address_id = str(email_address.id)
            if email_address_id not in self.manager.clients:
                self.stdout.write(f"Starting new IDLE client for {email_address.email}")
                self.manager.start_client(email_address_id)
    
    def handle_exit(self, sig, frame):
        """Handle exit signals"""
        self.stdout.write("\nStopping IDLE sync...")
        self.running = False
        if hasattr(self, 'manager'):
            self.manager.stop()
        sys.exit(0)
