from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

from ..services.auth_service import AuthService
from ..models.db_models import db_manager

# Create blueprint
user_access_bp = Blueprint('user_access', __name__)

# Initialize services
auth_service = AuthService()
logger = logging.getLogger(__name__)

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

@user_access_bp.route('/user-email-access', methods=['GET'])
@jwt_required()
@require_admin()
def get_user_email_access():
    """Get all user-email access assignments (admin only)."""
    try:
        # Get all email accounts
        email_accounts = db_manager.get_email_accounts()
        
        # Get all users
        users = auth_service.get_all_users()
        
        # Get access data for each email account
        access_data = []
        for account in email_accounts:
            users_with_access = db_manager.get_users_with_email_access(account.email)
            access_data.append({
                'email_account': account.email,
                'is_active': account.is_active,
                'users_with_access': users_with_access
            })
        
        return jsonify({
            'email_accounts': [{'email': acc.email, 'is_active': acc.is_active} for acc in email_accounts],
            'users': users,
            'access_data': access_data
        }), 200
        
    except Exception as e:
        logger.error(f"Get user email access error: {str(e)}")
        return jsonify({'error': 'Failed to get user email access data'}), 500

@user_access_bp.route('/user-email-access/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user_access(user_id):
    """Get email access for a specific user."""
    try:
        current_user_id = get_jwt_identity()
        current_user = auth_service.get_user_by_id(current_user_id)
        
        # Users can only see their own access, admins can see any user's access
        if not current_user or (current_user.role not in ['admin', 'super_admin'] and current_user_id != user_id):
            return jsonify({'error': 'Access denied'}), 403
        
        # Get user's email access
        user_access = db_manager.get_user_email_access(user_id)
        
        return jsonify({
            'user_id': user_id,
            'email_access': user_access
        }), 200
        
    except Exception as e:
        logger.error(f"Get user access error: {str(e)}")
        return jsonify({'error': 'Failed to get user access'}), 500

@user_access_bp.route('/user-email-access', methods=['POST'])
@jwt_required()
@require_admin()
def grant_email_access():
    """Grant email access to a user (admin only)."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body must be JSON'}), 400
        
        required_fields = ['user_id', 'account_email']
        if not all(field in data for field in required_fields):
            return jsonify({'error': f'Required fields: {required_fields}'}), 400
        
        user_id = int(data['user_id'])
        account_email = data['account_email'].strip()
        access_level = data.get('access_level', 'read')
        created_by = get_jwt_identity()
        
        # Validate access level
        if access_level not in ['read', 'write', 'admin']:
            return jsonify({'error': 'Access level must be read, write, or admin'}), 400
        
        # Grant access
        success = db_manager.grant_email_access(user_id, account_email, access_level, created_by)
        
        if success:
            return jsonify({
                'message': 'Email access granted successfully',
                'user_id': user_id,
                'account_email': account_email,
                'access_level': access_level
            }), 201
        else:
            return jsonify({'error': 'Failed to grant email access'}), 500
            
    except Exception as e:
        logger.error(f"Grant email access error: {str(e)}")
        return jsonify({'error': 'Failed to grant email access'}), 500

@user_access_bp.route('/user-email-access', methods=['DELETE'])
@jwt_required()
@require_admin()
def revoke_email_access():
    """Revoke email access from a user (admin only)."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body must be JSON'}), 400
        
        required_fields = ['user_id', 'account_email']
        if not all(field in data for field in required_fields):
            return jsonify({'error': f'Required fields: {required_fields}'}), 400
        
        user_id = int(data['user_id'])
        account_email = data['account_email'].strip()
        
        # Revoke access
        success = db_manager.revoke_email_access(user_id, account_email)
        
        if success:
            return jsonify({
                'message': 'Email access revoked successfully',
                'user_id': user_id,
                'account_email': account_email
            }), 200
        else:
            return jsonify({'error': 'Failed to revoke email access or access not found'}), 404
            
    except Exception as e:
        logger.error(f"Revoke email access error: {str(e)}")
        return jsonify({'error': 'Failed to revoke email access'}), 500

@user_access_bp.route('/user-email-access', methods=['PUT'])
@jwt_required()
@require_admin()
def update_email_access():
    """Update email access level for a user (admin only)."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body must be JSON'}), 400
        
        required_fields = ['user_id', 'account_email', 'access_level']
        if not all(field in data for field in required_fields):
            return jsonify({'error': f'Required fields: {required_fields}'}), 400
        
        user_id = int(data['user_id'])
        account_email = data['account_email'].strip()
        access_level = data['access_level']
        
        # Validate access level
        if access_level not in ['read', 'write', 'admin']:
            return jsonify({'error': 'Access level must be read, write, or admin'}), 400
        
        # Update access level
        success = db_manager.update_email_access_level(user_id, account_email, access_level)
        
        if success:
            return jsonify({
                'message': 'Email access level updated successfully',
                'user_id': user_id,
                'account_email': account_email,
                'access_level': access_level
            }), 200
        else:
            return jsonify({'error': 'Failed to update email access level or access not found'}), 404
            
    except Exception as e:
        logger.error(f"Update email access error: {str(e)}")
        return jsonify({'error': 'Failed to update email access level'}), 500

@user_access_bp.route('/user-email-access/bulk', methods=['POST'])
@jwt_required()
@require_admin()
def bulk_grant_email_access():
    """Grant email access to multiple users at once (admin only)."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body must be JSON'}), 400
        
        required_fields = ['assignments']
        if not all(field in data for field in required_fields):
            return jsonify({'error': f'Required fields: {required_fields}'}), 400
        
        assignments = data['assignments']
        if not isinstance(assignments, list):
            return jsonify({'error': 'Assignments must be a list'}), 400
        
        created_by = get_jwt_identity()
        results = {
            'successful': [],
            'failed': []
        }
        
        for assignment in assignments:
            if not all(field in assignment for field in ['user_id', 'account_email']):
                results['failed'].append({
                    'assignment': assignment,
                    'error': 'Missing required fields'
                })
                continue
            
            user_id = int(assignment['user_id'])
            account_email = assignment['account_email'].strip()
            access_level = assignment.get('access_level', 'read')
            
            if access_level not in ['read', 'write', 'admin']:
                results['failed'].append({
                    'assignment': assignment,
                    'error': 'Invalid access level'
                })
                continue
            
            success = db_manager.grant_email_access(user_id, account_email, access_level, created_by)
            
            if success:
                results['successful'].append({
                    'user_id': user_id,
                    'account_email': account_email,
                    'access_level': access_level
                })
            else:
                results['failed'].append({
                    'assignment': assignment,
                    'error': 'Database operation failed'
                })
        
        return jsonify({
            'message': f"Bulk operation completed. {len(results['successful'])} successful, {len(results['failed'])} failed",
            'results': results
        }), 200
        
    except Exception as e:
        logger.error(f"Bulk grant email access error: {str(e)}")
        return jsonify({'error': 'Failed to process bulk email access assignment'}), 500 