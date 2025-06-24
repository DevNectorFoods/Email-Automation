import logging
from datetime import datetime, timedelta
from typing import Optional, Dict
import jwt
from flask_jwt_extended import create_access_token, create_refresh_token

from ..models.user_models import User, UserSession
from ..models.db_models import db_manager
from ..config import Config

logger = logging.getLogger(__name__)

class AuthService:
    """Service for handling authentication and user management."""
    
    def __init__(self):
        """Initialize the auth service."""
        self.db = db_manager
    
    def login(self, email: str, password: str) -> Optional[Dict]:
        """
        Authenticate a user and return their session information.
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            Dict containing user info and tokens if successful, None otherwise
        """
        try:
            # Get user from database
            user = self.db.get_user_by_email(email)
            if not user:
                logger.error(f"User not found: {email}")
                return None
                
            # Verify password
            if not user.verify_password(password):
                logger.error(f"Invalid password for user: {email}")
                return None
                
            # Create access and refresh tokens
            access_token = create_access_token(identity=str(user.id))
            refresh_token = create_refresh_token(identity=str(user.id))
            
            # Update last login time
            user.last_login = datetime.utcnow()
            self.db.update_user(user)
            
            return {
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'name': user.name,
                    'role': user.role
                },
                'access_token': access_token,
                'refresh_token': refresh_token
            }
            
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return None
    
    def register(self, email: str, password: str, name: str) -> Optional[Dict]:
        """
        Register a new user.
        
        Args:
            email: User's email address
            password: User's password
            name: User's full name
            
        Returns:
            Dict containing user info if successful, None otherwise
        """
        try:
            # Check if user already exists
            if self.db.get_user_by_email(email):
                return None
                
            # Create new user
            user = User(
                email=email,
                name=name,
                role='user'  # Default role
            )
            user.set_password(password)
            
            # Save to database
            self.db.create_user(user)
            
            return {
                'id': user.id,
                'email': user.email,
                'name': user.name,
                'role': user.role
            }
            
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            return None
    
    def refresh_token(self, refresh_token: str) -> Optional[str]:
        """
        Generate a new access token using a refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            New access token if successful, None otherwise
        """
        try:
            # Verify refresh token
            payload = jwt.decode(
                refresh_token,
                Config.JWT_SECRET_KEY,
                algorithms=['HS256']
            )
            
            user_id = payload['sub']
            user = self.db.get_user_by_id(int(user_id))
            
            if not user:
                return None
                
            # Create new access token
            return create_access_token(identity=str(user_id))
            
        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}")
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Get a user by their ID.
        
        Args:
            user_id: User's ID
            
        Returns:
            User object if found, None otherwise
        """
        try:
            return self.db.get_user_by_id(user_id)
        except Exception as e:
            logger.error(f"Error getting user: {str(e)}")
            return None
    
    def update_user(self, user: User) -> bool:
        """
        Update a user's information.
        
        Args:
            user: User object with updated information
            
        Returns:
            True if successful, False otherwise
        """
        try:
            return self.db.update_user(user)
        except Exception as e:
            logger.error(f"Error updating user: {str(e)}")
            return False
    
    def delete_user(self, user_id: int) -> bool:
        """
        Delete a user.
        
        Args:
            user_id: ID of user to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            return self.db.delete_user(user_id)
        except Exception as e:
            logger.error(f"Error deleting user: {str(e)}")
            return False
    
    def create_user(self, username: str, email: str, password: str):
        """Create a new user with username, email, and password."""
        try:
            # Check if user already exists
            if self.db.get_user_by_email(email):
                return None
            user = User(
                email=email,
                name=username,  # Map username to name
                role='user'
            )
            user.set_password(password)
            if self.db.create_user(user):
                return user
            else:
                return None
        except Exception as e:
            logger.error(f"Create user error: {str(e)}")
            return None

    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get a user by their email address.
        
        Args:
            email: User's email address
            
        Returns:
            User object if found, None otherwise
        """
        try:
            return self.db.get_user_by_email(email)
        except Exception as e:
            logger.error(f"Error getting user by email: {str(e)}")
            return None
    
    def get_all_users(self) -> list:
        """
        Get all users from the database.
        
        Returns:
            List of user dictionaries
        """
        try:
            users = self.db.get_all_users()
            return [
                {
                    'id': user.id,
                    'name': user.name,
                    'email': user.email,
                    'role': user.role,
                    'is_active': user.is_active,
                    'created_at': user.created_at.isoformat() if user.created_at else None,
                    'last_login': user.last_login.isoformat() if user.last_login else None
                }
                for user in users
            ]
        except Exception as e:
            logger.error(f"Error getting all users: {str(e)}")
            return []
    
    def update_user_status(self, user_id: int, is_active: bool) -> bool:
        """
        Update user's active status.
        
        Args:
            user_id: User's ID
            is_active: Whether user should be active
            
        Returns:
            True if successful, False otherwise
        """
        try:
            user = self.db.get_user_by_id(user_id)
            if not user:
                return False
            
            user.is_active = is_active
            return self.db.update_user(user)
        except Exception as e:
            logger.error(f"Error updating user status: {str(e)}")
            return False