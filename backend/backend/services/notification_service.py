"""Service for handling email notifications and alerts."""

import logging
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

from ..models.email_models import Email as EmailModel
from ..models.user_models import User

logger = logging.getLogger(__name__)

@dataclass
class NotificationRule:
    """Model for notification rules."""
    id: str
    user_id: str
    name: str
    trigger_type: str  # new_email, keyword_match, sender_match, category_match
    conditions: Dict  # trigger-specific conditions
    notification_methods: List[str]  # email, webhook, browser
    is_active: bool = True
    created_at: Optional[datetime] = None
    last_triggered: Optional[datetime] = None

@dataclass
class Notification:
    """Model for individual notifications."""
    id: str
    user_id: str
    type: str
    title: str
    message: str
    email_id: Optional[str] = None
    is_read: bool = False
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

class NotificationService:
    """Service for managing email notifications and alerts."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')
        self.notifications_storage = {}  # In-memory storage for demo
        self.notification_rules = {}  # In-memory storage for demo
        
    def create_notification_rule(self, user_id: str, rule_data: Dict) -> Optional[str]:
        """
        Create a new notification rule.
        
        Args:
            user_id: User ID
            rule_data: Rule configuration data
            
        Returns:
            Rule ID if successful
        """
        try:
            rule_id = f"rule_{datetime.now().timestamp()}"
            
            rule = NotificationRule(
                id=rule_id,
                user_id=user_id,
                name=rule_data.get('name', 'Unnamed Rule'),
                trigger_type=rule_data.get('trigger_type', 'new_email'),
                conditions=rule_data.get('conditions', {}),
                notification_methods=rule_data.get('notification_methods', ['email']),
                created_at=datetime.now()
            )
            
            self.notification_rules[rule_id] = rule
            self.logger.info(f"Created notification rule {rule_id} for user {user_id}")
            
            return rule_id
            
        except Exception as e:
            self.logger.error(f"Error creating notification rule: {str(e)}")
            return None
    
    def check_email_triggers(self, email: EmailModel, user_id: str):
        """
        Check if an email triggers any notification rules.
        
        Args:
            email: Email object to check
            user_id: User ID to check rules for
        """
        try:
            user_rules = [rule for rule in self.notification_rules.values() 
                         if rule.user_id == user_id and rule.is_active]
            
            for rule in user_rules:
                if self._email_matches_rule(email, rule):
                    self._trigger_notification(email, rule)
                    
        except Exception as e:
            self.logger.error(f"Error checking email triggers: {str(e)}")
    
    def _email_matches_rule(self, email: EmailModel, rule: NotificationRule) -> bool:
        """Check if an email matches a notification rule."""
        try:
            conditions = rule.conditions
            
            if rule.trigger_type == 'new_email':
                return True
            
            elif rule.trigger_type == 'keyword_match':
                keywords = conditions.get('keywords', [])
                email_text = f"{email.subject} {email.body}".lower()
                return any(keyword.lower() in email_text for keyword in keywords)
            
            elif rule.trigger_type == 'sender_match':
                sender_patterns = conditions.get('sender_patterns', [])
                return any(pattern.lower() in email.sender.lower() for pattern in sender_patterns)
            
            elif rule.trigger_type == 'category_match':
                target_categories = conditions.get('categories', [])
                return email.category in target_categories
            
            elif rule.trigger_type == 'priority_email':
                priority_keywords = ['urgent', 'important', 'asap', 'priority']
                email_text = f"{email.subject} {email.body}".lower()
                return any(keyword in email_text for keyword in priority_keywords)
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error matching email to rule: {str(e)}")
            return False
    
    def _trigger_notification(self, email: EmailModel, rule: NotificationRule):
        """Trigger a notification based on a rule match."""
        try:
            notification_id = f"notif_{datetime.now().timestamp()}"
            
            # Create notification message
            title = f"Email Alert: {rule.name}"
            message = self._create_notification_message(email, rule)
            
            notification = Notification(
                id=notification_id,
                user_id=rule.user_id,
                type=rule.trigger_type,
                title=title,
                message=message,
                email_id=email.id,
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(days=7)
            )
            
            # Store notification
            if rule.user_id not in self.notifications_storage:
                self.notifications_storage[rule.user_id] = []
            self.notifications_storage[rule.user_id].append(notification)
            
            # Send notifications via configured methods
            for method in rule.notification_methods:
                if method == 'email':
                    self._send_email_notification(email, rule, notification)
                elif method == 'webhook':
                    self._send_webhook_notification(email, rule, notification)
                elif method == 'browser':
                    # Browser notifications are handled on frontend
                    pass
            
            # Update rule last triggered time
            rule.last_triggered = datetime.now()
            
            self.logger.info(f"Triggered notification {notification_id} for rule {rule.id}")
            
        except Exception as e:
            self.logger.error(f"Error triggering notification: {str(e)}")
    
    def _create_notification_message(self, email: EmailModel, rule: NotificationRule) -> str:
        """Create notification message text."""
        message = f"New email received matching rule '{rule.name}':\n\n"
        message += f"From: {email.sender}\n"
        message += f"Subject: {email.subject}\n"
        message += f"Account: {email.account_email}\n"
        message += f"Category: {email.category}\n"
        message += f"Received: {email.date.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Add preview of email body
        body_preview = email.body[:200] + "..." if len(email.body) > 200 else email.body
        message += f"Preview: {body_preview}"
        
        return message
    
    def _send_email_notification(self, email: EmailModel, rule: NotificationRule, notification: Notification):
        """Send email notification using SendGrid."""
        try:
            if not self.sendgrid_api_key:
                self.logger.warning("SendGrid API key not configured")
                return
            
            sg = SendGridAPIClient(self.sendgrid_api_key)
            
            # Get user email (you'd normally get this from user service)
            user_email = "admin@emailautomation.com"  # Placeholder
            
            message = Mail(
                from_email=Email("notifications@emailautomation.com"),
                to_emails=To(user_email),
                subject=notification.title,
                html_content=self._create_html_notification(email, rule, notification)
            )
            
            response = sg.send(message)
            self.logger.info(f"Email notification sent successfully: {response.status_code}")
            
        except Exception as e:
            self.logger.error(f"Error sending email notification: {str(e)}")
    
    def _create_html_notification(self, email: EmailModel, rule: NotificationRule, notification: Notification) -> str:
        """Create HTML content for email notification."""
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 20px;">
            <h2 style="color: #333;">Email Alert: {rule.name}</h2>
            
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3 style="margin-top: 0;">Email Details</h3>
                <p><strong>From:</strong> {email.sender}</p>
                <p><strong>Subject:</strong> {email.subject}</p>
                <p><strong>Account:</strong> {email.account_email}</p>
                <p><strong>Category:</strong> {email.category}</p>
                <p><strong>Received:</strong> {email.date.strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div style="background-color: #ffffff; padding: 15px; border: 1px solid #dee2e6; border-radius: 5px;">
                <h4>Email Preview:</h4>
                <p style="white-space: pre-wrap;">{email.body[:500]}{'...' if len(email.body) > 500 else ''}</p>
            </div>
            
            <p style="margin-top: 30px;">
                <a href="http://localhost:5000/dashboard" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                    View in Dashboard
                </a>
            </p>
            
            <hr style="margin: 30px 0;">
            <p style="color: #6c757d; font-size: 12px;">
                This notification was triggered by rule: {rule.name}<br>
                You can manage your notification settings in the dashboard.
            </p>
        </body>
        </html>
        """
        return html
    
    def _send_webhook_notification(self, email: EmailModel, rule: NotificationRule, notification: Notification):
        """Send webhook notification."""
        # Placeholder for webhook implementation
        self.logger.info(f"Webhook notification would be sent for rule {rule.id}")
    
    def get_user_notifications(self, user_id: str, unread_only: bool = False) -> List[Notification]:
        """Get notifications for a user."""
        try:
            user_notifications = self.notifications_storage.get(user_id, [])
            
            if unread_only:
                user_notifications = [n for n in user_notifications if not n.is_read]
            
            # Remove expired notifications
            now = datetime.now()
            user_notifications = [n for n in user_notifications 
                                if n.expires_at is None or n.expires_at > now]
            
            return sorted(user_notifications, key=lambda x: x.created_at or datetime.min, reverse=True)
            
        except Exception as e:
            self.logger.error(f"Error getting user notifications: {str(e)}")
            return []
    
    def mark_notification_read(self, notification_id: str, user_id: str) -> bool:
        """Mark a notification as read."""
        try:
            user_notifications = self.notifications_storage.get(user_id, [])
            
            for notification in user_notifications:
                if notification.id == notification_id:
                    notification.is_read = True
                    self.logger.info(f"Marked notification {notification_id} as read")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error marking notification as read: {str(e)}")
            return False
    
    def get_notification_rules(self, user_id: str) -> List[NotificationRule]:
        """Get notification rules for a user."""
        try:
            return [rule for rule in self.notification_rules.values() if rule.user_id == user_id]
        except Exception as e:
            self.logger.error(f"Error getting notification rules: {str(e)}")
            return []
    
    def delete_notification_rule(self, rule_id: str, user_id: str) -> bool:
        """Delete a notification rule."""
        try:
            if rule_id in self.notification_rules:
                rule = self.notification_rules[rule_id]
                if rule.user_id == user_id:
                    del self.notification_rules[rule_id]
                    self.logger.info(f"Deleted notification rule {rule_id}")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error deleting notification rule: {str(e)}")
            return False
    
    def create_default_rules(self, user_id: str):
        """Create default notification rules for a new user."""
        try:
            # Priority email rule
            self.create_notification_rule(user_id, {
                'name': 'Priority Emails',
                'trigger_type': 'priority_email',
                'conditions': {},
                'notification_methods': ['email', 'browser']
            })
            
            # New email rule (can be disabled by user)
            self.create_notification_rule(user_id, {
                'name': 'All New Emails',
                'trigger_type': 'new_email',
                'conditions': {},
                'notification_methods': ['browser']
            })
            
            self.logger.info(f"Created default notification rules for user {user_id}")
            
        except Exception as e:
            self.logger.error(f"Error creating default rules: {str(e)}")