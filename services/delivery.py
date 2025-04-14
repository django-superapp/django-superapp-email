import smtplib
import logging
import email.utils
import uuid
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from django.utils import timezone
from django.db import transaction
from superapp.apps.email.models import Email, EmailAddress
from superapp.apps.email.utils import html_to_text

logger = logging.getLogger(__name__)


class EmailDeliveryService:
    """
    Service for delivering outgoing emails
    """
    
    def __init__(self, email_id=None, force_tls=False, force_ssl=False):
        """
        Initialize the delivery service
        
        Args:
            email_id: Optional UUID of the email to deliver
            force_tls: Force TLS connection instead of the configured type
            force_ssl: Force SSL connection instead of the configured type
        """
        self.email_id = email_id
        self.force_tls = force_tls
        self.force_ssl = force_ssl
    
    def deliver_pending_emails(self, retry_errors=False):
        """
        Deliver all pending outgoing emails
        
        Args:
            retry_errors: If True, also retry emails in 'failed' state
        """
        status_list = ['draft', 'sending']
        if retry_errors:
            status_list.append('failed')
            
        emails = Email.objects.filter(
            direction='outgoing',
            status__in=status_list
        )
        
        if self.email_id:
            emails = emails.filter(id=self.email_id)
        
        for email_obj in emails:
            try:
                self.deliver_email(email_obj)
            except Exception as e:
                logger.error(f"Error delivering email {email_obj.id}: {str(e)}")
                email_obj.status = 'failed'
                email_obj.error_message = str(e)
                email_obj.save(update_fields=['status', 'error_message', 'updated_at'])
    
    @transaction.atomic
    def deliver_email(self, email_obj):
        """
        Deliver a single email
        
        Args:
            email_obj: Email instance to deliver
        """
        if email_obj.direction != 'outgoing':
            logger.warning(f"Cannot deliver incoming email {email_obj.id}")
            return
        
        if email_obj.status not in ['draft', 'sending']:
            logger.warning(f"Email {email_obj.id} is not in a deliverable state: {email_obj.status}")
            return
        
        # Update status to sending
        email_obj.status = 'sending'
        email_obj.save(update_fields=['status', 'updated_at'])
        
        try:
            # Get the email address configuration
            email_address = email_obj.email_address
            
            # Create the message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{email_obj.from_name} <{email_obj.from_email}>" if email_obj.from_name else email_obj.from_email
            msg['Subject'] = email_obj.subject
            msg['Date'] = email.utils.formatdate(localtime=True)
            
            # Generate a message ID if not present
            if not email_obj.message_id:
                domain = email_obj.from_email.split('@')[1]
                email_obj.message_id = f"<{uuid.uuid4()}@{domain}>"
            
            msg['Message-ID'] = email_obj.message_id
            
            # Add In-Reply-To and References headers if applicable
            if email_obj.in_reply_to:
                msg['In-Reply-To'] = email_obj.in_reply_to
            
            if email_obj.references:
                msg['References'] = email_obj.references
            
            # Add recipients
            if email_obj.to_emails:
                msg['To'] = ', '.join(email_obj.to_emails)
            
            if email_obj.cc_emails:
                msg['Cc'] = ', '.join(email_obj.cc_emails)
            
            # Add text and HTML parts
            if email_obj.body_html:
                # Generate plain text version if not provided
                if not email_obj.body_text:
                    email_obj.body_text = html_to_text(email_obj.body_html)
                    # Save the generated text
                    Email.objects.filter(id=email_obj.id).update(
                        body_text=email_obj.body_text
                    )
                
                # Add both parts to the email
                msg.attach(MIMEText(email_obj.body_text, 'plain'))
                msg.attach(MIMEText(email_obj.body_html, 'html'))
            elif email_obj.body_text:
                # Text-only email
                msg.attach(MIMEText(email_obj.body_text, 'plain'))
            
            # TODO: Add attachments handling
            
            # Connect to the SMTP server
            if self.force_ssl:
                server = smtplib.SMTP_SSL(email_address.smtp_server, email_address.smtp_port)
            elif self.force_tls:
                server = smtplib.SMTP(email_address.smtp_server, email_address.smtp_port)
                server.starttls()
            elif email_address.smtp_connection_type == EmailAddress.SSL:
                server = smtplib.SMTP_SSL(email_address.smtp_server, email_address.smtp_port)
            else:
                server = smtplib.SMTP(email_address.smtp_server, email_address.smtp_port)
                if email_address.smtp_connection_type == EmailAddress.TLS:
                    server.starttls()
            
            # Login
            server.login(email_address.smtp_username, email_address.smtp_password)
            
            # Get all recipients
            all_recipients = email_obj.to_emails + email_obj.cc_emails + email_obj.bcc_emails
            
            # Send the email
            server.sendmail(email_obj.from_email, all_recipients, msg.as_string())
            
            # Close the connection
            server.quit()
            
            # Update the email status
            now = timezone.now()
            email_obj.status = 'sent'
            email_obj.sent_at = now
            email_obj.delivered_at = now
            email_obj.raw_message = msg.as_string()
            email_obj.save(update_fields=[
                'status', 'sent_at', 'delivered_at', 'raw_message', 'updated_at'
            ])
            
            # Update the thread's last_message_at
            if email_obj.thread:
                email_obj.thread.last_message_at = now
                email_obj.thread.save(update_fields=['last_message_at', 'updated_at'])
            
            logger.info(f"Successfully delivered email: {email_obj.id}")
            
        except Exception as e:
            logger.error(f"Error delivering email {email_obj.id}: {str(e)}")
            email_obj.status = 'failed'
            email_obj.error_message = str(e)
            email_obj.save(update_fields=['status', 'error_message', 'updated_at'])
            raise
