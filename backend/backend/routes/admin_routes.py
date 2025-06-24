from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

from ..services.auth_service import AuthService
from ..services.categorization_service import EmailCategorizationService
from ..models.db_models import db_manager

# Create blueprint
admin_bp = Blueprint('admin', __name__)

# Initialize services
auth_service = AuthService()
categorization_service = EmailCategorizationService()
logger = logging.getLogger(__name__)

def require_super_admin():
    """Decorator to require super_admin role."""
    def decorator(f):
        def wrapper(*args, **kwargs):
            current_user_id = get_jwt_identity()
            user = auth_service.get_user_by_id(current_user_id)
            if not user or user.role != 'super_admin':
                return jsonify({'error': 'Super admin access required'}), 403
            return f(*args, **kwargs)
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator

def require_admin():
    """Decorator to require admin or super_admin role."""
    def decorator(f):
        def wrapper(*args, **kwargs):
            current_user_id = get_jwt_identity()
            user = auth_service.get_user_by_id(current_user_id)
            if not user or user.role not in ['admin', 'super_admin']:
                return jsonify({'error': 'Admin access required'}), 403
            return f(*args, **kwargs)
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
@require_admin()
def list_users():
    """List all users (admin only)."""
    try:
        users = auth_service.get_all_users()
        
        return jsonify({
            'users': users,
            'total_users': len(users)
        }), 200
        
    except Exception as e:
        logger.error(f"List users error: {str(e)}")
        return jsonify({'error': 'Failed to list users'}), 500

@admin_bp.route('/users/<user_id>/status', methods=['PUT'])
@jwt_required()
@require_admin()
def update_user_status(user_id):
    """Update user active status (admin only)."""
    try:
        data = request.get_json()
        
        if not data or 'is_active' not in data:
            return jsonify({'error': 'is_active field is required'}), 400
        
        is_active = data['is_active']
        
        if not isinstance(is_active, bool):
            return jsonify({'error': 'is_active must be a boolean'}), 400
        
        success = auth_service.update_user_status(user_id, is_active)
        
        if not success:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'message': f'User status updated successfully',
            'user_id': user_id,
            'is_active': is_active
        }), 200
        
    except Exception as e:
        logger.error(f"Update user status error: {str(e)}")
        return jsonify({'error': 'Failed to update user status'}), 500

@admin_bp.route('/sheets/info', methods=['GET'])
@jwt_required()
@require_admin()
def get_sheets_info():
    """Get Google Sheets information (admin only)."""
    try:
        # Validate sheet access
        has_access = sheets_service.validate_sheet_access()
        
        if not has_access:
            return jsonify({
                'accessible': False,
                'error': 'Cannot access configured Google Sheet'
            }), 200
        
        # Get sheet info
        sheet_info = sheets_service.get_sheet_info()
        
        return jsonify({
            'accessible': True,
            'sheet_info': sheet_info
        }), 200
        
    except Exception as e:
        logger.error(f"Get sheets info error: {str(e)}")
        return jsonify({'error': 'Failed to get sheets information'}), 500

@admin_bp.route('/categories', methods=['GET'])
@jwt_required()
@require_admin()
def get_category_management():
    """Get category management information (admin only)."""
    try:
        category_rules = categorization_service.get_category_rules()
        category_stats = categorization_service.get_categorization_stats()
        
        return jsonify({
            'category_rules': category_rules,
            'categorization_stats': category_stats
        }), 200
        
    except Exception as e:
        logger.error(f"Get category management error: {str(e)}")
        return jsonify({'error': 'Failed to get category information'}), 500

@admin_bp.route('/categories/<category>', methods=['PUT'])
@jwt_required()
@require_admin()
def update_category_rules(category):
    """Update category rules (admin only)."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body must be JSON'}), 400
        
        required_fields = ['keywords', 'sender_patterns', 'priority']
        if not all(field in data for field in required_fields):
            return jsonify({'error': f'Required fields: {required_fields}'}), 400
        
        success = categorization_service.update_category_rules(category, data)
        
        if not success:
            return jsonify({'error': 'Failed to update category rules'}), 400
        
        return jsonify({
            'message': f'Category rules updated for: {category}',
            'category': category,
            'rules': data
        }), 200
        
    except Exception as e:
        logger.error(f"Update category rules error: {str(e)}")
        return jsonify({'error': 'Failed to update category rules'}), 500

@admin_bp.route('/categories/<category>', methods=['DELETE'])
@jwt_required()
@require_admin()
def delete_category(category):
    """Delete a category (admin only)."""
    try:
        success = categorization_service.delete_category(category)
        
        if not success:
            return jsonify({'error': 'Cannot delete category or category not found'}), 400
        
        return jsonify({
            'message': f'Category deleted: {category}'
        }), 200
        
    except Exception as e:
        logger.error(f"Delete category error: {str(e)}")
        return jsonify({'error': 'Failed to delete category'}), 500

@admin_bp.route('/categories/stats/reset', methods=['POST'])
@jwt_required()
@require_admin()
def reset_categorization_stats():
    """Reset categorization statistics (admin only)."""
    try:
        categorization_service.reset_stats()
        
        return jsonify({
            'message': 'Categorization statistics reset successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Reset categorization stats error: {str(e)}")
        return jsonify({'error': 'Failed to reset categorization statistics'}), 500

@admin_bp.route('/system/status', methods=['GET'])
@jwt_required()
@require_admin()
def get_system_status():
    """Get system status information (admin only)."""
    try:
        from routes.email_routes import emails_storage, email_stats
        
        # Check Google Sheets connectivity
        sheets_accessible = sheets_service.validate_sheet_access()
        
        # Get system statistics
        status = {
            'system_health': 'healthy',
            'services': {
                'google_sheets': 'connected' if sheets_accessible else 'disconnected',
                'email_storage': 'active',
                'categorization': 'active'
            },
            'data_counts': {
                'emails_in_storage': len(emails_storage),
                'total_users': len(auth_service.users),
                'active_sessions': len([s for s in auth_service.sessions.values() if s.is_active])
            },
            'email_stats': email_stats
        }
        
        return jsonify({
            'status': status
        }), 200
        
    except Exception as e:
        logger.error(f"Get system status error: {str(e)}")
        return jsonify({'error': 'Failed to get system status'}), 500

@admin_bp.route('/storage/clear', methods=['POST'])
@jwt_required()
@require_admin()
def clear_email_storage():
    """Clear all email storage (admin only)."""
    try:
        data = request.get_json()
        
        # Require confirmation
        if not data or data.get('confirm') != 'yes':
            return jsonify({'error': 'Confirmation required: {"confirm": "yes"}'}), 400
        
        from routes.email_routes import emails_storage, email_stats
        
        # Clear storage
        emails_storage.clear()
        
        # Reset stats
        email_stats.update({
            'total_emails': 0,
            'emails_by_category': {},
            'emails_by_account': {},
            'fetch_errors': 0
        })
        
        logger.warning("Email storage cleared by admin")
        
        return jsonify({
            'message': 'Email storage cleared successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Clear email storage error: {str(e)}")
        return jsonify({'error': 'Failed to clear email storage'}), 500

@admin_bp.route('/users', methods=['POST'])
@jwt_required()
@require_admin()
def create_user():
    """Create a new user (admin only)."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body must be JSON'}), 400
        required_fields = ['name', 'email', 'password']
        if not all(field in data for field in required_fields):
            return jsonify({'error': f'Required fields: {required_fields}'}), 400
        name = data['name'].strip()
        email = data['email'].strip().lower()
        password = data['password']
        role = data.get('role', 'user')  # Default to 'user' role
        # Validate role
        if role not in ['user', 'admin', 'super_admin']:
            return jsonify({'error': 'Role must be either "user", "admin", or "super_admin"'}), 400
        # Check if user already exists
        existing_user = auth_service.get_user_by_email(email)
        if existing_user:
            return jsonify({'error': 'User with this email already exists'}), 400
        # Get current user
        current_user_id = get_jwt_identity()
        current_user = auth_service.get_user_by_id(current_user_id)
        # Only super_admin can create admin or super_admin
        if role in ['admin', 'super_admin'] and (not current_user or current_user.role != 'super_admin'):
            return jsonify({'error': 'Only super admin can create admin or super admin users'}), 403
        # Admin can only create users
        if role == 'user' and current_user.role not in ['admin', 'super_admin']:
            return jsonify({'error': 'Only admin or super admin can create users'}), 403
        # Create user
        user = auth_service.create_user(name, email, password)
        if not user:
            return jsonify({'error': 'Failed to create user'}), 500
        # Set role if specified
        user.role = role
        auth_service.update_user(user)
        return jsonify({
            'message': 'User created successfully',
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'role': user.role,
                'is_active': user.is_active
            }
        }), 201
    except Exception as e:
        logger.error(f"Create user error: {str(e)}")
        return jsonify({'error': 'Failed to create user'}), 500

@admin_bp.route('/users/<user_id>', methods=['DELETE'])
@jwt_required()
@require_admin()
def delete_user(user_id):
    """Delete a user (admin only)."""
    try:
        # Check if user exists
        user = auth_service.get_user_by_id(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        # Prevent admin from deleting themselves
        current_user_id = get_jwt_identity()
        current_user = auth_service.get_user_by_id(current_user_id)
        if str(user_id) == str(current_user_id):
            return jsonify({'error': 'Cannot delete your own account'}), 400
        # Only super_admin can delete admin or super_admin
        if user.role in ['admin', 'super_admin'] and (not current_user or current_user.role != 'super_admin'):
            return jsonify({'error': 'Only super admin can delete admin or super admin users'}), 403
        # Admin can only delete users
        if user.role == 'user' and current_user.role not in ['admin', 'super_admin']:
            return jsonify({'error': 'Only admin or super admin can delete users'}), 403
        # Delete user
        success = auth_service.delete_user(user_id)
        if not success:
            return jsonify({'error': 'Failed to delete user'}), 500
        return jsonify({
            'message': 'User deleted successfully',
            'deleted_user_id': user_id
        }), 200
    except Exception as e:
        logger.error(f"Delete user error: {str(e)}")
        return jsonify({'error': 'Failed to delete user'}), 500

@admin_bp.route('/users/<user_id>', methods=['PUT'])
@jwt_required()
@require_admin()
def update_user(user_id):
    """Update user information (admin only)."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body must be JSON'}), 400
        # Check if user exists
        user = auth_service.get_user_by_id(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        current_user_id = get_jwt_identity()
        current_user = auth_service.get_user_by_id(current_user_id)
        # If updating role, only super_admin can update to/from admin or super_admin
        if 'role' in data:
            role = data['role']
            if role not in ['user', 'admin', 'super_admin']:
                return jsonify({'error': 'Role must be either "user", "admin", or "super_admin"'}), 400
            if (user.role in ['admin', 'super_admin'] or role in ['admin', 'super_admin']) and (not current_user or current_user.role != 'super_admin'):
                return jsonify({'error': 'Only super admin can change admin or super admin roles'}), 403
            user.role = role
        if 'name' in data:
            user.name = data['name'].strip()
        if 'email' in data:
            new_email = data['email'].strip().lower()
            # Check if email is already taken by another user
            existing_user = auth_service.get_user_by_email(new_email)
            if existing_user and existing_user.id != user_id:
                return jsonify({'error': 'Email already taken by another user'}), 400
            user.email = new_email
        if 'password' in data and data['password']:
            user.set_password(data['password'])
        # Update user
        success = auth_service.update_user(user)
        if not success:
            return jsonify({'error': 'Failed to update user'}), 500
        return jsonify({
            'message': 'User updated successfully',
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'role': user.role,
                'is_active': user.is_active
            }
        }), 200
    except Exception as e:
        logger.error(f"Update user error: {str(e)}")
        return jsonify({'error': 'Failed to update user'}), 500

@admin_bp.route('/stats', methods=['GET'])
@jwt_required()
@require_admin()
def get_system_stats():
    """Get system statistics (admin only)."""
    try:
        # Get email statistics from database
        emails, total_emails = db_manager.get_emails()
        unread_emails = sum(1 for email in emails if not email.is_read)
        categorized_emails = sum(1 for email in emails if email.category and email.category != 'general')
        
        # Get email stats from database
        email_stats = db_manager.get_email_stats()
        
        # Get user statistics
        users = auth_service.get_all_users()
        total_users = len(users)
        active_users = sum(1 for user in users if user.get('is_active', True))
        
        # Get email account statistics
        email_accounts = db_manager.get_email_accounts()
        total_accounts = len(email_accounts)
        active_accounts = sum(1 for acc in email_accounts if acc.is_active)
        
        stats = {
            'emails': {
                'total': total_emails,
                'unread': unread_emails,
                'categorized': categorized_emails,
                'categories': email_stats.get('emails_by_category', {})
            },
            'users': {
                'total': total_users,
                'active': active_users,
                'inactive': total_users - active_users
            },
            'accounts': {
                'total': total_accounts,
                'active': active_accounts,
                'inactive': total_accounts - active_accounts
            },
            'system': {
                'uptime': 'running',
                'version': '1.0.0'
            }
        }
        
        return jsonify(stats), 200
        
    except Exception as e:
        logger.error(f"Get system stats error: {str(e)}")
        return jsonify({'error': 'Failed to get system statistics'}), 500

@admin_bp.route('/logs', methods=['GET'])
@jwt_required()
@require_admin()
def get_system_logs():
    """Get system logs (admin only)."""
    try:
        import os
        from datetime import datetime, timedelta
        
        # Get log file path
        log_file = 'email_automation.log'
        
        if not os.path.exists(log_file):
            return jsonify({
                'logs': [],
                'total_lines': 0,
                'message': 'No log file found'
            }), 200
        
        # Read last 100 lines from log file
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                last_lines = lines[-100:] if len(lines) > 100 else lines
                
            # Parse log entries
            log_entries = []
            for line in last_lines:
                if line.strip():
                    # Simple log parsing - you can enhance this based on your log format
                    try:
                        # Extract timestamp and message
                        if ' - ' in line:
                            timestamp_part, message_part = line.split(' - ', 1)
                            timestamp = timestamp_part.strip()
                            message = message_part.strip()
                        else:
                            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            message = line.strip()
                        
                        log_entries.append({
                            'timestamp': timestamp,
                            'message': message,
                            'level': 'INFO'  # Default level
                        })
                    except:
                        # If parsing fails, add as raw line
                        log_entries.append({
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'message': line.strip(),
                            'level': 'INFO'
                        })
            
            return jsonify({
                'logs': log_entries,
                'total_lines': len(lines),
                'showing_last': len(log_entries)
            }), 200
            
        except Exception as e:
            logger.error(f"Error reading log file: {str(e)}")
            return jsonify({
                'logs': [],
                'total_lines': 0,
                'error': 'Failed to read log file'
            }), 500
        
    except Exception as e:
        logger.error(f"Get system logs error: {str(e)}")
        return jsonify({'error': 'Failed to get system logs'}), 500
