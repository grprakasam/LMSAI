# app.py - Optimized main application with OpenRouter integration
from flask import Flask, render_template, request, jsonify
from flask_login import LoginManager, login_required, current_user
from werkzeug.security import generate_password_hash
from datetime import datetime
import os
import logging

# Import our modules
from config import config, PLANS, MODEL_CONFIGS, AUDIO_MODEL_CONFIGS
from models import init_db, User, Tutorial, UsageLog
from routes import main_bp, auth_bp, api_bp, admin_api_bp
from openrouter_service import openrouter_service
from utils import validate_email, check_system_health

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

    # Initialize database
    init_db(app)

    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access AI-powered R tutorials.'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

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
        from models import db
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

    # Custom CLI commands
    @app.command()
    def init_db_cmd():
        """Initialize the database."""
        from models import db
        db.create_all()
        print("[OK] Database initialized successfully!")

    @app.command()
    def test_openrouter():
        """Test OpenRouter connection."""
        status = openrouter_service.get_model_status()
        print(f"OpenRouter Status: {status['status']}")
        if status['status'] == 'connected':
            print(f"[OK] Connected! {status.get('model_count', 0)} models available")
        else:
            print(f"[ERROR] Connection failed: {status.get('error', 'Unknown')}")

    @app.command()
    def create_sample_user():
        """Create a sample user for testing."""
        from models import db
        email = "demo@rtutorpro.com"
        if User.query.filter_by(email=email).first():
            print(f"User {email} already exists")
            return
        user = User(
            email=email,
            password_hash=generate_password_hash('s'),
            name='Demo User',
            plan='free'
        )
        db.session.add(user)
        db.commit()
        print(f"[OK] Created sample user: {email} (password: s)")

    @app.route('/health')
    def health_check():
        """Comprehensive health check"""
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

    @app.route('/api/config')
    @login_required
    def get_config():
        """Get application configuration info"""
        return jsonify({
            'openrouter': {
                'enabled': bool(app.config.get('OPENROUTER_API_KEY')),
                'base_url': app.config.get('OPENROUTER_BASE_URL'),
                'default_text_model': app.config.get('DEFAULT_TEXT_MODEL'),
                'default_audio_model': app.config.get('DEFAULT_AUDIO_MODEL'),
                'available_text_models': app.config.get('AVAILABLE_TEXT_MODELS', []),
                'available_audio_models': app.config.get('AVAILABLE_AUDIO_MODELS', [])
            },
            'features': {
                'audio_generation': True,
                'model_selection': True,
                'unlimited_tutorials': True,
                'advanced_topics': True
            },
            'limits': {
                'max_duration': app.config.get('MAX_TUTORIAL_DURATION', 60),
                'min_duration': app.config.get('MIN_TUTORIAL_DURATION', 1)
            },
            'version': '2.0.0'
        })

    @app.before_request
    def validate_configuration():
        """Validate configuration on startup"""
        logger.info("Starting R Tutor Pro with OpenRouter integration")
        if app.config.get('OPENROUTER_API_KEY'):
            logger.info("OpenRouter API key configured")
            status = openrouter_service.get_model_status()
            if status['status'] == 'connected':
                logger.info(f"OpenRouter connected - {status.get('model_count', 0)} models available")
            else:
                logger.warning(f"OpenRouter connection issue: {status.get('error', 'Unknown')}")
        else:
            logger.warning("OpenRouter API key not configured - AI features will be limited")
        try:
            from models import db
            db.create_all()
            logger.info("Database connection verified")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
        upload_dir = app.config.get('UPLOAD_FOLDER', 'static/generated_audio')
        os.makedirs(upload_dir, exist_ok=True)
        logger.info(f"Upload directory ready: {upload_dir}")

    return app

# Create application instance
app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    app.run(
        debug=debug,
        host='0.0.0.0',
        port=port,
        threaded=True,
        use_reloader=debug,
        use_debugger=debug
    )
