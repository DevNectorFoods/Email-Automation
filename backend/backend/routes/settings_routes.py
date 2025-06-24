from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
from datetime import datetime
from flasgger import swag_from
from urllib.parse import unquote

from ..services.auth_service import AuthService
from ..services.email_service import EmailService
from ..models.email_models import EmailAccount
from ..models.db_models import db_manager

# Create blueprint
settings_bp = Blueprint('settings', __name__)

# Initialize services
auth_service = AuthService()
email_service = EmailService()
logger = logging.getLogger(__name__)

@settings_bp.route('/email-accounts', methods=['GET'])
@jwt_required()
@swag_from({
    'tags': ['Settings'],
    'summary': 'Get all email accounts',
    'description': 'Retrieve all configured email accounts',
    'security': [{'Bearer': []}],
    'responses': {
        200: {
            'description': 'List of email accounts',
            'schema': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'email': {'type': 'string'},
                        'active': {'type': 'boolean'}
                    }
                }
            }
        }
    }
})
def get_email_accounts():
    """Get all email accounts."""
    try:
        # Check if user is admin
        current_user_id = get_jwt_identity()
        user = auth_service.get_user_by_id(current_user_id)
        
        if not user or user.role not in ['admin', 'super_admin']:
            return jsonify({'error': 'Admin access required'}), 403
            
        accounts = db_manager.get_email_accounts()
        return jsonify([{
            'email': acc.email,
            'active': acc.is_active
        } for acc in accounts]), 200
    except Exception as e:
        logger.error(f"Error getting email accounts: {str(e)}")
        return jsonify({'error': 'Failed to get email accounts'}), 500

@settings_bp.route('/email-accounts', methods=['POST'])
@jwt_required()
@swag_from({
    'tags': ['Settings'],
    'summary': 'Add a new email account',
    'description': 'Add a new email account to the system',
    'security': [{'Bearer': []}],
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'email': {'type': 'string'},
                    'password': {'type': 'string'},
                    'imap_server': {'type': 'string'},
                    'imap_port': {'type': 'integer'}
                }
            }
        }
    ],
    'responses': {
        201: {
            'description': 'Email account added successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'}
                }
            }
        }
    }
})
def add_email_account():
    """Add a new email account."""
    try:
        # Check if user is admin
        current_user_id = get_jwt_identity()
        user = auth_service.get_user_by_id(current_user_id)
        
        if not user or user.role not in ['admin', 'super_admin']:
            return jsonify({'error': 'Admin access required'}), 403
            
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body must be JSON'}), 400

        logger.info(f"Adding email account with data: {data}")

        # Create new email account
        account = EmailAccount(
            email=data['email'],
            password=data['password'],
            imap_server=data.get('imap_server', 'imap.gmail.com'),
            imap_port=data.get('imap_port', 993),
            is_active=True
        )

        logger.info(f"Created EmailAccount object: {account.email}")

        # Test connection
        logger.info(f"Testing connection for {account.email}")
        if not email_service.test_account_connection(account):
            logger.error(f"Connection test failed for {account.email}")
            return jsonify({'error': 'Failed to connect to email account'}), 400

        logger.info(f"Connection test successful for {account.email}")

        # Save account
        logger.info(f"Saving account to database: {account.email}")
        if db_manager.add_email_account(account):
            logger.info(f"Account saved successfully: {account.email}")
            return jsonify({'message': 'Email account added successfully'}), 201
        else:
            logger.error(f"Failed to save account to database: {account.email}")
            return jsonify({'error': 'Failed to add email account'}), 500

    except Exception as e:
        logger.error(f"Error adding email account: {str(e)}")
        logger.error(f"Exception type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': 'Failed to add email account'}), 500

@settings_bp.route('/email-accounts/<email>', methods=['DELETE'])
@jwt_required()
@swag_from({
    'tags': ['Settings'],
    'summary': 'Delete an email account',
    'description': 'Delete a specific email account',
    'security': [{'Bearer': []}],
    'parameters': [
        {
            'name': 'email',
            'in': 'path',
            'required': True,
            'type': 'string'
        }
    ],
    'responses': {
        200: {
            'description': 'Email account deleted successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'}
                }
            }
        }
    }
})
def delete_email_account(email):
    """Delete an email account."""
    try:
        # URL decode the email parameter
        decoded_email = unquote(email)
        
        # Check if user is admin
        current_user_id = get_jwt_identity()
        user = auth_service.get_user_by_id(current_user_id)
        
        if not user or user.role not in ['admin', 'super_admin']:
            return jsonify({'error': 'Admin access required'}), 403
            
        if db_manager.delete_email_account(decoded_email):
            return jsonify({'message': 'Email account deleted successfully'}), 200
        else:
            return jsonify({'error': 'Email account not found'}), 404
    except Exception as e:
        logger.error(f"Error deleting email account: {str(e)}")
        return jsonify({'error': 'Failed to delete email account'}), 500

@settings_bp.route('/email-accounts/<email>/test', methods=['POST'])
@jwt_required()
@swag_from({
    'tags': ['Settings'],
    'summary': 'Test an email account',
    'description': 'Test the connection to a specific email account',
    'security': [{'Bearer': []}],
    'parameters': [
        {
            'name': 'email',
            'in': 'path',
            'required': True,
            'type': 'string'
        }
    ],
    'responses': {
        200: {
            'description': 'Email account test successful',
            'schema': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'}
                }
            }
        }
    }
})
def test_email_account(email):
    """Test an email account."""
    try:
        # URL decode the email parameter
        decoded_email = unquote(email)
        
        # Check if user is admin
        current_user_id = get_jwt_identity()
        user = auth_service.get_user_by_id(current_user_id)
        
        if not user or user.role not in ['admin', 'super_admin']:
            return jsonify({'error': 'Admin access required'}), 403
            
        account = db_manager.get_email_account(decoded_email)
        if not account:
            return jsonify({'error': 'Email account not found'}), 404

        if email_service.test_account_connection(account):
            return jsonify({'message': 'Email account test successful'}), 200
        else:
            return jsonify({'error': 'Failed to connect to email account'}), 400
    except Exception as e:
        logger.error(f"Error testing email account: {str(e)}")
        return jsonify({'error': 'Failed to test email account'}), 500

@settings_bp.route('/email-accounts/test-all', methods=['POST'])
@jwt_required()
@swag_from({
    'tags': ['Settings'],
    'summary': 'Test all email accounts',
    'description': 'Test the connection to all configured email accounts',
    'security': [{'Bearer': []}],
    'responses': {
        200: {
            'description': 'All email accounts tested successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'results': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'email': {'type': 'string'},
                                'status': {'type': 'string'}
                            }
                        }
                    }
                }
            }
        }
    }
})
def test_all_email_accounts():
    """Test all email accounts."""
    try:
        # Check if user is admin
        current_user_id = get_jwt_identity()
        user = auth_service.get_user_by_id(current_user_id)
        
        if not user or user.role not in ['admin', 'super_admin']:
            return jsonify({'error': 'Admin access required'}), 403
            
        accounts = db_manager.get_email_accounts()
        results = []

        for account in accounts:
            status = 'success' if email_service.test_account_connection(account) else 'failed'
            results.append({
                'email': account.email,
                'status': status
            })

        return jsonify({
            'message': 'All email accounts tested successfully',
            'results': results
        }), 200
    except Exception as e:
        logger.error(f"Error testing all email accounts: {str(e)}")
        return jsonify({'error': 'Failed to test email accounts'}), 500

@settings_bp.route('/email-accounts/<email>/update', methods=['PUT'])
@jwt_required()
@swag_from({
    'tags': ['Settings'],
    'summary': 'Update an email account',
    'description': 'Update settings for a specific email account',
    'security': [{'Bearer': []}],
    'parameters': [
        {
            'name': 'email',
            'in': 'path',
            'required': True,
            'type': 'string'
        },
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'password': {'type': 'string'},
                    'imap_server': {'type': 'string'},
                    'imap_port': {'type': 'integer'},
                    'active': {'type': 'boolean'}
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Email account updated successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'account': {
                        'type': 'object',
                        'properties': {
                            'email': {'type': 'string'},
                            'imap_server': {'type': 'string'},
                            'imap_port': {'type': 'integer'},
                            'active': {'type': 'boolean'}
                        }
                    }
                }
            }
        }
    }
})
def update_email_account(email):
    """Update an email account."""
    try:
        # URL decode the email parameter
        decoded_email = unquote(email)
        
        # Check if user is admin
        current_user_id = get_jwt_identity()
        user = auth_service.get_user_by_id(current_user_id)
        
        if not user or user.role not in ['admin', 'super_admin']:
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body must be JSON'}), 400
        
        # Get existing account
        account = db_manager.get_email_account(decoded_email)
        
        if not account:
            return jsonify({'error': 'Email account not found'}), 404
        
        # Update fields
        if 'password' in data:
            account.password = data['password']
        if 'imap_server' in data:
            account.imap_server = data['imap_server'].strip()
        if 'imap_port' in data:
            account.imap_port = int(data['imap_port'])
        if 'active' in data:
            account.is_active = bool(data['active'])
        
        # Test connection if credentials changed
        if 'password' in data or 'imap_server' in data or 'imap_port' in data:
            if not email_service.test_account_connection(account):
                return jsonify({'error': 'Failed to connect with updated credentials'}), 400
        
        # Save changes
        if db_manager.add_email_account(account):  # This will update existing account
            return jsonify({
                'message': 'Email account updated successfully',
                'account': {
                    'email': account.email,
                    'imap_server': account.imap_server,
                    'imap_port': account.imap_port,
                    'active': account.is_active
                }
            }), 200
        else:
            return jsonify({'error': 'Failed to update email account'}), 500
        
    except ValueError as e:
        return jsonify({'error': f'Invalid data: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Update email account error: {str(e)}")
        return jsonify({'error': 'Failed to update email account'}), 500

@settings_bp.route('/', methods=['GET'])
@jwt_required()
@swag_from({
    'tags': ['Settings'],
    'summary': 'Get system settings',
    'description': 'Retrieve current system settings',
    'security': [{'Bearer': []}],
    'responses': {
        200: {
            'description': 'System settings',
            'schema': {
                'type': 'object',
                'properties': {
                    'auto_reply_enabled': {'type': 'boolean'},
                    'reply_delay': {'type': 'integer'},
                    'max_replies_per_day': {'type': 'integer'},
                    'email_check_interval': {'type': 'integer'},
                    'categorization_enabled': {'type': 'boolean'}
                }
            }
        }
    }
})
def get_settings():
    """Get system settings."""
    try:
        # Check if user is admin
        current_user_id = get_jwt_identity()
        user = auth_service.get_user_by_id(current_user_id)
        
        if not user or user.role not in ['admin', 'super_admin']:
            return jsonify({'error': 'Admin access required'}), 403
        
        # Get settings from database or return defaults
        settings = db_manager.get_system_settings()
        
        if not settings:
            # Return default settings
            settings = {
                'auto_reply_enabled': False,
                'reply_delay': 5,
                'max_replies_per_day': 10,
                'email_check_interval': 300,
                'categorization_enabled': True
            }
        
        return jsonify(settings), 200
        
    except Exception as e:
        logger.error(f"Error getting settings: {str(e)}")
        return jsonify({'error': 'Failed to get settings'}), 500

@settings_bp.route('/', methods=['PUT'])
@jwt_required()
@swag_from({
    'tags': ['Settings'],
    'summary': 'Update system settings',
    'description': 'Update system settings',
    'security': [{'Bearer': []}],
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'auto_reply_enabled': {'type': 'boolean'},
                    'reply_delay': {'type': 'integer'},
                    'max_replies_per_day': {'type': 'integer'},
                    'email_check_interval': {'type': 'integer'},
                    'categorization_enabled': {'type': 'boolean'}
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Settings updated successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'settings': {'type': 'object'}
                }
            }
        }
    }
})
def update_settings():
    """Update system settings."""
    try:
        # Check if user is admin
        current_user_id = get_jwt_identity()
        user = auth_service.get_user_by_id(current_user_id)
        
        if not user or user.role not in ['admin', 'super_admin']:
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body must be JSON'}), 400
        
        # Validate settings
        valid_settings = {
            'auto_reply_enabled': bool,
            'reply_delay': int,
            'max_replies_per_day': int,
            'email_check_interval': int,
            'categorization_enabled': bool
        }
        
        settings_to_update = {}
        for key, value_type in valid_settings.items():
            if key in data:
                try:
                    settings_to_update[key] = value_type(data[key])
                except (ValueError, TypeError):
                    return jsonify({'error': f'Invalid value for {key}'}), 400
        
        # Update settings in database
        success = db_manager.update_system_settings(settings_to_update)
        
        if success:
            return jsonify({
                'message': 'Settings updated successfully',
                'settings': settings_to_update
            }), 200
        else:
            return jsonify({'error': 'Failed to update settings'}), 500
        
    except Exception as e:
        logger.error(f"Error updating settings: {str(e)}")
        return jsonify({'error': 'Failed to update settings'}), 500