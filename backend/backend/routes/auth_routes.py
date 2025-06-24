from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt, create_access_token
import logging
from datetime import datetime, timedelta
from flasgger import swag_from

from ..services.auth_service import AuthService
from ..models.db_models import db_manager

# Create blueprint
auth_bp = Blueprint('auth', __name__)

# Initialize auth service
auth_service = AuthService()
logger = logging.getLogger(__name__)

@auth_bp.route('/login', methods=['POST'])
@swag_from({
    'tags': ['Authentication'],
    'summary': 'Login user',
    'description': 'Authenticate user and return JWT tokens',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'email': {'type': 'string', 'format': 'email'},
                    'password': {'type': 'string'}
                },
                'required': ['email', 'password']
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Login successful',
            'schema': {
                'type': 'object',
                'properties': {
                    'user': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'integer'},
                            'email': {'type': 'string'},
                            'name': {'type': 'string'},
                            'role': {'type': 'string'}
                        }
                    },
                    'access_token': {'type': 'string'},
                    'refresh_token': {'type': 'string'}
                }
            }
        },
        401: {
            'description': 'Invalid credentials'
        }
    }
})
def login():
    """Login user and return JWT tokens."""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return {'error': 'Email and password are required'}, 400
        
        result = auth_service.login(email, password)
        if not result:
            return {'error': 'Invalid credentials'}, 401
        
        return result, 200
        
    except Exception as e:
        logging.error(f"Login error: {str(e)}")
        return {'error': 'Internal server error'}, 500

@auth_bp.route('/register', methods=['POST'])
def register():
    """User registration endpoint."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body must be JSON'}), 400
        
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not all([username, email, password]):
            return jsonify({'error': 'Username, email, and password are required'}), 400
        
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters long'}), 400
        
        # Create user
        user = auth_service.create_user(username, email, password)
        
        if not user:
            return jsonify({'error': 'Email already exists or registration failed'}), 409
        
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({'error': 'Registration failed'}), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token endpoint."""
    try:
        current_user_id = get_jwt_identity()
        
        # Create new access token
        new_access_token = auth_service.refresh_access_token(current_user_id)
        
        if not new_access_token:
            return jsonify({'error': 'Token refresh failed'}), 401
        
        return jsonify({
            'access_token': new_access_token
        }), 200
        
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        return jsonify({'error': 'Token refresh failed'}), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """User logout endpoint."""
    try:
        # In a production system, you might want to blacklist the token
        # For now, just return success
        return jsonify({'message': 'Logout successful'}), 200
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return jsonify({'error': 'Logout failed'}), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
@swag_from({
    'tags': ['Authentication'],
    'summary': 'Get user profile',
    'description': 'Get profile information for the authenticated user',
    'security': [{'Bearer': []}],
    'responses': {
        200: {
            'description': 'Profile information',
            'schema': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer'},
                    'email': {'type': 'string'},
                    'name': {'type': 'string'},
                    'role': {'type': 'string'},
                    'created_at': {'type': 'string', 'format': 'date-time'},
                    'last_login': {'type': 'string', 'format': 'date-time'}
                }
            }
        },
        401: {
            'description': 'Unauthorized'
        }
    }
})
def get_profile():
    """Get user profile information."""
    try:
        user_id = get_jwt_identity()
        user = auth_service.get_user_by_id(user_id)
        
        if not user:
            return {'error': 'User not found'}, 404
        
        return {
            'id': user.id,
            'email': user.email,
            'name': user.name,
            'role': user.role,
            'created_at': user.created_at.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None
        }, 200
        
    except Exception as e:
        logging.error(f"Get profile error: {str(e)}")
        return {'error': 'Internal server error'}, 500

@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update user profile endpoint."""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body must be JSON'}), 400
        
        user = auth_service.get_user_by_id(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Update allowed fields
        if 'username' in data:
            user.username = data['username'].strip()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Update profile error: {str(e)}")
        return jsonify({'error': 'Failed to update profile'}), 500

@auth_bp.route('/validate', methods=['GET'])
@jwt_required()
def validate_token():
    """Validate JWT token endpoint."""
    try:
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        
        user = auth_service.get_user_by_id(current_user_id)
        
        if not user or not user.is_active:
            return jsonify({'error': 'Invalid or inactive user'}), 401
        
        return jsonify({
            'valid': True,
            'user': user.to_dict(),
            'claims': claims
        }), 200
        
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        return jsonify({'error': 'Token validation failed'}), 500

@auth_bp.route('/test', methods=['GET'])
@jwt_required()
@swag_from({
    'tags': ['Authentication'],
    'summary': 'Test authentication',
    'description': 'Test if JWT authentication is working',
    'security': [{'Bearer': []}],
    'responses': {
        200: {
            'description': 'Authentication successful',
            'schema': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'user_id': {'type': 'integer'}
                }
            }
        },
        401: {
            'description': 'Unauthorized'
        }
    }
})
def test_auth():
    """Test authentication endpoint."""
    try:
        user_id = get_jwt_identity()
        return {
            'message': 'Authentication successful',
            'user_id': user_id
        }, 200
    except Exception as e:
        logging.error(f"Test auth error: {str(e)}")
        return {'error': 'Internal server error'}, 500
