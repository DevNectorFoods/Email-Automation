from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field
from werkzeug.security import generate_password_hash, check_password_hash

@dataclass
class User:
    """Model for user data."""
    id: Optional[int] = None
    email: str = ''
    password: str = ''  # Store hashed password
    name: str = ''
    role: str = "user"  # user, admin
    is_active: bool = True  # Add missing is_active field
    created_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None

    def set_password(self, raw_password: str):
        self.password = generate_password_hash(raw_password)

    def verify_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password, raw_password)

    def to_dict(self) -> dict:
        """Convert user to dictionary for API responses (excluding password)."""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

@dataclass
class UserSession:
    """Model for user session data."""
    session_id: str
    user_id: str
    access_token: str
    refresh_token: str
    created_at: datetime
    expires_at: datetime
    is_active: bool = True
    last_activity: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        """Convert session to dictionary for API responses (excluding tokens)."""
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'is_active': self.is_active,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None
        }
