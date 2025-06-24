from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
from datetime import datetime
from flasgger import swag_from

from ..services.email_service import EmailService
from ..services.auth_service import AuthService
from ..models.db_models import db_manager

# Create blueprint
email_bp = Blueprint('emails', __name__)

# Initialize services
email_service = EmailService()
auth_service = AuthService()
logger = logging.getLogger(__name__)

# In-memory storage for emails
email_stats = {
    'total_emails': 0,
    'total_accounts': 0,
    'emails_by_category': {},
    'emails_by_account': {},
    'last_fetch_time': None,
    'fetch_errors': 0
}

@email_bp.route('/accounts', methods=['GET'])
@jwt_required()
@swag_from({
    'tags': ['Email'],
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
def get_accounts():
    """Get all email accounts."""
    try:
        accounts = db_manager.get_email_accounts()
        return jsonify([{
            'email': acc.email,
            'active': acc.is_active
        } for acc in accounts]), 200
    except Exception as e:
        logger.error(f"Error getting email accounts: {str(e)}")
        return jsonify({'error': 'Failed to get email accounts'}), 500

@email_bp.route('/fetch', methods=['POST'])
@jwt_required()
@swag_from({
    'tags': ['Email'],
    'summary': 'Fetch emails',
    'description': 'Manually trigger email fetching from all accounts',
    'security': [{'Bearer': []}],
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': False,
            'schema': {
                'type': 'object',
                'properties': {
                    'limit': {'type': 'integer', 'default': 50}
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Email fetch completed',
            'schema': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'results': {
                        'type': 'object',
                        'properties': {
                            'total_accounts': {'type': 'integer'},
                            'successful_accounts': {'type': 'integer'},
                            'failed_accounts': {'type': 'integer'},
                            'total_emails_fetched': {'type': 'integer'},
                            'errors': {'type': 'array', 'items': {'type': 'string'}}
                        }
                    }
                }
            }
        }
    }
})
def fetch_emails():
    """Manually trigger email fetching from all accounts."""
    try:
        current_user_id = get_jwt_identity()
        user = auth_service.get_user_by_id(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get request parameters
        data = request.get_json() or {}
        limit_per_account = data.get('limit', 50)
        
        logger.info(f"Manual email fetch triggered by user: {user.email}")
        
        # Fetch accounts from database
        accounts = db_manager.get_email_accounts()
        
        if not accounts:
            return jsonify({'error': 'No email accounts configured or accessible'}), 400
        
        fetch_results = {
            'total_accounts': len(accounts),
            'successful_accounts': 0,
            'failed_accounts': 0,
            'total_emails_fetched': 0,
            'errors': []
        }
        
        # Fetch emails from each account
        for account in accounts:
            try:
                logger.info(f"Fetching emails from: {account.email}")
                
                # Test connection first
                if not email_service.test_account_connection(account):
                    error_msg = f"Connection failed for account: {account.email}"
                    fetch_results['errors'].append(error_msg)
                    fetch_results['failed_accounts'] += 1
                    continue
                
                # Fetch emails
                emails = email_service.fetch_emails_from_account(account, limit_per_account)
                
                # Store emails in database
                for email in emails:
                    db_manager.save_email(email)
                
                fetch_results['total_emails_fetched'] += len(emails)
                fetch_results['successful_accounts'] += 1
                
                # Update account stats
                if account.email not in email_stats['emails_by_account']:
                    email_stats['emails_by_account'][account.email] = 0
                email_stats['emails_by_account'][account.email] += len(emails)
                
                # Update category stats
                for email in emails:
                    if email.category not in email_stats['emails_by_category']:
                        email_stats['emails_by_category'][email.category] = 0
                    email_stats['emails_by_category'][email.category] += 1
                
                logger.info(f"Fetched {len(emails)} emails from {account.email}")
                
            except Exception as e:
                error_msg = f"Error fetching from {account.email}: {str(e)}"
                fetch_results['errors'].append(error_msg)
                fetch_results['failed_accounts'] += 1
                email_stats['fetch_errors'] += 1
                logger.error(error_msg)
        
        # Update global stats from database
        stats = db_manager.get_email_stats()
        email_stats.update(stats)
        
        return jsonify({
            'message': 'Email fetch completed',
            'results': fetch_results
        }), 200
        
    except Exception as e:
        logger.error(f"Email fetch error: {str(e)}")
        return jsonify({'error': 'Email fetch failed'}), 500

@email_bp.route('/', methods=['GET'])
@jwt_required()
@swag_from({
    'tags': ['Email'],
    'summary': 'List emails',
    'description': 'List emails with filtering and pagination',
    'security': [{'Bearer': []}],
    'parameters': [
        {
            'name': 'page',
            'in': 'query',
            'type': 'integer',
            'default': 1
        },
        {
            'name': 'per_page',
            'in': 'query',
            'type': 'integer',
            'default': 20
        },
        {
            'name': 'category',
            'in': 'query',
            'type': 'string'
        },
        {
            'name': 'account',
            'in': 'query',
            'type': 'string'
        },
        {
            'name': 'search',
            'in': 'query',
            'type': 'string'
        },
        {
            'name': 'main_category',
            'in': 'query',
            'type': 'string'
        },
        {
            'name': 'sub_category',
            'in': 'query',
            'type': 'string'
        },
        {
            'name': 'folder',
            'in': 'query',
            'type': 'string'
        }
    ],
    'responses': {
        200: {
            'description': 'List of emails',
            'schema': {
                'type': 'object',
                'properties': {
                    'emails': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'string'},
                                'subject': {'type': 'string'},
                                'from': {'type': 'string'},
                                'to': {'type': 'string'},
                                'date': {'type': 'string'},
                                'category': {'type': 'string'},
                                'is_read': {'type': 'boolean'}
                            }
                        }
                    },
                    'pagination': {
                        'type': 'object',
                        'properties': {
                            'page': {'type': 'integer'},
                            'per_page': {'type': 'integer'},
                            'total': {'type': 'integer'},
                            'pages': {'type': 'integer'}
                        }
                    },
                    'filters': {
                        'type': 'object',
                        'properties': {
                            'category': {'type': 'string'},
                            'account': {'type': 'string'},
                            'search': {'type': 'string'},
                            'main_category': {'type': 'string'},
                            'sub_category': {'type': 'string'},
                            'folder': {'type': 'string'}
                        }
                    }
                }
            }
        }
    }
})
def list_emails():
    """List emails with filtering and pagination."""
    try:
        current_user_id = get_jwt_identity()
        user = auth_service.get_user_by_id(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        filters = {
            'category': request.args.get('category'),
            'account': request.args.get('account'),
            'search': request.args.get('search'),
            'main_category': request.args.get('main_category'),
            'sub_category': request.args.get('sub_category'),
            'folder': request.args.get('folder', 'inbox')
        }
        
        # Security: Non-admins cannot access trash folder
        if user.role != 'admin' and filters['folder'] == 'trash':
            return jsonify({'error': 'Access denied to trash folder'}), 403
            
        # Proper filtering based on folder
        if filters.get('folder') == 'trash':
            # Show only trashed emails
            filters['is_trashed'] = True
        elif filters.get('folder') == 'inbox':
            # Show only non-trashed emails in inbox
            filters['is_trashed'] = False
        elif filters.get('folder') == 'archive':
            # Show only archived emails
            filters['is_archived'] = True
            filters['is_trashed'] = False
        elif filters.get('folder') == 'spam':
            # Show only spam emails
            filters['is_spam'] = True
            filters['is_trashed'] = False
        elif filters.get('folder') == 'starred':
            # Show only starred emails
            filters['is_starred'] = True
            filters['is_trashed'] = False
        elif filters.get('folder') == 'sent':
            # Show only sent emails (emails where sender is the user)
            filters['is_trashed'] = False
            # Note: This would need additional logic to identify sent emails
        elif filters.get('folder') == 'unread':
            # Show only unread emails
            filters['is_read'] = False
            filters['is_trashed'] = False
        else:
            # Default: exclude trashed emails unless specifically requested
            if user.role != 'admin':
                filters['is_trashed'] = False

        # Use access control: Admin/Super Admin see all emails, regular users see only their assigned emails
        if user.role in ['admin', 'super_admin']:
            # Admin/Super Admin can see all emails
            emails, total = db_manager.get_emails(filters=filters, page=page, per_page=per_page)
        else:
            # Regular users can only see emails from accounts they have access to
            emails, total = db_manager.get_user_accessible_emails(current_user_id, filters=filters, page=page, per_page=per_page)
        
        return jsonify({
            'emails': [email.to_dict() for email in emails],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            },
            'filters': filters
        }), 200
        
    except Exception as e:
        logger.error(f"List emails error: {str(e)}")
        return jsonify({'error': 'Failed to list emails'}), 500

@email_bp.route('/<email_id>', methods=['GET'])
@jwt_required()
def get_email(email_id):
    """Get a specific email by ID."""
    try:
        # New code: fetch from database
        email = db_manager.get_email_by_id(email_id)
        if not email:
            return jsonify({'error': 'Email not found'}), 404
        return jsonify({'email': email.to_dict()}), 200
    except Exception as e:
        logger.error(f"Get email error: {str(e)}")
        return jsonify({'error': 'Failed to get email'}), 500

@email_bp.route('/<email_id>/read', methods=['POST'])
@jwt_required()
def mark_email_read(email_id):
    """Mark email as read (local database only)."""
    try:
        # Find email in database
        email = db_manager.get_email_by_id(email_id)
        if not email:
            return jsonify({'error': 'Email not found'}), 404
        
        # Update local database only (no server update)
        email.is_read = True
        db_manager.save_email(email)
        
        logger.info(f"Email {email_id} marked as read in local database for account {email.account_email}")
        
        return jsonify({
            'message': 'Email marked as read (local only)',
            'email': email.to_dict()
        }), 200
    except Exception as e:
        logger.error(f"Mark email read error: {str(e)}")
        return jsonify({'error': 'Failed to mark email as read'}), 500

@email_bp.route('/<email_id>/unread', methods=['POST'])
@jwt_required()
def mark_email_unread(email_id):
    """Mark email as unread (local database only)."""
    try:
        # Find email in database
        email = db_manager.get_email_by_id(email_id)
        if not email:
            return jsonify({'error': 'Email not found'}), 404
        
        # Update local database only (no server update)
        email.is_read = False
        db_manager.save_email(email)
        
        logger.info(f"Email {email_id} marked as unread in local database for account {email.account_email}")
        
        return jsonify({
            'message': 'Email marked as unread (local only)',
            'email': email.to_dict()
        }), 200
    except Exception as e:
        logger.error(f"Mark email unread error: {str(e)}")
        return jsonify({'error': 'Failed to mark email as unread'}), 500

@email_bp.route('/<email_id>/action', methods=['POST'])
@jwt_required()
def email_action(email_id):
    """Perform an action on an email (e.g., archive, spam, trash)."""
    try:
        data = request.get_json()
        action = data.get('action')
        
        if not action or action not in ['archive', 'spam', 'trash', 'restore', 'star']:
            return jsonify({'error': 'Invalid action specified'}), 400
        
        email = db_manager.get_email_by_id(email_id)
        
        if not email:
            return jsonify({'error': 'Email not found'}), 404
        
        if action == 'archive':
            email.is_archived = True
            email.folder = 'archive'
        elif action == 'spam':
            email.is_spam = True
            email.folder = 'spam'
        elif action == 'trash':
            email.is_trashed = True
            email.folder = 'trash'
        elif action == 'restore':
            email.is_archived = False
            email.is_spam = False
            email.is_trashed = False
            email.folder = 'inbox'
        elif action == 'star':
            # Toggle star status
            email.is_starred = not email.is_starred

        if db_manager.save_email(email):
            return jsonify({
                'message': f'Email successfully moved to {action}',
                'email_id': email_id,
                'status': action
            }), 200
        else:
            return jsonify({'error': 'Failed to update email'}), 500
            
    except Exception as e:
        logger.error(f"Email action error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@email_bp.route('/<email_id>/tags', methods=['POST'])
@jwt_required()
def add_email_tags(email_id):
    """Add tags to an email."""
    try:
        data = request.get_json()
        
        if not data or 'tags' not in data:
            return jsonify({'error': 'Tags are required'}), 400
        
        new_tags = data['tags']
        if not isinstance(new_tags, list):
            return jsonify({'error': 'Tags must be a list'}), 400
        
        # Find email in storage
        email = None
        for stored_email in emails_storage.values():
            if stored_email.id == email_id:
                email = stored_email
                break
        
        if not email:
            return jsonify({'error': 'Email not found'}), 404
        
        # Add new tags (avoid duplicates)
        for tag in new_tags:
            if tag not in email.tags:
                email.tags.append(tag)
        
        return jsonify({
            'message': 'Tags added successfully',
            'email': email.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Add email tags error: {str(e)}")
        return jsonify({'error': 'Failed to add tags'}), 500

@email_bp.route('/stats', methods=['GET'])
@jwt_required()
@swag_from({
    'tags': ['Email'],
    'summary': 'Get email statistics',
    'description': 'Get email statistics including total emails, accounts, and categories',
    'security': [{'Bearer': []}],
    'responses': {
        200: {
            'description': 'Email statistics',
            'schema': {
                'type': 'object',
                'properties': {
                    'stats': {
                        'type': 'object',
                        'properties': {
                            'total_emails': {'type': 'integer'},
                            'total_accounts': {'type': 'integer'},
                            'emails_by_category': {'type': 'object'},
                            'emails_by_account': {'type': 'object'},
                            'last_fetch_time': {'type': 'string'},
                            'fetch_errors': {'type': 'integer'}
                        }
                    }
                }
            }
        }
    }
})
def get_email_stats():
    """Get email statistics."""
    try:
        # Get stats from database
        current_stats = db_manager.get_email_stats()
        
        return jsonify({
            'stats': current_stats
        }), 200
        
    except Exception as e:
        logger.error(f"Get email stats error: {str(e)}")
        return jsonify({'error': 'Failed to get email statistics'}), 500

@email_bp.route('/categories', methods=['GET'])
@jwt_required()
def get_categories():
    """Get all email categories."""
    try:
        # Get categories from categorization service
        categorization_service = email_service.categorization_service
        
        return jsonify({
            'categories': categorization_service.get_category_rules(),
            'stats': categorization_service.get_categorization_stats()
        }), 200
        
    except Exception as e:
        logger.error(f"Get categories error: {str(e)}")
        return jsonify({'error': 'Failed to get categories'}), 500

@email_bp.route('/accounts/test', methods=['POST'])
@jwt_required()
def test_accounts():
    """Test connectivity to all configured accounts."""
    try:
        current_user_id = get_jwt_identity()
        user = auth_service.get_user_by_id(current_user_id)
        
        if not user or user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        accounts = db_manager.get_email_accounts()
        
        if not accounts:
            return jsonify({'error': 'No accounts configured'}), 400
        
        test_results = []
        
        for account in accounts:
            try:
                is_connected = email_service.test_account_connection(account)
                test_results.append({
                    'email': account.email,
                    'status': 'connected' if is_connected else 'failed',
                    'imap_server': account.imap_server,
                    'imap_port': account.imap_port
                })
            except Exception as e:
                test_results.append({
                    'email': account.email,
                    'status': 'error',
                    'error': str(e),
                    'imap_server': account.imap_server,
                    'imap_port': account.imap_port
                })
        
        return jsonify({
            'test_results': test_results,
            'total_tested': len(test_results),
            'successful': len([r for r in test_results if r['status'] == 'connected']),
            'failed': len([r for r in test_results if r['status'] != 'connected'])
        }), 200
        
    except Exception as e:
        logger.error(f"Test accounts error: {str(e)}")
        return jsonify({'error': 'Failed to test accounts'}), 500

@email_bp.route('/mark_all_read', methods=['POST'])
@jwt_required()
def mark_all_emails_read():
    try:
        db_manager.mark_all_emails_read()
        return jsonify({'message': 'All emails marked as read'}), 200
    except Exception as e:
        logger.error(f"Failed to mark all emails as read: {str(e)}")
        return jsonify({'error': 'Failed to mark all emails as read'}), 500

@email_bp.route('/categorize/batch', methods=['POST'])
@jwt_required()
@swag_from({
    'tags': ['Email'],
    'summary': 'Categorize stored emails in batch',
    'description': 'Smart batch categorization for stored emails (after filtering) to minimize AI token usage',
    'security': [{'Bearer': []}],
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': False,
            'schema': {
                'type': 'object',
                'properties': {
                    'email_ids': {
                        'type': 'array',
                        'items': {'type': 'string'},
                        'description': 'Specific email IDs to categorize'
                    },
                    'limit': {'type': 'integer', 'default': 10},
                    'priority': {
                        'type': 'string',
                        'enum': ['recent', 'unread', 'all'],
                        'default': 'recent'
                    }
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Batch categorization completed',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'message': {'type': 'string'},
                    'categorized': {'type': 'integer'},
                    'skipped': {'type': 'integer'},
                    'errors': {'type': 'array', 'items': {'type': 'string'}}
                }
            }
        }
    }
})
def categorize_emails_batch():
    """Smart batch categorization for stored emails to minimize AI token usage."""
    try:
        current_user_id = get_jwt_identity()
        user = auth_service.get_user_by_id(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json() or {}
        email_ids = data.get('email_ids')
        limit = data.get('limit', 10)
        priority = data.get('priority', 'recent')
        
        logger.info(f"Batch categorization requested by user: {user.email}, limit: {limit}, priority: {priority}")
        
        # Use stored email categorization (after filtering)
        if email_ids:
            # Categorize specific emails
            result = email_service.categorize_emails_batch(email_ids=email_ids, limit=limit)
        else:
            # Use enhanced categorization for stored emails
            result = email_service.categorize_stored_emails_batch(limit=limit, priority=priority)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Batch categorization error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Categorization failed: {str(e)}',
            'categorized': 0,
            'skipped': 0,
            'errors': [str(e)]
        }), 500

@email_bp.route('/categorize/uncategorized', methods=['GET'])
@jwt_required()
@swag_from({
    'tags': ['Email'],
    'summary': 'Get uncategorized emails',
    'description': 'Get list of emails that need categorization',
    'security': [{'Bearer': []}],
    'parameters': [
        {
            'name': 'limit',
            'in': 'query',
            'type': 'integer',
            'default': 10
        },
        {
            'name': 'priority',
            'in': 'query',
            'type': 'string',
            'enum': ['unread', 'recent', 'all'],
            'default': 'unread'
        }
    ],
    'responses': {
        200: {
            'description': 'List of uncategorized emails',
            'schema': {
                'type': 'object',
                'properties': {
                    'emails': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'string'},
                                'subject': {'type': 'string'},
                                'sender': {'type': 'string'},
                                'date': {'type': 'string'},
                                'is_read': {'type': 'boolean'}
                            }
                        }
                    },
                    'count': {'type': 'integer'}
                }
            }
        }
    }
})
def get_uncategorized_emails():
    """Get emails that need categorization."""
    try:
        current_user_id = get_jwt_identity()
        user = auth_service.get_user_by_id(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        limit = request.args.get('limit', 10, type=int)
        priority = request.args.get('priority', 'unread')
        
        # Get uncategorized emails
        emails = email_service.get_emails_for_categorization(limit=limit, priority=priority)
        
        return jsonify({
            'emails': [email.to_dict() for email in emails],
            'count': len(emails)
        }), 200
        
    except Exception as e:
        logger.error(f"Get uncategorized emails error: {str(e)}")
        return jsonify({'error': 'Failed to get uncategorized emails'}), 500

@email_bp.route('/categories/main', methods=['GET'])
def get_main_categories():
    """Get all main categories with email counts."""
    try:
        categories = db_manager.get_main_categories_with_counts()
        return jsonify({
            'success': True,
            'categories': categories
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@email_bp.route('/categories/<main_category>/sub', methods=['GET'])
def get_sub_categories(main_category):
    """Get sub categories for a main category with email counts."""
    try:
        sub_categories = db_manager.get_sub_categories_with_counts(main_category)
        return jsonify({
            'success': True,
            'main_category': main_category,
            'sub_categories': sub_categories
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@email_bp.route('/categories/<main_category>/<sub_category>', methods=['GET'])
def get_emails_by_category_hierarchy(main_category, sub_category):
    """Get emails by main category and sub category."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        account_email = request.args.get('account_email')
        
        emails = db_manager.get_emails_by_category_hierarchy(
            main_category, sub_category, page, per_page, account_email
        )
        
        return jsonify({
            'success': True,
            'main_category': main_category,
            'sub_category': sub_category,
            'emails': [email.to_dict() for email in emails],
            'page': page,
            'per_page': per_page
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@email_bp.route('/categories/<main_category>', methods=['GET'])
def get_emails_by_main_category(main_category):
    """Get emails by main category only."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        account_email = request.args.get('account_email')
        
        emails = db_manager.get_emails_by_main_category(
            main_category, page, per_page, account_email
        )
        
        return jsonify({
            'success': True,
            'main_category': main_category,
            'emails': [email.to_dict() for email in emails],
            'page': page,
            'per_page': per_page
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@email_bp.route('/sync-read-status', methods=['POST'])
@jwt_required()
def sync_read_status():
    """Sync read status from email server to local database."""
    try:
        current_user_id = get_jwt_identity()
        user = auth_service.get_user_by_id(current_user_id)
        
        if not user or user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        accounts = db_manager.get_email_accounts()
        
        if not accounts:
            return jsonify({'error': 'No email accounts configured'}), 400
        
        sync_results = []
        total_updated = 0
        
        for account in accounts:
            try:
                success = email_service.sync_read_status_from_server(account)
                sync_results.append({
                    'email': account.email,
                    'status': 'success' if success else 'failed'
                })
                if success:
                    total_updated += 1
            except Exception as e:
                sync_results.append({
                    'email': account.email,
                    'status': 'error',
                    'error': str(e)
                })
        
        return jsonify({
            'message': 'Read status sync completed',
            'results': sync_results,
            'total_accounts': len(accounts),
            'successful_syncs': total_updated,
            'failed_syncs': len(accounts) - total_updated
        }), 200
        
    except Exception as e:
        logger.error(f"Sync read status error: {str(e)}")
        return jsonify({'error': 'Failed to sync read status'}), 500

@email_bp.route('/<email_id>', methods=['DELETE'])
@jwt_required()
def delete_email(email_id):
    """Permanently delete an email (only if in trash)."""
    try:
        current_user_id = get_jwt_identity()
        user = auth_service.get_user_by_id(current_user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        email = db_manager.get_email_by_id(email_id)
        if not email:
            return jsonify({'error': 'Email not found'}), 404
        if not email.is_trashed:
            return jsonify({'error': 'Email must be in trash to delete permanently'}), 400
        if db_manager.delete_email(email_id):
            return jsonify({'message': 'Email permanently deleted', 'email_id': email_id}), 200
        else:
            return jsonify({'error': 'Failed to delete email'}), 500
    except Exception as e:
        logger.error(f"Permanent delete email error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
