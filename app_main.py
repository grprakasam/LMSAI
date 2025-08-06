#!/usr/bin/env python3
# app_main.py - Updated main application entry point
import os
import sys
from flask import Flask, render_template, request, jsonify
from flask_login import LoginManager
from werkzeug.security import generate_password_hash
from datetime import datetime
import logging

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Use existing routes and components for now
from routes import main_bp, auth_bp, api_bp, admin_api_bp
from app.core.config import config, PLANS, MODEL_CONFIGS, AUDIO_MODEL_CONFIGS
from app.core.extensions import db, login_manager, setup_logging
from app.models import init_db, User

def create_app(config_name=None):
    """Application factory pattern"""
    app = Flask(__name__)

    # Determine configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app_config = config.get(config_name, config['default'])
    app.config.from_object(app_config)

    # Ensure required directories exist
    os.makedirs(app.config.get('UPLOAD_FOLDER', 'static/generated_audio'), exist_ok=True)
    os.makedirs('logs', exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Setup logging
    logger = setup_logging()

    # User loader
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Initialize database
    init_db(app)

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(admin_api_bp, url_prefix='/api/admin')

    # Global template variables
    @app.context_processor
    def inject_global_vars():
        return {
            'plans': PLANS,
            'models': MODEL_CONFIGS,
            'audio_models': AUDIO_MODEL_CONFIGS,
            'openrouter_enabled': bool(app.config.get('OPENROUTER_API_KEY')),
            'app_version': '2.0.0'
        }

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Resource not found', 'status': 404}), 404
        return render_template('error.html', error_code=404, error_message='Page not found'), 404

    @app.errorhandler(403)
    def forbidden(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Access denied', 'status': 403}), 403
        return render_template('error.html', error_code=403, error_message='Access denied'), 403

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        logger.error(f"Internal server error: {error}")
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Internal server error', 'status': 500}), 500
        return render_template('error.html', error_code=500, error_message='Internal server error'), 500

    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        return jsonify({
            'error': 'Rate limit exceeded',
            'message': 'Too many requests. Please try again later.',
            'retry_after': 60,
            'status': 429
        }), 429

    return app

# Create application instance
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'
    app.run(
        debug=debug,
        host='0.0.0.0',
        port=port,
        threaded=True,
        use_reloader=debug,
        use_debugger=debug
    )