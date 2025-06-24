"""Routes for email reply functionality."""

import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..services.email_reply_service import EmailReplyService, EmailReply
from ..services.auth_service import AuthService
from ..models.db_models import DatabaseManager

logger = logging.getLogger(__name__)

reply_bp = Blueprint('reply', __name__, url_prefix='/api/replies')

# Initialize services
email_reply_service = EmailReplyService()
auth_service = AuthService()
db_manager = DatabaseManager()

@reply_bp.route('/compose', methods=['POST'])
@jwt_required()
def compose_reply():
    """Compose and send an email reply."""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['account_email', 'to_email', 'subject', 'body']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Get email account from database
        accounts = db_manager.get_email_accounts()
        account = None
        for acc in accounts:
            if acc.email == data['account_email']:
                account = acc
                break
        
        if not account:
            return jsonify({'error': 'Email account not found'}), 404
        
        # Create reply object
        reply = EmailReply(
            to_email=data['to_email'],
            subject=data['subject'],
            body=data['body'],
            body_html=data.get('body_html'),
            cc=data.get('cc', []),
            bcc=data.get('bcc', []),
            reply_to_id=data.get('reply_to_id')
        )
        
        # Send reply
        success = email_reply_service.send_reply(account, reply)
        
        if success:
            logger.info(f"Reply sent successfully from {account.email} to {reply.to_email}")
            return jsonify({
                'message': 'Reply sent successfully',
                'from': account.email,
                'to': reply.to_email,
                'subject': reply.subject
            }), 200
        else:
            return jsonify({'error': 'Failed to send reply'}), 500
            
    except Exception as e:
        logger.error(f"Compose reply error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@reply_bp.route('/template/<email_id>', methods=['GET'])
@jwt_required()
def get_reply_template(email_id):
    """Get a reply template for a specific email."""
    try:
        user_id = get_jwt_identity()
        
        # Find email in database
        all_emails = db_manager.get_emails(limit=1000)
        original_email = None
        for email in all_emails:
            if email.id == email_id:
                original_email = email
                break
        
        if not original_email:
            return jsonify({'error': 'Email not found'}), 404
        
        # Create reply template
        reply_template = email_reply_service.create_reply_template(original_email.to_dict())
        
        return jsonify({
            'template': {
                'to_email': reply_template.to_email,
                'subject': reply_template.subject,
                'body': reply_template.body,
                'reply_to_id': reply_template.reply_to_id,
                'original_email': original_email.to_dict()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get reply template error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@reply_bp.route('/test-smtp/<account_email>', methods=['POST'])
@jwt_required()
def test_smtp_connection(account_email):
    """Test SMTP connection for an email account."""
    try:
        user_id = get_jwt_identity()
        
        # Get email account from database
        accounts = db_manager.get_email_accounts()
        account = None
        for acc in accounts:
            if acc.email == account_email:
                account = acc
                break
        
        if not account:
            return jsonify({'error': 'Email account not found'}), 404
        
        # Test SMTP connection
        success = email_reply_service.test_smtp_connection(account)
        
        return jsonify({
            'account': account_email,
            'smtp_status': 'connected' if success else 'failed',
            'message': 'SMTP connection successful' if success else 'SMTP connection failed'
        }), 200
        
    except Exception as e:
        logger.error(f"Test SMTP connection error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@reply_bp.route('/accounts', methods=['GET'])
@jwt_required()
def get_reply_accounts():
    """Get available email accounts for sending replies."""
    try:
        user_id = get_jwt_identity()
        
        # Get active email accounts
        accounts = db_manager.get_email_accounts()
        active_accounts = [acc for acc in accounts if acc.is_active]
        
        account_list = []
        for account in active_accounts:
            account_list.append({
                'email': account.email,
                'account_type': account.account_type,
                'imap_server': account.imap_server,
                'is_active': account.is_active
            })
        
        return jsonify({
            'accounts': account_list,
            'total': len(account_list)
        }), 200
        
    except Exception as e:
        logger.error(f"Get reply accounts error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@reply_bp.route('/', methods=['GET'])
@jwt_required()
def get_reply_templates():
    """Get all reply templates."""
    try:
        user_id = get_jwt_identity()
        
        # Get reply templates from database
        templates = db_manager.get_reply_templates()
        
        template_list = []
        for template in templates:
            template_list.append({
                'id': template.id,
                'name': template.name,
                'subject': template.subject,
                'content': template.content,
                'created_at': template.created_at.isoformat() if template.created_at else None,
                'updated_at': template.updated_at.isoformat() if template.updated_at else None
            })
        
        return jsonify({
            'templates': template_list,
            'total': len(template_list)
        }), 200
        
    except Exception as e:
        logger.error(f"Get reply templates error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@reply_bp.route('/', methods=['POST'])
@jwt_required()
def create_reply_template():
    """Create a new reply template."""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'subject', 'content']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create template object
        template_data = {
            'name': data['name'],
            'subject': data['subject'],
            'content': data['content'],
            'user_id': user_id
        }
        
        # Save template to database
        template_id = db_manager.create_reply_template(template_data)
        
        if template_id:
            return jsonify({
                'message': 'Reply template created successfully',
                'template_id': template_id,
                'template': template_data
            }), 201
        else:
            return jsonify({'error': 'Failed to create reply template'}), 500
            
    except Exception as e:
        logger.error(f"Create reply template error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@reply_bp.route('/<template_id>', methods=['GET'])
@jwt_required()
def get_reply_template_by_id(template_id):
    """Get a specific reply template by ID."""
    try:
        user_id = get_jwt_identity()
        
        # Get template from database
        template = db_manager.get_reply_template_by_id(template_id)
        
        if not template:
            return jsonify({'error': 'Reply template not found'}), 404
        
        return jsonify({
            'template': {
                'id': template.id,
                'name': template.name,
                'subject': template.subject,
                'content': template.content,
                'created_at': template.created_at.isoformat() if template.created_at else None,
                'updated_at': template.updated_at.isoformat() if template.updated_at else None
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get reply template by ID error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@reply_bp.route('/<template_id>', methods=['PUT'])
@jwt_required()
def update_reply_template(template_id):
    """Update a reply template."""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'subject', 'content']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Update template in database
        success = db_manager.update_reply_template(template_id, {
            'name': data['name'],
            'subject': data['subject'],
            'content': data['content']
        })
        
        if success:
            return jsonify({
                'message': 'Reply template updated successfully',
                'template_id': template_id
            }), 200
        else:
            return jsonify({'error': 'Reply template not found or update failed'}), 404
            
    except Exception as e:
        logger.error(f"Update reply template error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@reply_bp.route('/<template_id>', methods=['DELETE'])
@jwt_required()
def delete_reply_template(template_id):
    """Delete a reply template."""
    try:
        user_id = get_jwt_identity()
        
        # Delete template from database
        success = db_manager.delete_reply_template(template_id)
        
        if success:
            return jsonify({
                'message': 'Reply template deleted successfully',
                'template_id': template_id
            }), 200
        else:
            return jsonify({'error': 'Reply template not found or delete failed'}), 404
            
    except Exception as e:
        logger.error(f"Delete reply template error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500