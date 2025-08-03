
#!/usr/bin/env python3
"""
R Tutor Pro SaaS - Development Server
Run this file for local development with hot reload and debugging
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_app():
    """Create and configure the Flask application"""
    from flask import Flask
    from config import config
    from models import init_db
    from flask_login import LoginManager
    
    # Determine configuration
    config_name = os.environ.get('FLASK_ENV', 'development')
    app_config = config.get(config_name, config['default'])
    
    # Create Flask app
    app = Flask(__name__)
    app.config.from_object(app_config)
    
    # Initialize database
    init_db(app)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return User.query.get(int(user_id))
    
    # Register blueprints
    from routes import main_bp, auth_bp, api_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Resource not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        from models import db
        db.session.rollback()
        return {'error': 'Internal server error'}, 500
    
    return app

def init_database():
    """Initialize database with sample data"""
    app = create_app()
    
    with app.app_context():
        from models import db, User
        from werkzeug.security import generate_password_hash
        
        print("Initializing database...")
        db.create_all()
        
        # Create sample admin user if none exists
        if not User.query.filter_by(email='admin@rtutorpro.com').first():
            admin_user = User(
                email='admin@rtutorpro.com',
                password_hash=generate_password_hash('admin123'),
                name='Admin User',
                plan='team',
                is_active=True,
                email_verified=True
            )
            db.session.add(admin_user)
            
            # Create sample free user
            free_user = User(
                email='demo@rtutorpro.com',
                password_hash=generate_password_hash('demo123'),
                name='Demo User',
                plan='free',
                is_active=True,
                email_verified=True
            )
            db.session.add(free_user)
            
            db.session.commit()
            print("Sample users created:")
            print("   Admin: admin@rtutorpro.com / admin123")
            print("   Demo:  demo@rtutorpro.com / demo123")
        
        print("✅ Database initialized successfully!")

def run_tests():
    """Run the test suite"""
    import pytest
    
    print("🧪 Running test suite...")
    exit_code = pytest.main(['-v', 'tests/'])
    sys.exit(exit_code)

def run_development_server():
    """Run development server with debugging enabled"""
    app = create_app()
    
    print("Starting R Tutor Pro SaaS - Development Mode")
    print("=" * 50)
    print(f"Dashboard: http://localhost:{app.config.get('PORT', 5000)}")
    print(f"Environment: {app.config.get('ENV', 'development')}")
    print(f"Database: {app.config.get('SQLALCHEMY_DATABASE_URI', 'Not configured')}")
    print("=" * 50)
    
    # Check environment setup
    warnings = []
    
    if not os.environ.get('SECRET_KEY'):
        warnings.append("SECRET_KEY not set - using default (insecure)")
    
    if not os.environ.get('DEEPSEEK_API_KEY') and not os.environ.get('OPENAI_API_KEY'):
        warnings.append("No AI API keys configured - premium features disabled")
    
    if warnings:
        print("⚠️  Configuration Warnings:")
        for warning in warnings:
            print(f"   - {warning}")
        print()
    
    # Start development server
    app.run(
        debug=True,
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        use_reloader=True,
        threaded=True
    )

def show_usage():
    """Show usage information"""
    print("""
R Tutor Pro SaaS - Development Tools

Usage:
    python run.py [command]

Commands:
    (no command)  - Start development server
    --init-db     - Initialize database with sample data  
    --test        - Run test suite
    --help        - Show this help message

Environment Variables:
    SECRET_KEY          - Flask secret key for sessions
    DATABASE_URL        - Database connection string
    DEEPSEEK_API_KEY    - DeepSeek AI API key (optional)
    OPENAI_API_KEY      - OpenAI API key (optional)
    FLASK_ENV           - Environment (development/production)
    PORT                - Server port (default: 5000)

Examples:
    python run.py                    # Start development server
    python run.py --init-db          # Initialize database
    python run.py --test             # Run tests
    
For production deployment, use gunicorn:
    gunicorn --bind 0.0.0.0:5000 app:app
    """)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == '--init-db':
            init_database()
        elif command == '--test':
            run_tests()
        elif command == '--help':
            show_usage()
        else:
            print(f"Unknown command: {command}")
            show_usage()
            sys.exit(1)
    else:
        run_development_server()