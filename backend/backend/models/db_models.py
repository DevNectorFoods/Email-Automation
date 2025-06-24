from datetime import datetime
from typing import Optional, List, Dict
import mysql.connector
from mysql.connector import Error
from dataclasses import dataclass, field
from .email_models import EmailAccount, Email
from .user_models import User
from email.utils import parsedate_to_datetime
import json
from ..config import Config
import logging

class DatabaseManager:
    """Simple MySQL database manager for storing email accounts and emails."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.init_database()
    
    def get_connection(self):
        return mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB
        )
    
    def init_database(self):
        """Initialize database tables."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Create email_accounts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS email_accounts (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    imap_server VARCHAR(255) NOT NULL,
                    imap_port INT DEFAULT 993,
                    account_type VARCHAR(50) DEFAULT 'hostinger',
                    is_active TINYINT(1) DEFAULT 1,
                    last_checked DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_fetched_uid INT DEFAULT 0,
                    last_fetched_date DATETIME
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            ''')
            
            # Create emails table (add message_id column)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS emails (
                    id VARCHAR(255) PRIMARY KEY,
                    account_email VARCHAR(255) NOT NULL,
                    subject TEXT,
                    sender VARCHAR(255),
                    date DATETIME,
                    body LONGTEXT,
                    raw_data LONGTEXT,
                    category VARCHAR(100) DEFAULT 'general',
                    main_category VARCHAR(100) DEFAULT 'general',
                    sub_category VARCHAR(100) DEFAULT 'general',
                    is_read TINYINT(1) DEFAULT 0,
                    is_starred BOOLEAN DEFAULT FALSE,
                    is_archived BOOLEAN DEFAULT FALSE,
                    is_spam BOOLEAN DEFAULT FALSE,
                    is_trashed BOOLEAN DEFAULT FALSE,
                    folder VARCHAR(255) DEFAULT 'inbox',
                    tags TEXT,
                    metadata TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    email_hash VARCHAR(255),
                    verification_hash VARCHAR(255),
                    message_id VARCHAR(255),
                    FOREIGN KEY (account_email) REFERENCES email_accounts (email)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            ''')
            
            # Create users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    name VARCHAR(255),
                    role VARCHAR(50) DEFAULT 'user',
                    is_active TINYINT(1) DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_login DATETIME
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            ''')
            
            # Create user_email_access table for access control
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_email_access (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    user_id INT NOT NULL,
                    account_email VARCHAR(255) NOT NULL,
                    access_level ENUM('read', 'write', 'admin') DEFAULT 'read',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    created_by INT,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                    FOREIGN KEY (account_email) REFERENCES email_accounts (email) ON DELETE CASCADE,
                    FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE SET NULL,
                    UNIQUE KEY unique_user_account (user_id, account_email)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            ''')
            
            # Create indexes for better performance
            try:
                cursor.execute('CREATE INDEX idx_emails_account ON emails(account_email)')
            except Exception as e:
                if 'Duplicate key name' not in str(e):
                    raise
            try:
                cursor.execute('CREATE INDEX idx_emails_category ON emails(category)')
            except Exception as e:
                if 'Duplicate key name' not in str(e):
                    raise
            try:
                cursor.execute('CREATE INDEX idx_emails_date ON emails(date)')
            except Exception as e:
                if 'Duplicate key name' not in str(e):
                    raise
            try:
                cursor.execute('CREATE INDEX idx_emails_message_id ON emails(message_id)')
            except Exception as e:
                if 'Duplicate key name' not in str(e):
                    raise
            
            conn.commit()
            conn.close()
            
            self.logger.info("MySQL Database initialized successfully")
            
        except Error as e:
            self.logger.error(f"MySQL Database initialization failed: {str(e)}")
            raise
    
    def add_email_account(self, account: EmailAccount) -> bool:
        """Add a new email account to the database."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO email_accounts 
                (email, password, imap_server, imap_port, account_type, is_active, last_checked, created_at, last_fetched_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    password=VALUES(password),
                    imap_server=VALUES(imap_server),
                    imap_port=VALUES(imap_port),
                    account_type=VALUES(account_type),
                    is_active=VALUES(is_active),
                    last_checked=VALUES(last_checked),
                    created_at=VALUES(created_at),
                    last_fetched_date=VALUES(last_fetched_date)
            ''', (
                account.email,
                account.password,
                account.imap_server,
                account.imap_port,
                account.account_type,
                account.is_active,
                account.last_checked.isoformat() if account.last_checked else None,
                account.created_at.isoformat() if account.created_at else datetime.now().isoformat(),
                account.last_fetched_date.isoformat() if account.last_fetched_date else None
            ))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Email account added: {account.email}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add email account: {str(e)}")
            return False
    
    def get_email_accounts(self) -> List[EmailAccount]:
        """Get all email accounts from the database."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM email_accounts WHERE is_active = 1')
            rows = cursor.fetchall()
            conn.close()
            accounts = []
            for row in rows:
                account = EmailAccount(
                    email=row[1] or '',
                    password=row[2] or '',
                    imap_server=row[3] or '',
                    imap_port=row[4] or 993,
                    account_type=row[5] or 'hostinger',
                    is_active=bool(row[6]),
                    last_checked=row[7],  # Direct use of datetime or None
                    created_at=row[8] or datetime.now(),  # Direct use, fallback to now
                    last_fetched_uid=row[9] if row[9] is not None else 0,
                    last_fetched_date=row[10]  # Direct use of datetime or None
                )
                accounts.append(account)
            return accounts
        except Exception as e:
            self.logger.error(f"Failed to get email accounts: {str(e)}")
            return []

    def get_email_account(self, email: str) -> Optional[EmailAccount]:
        """Get a specific email account by email address."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM email_accounts WHERE email = %s', (email,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                account = EmailAccount(
                    email=row[1] or '',
                    password=row[2] or '',
                    imap_server=row[3] or '',
                    imap_port=row[4] or 993,
                    account_type=row[5] or 'hostinger',
                    is_active=bool(row[6]),
                    last_checked=row[7],  # Direct use of datetime or None
                    created_at=row[8] or datetime.now(),  # Direct use, fallback to now
                    last_fetched_uid=row[9] if row[9] is not None else 0,
                    last_fetched_date=row[10]  # Direct use of datetime or None
                )
                return account
            return None
        except Exception as e:
            self.logger.error(f"Failed to get email account {email}: {str(e)}")
            return None
    
    def delete_email_account(self, email: str) -> bool:
        """Delete an email account from the database."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # First check if the account exists
            cursor.execute('SELECT COUNT(*) FROM email_accounts WHERE email = %s', (email,))
            count = cursor.fetchone()[0]
            
            if count == 0:
                self.logger.warning(f"Email account not found for deletion: {email}")
                conn.close()
                return False
            
            # Delete child records first (emails) to avoid foreign key constraint
            cursor.execute('DELETE FROM emails WHERE account_email = %s', (email,))
            deleted_emails = cursor.rowcount
            self.logger.info(f"Deleted {deleted_emails} emails for account: {email}")
            
            # Then delete the parent record (email account)
            cursor.execute('DELETE FROM email_accounts WHERE email = %s', (email,))
            deleted_accounts = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            if deleted_accounts > 0:
                self.logger.info(f"Email account deleted successfully: {email} (with {deleted_emails} emails)")
                return True
            else:
                self.logger.error(f"Failed to delete email account: {email}")
                return False
            
        except Exception as e:
            self.logger.error(f"Failed to delete email account: {str(e)}")
            return False

    def delete_email(self, email_id: str) -> bool:
        """Permanently delete an email by ID."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM emails WHERE id = %s', (email_id,))
            conn.commit()
            deleted = cursor.rowcount
            conn.close()
            return deleted > 0
        except Exception as e:
            self.logger.error(f"Failed to delete email: {str(e)}")
            return False
    
    def get_all_emails(self, filters: dict = {}) -> (List[Email], int):
        """Get all emails from the database with optional filters."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)

            query = "SELECT * FROM emails"
            count_query = "SELECT COUNT(*) as total FROM emails"
            where_clauses = []
            params = {}

            if 'category' in filters and filters['category']:
                if filters['category'] == 'unread':
                    where_clauses.append("is_read = 0")
                elif filters['category'] != 'all':
                    where_clauses.append("category = %(category)s")
                    params['category'] = filters['category']
            
            if 'account' in filters and filters['account']:
                where_clauses.append("account_email = %(account)s")
                params['account'] = filters['account']

            if 'search' in filters and filters['search']:
                where_clauses.append("(subject LIKE %(search)s OR sender LIKE %(search)s)")
                params['search'] = f"%{filters['search']}%"

            if 'main_category' in filters and filters['main_category']:
                where_clauses.append("main_category = %(main_category)s")
                params['main_category'] = filters['main_category']

            if 'sub_category' in filters and filters['sub_category']:
                where_clauses.append("sub_category = %(sub_category)s")
                params['sub_category'] = filters['sub_category']

            # Handle boolean filters (convert to int for MySQL)
            for bool_key in ['is_trashed', 'is_starred', 'is_read', 'is_archived', 'is_spam']:
                if bool_key in filters:
                    where_clauses.append(f"{bool_key} = %({bool_key})s")
                    params[bool_key] = int(filters[bool_key]) if isinstance(filters[bool_key], bool) else filters[bool_key]

            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
                count_query += " WHERE " + " AND ".join(where_clauses)

            query += " ORDER BY date DESC"

            # Get total count
            cursor.execute(count_query, params)
            total = cursor.fetchone()['total']

            # Get all emails
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            conn.close()
            
            emails = [Email.from_dict(row) for row in rows]
            return emails, total
            
        except Exception as e:
            self.logger.error(f"Failed to get all emails: {str(e)}")
            return [], 0

    def _ensure_datetime(self, value):
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, (int, float)):
            # Assume timestamp
            try:
                return datetime.fromtimestamp(value)
            except Exception:
                self.logger.error(f"_ensure_datetime: Invalid timestamp: {value}")
                return datetime.now()
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except Exception:
                try:
                    return parsedate_to_datetime(value)
                except Exception:
                    try:
                        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                    except Exception:
                        self.logger.error(f"_ensure_datetime: Invalid date string: {value}")
                        return datetime.now()
        self.logger.error(f"_ensure_datetime: Unexpected type {type(value)}: {value}")
        return datetime.now()

    def parse_datetime(self, dt):
        """Parse a datetime value, handling None and datetime objects directly."""
        if dt is None:
            return None
        if isinstance(dt, datetime):
            return dt
        # Handle string inputs as a fallback
        try:
            return datetime.fromisoformat(str(dt))
        except ValueError:
            try:
                return datetime.strptime(str(dt), "%Y-%m-%d %H:%M:%S")
            except ValueError:
                self.logger.error(f"Invalid datetime format: {dt} (type: {type(dt)})")
                return None
    
    def save_email(self, email: Email) -> bool:
        """Save an email to the database."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # First check if the email account exists
            cursor.execute('SELECT COUNT(*) FROM email_accounts WHERE email = %s', (email.account_email,))
            account_exists = cursor.fetchone()[0] > 0
            
            if not account_exists:
                self.logger.warning(f"Cannot save email: Email account '{email.account_email}' does not exist")
                conn.close()
                return False
            
            # Ensure date and created_at are datetime objects
            self.logger.debug(f"Input email.date: {email.date} (type: {type(email.date)})")
            date_val = self._ensure_datetime(email.date)
            if not isinstance(date_val, datetime):
                self.logger.error(f"date_val is not datetime, got {type(date_val)}: {date_val}")
                date_val = datetime.now()
            created_at_val = self._ensure_datetime(getattr(email, 'created_at', datetime.now()))
            if not isinstance(created_at_val, datetime):
                self.logger.error(f"created_at_val is not datetime, got {type(created_at_val)}: {created_at_val}")
                created_at_val = datetime.now()
            # Ensure all fields are not None
            subject = email.subject if email.subject is not None else ''
            sender = email.sender if email.sender is not None else ''
            body = email.body if email.body is not None else ''
            raw_data = email.raw_data if email.raw_data is not None else ''
            category = email.category if email.category is not None else 'general'
            main_category = email.main_category if email.main_category is not None else 'general'
            sub_category = email.sub_category if email.sub_category is not None else 'general'
            tags = email.tags if isinstance(email.tags, list) else []
            metadata = email.metadata if isinstance(email.metadata, dict) else {}
            email_hash = email.email_hash if email.email_hash is not None else ''
            verification_hash = email.verification_hash if email.verification_hash is not None else ''
            message_id = email.message_id if email.message_id is not None else ''
            # Ensure id is always a plain string
            if isinstance(email.id, bytes):
                email_id = email.id.decode('utf-8')
            elif isinstance(email.id, str) and email.id.startswith("b'") and email.id.endswith("'"):
                email_id = email.id[2:-1]
            else:
                email_id = str(email.id)
            self.logger.info(f"[DEBUG] id (cleaned): {email_id} ({type(email_id)})")
            # Log all field types and values before insert
            self.logger.info(f"[DEBUG] account_email: {email.account_email} ({type(email.account_email)})")
            self.logger.info(f"[DEBUG] subject: {subject} ({type(subject)})")
            self.logger.info(f"[DEBUG] sender: {sender} ({type(sender)})")
            self.logger.info(f"[DEBUG] date_val: {date_val} ({type(date_val)})")
            self.logger.info(f"[DEBUG] body: {body} ({type(body)})")
            self.logger.info(f"[DEBUG] raw_data: {raw_data} ({type(raw_data)})")
            self.logger.info(f"[DEBUG] category: {category} ({type(category)})")
            self.logger.info(f"[DEBUG] main_category: {main_category} ({type(main_category)})")
            self.logger.info(f"[DEBUG] sub_category: {sub_category} ({type(sub_category)})")
            self.logger.info(f"[DEBUG] is_read: {email.is_read} ({type(email.is_read)})")
            tags_json = json.dumps(tags)
            metadata_json = json.dumps(metadata)
            self.logger.info(f"[DEBUG] tags_json: {tags_json} ({type(tags_json)})")
            self.logger.info(f"[DEBUG] metadata_json: {metadata_json} ({type(metadata_json)})")
            self.logger.info(f"[DEBUG] created_at_val: {created_at_val} ({type(created_at_val)})")
            self.logger.info(f"[DEBUG] email_hash: {email_hash} ({type(email_hash)})")
            self.logger.info(f"[DEBUG] verification_hash: {verification_hash} ({type(verification_hash)})")
            self.logger.info(f"[DEBUG] message_id: {message_id} ({type(message_id)})")
            cursor.execute('''
                INSERT INTO emails 
                (id, account_email, subject, sender, date, body, raw_data, category, 
                 main_category, sub_category, is_read, is_starred, is_archived, is_spam, is_trashed, folder, tags, metadata, created_at, email_hash, verification_hash, message_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    is_read=VALUES(is_read),
                    category=VALUES(category),
                    main_category=VALUES(main_category),
                    sub_category=VALUES(sub_category),
                    is_starred=VALUES(is_starred),
                    is_archived=VALUES(is_archived),
                    is_spam=VALUES(is_spam),
                    is_trashed=VALUES(is_trashed),
                    folder=VALUES(folder),
                    tags=VALUES(tags),
                    metadata=VALUES(metadata),
                    created_at=VALUES(created_at),
                    email_hash=VALUES(email_hash),
                    verification_hash=VALUES(verification_hash),
                    message_id=VALUES(message_id)
            ''', (
                email_id,
                email.account_email,
                subject,
                sender,
                date_val.isoformat(),
                body,
                raw_data,
                category,
                main_category,
                sub_category,
                int(email.is_read),
                int(email.is_starred),
                int(email.is_archived),
                int(email.is_spam),
                int(email.is_trashed),
                email.folder,
                tags_json,
                metadata_json,
                created_at_val.isoformat(),
                email_hash,
                verification_hash,
                message_id
            ))
            self.logger.info(f"[DEBUG] Executed email UPSERT for id={email_id}, account_email={email.account_email}, is_trashed={email.is_trashed}, folder={email.folder}")
            self.logger.info(f"[DEBUG] cursor.rowcount after UPSERT: {cursor.rowcount}")
            conn.commit()
            if cursor.rowcount == 0:
                self.logger.warning(f"[WARNING] Email UPSERT did not affect any rows for id={email_id}, account_email={email.account_email}")
            conn.close()
            self.logger.info(f"Email saved: {subject[:50]}...")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save email: {str(e)}")
            return False
    
    def get_emails(self, filters: dict = {}, page: int = 1, per_page: int = 20) -> (List[Email], int):
        """Get emails from the database with filtering and pagination."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)

            query = "SELECT * FROM emails"
            count_query = "SELECT COUNT(*) as total FROM emails"
            where_clauses = []
            params = {}

            if 'category' in filters and filters['category']:
                if filters['category'] == 'unread':
                    where_clauses.append("is_read = 0")
                elif filters['category'] != 'all':
                    where_clauses.append("category = %(category)s")
                    params['category'] = filters['category']

            if 'account' in filters and filters['account']:
                where_clauses.append("account_email = %(account)s")
                params['account'] = filters['account']

            if 'search' in filters and filters['search']:
                where_clauses.append("(subject LIKE %(search)s OR sender LIKE %(search)s)")
                params['search'] = f"%{filters['search']}%"

            if 'main_category' in filters and filters['main_category']:
                where_clauses.append("main_category = %(main_category)s")
                params['main_category'] = filters['main_category']

            if 'sub_category' in filters and filters['sub_category']:
                where_clauses.append("sub_category = %(sub_category)s")
                params['sub_category'] = filters['sub_category']

            # Handle boolean filters (convert to int for MySQL)
            for bool_key in ['is_trashed', 'is_starred', 'is_read', 'is_archived', 'is_spam']:
                if bool_key in filters:
                    where_clauses.append(f"{bool_key} = %({bool_key})s")
                    params[bool_key] = int(filters[bool_key]) if isinstance(filters[bool_key], bool) else filters[bool_key]

            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
                count_query += " WHERE " + " AND ".join(where_clauses)

            # Get total count
            cursor.execute(count_query, params)
            total = cursor.fetchone()['total']
            
            # Add pagination
            offset = (page - 1) * per_page
            query += " ORDER BY date DESC LIMIT %(limit)s OFFSET %(offset)s"
            params['limit'] = per_page
            params['offset'] = offset
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            conn.close()
            
            emails = [Email.from_dict(row) for row in rows]
            return emails, total
            
        except Exception as e:
            self.logger.error(f"Failed to get emails: {str(e)}")
            return [], 0
    
    def get_email_stats(self) -> dict:
        """Get email statistics from the database."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Total emails
            cursor.execute('SELECT COUNT(*) FROM emails')
            total_emails = cursor.fetchone()[0]
            
            # Total accounts
            cursor.execute('SELECT COUNT(*) FROM email_accounts WHERE is_active = 1')
            total_accounts = cursor.fetchone()[0]
            
            # Emails by category
            cursor.execute('SELECT category, COUNT(*) FROM emails GROUP BY category')
            category_rows = cursor.fetchall()
            emails_by_category = {row[0]: row[1] for row in category_rows}
            
            # Emails by account
            cursor.execute('SELECT account_email, COUNT(*) FROM emails GROUP BY account_email')
            account_rows = cursor.fetchall()
            emails_by_account = {row[0]: row[1] for row in account_rows}
            
            # Read/unread counts
            cursor.execute('SELECT COUNT(*) FROM emails WHERE is_read = 1')
            read_emails = cursor.fetchone()[0]
            unread_emails = total_emails - read_emails
            
            # Last fetch time (from last email created)
            cursor.execute('SELECT MAX(created_at) FROM emails')
            last_fetch = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_emails': total_emails,
                'total_accounts': total_accounts,
                'emails_by_category': emails_by_category,
                'emails_by_account': emails_by_account,
                'read_emails': read_emails,
                'unread_emails': unread_emails,
                'last_fetch_time': last_fetch,
                'fetch_errors': 0  # We'll track this separately
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get email stats: {str(e)}")
            return {
                'total_emails': 0,
                'total_accounts': 0,
                'emails_by_category': {},
                'emails_by_account': {},
                'read_emails': 0,
                'unread_emails': 0,
                'last_fetch_time': None,
                'fetch_errors': 0
            }
    
    def get_email_by_id(self, email_id: str) -> Optional[Email]:
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute('SELECT * FROM emails WHERE id = %s', (email_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                import json
                # Handle tags field with better error handling
                tags = []
                if row.get('tags'):
                    try:
                        tags = json.loads(row['tags'])
                    except (json.JSONDecodeError, TypeError) as e:
                        self.logger.warning(f"Failed to parse tags for email {email_id}: {e}")
                        tags = []
                
                # Handle metadata field with better error handling
                metadata = {}
                if row.get('metadata'):
                    try:
                        metadata = json.loads(row['metadata'])
                    except (json.JSONDecodeError, TypeError) as e:
                        self.logger.warning(f"Failed to parse metadata for email {email_id}: {e}")
                        metadata = {}
                
                return Email(
                    id=str(row['id']),
                    account_email=row['account_email'] or '',
                    subject=row['subject'] or '',
                    sender=row['sender'] or '',
                    date=self._ensure_datetime(row['date']) if row['date'] else datetime.now(),
                    body=row['body'] or '',
                    raw_data=row['raw_data'] or '',
                    category=row['category'] or 'general',
                    main_category=row['main_category'] or 'general',
                    sub_category=row['sub_category'] or 'general',
                    is_read=bool(row['is_read']),
                    is_starred=bool(row['is_starred']),
                    is_archived=bool(row['is_archived']),
                    is_spam=bool(row['is_spam']),
                    is_trashed=bool(row['is_trashed']),
                    folder=row['folder'] or 'inbox',
                    tags=tags,
                    metadata=metadata,
                    created_at=self._ensure_datetime(row['created_at']) if row['created_at'] else datetime.now(),
                    email_hash=row.get('email_hash'),
                    verification_hash=row.get('verification_hash'),
                    message_id=row.get('message_id')
                )
            return None
        except Exception as e:
            self.logger.error(f"Failed to get email by id: {str(e)}")
            return None
    
    def mark_all_emails_read(self):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('UPDATE emails SET is_read = 1')
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            self.logger.error(f"Failed to mark all emails as read: {str(e)}")
            return False

    def update_last_fetched_uid(self, account_email: str, last_uid: int) -> bool:
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('UPDATE email_accounts SET last_fetched_uid = %s WHERE email = %s', (last_uid, account_email))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            self.logger.error(f"Failed to update last_fetched_uid: {str(e)}")
            return False

    def update_last_fetched_date(self, account_email: str, last_date: datetime) -> bool:
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('UPDATE email_accounts SET last_fetched_date = %s WHERE email = %s', (last_date.isoformat(), account_email))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            self.logger.error(f"Failed to update last_fetched_date: {str(e)}")
            return False

    def update_email_account(self, account: EmailAccount) -> bool:
        """Update an existing email account in the database."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE email_accounts 
                SET password = %s, imap_server = %s, imap_port = %s, 
                    account_type = %s, is_active = %s, last_checked = %s
                WHERE email = %s
            ''', (
                account.password,
                account.imap_server,
                account.imap_port,
                account.account_type,
                account.is_active,
                account.last_checked.isoformat() if account.last_checked else None,
                account.email
            ))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Email account updated: {account.email}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update email account: {str(e)}")
            return False

    def email_exists(self, message_id: str = None, email_hash: str = None) -> bool:
        """Check if an email exists by message_id or email_hash."""
        if not message_id and not email_hash:
            return False
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            query = "SELECT id FROM emails WHERE "
            params = []
            
            if message_id:
                query += "message_id = %s"
                params.append(message_id)
            elif email_hash:
                query += "email_hash = %s"
                params.append(email_hash)
                
            cursor.execute(query, tuple(params))
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result else None
            
        except Exception as e:
            self.logger.error(f"Error checking if email exists: {str(e)}")
            return None

    # --- User Management Methods ---
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email address."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
            row = cursor.fetchone()
            conn.close()
            if row:
                user = User(
                    id=row[0],
                    email=row[1],
                    password=row[2],
                    name=row[3],
                    role=row[4],
                    is_active=bool(row[5]),
                    created_at=self.parse_datetime(row[6]),
                    last_login=self.parse_datetime(row[7])
                )
                return user
            return None
        except Exception as e:
            self.logger.error(f"Failed to get user by email: {str(e)}")
            return None

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get a user by user ID."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                user = User(
                    id=row[0],
                    email=row[1],
                    password=row[2],
                    name=row[3],
                    role=row[4],
                    is_active=bool(row[5]),
                    created_at=self.parse_datetime(row[6]),
                    last_login=self.parse_datetime(row[7])
                )
                return user
            return None
        except Exception as e:
            self.logger.error(f"Failed to get user by id: {str(e)}")
            return None

    def create_user(self, user: User) -> bool:
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (email, password, name, role, is_active, created_at, last_login)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (
                user.email,
                user.password,
                user.name,
                user.role,
                user.is_active,
                user.created_at.isoformat() if user.created_at else datetime.now().isoformat(),
                user.last_login.isoformat() if user.last_login else None
            ))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            self.logger.error(f"Failed to create user: {str(e)}")
            return False

    def update_user(self, user: User) -> bool:
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users SET email=%s, password=%s, name=%s, role=%s, is_active=%s, created_at=%s, last_login=%s WHERE id=%s
            ''', (
                user.email,
                user.password,
                user.name,
                user.role,
                user.is_active,
                user.created_at.isoformat() if user.created_at else datetime.now().isoformat(),
                user.last_login.isoformat() if user.last_login else None,
                user.id
            ))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            self.logger.error(f"Failed to update user: {str(e)}")
            return False

    def delete_user(self, user_id: int) -> bool:
        """Delete a user from the database."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM users WHERE id = %s', (user_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            self.logger.error(f"Error deleting user: {str(e)}")
            return False

    def verification_hash_exists(self, verification_hash: str) -> bool:
        """Check if verification hash already exists in database."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM emails WHERE verification_hash = %s', (verification_hash,))
            count = cursor.fetchone()[0]
            conn.close()
            return count > 0
        except Exception as e:
            self.logger.error(f"Error checking verification hash: {str(e)}")
            return False

    def get_emails_by_category(self, category: str, limit: int = 50) -> List[Email]:
        """Get emails by specific category."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM emails 
                WHERE category = %s 
                ORDER BY date DESC 
                LIMIT %s
            ''', (category, limit))
            rows = cursor.fetchall()
            conn.close()
            emails = []
            for row in rows:
                import json
                email = Email(
                    id=row[0] or '',
                    account_email=row[1] or '',
                    subject=row[2] or '',
                    sender=row[3] or '',
                    date=self._ensure_datetime(row[4]) if len(row) > 4 else datetime.now(),
                    body=row[5] or '',
                    raw_data=row[6] or '',
                    category=row[7] or 'general',
                    main_category=row[8] if len(row) > 8 else 'general',
                    sub_category=row[9] if len(row) > 9 else 'general',
                    is_read=bool(row[10]),
                    is_starred=bool(row[11]) if len(row) > 11 else False,
                    is_archived=bool(row[12]) if len(row) > 12 else False,
                    is_spam=bool(row[13]) if len(row) > 13 else False,
                    is_trashed=bool(row[14]) if len(row) > 14 else False,
                    folder=row[15] if len(row) > 15 else 'inbox',
                    tags=json.loads(row[16]) if row[16] else [],
                    metadata=json.loads(row[17]) if row[17] else {},
                    created_at=self._ensure_datetime(row[18]) if len(row) > 18 else datetime.now(),
                    email_hash=row[19] if len(row) > 19 else None,
                    verification_hash=row[20] if len(row) > 20 else None,
                    message_id=row[21] if len(row) > 21 else None
                )
                emails.append(email)
            return emails
        except Exception as e:
            self.logger.error(f"Error getting emails by category: {str(e)}")
            return []

    def get_main_categories_with_counts(self) -> List[Dict]:
        """Get all main categories with email counts."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT main_category, COUNT(*) as count
                FROM emails
                WHERE main_category IS NOT NULL AND main_category != 'general'
                GROUP BY main_category
                ORDER BY count DESC
            ''')
            
            categories = []
            for row in cursor.fetchall():
                categories.append({
                    'main_category': row[0],
                    'count': row[1]
                })
            conn.close()
            return categories
        except Exception as e:
            self.logger.error(f"Error getting main categories: {str(e)}")
            return []
    
    def get_sub_categories_with_counts(self, main_category: str) -> List[Dict]:
        """Get sub categories for a main category with email counts."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT sub_category, COUNT(*) as count
                FROM emails
                WHERE main_category = %s AND sub_category IS NOT NULL AND sub_category != 'general'
                GROUP BY sub_category
                ORDER BY count DESC
            ''', (main_category,))
            
            sub_categories = []
            for row in cursor.fetchall():
                sub_categories.append({
                    'sub_category': row[0],
                    'count': row[1]
                })
            conn.close()
            return sub_categories
        except Exception as e:
            self.logger.error(f"Error getting sub categories: {str(e)}")
            return []
    
    def get_emails_by_category_hierarchy(self, main_category: str, sub_category: str, 
                                       page: int = 1, per_page: int = 50, 
                                       account_email: str = None) -> List[Email]:
        """Get emails by main category and sub category."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            offset = (page - 1) * per_page
            query = '''
                SELECT id, account_email, subject, sender, date, body, raw_data, 
                       category, main_category, sub_category, is_read, is_starred, is_archived, is_spam, is_trashed, folder, tags, metadata, 
                       created_at, email_hash, verification_hash, message_id
                FROM emails
                WHERE main_category = %s AND sub_category = %s
            '''
            params = [main_category, sub_category]
            if account_email:
                query += ' AND account_email = %s'
                params.append(account_email)
            query += ' ORDER BY date DESC LIMIT %s OFFSET %s'
            params.extend([per_page, offset])
            cursor.execute(query, params)
            emails = []
            for row in cursor.fetchall():
                email = Email(
                    id=row[0],
                    account_email=row[1],
                    subject=row[2],
                    sender=row[3],
                    date=self._ensure_datetime(row[4]) if len(row) > 4 else datetime.now(),
                    body=row[5],
                    raw_data=row[6],
                    category=row[7],
                    main_category=row[8],
                    sub_category=row[9],
                    is_read=bool(row[10]),
                    is_starred=bool(row[11]) if len(row) > 11 else False,
                    is_archived=bool(row[12]) if len(row) > 12 else False,
                    is_spam=bool(row[13]) if len(row) > 13 else False,
                    is_trashed=bool(row[14]) if len(row) > 14 else False,
                    folder=row[15] if len(row) > 15 else 'inbox',
                    tags=json.loads(row[16]) if row[16] else [],
                    metadata=json.loads(row[17]) if row[17] else {},
                    created_at=self._ensure_datetime(row[18]) if len(row) > 18 else datetime.now(),
                    email_hash=row[19],
                    verification_hash=row[20],
                    message_id=row[21] if len(row) > 21 else None
                )
                emails.append(email)
            conn.close()
            return emails
        except Exception as e:
            self.logger.error(f"Error getting emails by category hierarchy: {str(e)}")
            return []
    
    def get_emails_by_main_category(self, main_category: str, 
                                  page: int = 1, per_page: int = 50, 
                                  account_email: str = None) -> List[Email]:
        """Get emails by main category only."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            offset = (page - 1) * per_page
            query = '''
                SELECT id, account_email, subject, sender, date, body, raw_data, 
                       category, main_category, sub_category, is_read, is_starred, is_archived, is_spam, is_trashed, folder, tags, metadata, 
                       created_at, email_hash, verification_hash, message_id
                FROM emails
                WHERE main_category = %s
            '''
            params = [main_category]
            if account_email:
                query += ' AND account_email = %s'
                params.append(account_email)
            query += ' ORDER BY date DESC LIMIT %s OFFSET %s'
            params.extend([per_page, offset])
            cursor.execute(query, params)
            emails = []
            for row in cursor.fetchall():
                email = Email(
                    id=row[0],
                    account_email=row[1],
                    subject=row[2],
                    sender=row[3],
                    date=self._ensure_datetime(row[4]) if len(row) > 4 else datetime.now(),
                    body=row[5],
                    raw_data=row[6],
                    category=row[7],
                    main_category=row[8],
                    sub_category=row[9],
                    is_read=bool(row[10]),
                    is_starred=bool(row[11]) if len(row) > 11 else False,
                    is_archived=bool(row[12]) if len(row) > 12 else False,
                    is_spam=bool(row[13]) if len(row) > 13 else False,
                    is_trashed=bool(row[14]) if len(row) > 14 else False,
                    folder=row[15] if len(row) > 15 else 'inbox',
                    tags=json.loads(row[16]) if row[16] else [],
                    metadata=json.loads(row[17]) if row[17] else {},
                    created_at=self._ensure_datetime(row[18]) if len(row) > 18 else datetime.now(),
                    email_hash=row[19],
                    verification_hash=row[20],
                    message_id=row[21] if len(row) > 21 else None
                )
                emails.append(email)
            conn.close()
            return emails
        except Exception as e:
            self.logger.error(f"Error getting emails by main category: {str(e)}")
            return []

    def get_all_users(self) -> List[User]:
        """Get all users from the database."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users ORDER BY created_at DESC')
            rows = cursor.fetchall()
            conn.close()
            
            users = []
            for row in rows:
                created_at = self.parse_datetime(row[6]) if len(row) > 6 else datetime.now()
                last_login = self.parse_datetime(row[7]) if len(row) > 7 else None
                user = User(
                    id=row[0],
                    email=row[1],
                    password=row[2],
                    name=row[3] or '',
                    role=row[4] or 'user',
                    is_active=bool(row[5]),
                    created_at=created_at,
                    last_login=last_login
                )
                users.append(user)
            
            return users
        except Exception as e:
            self.logger.error(f"Error getting all users: {str(e)}")
            return []

    def get_system_settings(self) -> dict:
        """Get system settings from database."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Create settings table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_settings (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    setting_key VARCHAR(255) UNIQUE NOT NULL,
                    setting_value TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            ''')
            
            cursor.execute('SELECT setting_key, setting_value FROM system_settings')
            rows = cursor.fetchall()
            conn.close()
            
            settings = {}
            for row in rows:
                key, value = row
                try:
                    # Try to parse JSON values
                    settings[key] = json.loads(value) if value else None
                except:
                    # If not JSON, use as string
                    settings[key] = value
            
            return settings
            
        except Exception as e:
            self.logger.error(f"Failed to get system settings: {str(e)}")
            return {}
    
    def update_system_settings(self, settings: dict) -> bool:
        """Update system settings in database."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Create settings table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_settings (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    setting_key VARCHAR(255) UNIQUE NOT NULL,
                    setting_value TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            ''')
            
            for key, value in settings.items():
                # Convert value to JSON string
                json_value = json.dumps(value) if value is not None else None
                
                cursor.execute('''
                    INSERT INTO system_settings (setting_key, setting_value)
                    VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE
                        setting_value = VALUES(setting_value),
                        updated_at = CURRENT_TIMESTAMP
                ''', (key, json_value))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update system settings: {str(e)}")
            return False
    
    def get_reply_templates(self) -> List[dict]:
        """Get all reply templates from database."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Create reply_templates table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reply_templates (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    name VARCHAR(255) NOT NULL,
                    subject VARCHAR(500),
                    content TEXT,
                    user_id INT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            ''')
            
            cursor.execute('SELECT * FROM reply_templates ORDER BY created_at DESC')
            rows = cursor.fetchall()
            conn.close()
            
            templates = []
            for row in rows:
                template = {
                    'id': row[0],
                    'name': row[1],
                    'subject': row[2],
                    'content': row[3],
                    'user_id': row[4],
                    'created_at': row[5],
                    'updated_at': row[6]
                }
                templates.append(template)
            
            return templates
            
        except Exception as e:
            self.logger.error(f"Failed to get reply templates: {str(e)}")
            return []
    
    def create_reply_template(self, template_data: dict) -> Optional[int]:
        """Create a new reply template."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Create reply_templates table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reply_templates (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    name VARCHAR(255) NOT NULL,
                    subject VARCHAR(500),
                    content TEXT,
                    user_id INT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            ''')
            
            cursor.execute('''
                INSERT INTO reply_templates (name, subject, content, user_id)
                VALUES (%s, %s, %s, %s)
            ''', (
                template_data['name'],
                template_data['subject'],
                template_data['content'],
                template_data['user_id']
            ))
            
            template_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return template_id
            
        except Exception as e:
            self.logger.error(f"Failed to create reply template: {str(e)}")
            return None
    
    def get_reply_template_by_id(self, template_id: int) -> Optional[dict]:
        """Get a specific reply template by ID."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM reply_templates WHERE id = %s', (template_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'id': row[0],
                    'name': row[1],
                    'subject': row[2],
                    'content': row[3],
                    'user_id': row[4],
                    'created_at': row[5],
                    'updated_at': row[6]
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get reply template: {str(e)}")
            return None
    
    def update_reply_template(self, template_id: int, template_data: dict) -> bool:
        """Update a reply template."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE reply_templates 
                SET name = %s, subject = %s, content = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            ''', (
                template_data['name'],
                template_data['subject'],
                template_data['content'],
                template_id
            ))
            
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to update reply template: {str(e)}")
            return False
    
    def delete_reply_template(self, template_id: int) -> bool:
        """Delete a reply template."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM reply_templates WHERE id = %s', (template_id,))
            
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to delete reply template: {str(e)}")
            return False

    # --- User Email Access Control Methods ---
    
    def get_user_email_access(self, user_id: int) -> List[Dict]:
        """Get all email accounts a user has access to."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute('''
                SELECT uea.account_email, uea.access_level, uea.created_at, ea.is_active
                FROM user_email_access uea
                JOIN email_accounts ea ON uea.account_email = ea.email
                WHERE uea.user_id = %s
                ORDER BY uea.created_at DESC
            ''', (user_id,))
            
            access_list = cursor.fetchall()
            conn.close()
            
            return access_list
        except Exception as e:
            self.logger.error(f"Failed to get user email access: {str(e)}")
            return []
    
    def get_users_with_email_access(self, account_email: str) -> List[Dict]:
        """Get all users who have access to a specific email account."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute('''
                SELECT uea.user_id, uea.access_level, uea.created_at, u.name, u.email, u.role
                FROM user_email_access uea
                JOIN users u ON uea.user_id = u.id
                WHERE uea.account_email = %s
                ORDER BY uea.created_at DESC
            ''', (account_email,))
            
            users_list = cursor.fetchall()
            conn.close()
            
            return users_list
        except Exception as e:
            self.logger.error(f"Failed to get users with email access: {str(e)}")
            return []
    
    def grant_email_access(self, user_id: int, account_email: str, access_level: str = 'read', created_by: int = None) -> bool:
        """Grant email access to a user."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Check if user and email account exist
            cursor.execute('SELECT COUNT(*) FROM users WHERE id = %s', (user_id,))
            user_exists = cursor.fetchone()[0] > 0
            
            cursor.execute('SELECT COUNT(*) FROM email_accounts WHERE email = %s', (account_email,))
            account_exists = cursor.fetchone()[0] > 0
            
            if not user_exists or not account_exists:
                self.logger.warning(f"User {user_id} or email account {account_email} does not exist")
                conn.close()
                return False
            
            # Insert or update access
            cursor.execute('''
                INSERT INTO user_email_access (user_id, account_email, access_level, created_by)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    access_level = VALUES(access_level),
                    created_by = VALUES(created_by)
            ''', (user_id, account_email, access_level, created_by))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Email access granted: User {user_id} -> {account_email} ({access_level})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to grant email access: {str(e)}")
            return False
    
    def revoke_email_access(self, user_id: int, account_email: str) -> bool:
        """Revoke email access from a user."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM user_email_access 
                WHERE user_id = %s AND account_email = %s
            ''', (user_id, account_email))
            
            deleted_rows = cursor.rowcount
            conn.commit()
            conn.close()
            
            if deleted_rows > 0:
                self.logger.info(f"Email access revoked: User {user_id} -> {account_email}")
                return True
            else:
                self.logger.warning(f"No email access found to revoke: User {user_id} -> {account_email}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to revoke email access: {str(e)}")
            return False
    
    def update_email_access_level(self, user_id: int, account_email: str, access_level: str) -> bool:
        """Update the access level for a user's email access."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE user_email_access 
                SET access_level = %s
                WHERE user_id = %s AND account_email = %s
            ''', (access_level, user_id, account_email))
            
            updated_rows = cursor.rowcount
            conn.commit()
            conn.close()
            
            if updated_rows > 0:
                self.logger.info(f"Email access level updated: User {user_id} -> {account_email} ({access_level})")
                return True
            else:
                self.logger.warning(f"No email access found to update: User {user_id} -> {account_email}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to update email access level: {str(e)}")
            return False
    
    def get_user_accessible_emails(self, user_id: int, filters: dict = {}, page: int = 1, per_page: int = 20) -> (List[Email], int):
        """Get emails that a user has access to based on their email access permissions."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Get user's accessible email accounts
            cursor.execute('''
                SELECT account_email FROM user_email_access 
                WHERE user_id = %s
            ''', (user_id,))
            
            accessible_accounts = [row['account_email'] for row in cursor.fetchall()]
            
            if not accessible_accounts:
                conn.close()
                return [], 0
            
            # Build query with account filter
            query = "SELECT * FROM emails WHERE account_email IN ({})".format(
                ','.join(['%s'] * len(accessible_accounts))
            )
            count_query = "SELECT COUNT(*) as total FROM emails WHERE account_email IN ({})".format(
                ','.join(['%s'] * len(accessible_accounts))
            )
            
            where_clauses = []
            params = accessible_accounts.copy()
            
            if 'category' in filters and filters['category']:
                if filters['category'] == 'unread':
                    where_clauses.append("is_read = 0")
                elif filters['category'] != 'all':
                    where_clauses.append("category = %s")
                    params.append(filters['category'])
            
            if 'search' in filters and filters['search']:
                where_clauses.append("(subject LIKE %s OR sender LIKE %s)")
                params.append(f"%{filters['search']}%")
                params.append(f"%{filters['search']}%")
            
            if 'main_category' in filters and filters['main_category']:
                where_clauses.append("main_category = %s")
                params.append(filters['main_category'])
            
            if 'sub_category' in filters and filters['sub_category']:
                where_clauses.append("sub_category = %s")
                params.append(filters['sub_category'])
            
            # Handle boolean filters
            for bool_key in ['is_trashed', 'is_starred', 'is_read', 'is_archived', 'is_spam']:
                if bool_key in filters:
                    where_clauses.append(f"{bool_key} = %s")
                    params.append(int(filters[bool_key]) if isinstance(filters[bool_key], bool) else filters[bool_key])
            
            if where_clauses:
                query += " AND " + " AND ".join(where_clauses)
                count_query += " AND " + " AND ".join(where_clauses)
            
            query += " ORDER BY date DESC LIMIT %s OFFSET %s"
            params.extend([per_page, (page - 1) * per_page])
            
            # Get total count
            cursor.execute(count_query, params[:-2])  # Exclude LIMIT and OFFSET
            total = cursor.fetchone()['total']
            
            # Get emails
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            
            emails = []
            for row in rows:
                tags = json.loads(row['tags']) if row['tags'] else []
                metadata = json.loads(row['metadata']) if row['metadata'] else {}
                
                email = Email(
                    id=str(row['id']),
                    account_email=row['account_email'] or '',
                    subject=row['subject'] or '',
                    sender=row['sender'] or '',
                    date=self._ensure_datetime(row['date']) if row['date'] else datetime.now(),
                    body=row['body'] or '',
                    raw_data=row['raw_data'] or '',
                    category=row['category'] or 'general',
                    main_category=row['main_category'] or 'general',
                    sub_category=row['sub_category'] or 'general',
                    is_read=bool(row['is_read']),
                    is_starred=bool(row['is_starred']),
                    is_archived=bool(row['is_archived']),
                    is_spam=bool(row['is_spam']),
                    is_trashed=bool(row['is_trashed']),
                    folder=row['folder'] or 'inbox',
                    tags=tags,
                    metadata=metadata,
                    created_at=self._ensure_datetime(row['created_at']) if row['created_at'] else datetime.now(),
                    email_hash=row.get('email_hash'),
                    verification_hash=row.get('verification_hash'),
                    message_id=row.get('message_id')
                )
                emails.append(email)
            
            return emails, total
            
        except Exception as e:
            self.logger.error(f"Failed to get user accessible emails: {str(e)}")
            return [], 0

# Global database instance
db_manager = DatabaseManager()

@dataclass
class EmailAccount:
    email: str
    password: str
    imap_server: str
    imap_port: int = 993
    account_type: str = 'hostinger'
    is_active: bool = True
    last_checked: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_fetched_uid: int = 0  # UID tracking
    last_fetched_date: Optional[datetime] = None  # Timestamp tracking
    last_fetched_hash: Optional[str] = None  # Email hash tracking
