import imaplib
import email
import email.header
import email.utils
import logging
import re
import uuid
from datetime import datetime
from django.utils import timezone
from django.db import transaction
from superapp.apps.email.models import EmailAddress, Email, Contact, Thread
from superapp.apps.email.utils import html_to_text

logger = logging.getLogger(__name__)


class EmailSyncService:
    """
    Service for synchronizing emails from IMAP servers
    """
    
    def __init__(self, email_address_id=None, force_tls=False, force_ssl=False):
        """
        Initialize the sync service
        
        Args:
            email_address_id: Optional UUID of the email address to sync
            force_tls: Force TLS connection instead of the configured type
            force_ssl: Force SSL connection instead of the configured type
        """
        self.email_address_id = email_address_id
        self.force_tls = force_tls
        self.force_ssl = force_ssl
    
    def sync_all_accounts(self):
        """
        Synchronize all active email accounts
        """
        email_addresses = EmailAddress.objects.filter(is_active=True)
        
        if self.email_address_id:
            email_addresses = email_addresses.filter(id=self.email_address_id)
        
        for email_address in email_addresses:
            try:
                self.sync_account(email_address)
            except Exception as e:
                logger.error(f"Error syncing account {email_address.email}: {str(e)}")
    
    def sync_account(self, email_address):
        """
        Synchronize a single email account
        
        Args:
            email_address: EmailAddress instance to sync
        """
        if not email_address.imap_server or not email_address.imap_username or not email_address.imap_password:
            logger.warning(f"Skipping sync for {email_address.email}: Missing IMAP configuration")
            return
        
        try:
            # Connect to the IMAP server
            if self.force_ssl:
                mail = imaplib.IMAP4_SSL(email_address.imap_server, email_address.imap_port)
            elif self.force_tls:
                mail = imaplib.IMAP4(email_address.imap_server, email_address.imap_port)
                mail.starttls()
            elif email_address.imap_connection_type == EmailAddress.SSL:
                mail = imaplib.IMAP4_SSL(email_address.imap_server, email_address.imap_port)
            elif email_address.imap_connection_type == EmailAddress.TLS:
                mail = imaplib.IMAP4(email_address.imap_server, email_address.imap_port)
                mail.starttls()
            else:
                mail = imaplib.IMAP4(email_address.imap_server, email_address.imap_port)
            
            # Login
            mail.login(email_address.imap_username, email_address.imap_password)
            
            # Select the inbox
            mail.select('INBOX')
            
            # Search for all unseen emails
            status, data = mail.search(None, 'UNSEEN')
            
            if status != 'OK':
                logger.error(f"Error searching for emails: {status}")
                return
            
            # Process each email
            for num in data[0].split():
                status, data = mail.fetch(num, '(RFC822)')
                
                if status != 'OK':
                    logger.error(f"Error fetching email {num}: {status}")
                    continue
                
                raw_email = data[0][1]
                self.process_email(raw_email, email_address)
            
            # Close the connection
            mail.close()
            mail.logout()
            
        except Exception as e:
            logger.error(f"Error syncing account {email_address.email}: {str(e)}")
            raise
    
    @transaction.atomic
    def process_email(self, raw_email, email_address):
        """
        Process a single email
        
        Args:
            raw_email: Raw email data
            email_address: EmailAddress instance
        """
        try:
            # Parse the email
            msg = email.message_from_bytes(raw_email)
            
            # Extract headers
            message_id = msg.get('Message-ID', '')
            in_reply_to = msg.get('In-Reply-To', '')
            references = msg.get('References', '')
            subject = self._decode_header(msg.get('Subject', 'No Subject'))
            from_header = self._decode_header(msg.get('From', ''))
            to_header = self._decode_header(msg.get('To', ''))
            cc_header = self._decode_header(msg.get('Cc', ''))
            date_header = msg.get('Date', '')
            
            # Parse the from header
            from_name, from_email = self._parse_email_header(from_header)
            
            # Parse the to header
            to_emails = self._parse_recipients(to_header)
            
            # Parse the cc header
            cc_emails = self._parse_recipients(cc_header)
            
            # Parse the date
            date = email.utils.parsedate_to_datetime(date_header) if date_header else timezone.now()
            
            # Extract the body
            body_text, body_html = self._get_email_body(msg)
            
            # Generate plain text from HTML if needed
            if body_html and not body_text:
                body_text = html_to_text(body_html)
            
            # Check if this email already exists
            if message_id and Email.objects.filter(message_id=message_id).exists():
                logger.info(f"Email with Message-ID {message_id} already exists, skipping")
                return
            
            # Find or create the contact
            contact = None
            if from_email:
                contact, _ = Contact.objects.get_or_create(
                    email=from_email,
                    defaults={
                        'name': from_name or '',
                        'is_active': True
                    }
                )
            
            # Find the thread based on In-Reply-To or References
            thread = None
            if in_reply_to:
                # Try to find an email with this message ID
                try:
                    reply_to_email = Email.objects.get(message_id=in_reply_to)
                    thread = reply_to_email.thread
                except Email.DoesNotExist:
                    pass
            
            if not thread and references:
                # Try to find an email with any of the references
                ref_ids = re.findall(r'<([^>]+)>', references)
                if ref_ids:
                    thread_emails = Email.objects.filter(message_id__in=ref_ids).select_related('thread')
                    if thread_emails.exists():
                        thread = thread_emails.first().thread
            
            # If no thread found, create a new one
            if not thread:
                thread = Thread.objects.create(
                    subject=subject,
                    participants=to_emails + ([from_email] if from_email else []),
                    email_address=email_address,
                    contact=contact,
                    last_message_at=date
                )
            
            # Create the email
            email_obj = Email.objects.create(
                email_address=email_address,
                thread=thread,
                direction='incoming',
                status='received',
                message_id=message_id,
                in_reply_to=in_reply_to,
                references=references,
                from_email=from_email,
                from_name=from_name,
                to_emails=to_emails,
                cc_emails=cc_emails,
                subject=subject,
                body_text=body_text,
                body_html=body_html,
                sent_at=date,
                delivered_at=date,
                contact=contact,
                raw_message=raw_email.decode('utf-8', errors='replace')
            )
            
            # Update the thread's last_message_at
            thread.last_message_at = date
            thread.save(update_fields=['last_message_at', 'updated_at'])
            
            logger.info(f"Successfully processed incoming email: {email_obj.id}")
            
            return email_obj
            
        except Exception as e:
            logger.error(f"Error processing email: {str(e)}")
            raise
    
    def _decode_header(self, header):
        """
        Decode an email header
        
        Args:
            header: Email header to decode
            
        Returns:
            Decoded header string
        """
        if not header:
            return ""
        
        decoded_header = ""
        for part, encoding in email.header.decode_header(header):
            if isinstance(part, bytes):
                try:
                    decoded_part = part.decode(encoding or 'utf-8', errors='replace')
                except (LookupError, TypeError):
                    decoded_part = part.decode('utf-8', errors='replace')
            else:
                decoded_part = part
            
            decoded_header += decoded_part
        
        return decoded_header
    
    def _parse_email_header(self, header):
        """
        Parse an email header into name and email
        
        Args:
            header: Email header to parse
            
        Returns:
            Tuple of (name, email)
        """
        if not header:
            return "", ""
        
        # Try to match "Name <email@example.com>" format
        match = re.match(r'"?([^"<]+)"?\s*<?([^>]+)>?', header)
        
        if match:
            name = match.group(1).strip()
            email_addr = match.group(2).strip()
            return name, email_addr
        
        # If no match, assume it's just an email address
        return "", header.strip()
    
    def _parse_recipients(self, header):
        """
        Parse a recipient header into a list of email addresses
        
        Args:
            header: Recipient header to parse
            
        Returns:
            List of email addresses
        """
        if not header:
            return []
        
        emails = []
        
        # Split by commas
        parts = header.split(',')
        
        for part in parts:
            _, email_addr = self._parse_email_header(part)
            if email_addr:
                emails.append(email_addr)
        
        return emails
    
    def _get_email_body(self, msg):
        """
        Extract the text and HTML body from an email
        
        Args:
            msg: Email message
            
        Returns:
            Tuple of (text_body, html_body)
        """
        text_body = ""
        html_body = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                # Skip attachments
                if "attachment" in content_disposition:
                    continue
                
                payload = part.get_payload(decode=True)
                if payload is None:
                    continue
                
                charset = part.get_content_charset() or 'utf-8'
                try:
                    decoded_payload = payload.decode(charset, errors='replace')
                except (LookupError, TypeError):
                    decoded_payload = payload.decode('utf-8', errors='replace')
                
                if content_type == "text/plain":
                    text_body = decoded_payload
                elif content_type == "text/html":
                    html_body = decoded_payload
        else:
            # Not multipart - get the payload directly
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or 'utf-8'
                try:
                    decoded_payload = payload.decode(charset, errors='replace')
                except (LookupError, TypeError):
                    decoded_payload = payload.decode('utf-8', errors='replace')
                
                content_type = msg.get_content_type()
                if content_type == "text/plain":
                    text_body = decoded_payload
                elif content_type == "text/html":
                    html_body = decoded_payload
        
        return text_body, html_body
