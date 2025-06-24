import imaplib
import email
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from email.header import decode_header
import hashlib
import json
from email.utils import parsedate_to_datetime
import re

from ..models.email_models import Email, EmailAccount
from .categorization_service import EmailCategorizationService
# from services.notification_service import NotificationService
from ..config import Config
from ..models.db_models import db_manager

logger = logging.getLogger(__name__)

class EmailService:
    """Service for handling email operations."""
    
    def __init__(self):
        """Initialize the email service."""
        self.db = db_manager
        self.categorization_service = EmailCategorizationService()
        # self.notification_service = NotificationService()
    
    def fetch_emails(self, account: EmailAccount) -> List[Email]:
        """
        Fetch new emails from the specified account.
        
        Args:
            account: EmailAccount object containing connection details
            
        Returns:
            List of fetched Email objects
        """
        try:
            # Connect to IMAP server
            mail = imaplib.IMAP4_SSL(account.imap_server, account.imap_port)
            mail.login(account.email, account.password)
            mail.select('INBOX')
            
            # Search for new emails since last check
            _, messages = mail.search(None, 'ALL')
            
            fetched_emails = []
            for num in messages[0].split():
                # Use PEEK to avoid marking as read
                _, msg_data = mail.fetch(num, '(BODY.PEEK[])')
                email_body = msg_data[0][1]
                email_message = email.message_from_bytes(email_body)
                
                # Extract email details
                subject = self._decode_email_header(email_message['subject']) or ''
                sender = self._decode_email_header(email_message['from']) or ''
                date_str = email_message['date']
                date = self.robust_parse_date(date_str)
                
                # Get email body
                body = ""
                if email_message.is_multipart():
                    for part in email_message.walk():
                        if part.get_content_type() == "text/plain":
                            payload = part.get_payload(decode=True)
                            if payload is not None:
                                try:
                                    body = payload.decode('utf-8')
                                except Exception as e_utf8:
                                    try:
                                        body = payload.decode('latin1')
                                    except Exception as e_latin1:
                                        try:
                                            body = payload.decode('utf-8', errors='ignore')
                                        except Exception as e_ignore:
                                            logger.error(f"Body decode failed for email {num} in {account.email}: {e_ignore}")
                                            body = ''
                            break
                else:
                    payload = email_message.get_payload(decode=True)
                    if payload is not None:
                        try:
                            body = payload.decode('utf-8')
                        except Exception as e_utf8:
                            try:
                                body = payload.decode('latin1')
                            except Exception as e_latin1:
                                try:
                                    body = payload.decode('utf-8', errors='ignore')
                                except Exception as e_ignore:
                                    logger.error(f"Body decode failed for email {num} in {account.email}: {e_ignore}")
                                    body = ''
                
                # Create Email object
                raw_data_str = ''
                try:
                    raw_data_str = email_body.decode('utf-8')
                except Exception as e_utf8:
                    try:
                        raw_data_str = email_body.decode('latin1')
                    except Exception as e_latin1:
                        try:
                            raw_data_str = email_body.decode('utf-8', errors='ignore')
                        except Exception as e_ignore:
                            logger.error(f"Raw data decode failed for email {num} in {account.email}: {e_ignore}")
                            raw_data_str = ''
                email_obj = Email(
                    id=str(num),
                    account_email=account.email,
                    subject=subject,
                    sender=sender,
                    date=self.ensure_datetime(date),
                    body=body,
                    raw_data=raw_data_str,
                    category='general'  # Will be categorized later
                )
                # Always set email_hash before saving
                email_obj.email_hash = self.generate_email_hash(email_obj)
                # Ensure date and created_at are datetime
                email_obj.date = self.ensure_datetime(email_obj.date)
                email_obj.created_at = self.ensure_datetime(getattr(email_obj, 'created_at', datetime.now()))
                # Save to database
                if self.db.save_email(email_obj):
                    fetched_emails.append(email_obj)
            
            # Update last checked time
            account.last_checked = datetime.now()
            self.db.update_email_account(account)
            
            # Categorize new emails
            for email_obj in fetched_emails:
                # Use enhanced categorization
                main_category, sub_category = self._enhanced_categorize_email(email_obj)
                email_obj.main_category = main_category
                email_obj.sub_category = sub_category
                email_obj.category = f"{main_category}_{sub_category}"  # Combined for compatibility
                email_obj.date = self.ensure_datetime(email_obj.date)
                email_obj.created_at = self.ensure_datetime(getattr(email_obj, 'created_at', datetime.now()))
                self.db.save_email(email_obj)
            
            return fetched_emails
            
        except Exception as e:
            logger.error(f"Error fetching emails for {account.email}: {str(e)}")
            return []
    
    def _decode_email_header(self, header: str) -> str:
        """Decode email header to handle special characters. Returns empty string if header is None."""
        if header is None:
            return ''
        try:
            decoded_header = decode_header(header)
            return " ".join(
                part.decode(charset or 'utf-8') if isinstance(part, bytes) else part
                for part, charset in decoded_header
            )
        except Exception as e:
            logger.error(f"Error decoding header: {str(e)}")
            return ''
    
    def fetch_emails_from_account(self, account: EmailAccount, limit: int = None) -> List[Email]:
        """
        Fetch emails from a single email account via IMAP.
        
        Args:
            account: EmailAccount object with connection details
            limit: Maximum number of emails to fetch
            
        Returns:
            List of Email objects
        """
        emails = []
        mail = None
        max_num = None
        try:
            # Connect to IMAP server
            mail = imaplib.IMAP4_SSL(account.imap_server, account.imap_port)
            mail.login(account.email, account.password)
            mail.select('inbox')

            # Use sequence number-based search/fetch instead of UID
            status, messages = mail.search(None, 'ALL')
            if status == 'OK':
                email_nums = messages[0].split()
                logger.info(f"Fetched {len(email_nums)} sequence numbers from IMAP for {account.email}")
                if email_nums:
                    max_num = max(int(num) for num in email_nums)
                # Apply limit if specified
                if limit:
                    email_nums = email_nums[-limit:]
                logger.info(f"Found {len(email_nums)} new emails for account {account.email} (using sequence numbers)")
                for num in email_nums:
                    try:
                        email_obj = self._fetch_single_email(mail, num, account)
                        if email_obj:
                            # Generate email hash
                            email_hash = self.generate_email_hash(email_obj)
                            email_obj.email_hash = email_hash
                            # Use enhanced categorization
                            main_category, sub_category = self._enhanced_categorize_email(email_obj)
                            email_obj.main_category = main_category
                            email_obj.sub_category = sub_category
                            email_obj.category = f"{main_category}_{sub_category}"  # Combined for compatibility
                            # Ensure date and created_at are datetime
                            email_obj.date = self.ensure_datetime(email_obj.date)
                            email_obj.created_at = self.ensure_datetime(getattr(email_obj, 'created_at', datetime.now()))
                            
                            # Check for duplicates
                            existing_email_id = self.db.email_exists(message_id=email_obj.message_id, email_hash=email_obj.email_hash)
                            if existing_email_id:
                                email_obj.id = existing_email_id
                            
                            # Save email (will insert or update)
                            self.db.save_email(email_obj)
                            
                            if not existing_email_id:
                                emails.append(email_obj)
                                logger.info(f"Email fetched and saved: {email_obj.subject[:50]}...")
                            else:
                                logger.info(f"Email updated: {email_obj.subject[:50]}...")
                    except Exception as e:
                        logger.error(f"Error fetching email {num}: {str(e)}")
                        continue
            # No need to update last_fetched_uid for sequence numbers
        except imaplib.IMAP4.error as e:
            logger.error(f"IMAP error for account {account.email}: {str(e)}")
            raise Exception(f"Failed to connect to email account: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error fetching emails for {account.email}: {str(e)}")
            raise Exception(f"Email fetch failed: {str(e)}")
        finally:
            if mail:
                try:
                    mail.close()
                    mail.logout()
                except:
                    pass
        return emails
    
    def _fetch_single_email(self, mail, email_id, account: EmailAccount) -> Optional[Email]:
        """
        Fetch and parse a single email.
        
        Args:
            mail: IMAP connection object
            email_id: Email ID (bytes or int)
            account: EmailAccount object
            
        Returns:
            Email object or None if failed
        """
        try:
            if isinstance(email_id, bytes):
                email_id_str = email_id.decode('utf-8')
            else:
                email_id_str = str(email_id)
            
            # Fetch the email's flags first to check the read status
            status_flags, flags_data = mail.fetch(email_id_str, '(FLAGS)')
            is_read = False
            if status_flags == 'OK':
                flags = imaplib.ParseFlags(flags_data[0])
                if b'\\Seen' in flags:
                    is_read = True

            # Fetch the full email data using PEEK to avoid marking it as read
            status_body, msg_data = mail.fetch(email_id_str, '(BODY.PEEK[])')
            if status_body != 'OK' or not msg_data[0] or not isinstance(msg_data[0], tuple):
                logger.error(f"Failed to fetch email body for ID {email_id_str}")
                return None

            raw_email = msg_data[0][1]
            email_message = email.message_from_bytes(raw_email)

            subject = self._decode_header(email_message.get('Subject', 'No Subject'))
            sender = self._decode_header(email_message.get('From', 'Unknown Sender'))
            date_str = email_message.get('Date')
            email_date = self.robust_parse_date(date_str)
            message_id = email_message.get('Message-ID')
            
            # Extract additional metadata for "Show details"
            metadata = {}
            if email_message.get('Mailed-By'):
                metadata['mailed_by'] = self._decode_header(email_message.get('Mailed-By'))
            if email_message.get('Signed-By'):
                metadata['signed_by'] = self._decode_header(email_message.get('Signed-By'))

            # Extract security info (TLS) from Received headers
            received_headers = email_message.get_all('Received', [])
            security_info = "No encryption information found"
            for header in received_headers:
                if 'TLS' in header or 'SSL' in header:
                    match = re.search(r'\(version=(.+?)\s', header)
                    if match:
                        security_info = f"Standard encryption ({match.group(1).split(',')[0]})"
                    else:
                        security_info = "Standard encryption (TLS)"
                    break
            metadata['security'] = security_info

            body = self._extract_email_body(email_message, email_id_str, account.email)
            
            email_obj = Email(
                id=email_id_str,
                account_email=account.email,
                subject=subject,
                sender=sender,
                date=self.ensure_datetime(email_date),
                body=body,
                raw_data=raw_email.decode('utf-8', 'ignore'),
                is_read=is_read,
                message_id=message_id,
                metadata=metadata,
                created_at=datetime.now()
            )

            email_obj.email_hash = self.generate_email_hash_from_msg(email_message) if not message_id else None
            
            return email_obj

        except Exception as e:
            logger.error(f"Error parsing email {email_id}: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None
    
    def _decode_header(self, header: str) -> str:
        """Decode email header to handle special characters."""
        if not header:
            return ''
        
        try:
            decoded_parts = decode_header(header)
            decoded_string = ''
            
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    if encoding:
                        decoded_string += part.decode(encoding)
                    else:
                        decoded_string += part.decode('utf-8', errors='ignore')
                else:
                    decoded_string += part
            
            return decoded_string
        except Exception:
            return header
    
    def _parse_email_date(self, date_str: str) -> datetime:
        """Parse email date string."""
        try:
            return email.utils.parsedate_to_datetime(date_str)
        except Exception:
            return datetime.now()
    
    def robust_parse_date(self, date_str):
        if isinstance(date_str, datetime):
            return date_str
        try:
            # Remove all (XYZ) patterns and extra spaces
            cleaned = re.sub(r'\s*\([^)]*\)', '', str(date_str)).strip()
            return datetime.fromisoformat(cleaned)
        except Exception:
            try:
                cleaned = re.sub(r'\s*\([^)]*\)', '', str(date_str)).strip()
                return parsedate_to_datetime(cleaned)
            except Exception:
                return datetime.now()
    
    def _extract_email_body(self, email_message, email_id=None, account_email=None) -> str:
        """Extract email body content with robust decoding."""
        body = ""
        try:
            if email_message.is_multipart():
                for part in email_message.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))
                    if (content_type == "text/plain" and "attachment" not in content_disposition):
                        payload = part.get_payload(decode=True)
                        if payload is not None:
                            try:
                                body = payload.decode('utf-8')
                            except Exception as e_utf8:
                                try:
                                    body = payload.decode('latin1')
                                except Exception as e_latin1:
                                    try:
                                        body = payload.decode('utf-8', errors='ignore')
                                    except Exception as e_ignore:
                                        logger.error(f"Body decode failed for email {email_id} in {account_email}: {e_ignore}")
                                        body = ''
                        break
            else:
                payload = email_message.get_payload(decode=True)
                if payload is not None:
                    try:
                        body = payload.decode('utf-8')
                    except Exception as e_utf8:
                        try:
                            body = payload.decode('latin1')
                        except Exception as e_latin1:
                            try:
                                body = payload.decode('utf-8', errors='ignore')
                            except Exception as e_ignore:
                                logger.error(f"Body decode failed for email {email_id} in {account_email}: {e_ignore}")
                                body = ''
        except Exception as e:
            logger.error(f"Error extracting email body for email {email_id} in {account_email}: {str(e)}")
            body = ""
        return body.strip()
    
    def test_account_connection(self, account: EmailAccount) -> bool:
        """
        Test if an email account connection is valid.
        
        Args:
            account: EmailAccount object to test
            
        Returns:
            True if connection successful, False otherwise
        """
        try:
            mail = imaplib.IMAP4_SSL(account.imap_server, account.imap_port)
            mail.login(account.email, account.password)
            mail.select('inbox')
            mail.close()
            mail.logout()
            return True
        except Exception as e:
            logger.error(f"Connection test failed for {account.email}: {str(e)}")
            return False

    def generate_email_hash(self, email: Email) -> str:
        # Combine unique fields to create a hash
        # Ensure all fields are strings
        email_id = email.id
        if isinstance(email_id, bytes):
            email_id = email_id.decode('utf-8')
        else:
            email_id = str(email_id)
            
        subject = email.subject
        if isinstance(subject, bytes):
            subject = subject.decode('utf-8')
        else:
            subject = str(subject)
            
        sender = email.sender
        if isinstance(sender, bytes):
            sender = sender.decode('utf-8')
        else:
            sender = str(sender)
            
        date_str = str(email.date) if email.date else str(datetime.now())
            
        unique_fields = f"{subject}_{sender}_{date_str}_{email_id}"
        return hashlib.md5(unique_fields.encode('utf-8')).hexdigest()
    
    def generate_verification_hash(self, uid: str, timestamp: datetime, email_hash: str) -> str:
        """Generate verification hash using UID + timestamp + email_hash."""
        # Ensure all parameters are strings
        uid_str = uid
        if isinstance(uid_str, bytes):
            uid_str = uid_str.decode('utf-8')
        else:
            uid_str = str(uid_str)
        
        # Ensure timestamp is always a datetime object
        timestamp_dt = self.ensure_datetime(timestamp) if timestamp else datetime.now()
        timestamp_str = timestamp_dt.isoformat()
        
        email_hash_str = email_hash
        if isinstance(email_hash_str, bytes):
            email_hash_str = email_hash_str.decode('utf-8')
        else:
            email_hash_str = str(email_hash_str)
        
        verification_string = f"{uid_str}_{timestamp_str}_{email_hash_str}"
        return hashlib.sha256(verification_string.encode('utf-8')).hexdigest()
    
    def verify_email_uniqueness(self, uid: str, timestamp: datetime, email_hash: str) -> bool:
        """Verify email uniqueness using UID + timestamp + hash."""
        # Ensure all parameters are strings
        uid_str = uid
        if isinstance(uid_str, bytes):
            uid_str = uid_str.decode('utf-8')
        else:
            uid_str = str(uid_str)
        
        # Ensure timestamp is always a datetime object
        timestamp_dt = self.ensure_datetime(timestamp) if timestamp else datetime.now()
        timestamp_str = timestamp_dt.isoformat()
        
        email_hash_str = email_hash
        if isinstance(email_hash_str, bytes):
            email_hash_str = email_hash_str.decode('utf-8')
        else:
            email_hash_str = str(email_hash_str)
        
        verification_hash = self.generate_verification_hash(uid_str, timestamp_str, email_hash_str)
        
        # Check if this verification hash already exists
        return not self.db.verification_hash_exists(verification_hash)

    def _extract_domain(self, sender: str) -> str:
        """Extract domain from email address."""
        if '@' in sender:
            return sender.split('@')[-1].split('>')[0].strip()
        return sender

    def _enhanced_categorize_email(self, email: Email) -> tuple:
        """
        Hierarchical categorization system without AI.
        Returns (main_category, sub_category) tuple.
        """
        subject_lower = email.subject.lower()
        sender_lower = email.sender.lower()
        body_lower = email.body.lower()
        
        # Extract domain from sender email
        domain = self._extract_domain(sender_lower)
        
        # Extract sender name/company name dynamically
        sender_name = self._extract_sender_name(email.sender)
        
        # BANK CATEGORIES - Dynamic detection
        if self._is_bank_email(subject_lower, sender_lower, domain):
            bank_name = self._detect_bank_name_dynamic(subject_lower, sender_lower, domain, sender_name)
            return ('bank', bank_name)
        
        # COMPANY CATEGORIES - Dynamic detection
        elif self._is_company_email(subject_lower, sender_lower, domain):
            company_name = self._detect_company_name_dynamic(subject_lower, sender_lower, domain, sender_name)
            return ('company', company_name)
        
        # SUPPORT CATEGORIES
        elif self._is_support_email(subject_lower, sender_lower):
            support_type = self._detect_support_type(subject_lower, body_lower)
            return ('support', support_type)
        
        # NEWSLETTER CATEGORIES
        elif self._is_newsletter_email(subject_lower, sender_lower):
            newsletter_type = self._detect_newsletter_type(subject_lower, body_lower)
            return ('newsletter', newsletter_type)
        
        # BILLING/PAYMENT CATEGORIES
        elif self._is_billing_email(subject_lower, sender_lower):
            billing_type = self._detect_billing_type(subject_lower, body_lower)
            return ('billing', billing_type)
        
        # ORDER/SHIPPING CATEGORIES
        elif self._is_order_email(subject_lower, sender_lower):
            order_type = self._detect_order_type(subject_lower, body_lower)
            return ('order', order_type)
        
        # SOCIAL MEDIA CATEGORIES
        elif self._is_social_email(subject_lower, sender_lower, domain):
            social_platform = self._detect_social_platform(subject_lower, sender_lower, domain)
            return ('social', social_platform)
        
        # SECURITY CATEGORIES
        elif self._is_security_email(subject_lower, sender_lower):
            security_type = self._detect_security_type(subject_lower, body_lower)
            return ('security', security_type)
        
        # MEETING/CALENDAR CATEGORIES
        elif self._is_meeting_email(subject_lower, sender_lower):
            meeting_type = self._detect_meeting_type(subject_lower, body_lower)
            return ('meeting', meeting_type)
        
        # CAREER/JOB CATEGORIES
        elif self._is_career_email(subject_lower, sender_lower):
            career_type = self._detect_career_type(subject_lower, body_lower)
            return ('career', career_type)
        
        # NOTIFICATION CATEGORIES
        elif self._is_notification_email(subject_lower, sender_lower):
            notification_type = self._detect_notification_type(subject_lower, body_lower)
            return ('notification', notification_type)
        
        # Default - Use sender name as sub-category
        return ('general', sender_name)

    def _extract_sender_name(self, sender: str) -> str:
        """
        Extract sender name/company name from email address.
        Returns a clean, folder-friendly name.
        """
        try:
            # Remove email part and extract name
            if '<' in sender and '>' in sender:
                # Format: "Name <email@domain.com>"
                name_part = sender.split('<')[0].strip()
            else:
                # Format: "email@domain.com" or just domain
                if '@' in sender:
                    name_part = sender.split('@')[0]
                else:
                    name_part = sender
            
            # Clean the name
            name_part = name_part.replace('"', '').replace("'", '').strip()
            
            # If name is empty or just email, extract from domain
            if not name_part or '@' in name_part:
                domain = self._extract_domain(sender)
                if '.' in domain:
                    name_part = domain.split('.')[0]
                else:
                    name_part = domain
            
            # Convert to folder-friendly format
            folder_name = name_part.replace('-', '_').replace('.', '_').replace(' ', '_')
            folder_name = ''.join(c for c in folder_name if c.isalnum() or c == '_')
            
            # Ensure it's not empty
            if not folder_name:
                folder_name = 'unknown_sender'
            
            return folder_name.lower()
            
        except Exception as e:
            logger.error(f"Error extracting sender name from '{sender}': {str(e)}")
            return 'unknown_sender'

    def _detect_bank_name_dynamic(self, subject: str, sender: str, domain: str, sender_name: str) -> str:
        """
        Dynamically detect bank name from email content.
        Uses sender name as primary identifier.
        """
        # First try to detect known banks
        known_banks = {
            'sbi': 'state_bank_of_india',
            'hdfc': 'hdfc_bank',
            'icici': 'icici_bank',
            'axis': 'axis_bank',
            'kotak': 'kotak_bank',
            'yes': 'yes_bank',
            'pnb': 'punjab_national_bank',
            'union': 'union_bank',
            'canara': 'canara_bank',
            'bankofbaroda': 'bank_of_baroda',
            'idbi': 'idbi_bank'
        }
        
        # Check for known bank keywords in subject/sender/domain
        for bank_keyword, bank_name in known_banks.items():
            if (bank_keyword in subject or 
                bank_keyword in sender or 
                bank_keyword in domain):
                return bank_name
        
        # If no known bank found, use sender name as bank name
        return sender_name

    def _detect_company_name_dynamic(self, subject: str, sender: str, domain: str, sender_name: str) -> str:
        """
        Dynamically detect company name from email content.
        Uses sender name as primary identifier.
        """
        # Extract company name from domain if available
        if '.' in domain:
            company_part = domain.split('.')[0]
            # Clean company name
            company_name = company_part.replace('-', '_').replace('.', '_')
            company_name = ''.join(c for c in company_name if c.isalnum() or c == '_')
            
            if company_name and company_name != 'www':
                return company_name.lower()
        
        # If domain extraction fails, use sender name
        return sender_name
    
    def _is_bank_email(self, subject: str, sender: str, domain: str) -> bool:
        """Check if email is from a bank."""
        bank_keywords = ['bank', 'sbi', 'hdfc', 'icici', 'axis', 'kotak', 'yes', 'pnb', 'union']
        bank_domains = ['sbi.co.in', 'hdfcbank.com', 'icicibank.com', 'axisbank.com', 'kotak.com', 'yesbank.in', 'pnb.co.in']
        
        return (any(keyword in subject or keyword in sender for keyword in bank_keywords) or
                any(bank_domain in domain for bank_domain in bank_domains))
    
    def _is_company_email(self, subject: str, sender: str, domain: str) -> bool:
        """Check if email is from a company."""
        company_keywords = ['invoice', 'receipt', 'statement', 'account', 'business', 'corporate']
        return any(keyword in subject for keyword in company_keywords)
    
    def _is_support_email(self, subject: str, sender: str) -> bool:
        """Check if email is support related."""
        support_keywords = ['support', 'help', 'issue', 'problem', 'ticket', 'assistance']
        return any(keyword in subject for keyword in support_keywords)
    
    def _detect_support_type(self, subject: str, body: str) -> str:
        """Detect support type."""
        if any(word in subject for word in ['technical', 'tech', 'software', 'app']):
            return 'technical'
        elif any(word in subject for word in ['billing', 'payment', 'invoice']):
            return 'billing'
        elif any(word in subject for word in ['general', 'inquiry', 'question']):
            return 'general'
        else:
            return 'general'
    
    def _is_newsletter_email(self, subject: str, sender: str) -> bool:
        """Check if email is a newsletter."""
        newsletter_keywords = ['newsletter', 'news', 'update', 'digest', 'weekly', 'monthly']
        return any(keyword in subject for keyword in newsletter_keywords)
    
    def _detect_newsletter_type(self, subject: str, body: str) -> str:
        """Detect newsletter type."""
        if any(word in subject for word in ['tech', 'technology', 'software']):
            return 'tech_news'
        elif any(word in subject for word in ['business', 'finance', 'market']):
            return 'business_news'
        elif any(word in subject for word in ['health', 'medical', 'fitness']):
            return 'health_news'
        else:
            return 'general_news'
    
    def _is_billing_email(self, subject: str, sender: str) -> bool:
        """Check if email is billing related."""
        billing_keywords = ['invoice', 'payment', 'bill', 'receipt', 'statement', 'due']
        return any(keyword in subject for keyword in billing_keywords)
    
    def _detect_billing_type(self, subject: str, body: str) -> str:
        """Detect billing type."""
        if 'invoice' in subject:
            return 'invoice'
        elif 'payment' in subject:
            return 'payment'
        elif 'receipt' in subject:
            return 'receipt'
        else:
            return 'billing'
    
    def _is_order_email(self, subject: str, sender: str) -> bool:
        """Check if email is order related."""
        order_keywords = ['order', 'purchase', 'buy', 'shipping', 'delivery', 'tracking']
        return any(keyword in subject for keyword in order_keywords)
    
    def _detect_order_type(self, subject: str, body: str) -> str:
        """Detect order type."""
        if 'shipping' in subject or 'delivery' in subject:
            return 'shipping'
        elif 'tracking' in subject:
            return 'tracking'
        elif 'order' in subject:
            return 'order_confirmation'
        else:
            return 'order'
    
    def _is_social_email(self, subject: str, sender: str, domain: str) -> bool:
        """Check if email is from social media."""
        social_domains = ['facebook.com', 'twitter.com', 'linkedin.com', 'instagram.com', 'youtube.com']
        social_keywords = ['facebook', 'twitter', 'linkedin', 'instagram', 'youtube']
        
        return (any(social_domain in domain for social_domain in social_domains) or
                any(keyword in subject or keyword in sender for keyword in social_keywords))
    
    def _detect_social_platform(self, subject: str, sender: str, domain: str) -> str:
        """Detect social media platform."""
        if 'facebook' in subject or 'facebook' in sender or 'facebook.com' in domain:
            return 'facebook'
        elif 'twitter' in subject or 'twitter' in sender or 'twitter.com' in domain:
            return 'twitter'
        elif 'linkedin' in subject or 'linkedin' in sender or 'linkedin.com' in domain:
            return 'linkedin'
        elif 'instagram' in subject or 'instagram' in sender or 'instagram.com' in domain:
            return 'instagram'
        elif 'youtube' in subject or 'youtube' in sender or 'youtube.com' in domain:
            return 'youtube'
        else:
            return 'other_social'
    
    def _is_security_email(self, subject: str, sender: str) -> bool:
        """Check if email is security related."""
        security_keywords = ['security', 'password', 'login', 'verification', 'otp', '2fa']
        return any(keyword in subject for keyword in security_keywords)
    
    def _detect_security_type(self, subject: str, body: str) -> str:
        """Detect security type."""
        if 'otp' in subject or 'verification' in subject:
            return 'otp'
        elif 'password' in subject:
            return 'password'
        elif 'login' in subject:
            return 'login'
        else:
            return 'security'
    
    def _is_meeting_email(self, subject: str, sender: str) -> bool:
        """Check if email is meeting related."""
        meeting_keywords = ['meeting', 'appointment', 'schedule', 'calendar', 'call']
        return any(keyword in subject for keyword in meeting_keywords)
    
    def _detect_meeting_type(self, subject: str, body: str) -> str:
        """Detect meeting type."""
        if 'appointment' in subject:
            return 'appointment'
        elif 'call' in subject:
            return 'call'
        else:
            return 'meeting'
    
    def _is_career_email(self, subject: str, sender: str) -> bool:
        """Check if email is career related."""
        career_keywords = ['job', 'career', 'application', 'resume', 'interview', 'position']
        return any(keyword in subject for keyword in career_keywords)
    
    def _detect_career_type(self, subject: str, body: str) -> str:
        """Detect career type."""
        if 'interview' in subject:
            return 'interview'
        elif 'application' in subject:
            return 'application'
        else:
            return 'job'
    
    def _is_notification_email(self, subject: str, sender: str) -> bool:
        # Check for keywords related to notifications
        keywords = ['notification', 'alert', 'reminder', 'update']
        return any(keyword in subject for keyword in keywords)

    def _detect_notification_type(self, subject: str, body: str) -> str:
        # Simple detection based on subject keywords
        if 'failed' in subject or 'error' in subject:
            return 'failure'
        elif 'success' in subject or 'completed' in subject:
            return 'success'
        return 'general'
        
    def set_email_action(self, email_id: str, action: str, value: any) -> bool:
        """
        Set a specific action/status for an email.
        
        Args:
            email_id: The ID of the email to update.
            action: The action to perform (e.g., 'star', 'archive', 'trash', 'move').
            value: The value for the action (e.g., True/False for star, folder name for move).
            
        Returns:
            True if successful, False otherwise.
        """
        email = self.db.get_email_by_id(email_id)
        if not email:
            logger.error(f"Email with ID {email_id} not found.")
            return False

        try:
            if action == 'star':
                email.is_starred = bool(value)
            elif action == 'archive':
                email.is_archived = bool(value)
            elif action == 'trash':
                email.is_trashed = bool(value)
            elif action == 'report_spam':
                email.is_spam = bool(value)
            elif action == 'move':
                email.folder = str(value)
            else:
                logger.error(f"Unknown action: {action}")
                return False
            
            # Save the updated email object
            self.db.save_email(email)
            logger.info(f"Email {email_id} updated: {action} = {value}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating email {email_id} for action {action}: {e}")
            return False

    def categorize_stored_emails_batch(self, emails_to_categorize: List[Email]) -> Dict[str, int]:
        """
        Categorize a batch of emails using the new hierarchical categorization system.
        
        Args:
            emails_to_categorize: List of Email objects to categorize
            
        Returns:
            Dictionary with categorized and skipped email counts
        """
        results = {'categorized': 0, 'skipped': 0, 'errors': []}
        for email in emails_to_categorize:
            try:
                # Use hierarchical categorization (no AI needed)
                main_category, sub_category = self._enhanced_categorize_email(email)
                
                if main_category != 'general':
                    email.main_category = main_category
                    email.sub_category = sub_category
                    email.category = f"{main_category}_{sub_category}"  # Combined for compatibility
                    email.date = self.ensure_datetime(email.date)
                    email.created_at = self.ensure_datetime(getattr(email, 'created_at', datetime.now()))
                    self.db.save_email(email)
                    results['categorized'] += 1
                    logger.info(f"Categorized email '{email.subject[:30]}...' as '{main_category}/{sub_category}'")
                else:
                    results['skipped'] += 1
                    
            except Exception as e:
                error_msg = f"Error categorizing email {email.id}: {str(e)}"
                results['errors'].append(error_msg)
                logger.error(error_msg)
        return results

    def generate_email_hash_from_msg(self, msg):
        # Generate a hash from From, To, Date, Subject, Body
        import hashlib
        from_addr = msg.get('From', '')
        to_addr = msg.get('To', '')
        date = msg.get('Date', '')
        subject = msg.get('Subject', '')
        body = ''
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == 'text/plain':
                    body += part.get_payload(decode=True).decode(errors='ignore')
        else:
            body = msg.get_payload(decode=True).decode(errors='ignore')
        hash_input = f"{from_addr}{to_addr}{date}{subject}{body}".encode('utf-8')
        return hashlib.sha256(hash_input).hexdigest()

    def ensure_datetime(self, val):
        if isinstance(val, datetime):
            return val
        try:
            return datetime.fromisoformat(str(val))
        except Exception:
            try:
                return parsedate_to_datetime(str(val))
            except Exception:
                return datetime.now()

    def sync_read_status_from_server(self, account: EmailAccount) -> bool:
        """
        Sync read status from email server to local database.
        
        Args:
            account: EmailAccount object with connection details
            
        Returns:
            True if sync successful, False otherwise
        """
        try:
            # Connect to IMAP server
            mail = imaplib.IMAP4_SSL(account.imap_server, account.imap_port)
            mail.login(account.email, account.password)
            mail.select('inbox')
            
            # Get all emails from local database for this account
            local_emails = db_manager.get_emails({'account': account.email}, page=1, per_page=1000)[0]
            
            updated_count = 0
            
            for local_email in local_emails:
                try:
                    # Check read status on server
                    status_flags, flags_data = mail.fetch(local_email.id, '(FLAGS)')
                    if status_flags == 'OK':
                        flags = imaplib.ParseFlags(flags_data[0])
                        server_is_read = b'\\Seen' in flags
                        
                        # Update local database if status differs
                        if local_email.is_read != server_is_read:
                            local_email.is_read = server_is_read
                            db_manager.save_email(local_email)
                            updated_count += 1
                            logger.info(f"Synced read status for email {local_email.id}: {server_is_read}")
                            
                except Exception as e:
                    logger.error(f"Error checking read status for email {local_email.id}: {str(e)}")
                    continue
            
            mail.close()
            mail.logout()
            
            logger.info(f"Read status sync completed for {account.email}: {updated_count} emails updated")
            return True
            
        except Exception as e:
            logger.error(f"Error syncing read status for {account.email}: {str(e)}")
            return False
