"""Routes for notification management."""

import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..services.notification_service import NotificationService
from ..services.auth_service import AuthService
from ..models.email_models import Email

logger = logging.getLogger(__name__)

notification_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')

# Initialize services
notification_service = NotificationService()
auth_service = AuthService()

@notification_bp.route('/', methods=['GET'])
@jwt_required()
def get_notifications():
    """Get user notifications."""
    try:
        user_id = get_jwt_identity()
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        
        notifications = notification_service.get_user_notifications(user_id, unread_only)
        
        return jsonify({
            'notifications': [
                {
                    'id': n.id,
                    'type': n.type,
                    'title': n.title,
                    'message': n.message,
                    'email_id': n.email_id,
                    'is_read': n.is_read,
                    'created_at': n.created_at.isoformat() if n.created_at else None,
                    'expires_at': n.expires_at.isoformat() if n.expires_at else None
                }
                for n in notifications
            ],
            'total': len(notifications),
            'unread_count': len([n for n in notifications if not n.is_read])
        }), 200
        
    except Exception as e:
        logger.error(f"Get notifications error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@notification_bp.route('/<notification_id>/read', methods=['POST'])
@jwt_required()
def mark_notification_read(notification_id):
    """Mark a notification as read."""
    try:
        user_id = get_jwt_identity()
        
        success = notification_service.mark_notification_read(notification_id, user_id)
        
        if success:
            return jsonify({'message': 'Notification marked as read'}), 200
        else:
            return jsonify({'error': 'Notification not found'}), 404
            
    except Exception as e:
        logger.error(f"Mark notification read error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@notification_bp.route('/<notification_id>/read', methods=['PUT'])
@jwt_required()
def mark_notification_read_put(notification_id):
    """Mark a notification as read (PUT method)."""
    try:
        user_id = get_jwt_identity()
        
        success = notification_service.mark_notification_read(notification_id, user_id)
        
        if success:
            return jsonify({'message': 'Notification marked as read'}), 200
        else:
            return jsonify({'error': 'Notification not found'}), 404
            
    except Exception as e:
        logger.error(f"Mark notification read error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@notification_bp.route('/rules', methods=['GET'])
@jwt_required()
def get_notification_rules():
    """Get user notification rules."""
    try:
        user_id = get_jwt_identity()
        
        rules = notification_service.get_notification_rules(user_id)
        
        return jsonify({
            'rules': [
                {
                    'id': r.id,
                    'name': r.name,
                    'trigger_type': r.trigger_type,
                    'conditions': r.conditions,
                    'notification_methods': r.notification_methods,
                    'is_active': r.is_active,
                    'created_at': r.created_at.isoformat() if r.created_at else None,
                    'last_triggered': r.last_triggered.isoformat() if r.last_triggered else None
                }
                for r in rules
            ],
            'total': len(rules)
        }), 200
        
    except Exception as e:
        logger.error(f"Get notification rules error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@notification_bp.route('/rules', methods=['POST'])
@jwt_required()
def create_notification_rule():
    """Create a new notification rule."""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'trigger_type', 'notification_methods']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate trigger type
        valid_triggers = ['new_email', 'keyword_match', 'sender_match', 'category_match', 'priority_email']
        if data['trigger_type'] not in valid_triggers:
            return jsonify({'error': 'Invalid trigger type'}), 400
        
        # Validate notification methods
        valid_methods = ['email', 'webhook', 'browser']
        for method in data['notification_methods']:
            if method not in valid_methods:
                return jsonify({'error': f'Invalid notification method: {method}'}), 400
        
        rule_id = notification_service.create_notification_rule(user_id, data)
        
        if rule_id:
            return jsonify({
                'message': 'Notification rule created successfully',
                'rule_id': rule_id
            }), 201
        else:
            return jsonify({'error': 'Failed to create notification rule'}), 500
            
    except Exception as e:
        logger.error(f"Create notification rule error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@notification_bp.route('/rules/<rule_id>', methods=['DELETE'])
@jwt_required()
def delete_notification_rule(rule_id):
    """Delete a notification rule."""
    try:
        user_id = get_jwt_identity()
        
        success = notification_service.delete_notification_rule(rule_id, user_id)
        
        if success:
            return jsonify({'message': 'Notification rule deleted successfully'}), 200
        else:
            return jsonify({'error': 'Notification rule not found'}), 404
            
    except Exception as e:
        logger.error(f"Delete notification rule error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@notification_bp.route('/test', methods=['POST'])
@jwt_required()
def test_notification():
    """Send a test notification."""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Create a test notification rule
        test_rule_data = {
            'name': 'Test Notification',
            'trigger_type': 'new_email',
            'conditions': {},
            'notification_methods': data.get('methods', ['browser'])
        }
        
        rule_id = notification_service.create_notification_rule(user_id, test_rule_data)
        
        if rule_id:
            # Create a mock email for testing
            from datetime import datetime
            
            test_email = Email(
                id='test_email_123',
                account_email='test@example.com',
                subject='Test Email for Notification',
                sender='sender@example.com',
                date=datetime.now(),
                body='This is a test email to verify notification functionality.'
            )
            
            # Trigger notification
            notification_service.check_email_triggers(test_email, user_id)
            
            # Clean up test rule
            notification_service.delete_notification_rule(rule_id, user_id)
            
            return jsonify({
                'message': 'Test notification sent successfully',
                'test_email_id': test_email.id
            }), 200
        else:
            return jsonify({'error': 'Failed to create test notification'}), 500
            
    except Exception as e:
        logger.error(f"Test notification error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500