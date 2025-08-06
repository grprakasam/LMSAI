# factory.py - Application factory
import os
from flask import Flask, render_template, request, jsonify
from .config import config, PLANS, MODEL_CONFIGS, AUDIO_MODEL_CONFIGS
from .extensions import db, login_manager, setup_logging

def create_app(config_name=None):
    """Application factory pattern"""
    app = Flask(__name__, 
                template_folder='../../templates',
                static_folder='../../static')

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
        from ..models.user import User
        return User.query.get(int(user_id))

    # Register blueprints (using existing routes for now)
    import sys
    sys.path.append('/root/repo')
    from routes import main_bp, auth_bp, api_bp, admin_api_bp
    
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

    # Health check endpoint
    @app.route('/health')
    def health_check():
        """Comprehensive health check"""
        from utils import check_system_health
        from openrouter_service import openrouter_service
        
        health_status = check_system_health()
        openrouter_status = openrouter_service.get_model_status()
        health_status['services'] = health_status.get('services', {})
        health_status['services']['openrouter'] = {
            'status': openrouter_status['status'],
            'api_key_configured': bool(app.config.get('OPENROUTER_API_KEY')),
            'models_available': openrouter_status.get('model_count', 0),
            'last_check': openrouter_status.get('last_check')
        }
        
        if health_status['checks']['database'] == 'unhealthy':
            health_status['status'] = 'unhealthy'
            status_code = 503
        elif openrouter_status['status'] != 'connected':
            health_status['status'] = 'warning'
            status_code = 200
        else:
            health_status['status'] = 'healthy'
            status_code = 200
            
        return jsonify(health_status), status_code

    return app