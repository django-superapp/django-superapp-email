import logging
import time
import signal
import threading
import queue
from imapclient import IMAPClient
from django.utils import timezone
from django.db import transaction
from superapp.apps.email.models import EmailAddress
from superapp.apps.email.services.sync import EmailSyncService

logger = logging.getLogger(__name__)

class IMAPIdleClient:
    """
    Client for real-time IMAP synchronization using IDLE
    """
    
    def __init__(self, email_address_id):
        """
        Initialize the IDLE client
        
        Args:
            email_address_id: UUID of the email address to monitor
        """
        self.email_address_id = email_address_id
        self.email_address = EmailAddress.objects.get(id=email_address_id)
        self.client = None
        self.running = False
        self.idle_thread = None
        self.event_queue = queue.Queue()
        self.last_check = timezone.now()
        self.sync_service = EmailSyncService(email_address_id=email_address_id)
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)
    
    def connect(self):
        """
        Connect to the IMAP server
        """
        if self.client:
            try:
                self.client.logout()
            except:
                pass
            self.client = None
        
        try:
            # Connect to the IMAP server
            if self.email_address.imap_connection_type == EmailAddress.SSL:
                self.client = IMAPClient(
                    self.email_address.imap_server, 
                    port=self.email_address.imap_port,
                    ssl=True
                )
            elif self.email_address.imap_connection_type == EmailAddress.TLS:
                self.client = IMAPClient(
                    self.email_address.imap_server, 
                    port=self.email_address.imap_port,
                    ssl=False,
                    use_uid=True
                )
                self.client.starttls()
            else:
                self.client = IMAPClient(
                    self.email_address.imap_server, 
                    port=self.email_address.imap_port,
                    ssl=False
                )
            
            # Login
            self.client.login(self.email_address.imap_username, self.email_address.imap_password)
            
            # Select the folder to monitor
            folder = self.email_address.idle_folder or 'INBOX'
            self.client.select_folder(folder)
            
            logger.info(f"Connected to IMAP server for {self.email_address.email}")
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to IMAP server for {self.email_address.email}: {str(e)}")
            self.client = None
            return False
    
    def idle_loop(self):
        """
        Run the IDLE loop in a separate thread
        """
        logger.info(f"Starting IDLE loop for {self.email_address.email}")
        
        while self.running:
            try:
                if not self.client:
                    logger.warning(f"No IMAP client for {self.email_address.email}, reconnecting...")
                    if not self.connect():
                        # Failed to connect, wait before retrying
                        time.sleep(30)
                        continue
                
                # Start IDLE mode
                self.client.idle()
                
                # Wait for up to 10 minutes for an event
                responses = self.client.idle_check(timeout=600)
                
                # End IDLE mode
                self.client.idle_done()
                
                # Process responses
                if responses:
                    logger.debug(f"IDLE responses for {self.email_address.email}: {responses}")
                    self.event_queue.put(responses)
                
                # Check if we need to reconnect (every 29 minutes to prevent timeouts)
                if (timezone.now() - self.last_check).total_seconds() > 1740:  # 29 minutes
                    logger.debug(f"Refreshing IMAP connection for {self.email_address.email}")
                    try:
                        self.client.noop()  # Send NOOP to keep connection alive
                        self.last_check = timezone.now()
                    except Exception as e:
                        logger.warning(f"Error refreshing connection for {self.email_address.email}: {str(e)}")
                        # Force reconnection
                        self.event_queue.put(None)
                        break
                
            except ConnectionError as e:
                logger.error(f"Connection error in IDLE loop for {self.email_address.email}: {str(e)}")
                self.event_queue.put(None)  # Signal to reconnect
                time.sleep(5)  # Wait before reconnecting
                break
            except TimeoutError as e:
                logger.error(f"Timeout error in IDLE loop for {self.email_address.email}: {str(e)}")
                self.event_queue.put(None)  # Signal to reconnect
                time.sleep(5)  # Wait before reconnecting
                break
            except Exception as e:
                logger.error(f"Error in IDLE loop for {self.email_address.email}: {e.__class__.__name__}: {str(e)}")
                self.event_queue.put(None)  # Signal to reconnect
                time.sleep(5)  # Wait before reconnecting
                break
    
    def process_events(self):
        """
        Process events from the IDLE loop
        """
        reconnect_attempts = 0
        max_reconnect_attempts = 5
        reconnect_delay = 30  # seconds
        
        while self.running:
            try:
                # Get an event from the queue
                event = self.event_queue.get(timeout=1)
                
                if event is None:
                    # Reconnect signal
                    reconnect_attempts += 1
                    backoff_delay = min(reconnect_delay * reconnect_attempts, 300)  # Max 5 minutes
                    
                    logger.info(f"Reconnecting to IMAP server for {self.email_address.email} (attempt {reconnect_attempts})")
                    
                    if self.connect():
                        # Restart the IDLE thread
                        self.start_idle_thread()
                        reconnect_attempts = 0  # Reset counter on successful connection
                    else:
                        # Wait before trying again with exponential backoff
                        logger.warning(
                            f"Failed to reconnect to IMAP server for {self.email_address.email}, "
                            f"retrying in {backoff_delay} seconds..."
                        )
                        time.sleep(backoff_delay)
                        
                        # If we've tried too many times, pause for longer
                        if reconnect_attempts >= max_reconnect_attempts:
                            logger.error(
                                f"Failed to reconnect after {max_reconnect_attempts} attempts for "
                                f"{self.email_address.email}, pausing for 10 minutes"
                            )
                            time.sleep(600)  # 10 minutes
                            reconnect_attempts = 0  # Reset counter
                else:
                    # Process the event
                    has_new_mail = False
                    for response in event:
                        if response[1] == b'EXISTS' or response[1] == b'RECENT':
                            has_new_mail = True
                            break
                    
                    if has_new_mail:
                        logger.info(f"New mail detected for {self.email_address.email}, syncing...")
                        try:
                            # Sync the account
                            with transaction.atomic():
                                self.sync_service.sync_account(self.email_address)
                        except Exception as e:
                            logger.error(f"Error syncing account {self.email_address.email}: {e.__class__.__name__}: {str(e)}")
                            # If sync fails, we might need to reconnect
                            if "Connection" in str(e) or "socket" in str(e) or "timeout" in str(e).lower():
                                logger.warning(f"Connection issue detected, triggering reconnect for {self.email_address.email}")
                                self.event_queue.put(None)  # Signal to reconnect
                
                self.event_queue.task_done()
                
            except queue.Empty:
                # No events, continue
                pass
            except Exception as e:
                logger.error(f"Error processing events for {self.email_address.email}: {e.__class__.__name__}: {str(e)}")
                time.sleep(5)
                
                # If there's a serious error, try to reconnect
                if "Connection" in str(e) or "socket" in str(e) or "timeout" in str(e).lower():
                    logger.warning(f"Connection issue detected in event processing, triggering reconnect for {self.email_address.email}")
                    self.event_queue.put(None)  # Signal to reconnect
    
    def start_idle_thread(self):
        """
        Start the IDLE thread
        """
        if self.idle_thread and self.idle_thread.is_alive():
            return
        
        self.idle_thread = threading.Thread(target=self.idle_loop)
        self.idle_thread.daemon = True
        self.idle_thread.start()
    
    def start(self):
        """
        Start the IDLE client
        """
        if self.running:
            return
        
        self.running = True
        
        # Connect to the IMAP server
        if not self.connect():
            logger.error(f"Failed to connect to IMAP server for {self.email_address.email}")
            self.running = False
            return False
        
        # Start the IDLE thread
        self.start_idle_thread()
        
        # Start processing events
        self.process_events()
        
        return True
    
    def stop(self, *args):
        """
        Stop the IDLE client
        """
        logger.info(f"Stopping IDLE client for {self.email_address.email}")
        self.running = False
        
        if self.idle_thread and self.idle_thread.is_alive():
            self.idle_thread.join(timeout=5)
        
        if self.client:
            try:
                self.client.idle_done()
                self.client.logout()
            except:
                pass
            self.client = None


class IdleSyncManager:
    """
    Manager for IDLE-based email synchronization
    """
    
    def __init__(self):
        """
        Initialize the IDLE sync manager
        """
        self.clients = {}
        self.running = False
    
    def start_client(self, email_address_id):
        """
        Start an IDLE client for an email address
        
        Args:
            email_address_id: UUID of the email address to monitor
        """
        if email_address_id in self.clients:
            return
        
        try:
            email_address = EmailAddress.objects.get(id=email_address_id)
            
            if not email_address.is_active or not email_address.use_idle:
                logger.info(f"IDLE not enabled for {email_address.email}")
                return
            
            if not email_address.imap_server or not email_address.imap_username or not email_address.imap_password:
                logger.warning(f"Missing IMAP configuration for {email_address.email}")
                return
            
            logger.info(f"Starting IDLE client for {email_address.email}")
            client = IMAPIdleClient(email_address_id)
            self.clients[email_address_id] = client
            
            # Start the client in a separate thread
            thread = threading.Thread(target=client.start)
            thread.daemon = True
            thread.start()
            
        except EmailAddress.DoesNotExist:
            logger.error(f"Email address with ID {email_address_id} does not exist")
        except Exception as e:
            logger.error(f"Error starting IDLE client for {email_address_id}: {str(e)}")
    
    def stop_client(self, email_address_id):
        """
        Stop an IDLE client
        
        Args:
            email_address_id: UUID of the email address to stop monitoring
        """
        if email_address_id not in self.clients:
            return
        
        try:
            client = self.clients[email_address_id]
            client.stop()
            del self.clients[email_address_id]
            logger.info(f"Stopped IDLE client for {email_address_id}")
        except Exception as e:
            logger.error(f"Error stopping IDLE client for {email_address_id}: {str(e)}")
    
    def start(self):
        """
        Start all IDLE clients
        """
        if self.running:
            return
        
        self.running = True
        
        # Get all active email addresses with IDLE enabled
        email_addresses = EmailAddress.objects.filter(is_active=True, use_idle=True)
        
        for email_address in email_addresses:
            self.start_client(str(email_address.id))
    
    def stop(self):
        """
        Stop all IDLE clients
        """
        self.running = False
        
        for email_address_id in list(self.clients.keys()):
            self.stop_client(email_address_id)
