# user.py - User model
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from ..core.extensions import db

class User(UserMixin, db.Model):
    """User model for authentication"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    plan = db.Column(db.String(20), default='free', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    email_verified = db.Column(db.Boolean, default=True, nullable=False)
    
    # User preferences for OpenRouter
    preferred_text_model = db.Column(db.String(100), default='anthropic/claude-3.5-sonnet')
    preferred_audio_model = db.Column(db.String(100), default='openai/tts-1')
    preferred_voice = db.Column(db.String(50), default='alloy')
    preferred_expertise = db.Column(db.String(20), default='beginner')
    preferred_duration = db.Column(db.Integer, default=5)
    
    # Stripe integration
    stripe_customer_id = db.Column(db.String(100), unique=True)
    stripe_subscription_id = db.Column(db.String(100), unique=True)
    subscription_status = db.Column(db.String(50), default='active')
    
    # Relationships
    tutorials = db.relationship('Tutorial', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    usage_logs = db.relationship('UsageLog', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password"""
        return check_password_hash(self.password_hash, password)
    
    def get_monthly_usage(self, year=None, month=None):
        """Get tutorial usage for a specific month"""
        from .usage import UsageLog
        
        if year is None or month is None:
            now = datetime.now()
            year, month = now.year, now.month
        
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        return self.usage_logs.filter(
            UsageLog.action == 'tutorial_created',
            UsageLog.created_at >= start_date,
            UsageLog.created_at < end_date
        ).count()
    
    def can_create_tutorial(self):
        """Check if user can create more tutorials"""
        return True
    
    def get_plan_info(self):
        """Get current plan information"""
        from ..core.config import PLANS
        return PLANS.get('free', PLANS['free'])
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'plan': 'premium',
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active,
            'monthly_usage': self.get_monthly_usage(),
            'has_full_access': True,
            'preferred_models': {
                'text': self.preferred_text_model,
                'audio': self.preferred_audio_model,
                'voice': self.preferred_voice
            }
        }