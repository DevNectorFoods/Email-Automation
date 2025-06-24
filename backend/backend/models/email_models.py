from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
import json

@dataclass
class EmailAccount:
    """Model for email account credentials and configuration."""
    email: str
    password: str
    imap_server: str
    imap_port: int = 993
    account_type: str = 'hostinger'
    is_active: bool = True
    last_checked: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_fetched_uid: int = 0
    last_fetched_date: Optional[datetime] = None

@dataclass
class Email:
    """Model for individual email data."""
    id: str
    account_email: str
    subject: str
    sender: str
    date: datetime
    body: str
    raw_data: str = ""
    category: str = "general"
    main_category: str = "general"  # Main category (bank, company, support, etc.)
    sub_category: str = "general"   # Sub category (state bank, hdfc, etc.)
    is_read: bool = False
    is_starred: bool = False
    is_archived: bool = False
    is_spam: bool = False
    is_trashed: bool = False
    folder: str = "inbox" # e.g., inbox, sent, trash, etc.
    tags: list = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    email_hash: Optional[str] = None
    verification_hash: Optional[str] = None  # For UID+timestamp+hash verification
    message_id: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Email":
        """Create an Email instance from a dictionary."""
        # Handle JSON strings for tags and metadata
        tags = data.get('tags')
        if isinstance(tags, str):
            try:
                tags = json.loads(tags)
            except json.JSONDecodeError:
                tags = []
        
        metadata = data.get('metadata')
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except json.JSONDecodeError:
                metadata = {}

        return cls(
            id=data.get('id'),
            account_email=data.get('account_email'),
            subject=data.get('subject'),
            sender=data.get('sender'),
            date=data.get('date'),
            body=data.get('body'),
            raw_data=data.get('raw_data', ''),
            category=data.get('category', 'general'),
            main_category=data.get('main_category', 'general'),
            sub_category=data.get('sub_category', 'general'),
            is_read=data.get('is_read', False),
            is_starred=data.get('is_starred', False),
            is_archived=data.get('is_archived', False),
            is_spam=data.get('is_spam', False),
            is_trashed=data.get('is_trashed', False),
            folder=data.get('folder', 'inbox'),
            tags=tags or [],
            metadata=metadata or {},
            created_at=data.get('created_at'),
            email_hash=data.get('email_hash'),
            verification_hash=data.get('verification_hash'),
            message_id=data.get('message_id')
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert email to dictionary for API responses."""
        return {
            'id': self.id,
            'account_email': self.account_email,
            'subject': self.subject,
            'sender': self.sender,
            'date': self.date.isoformat(),
            'body': self.body,
            'category': self.category,
            'is_read': self.is_read,
            'is_starred': self.is_starred,
            'is_archived': self.is_archived,
            'is_spam': self.is_spam,
            'is_trashed': self.is_trashed,
            'folder': self.folder,
            'tags': self.tags,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'message_id': self.message_id
        }

@dataclass
class EmailStats:
    """Model for email statistics."""
    total_emails: int = 0
    total_accounts: int = 0
    emails_by_category: Dict[str, int] = field(default_factory=dict)
    emails_by_account: Dict[str, int] = field(default_factory=dict)
    last_fetch_time: Optional[datetime] = None
    fetch_errors: int = 0
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary for API responses."""
        return {
            'total_emails': self.total_emails,
            'total_accounts': self.total_accounts,
            'emails_by_category': self.emails_by_category,
            'emails_by_account': self.emails_by_account,
            'last_fetch_time': self.last_fetch_time.isoformat() if self.last_fetch_time else None,
            'fetch_errors': self.fetch_errors,
            'last_updated': self.last_updated.isoformat()
        }
