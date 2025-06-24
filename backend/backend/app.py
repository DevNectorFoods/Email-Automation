import os
import logging
from flask import Flask, render_template, redirect, url_for, jsonify
from flask_jwt_extended import JWTManager
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_cors import CORS, cross_origin
from flasgger import Swagger

from .config import Config
from .utils.logger import setup_logging
from .routes.auth_routes import auth_bp
from .routes.email_routes import email_bp
from .routes.admin_routes import admin_bp
from .routes.settings_routes import settings_bp
from .routes.user_access_routes import user_access_bp
from .utils.background_tasks import BackgroundTaskManager
from .routes.notification_routes import notification_bp
from .routes.reply_routes import reply_bp
from .models.db_models import db_manager

def create_app():
    """Application factory pattern for Flask app creation."""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(Config)
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Configure CORS to allow requests from frontend
    CORS(app, origins=['http://localhost:5173', 'http://127.0.0.1:5173'], 
          supports_credentials=True, methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
    
    # Debug JWT configuration
    logging.info(f"JWT_SECRET_KEY: {app.config.get('JWT_SECRET_KEY')}")
    logging.info(f"JWT_ACCESS_TOKEN_EXPIRES: {app.config.get('JWT_ACCESS_TOKEN_EXPIRES')}")
    
    # Setup logging
    setup_logging()
    
    # Initialize JWT
    jwt = JWTManager(app)
    
    # JWT identity callback to handle string user IDs
    @jwt.user_identity_loader
    def user_identity_lookup(user):
        return str(user)
    
    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        identity = jwt_data["sub"]
        return db_manager.get_user_by_id(int(identity))
    
    # Configure Swagger with complete settings
    swagger = Swagger(app, template={
        "swagger": "2.0",
        "info": {
            "title": "Email Automation API",
            "description": "API documentation for Email Automation Tool",
            "version": "1.0.0"
        },
        "basePath": "/",
        "schemes": ["http", "https"],
        "consumes": ["application/json"],
        "produces": ["application/json"],
        "securityDefinitions": {
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "JWT Authorization header using the Bearer scheme. Example: \"Authorization: Bearer {token}\""
            }
        },
        "security": [
            {
                "Bearer": []
            }
        ]
    })
    
    # Register blueprints with proper URL prefixes
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(email_bp, url_prefix='/api/emails')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(settings_bp, url_prefix='/api/settings')
    app.register_blueprint(user_access_bp, url_prefix='/api/user-access')
    app.register_blueprint(notification_bp, url_prefix='/api/notifications')
    app.register_blueprint(reply_bp, url_prefix='/api/replies')
    
    # Initialize background task manager
    app.background_tasks = BackgroundTaskManager()
    
    # Main routes
    @app.route('/')
    def index():
        """Main landing page."""
        return render_template('index.html')
    
    @app.route('/login')
    def login_page():
        """Login page."""
        return render_template('login.html')
    
    @app.route('/dashboard')
    def dashboard():
        """Dashboard page."""
        return render_template('dashboard.html')
    
    @app.route('/settings')
    def settings():
        """Settings page."""
        return render_template('settings.html')
    
    @app.route('/reply')
    def email_reply():
        """Email reply page."""
        return render_template('email_reply.html')
    
    @app.route('/api-docs')
    def api_docs():
        """API documentation page."""
        return render_template('api_docs.html')
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """
        Health check endpoint
        ---
        tags:
          - System
        responses:
          200:
            description: System is healthy
            schema:
              type: object
              properties:
                status:
                  type: string
                  example: healthy
        """
        return jsonify({'status': 'healthy'})
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        return {'error': 'Resource not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        logging.error(f"Internal server error: {error}")
        return {'error': 'Internal server error'}, 500
    
    # JWT error handlers
    @jwt.expired_token_loader
    @cross_origin()
    def expired_token_callback(jwt_header, jwt_payload):
        logging.warning(f"JWT Token expired: {jwt_payload}")
        return {'error': 'Token has expired'}, 401
    
    @jwt.invalid_token_loader
    @cross_origin()
    def invalid_token_callback(error):
        logging.warning(f"JWT Invalid token error: {error}")
        return {'error': 'Invalid token'}, 401
    
    @jwt.unauthorized_loader
    @cross_origin()
    def missing_token_callback(error):
        logging.warning(f"JWT Missing token error: {error}")
        return {'error': 'Authorization token is required'}, 401
    
    # Print all registered routes (remove in production)
    # logging.info("Registered Routes:")
    # for rule in app.url_map.iter_rules():
    #     logging.info(f"{rule.endpoint}: {rule.rule}")
    
    return app

# Create the app instance
app = create_app()

if __name__ == '__main__':
    app.background_tasks.start()
    app.run(host='0.0.0.0', port=5000, debug=True)
