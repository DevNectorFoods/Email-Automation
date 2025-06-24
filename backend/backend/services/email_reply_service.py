"""Service for handling email replies using SMTP."""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, Dict, List, Union
import os
from dataclasses import dataclass
from datetime import datetime

from ..models.email_models import EmailAccount, Email
from ..models.db_models import db_manager
from ..config import Config

logger = logging.getLogger(__name__)

@dataclass
class EmailReply:
    """Model for email reply data."""
    to_email: str
    subject: str
    body: str
    body_html: Optional[str] = None
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    attachments: Optional[List[Dict]] = None
    reply_to_id: Optional[str] = None
    
class EmailReplyService:
    """Service for sending email replies via SMTP."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def send_reply(self, account: EmailAccount, reply: EmailReply) -> bool:
        """
        Send an email reply using the specified email account.
        
        Args:
            account: EmailAccount object with SMTP credentials
            reply: EmailReply object with reply details
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create message
            message = self._create_message(account, reply)
            
            # Get SMTP settings for the account
            smtp_settings = self._get_smtp_settings(account)
            
            # Send email
            return self._send_via_smtp(smtp_settings, message, account.email, reply.to_email)
            
        except Exception as e:
            self.logger.error(f"Error sending reply: {str(e)}")
            return False
    
    def _create_message(self, account: EmailAccount, reply: EmailReply) -> MIMEMultipart:
        """Create email message with proper headers."""
        message = MIMEMultipart('alternative')
        
        # Set headers
        message['From'] = account.email
        message['To'] = reply.to_email
        message['Subject'] = reply.subject
        
        if reply.cc:
            message['Cc'] = ', '.join(reply.cc)
        if reply.bcc:
            message['Bcc'] = ', '.join(reply.bcc)
            
        # Add reply-to header if this is a reply
        if reply.reply_to_id:
            message['In-Reply-To'] = reply.reply_to_id
            message['References'] = reply.reply_to_id
        
        # Add text content
        if reply.body:
            text_part = MIMEText(reply.body, 'plain', 'utf-8')
            message.attach(text_part)
        
        # Add HTML content if provided
        if reply.body_html:
            html_part = MIMEText(reply.body_html, 'html', 'utf-8')
            message.attach(html_part)
        
        # Add attachments if any
        if reply.attachments:
            for attachment in reply.attachments:
                self._add_attachment(message, attachment)
        
        return message
    
    def _add_attachment(self, message: MIMEMultipart, attachment: Dict):
        """Add attachment to email message."""
        try:
            with open(attachment['path'], 'rb') as file:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(file.read())
                
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {attachment["filename"]}'
            )
            message.attach(part)
        except Exception as e:
            self.logger.error(f"Error adding attachment {attachment['filename']}: {str(e)}")
    
    def _get_smtp_settings(self, account: EmailAccount) -> Dict:
        """Get SMTP settings based on account type."""
        smtp_settings = {
            'hostinger': {
                'server': 'smtp.hostinger.com',
                'port': 587,
                'use_tls': True
            },
            'gmail': {
                'server': 'smtp.gmail.com',
                'port': 587,
                'use_tls': True
            },
            'outlook': {
                'server': 'smtp-mail.outlook.com',
                'port': 587,
                'use_tls': True
            }
        }
        
        return smtp_settings.get(account.account_type, {
            'server': account.imap_server.replace('imap.', 'smtp.'),
            'port': 587,
            'use_tls': True
        })
    
    def _send_via_smtp(self, smtp_settings: Dict, message: MIMEMultipart, 
                      from_email: str, to_email: str) -> bool:
        """Send email via SMTP."""
        try:
            # Connect to SMTP server
            server = smtplib.SMTP(smtp_settings['server'], smtp_settings['port'])
            
            if smtp_settings.get('use_tls'):
                server.starttls()
            
            # Login with account credentials
            # Note: In production, you'd get the password from the account
            # For now, we'll need to handle authentication properly
            
            # Send email
            text = message.as_string()
            server.sendmail(from_email, to_email, text)
            server.quit()
            
            self.logger.info(f"Email sent successfully from {from_email} to {to_email}")
            return True
            
        except Exception as e:
            self.logger.error(f"SMTP error: {str(e)}")
            return False
    
    def test_smtp_connection(self, account: EmailAccount) -> bool:
        """
        Test SMTP connection for an email account.
        
        Args:
            account: EmailAccount object to test
            
        Returns:
            True if connection successful, False otherwise
        """
        try:
            smtp_settings = self._get_smtp_settings(account)
            
            server = smtplib.SMTP(smtp_settings['server'], smtp_settings['port'])
            
            if smtp_settings.get('use_tls'):
                server.starttls()
            
            # Test authentication
            server.login(account.email, account.password)
            server.quit()
            
            return True
            
        except Exception as e:
            self.logger.error(f"SMTP connection test failed for {account.email}: {str(e)}")
            return False
    
    def create_reply_template(self, original_email: Dict) -> EmailReply:
        """
        Create a reply template based on the original email.
        
        Args:
            original_email: Original email data
            
        Returns:
            EmailReply object with prefilled data
        """
        # Extract original sender
        original_sender = original_email.get('sender', '')
        original_subject = original_email.get('subject', '')
        
        # Create reply subject
        reply_subject = original_subject
        if not reply_subject.lower().startswith('re:'):
            reply_subject = f"Re: {reply_subject}"
        
        # Create reply body with quote
        original_body = original_email.get('body', '')
        original_date = original_email.get('date', '')
        
        reply_body = f"\n\n--- Original Message ---\n"
        reply_body += f"From: {original_sender}\n"
        reply_body += f"Date: {original_date}\n"
        reply_body += f"Subject: {original_subject}\n\n"
        reply_body += original_body
        
        return EmailReply(
            to_email=original_sender,
            subject=reply_subject,
            body=reply_body,
            reply_to_id=original_email.get('id')
        )