# extensions.py - Flask extensions initialization
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import logging

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()

# Configure login manager
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access AI-powered R tutorials.'
login_manager.login_message_category = 'info'

# Configure logging
def setup_logging():
    """Setup application logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)