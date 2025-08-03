# models.py - Updated to support OpenRouter integration
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model for authentication - all users get full access"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    plan = db.Column(db.String(20), default='free', nullable=False)  # Always 'free' but with full access
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    email_verified = db.Column(db.Boolean, default=True, nullable=False)  # Auto-verify for demo
    
    # User preferences for OpenRouter
    preferred_text_model = db.Column(db.String(100), default='anthropic/claude-3.5-sonnet')
    preferred_audio_model = db.Column(db.String(100), default='openai/tts-1')
    preferred_voice = db.Column(db.String(50), default='alloy')
    preferred_expertise = db.Column(db.String(20), default='beginner')
    preferred_duration = db.Column(db.Integer, default=5)
    
    # Stripe integration (kept for future use)
    stripe_customer_id = db.Column(db.String(100), unique=True)
    stripe_subscription_id = db.Column(db.String(100), unique=True)
    subscription_status = db.Column(db.String(50), default='active')  # Always active
    
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
        """Check if user can create more tutorials - always True now"""
        return True  # Everyone has unlimited access
    
    def get_plan_info(self):
        """Get current plan information - everyone gets full features"""
        from config import PLANS
        return PLANS.get('free', PLANS['free'])  # Everyone gets full access
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'plan': 'premium',  # Show as premium for UI purposes
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

class Tutorial(db.Model):
    """Tutorial model for storing generated content with OpenRouter integration"""
    __tablename__ = 'tutorials'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    topic = db.Column(db.String(200), nullable=False, index=True)
    expertise = db.Column(db.String(50), nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Content metadata
    is_premium = db.Column(db.Boolean, default=True, nullable=False)  # All content is premium now
    concepts = db.Column(db.Text)  # JSON array of concepts
    packages = db.Column(db.Text)  # JSON array of R packages
    learning_objectives = db.Column(db.Text)  # JSON array of objectives
    
    # OpenRouter integration fields
    text_model = db.Column(db.String(100))  # Model used for text generation
    audio_model = db.Column(db.String(100))  # Model used for audio generation
    audio_voice = db.Column(db.String(50))  # Voice used for audio
    generated_via = db.Column(db.String(50), default='openrouter')  # Generation method
    
    # Media files
    audio_url = db.Column(db.String(500))
    audio_duration = db.Column(db.Integer)  # in seconds
    audio_format = db.Column(db.String(10), default='mp3')
    pdf_url = db.Column(db.String(500))
    
    # Analytics
    view_count = db.Column(db.Integer, default=0)
    like_count = db.Column(db.Integer, default=0)
    share_count = db.Column(db.Integer, default=0)
    
    # Status
    status = db.Column(db.String(20), default='completed')  # draft, processing, completed, failed
    
    def __repr__(self):
        return f'<Tutorial {self.topic} by {self.user.email}>'
    
    def get_concepts(self):
        """Get concepts as list"""
        return json.loads(self.concepts) if self.concepts else []
    
    def set_concepts(self, concepts_list):
        """Set concepts from list"""
        self.concepts = json.dumps(concepts_list)
    
    def get_packages(self):
        """Get packages as list"""
        return json.loads(self.packages) if self.packages else []
    
    def set_packages(self, packages_list):
        """Set packages from list"""
        self.packages = json.dumps(packages_list)
    
    def get_learning_objectives(self):
        """Get learning objectives as list"""
        return json.loads(self.learning_objectives) if self.learning_objectives else []
    
    def set_learning_objectives(self, objectives_list):
        """Set learning objectives from list"""
        self.learning_objectives = json.dumps(objectives_list)
    
    def increment_view(self):
        """Increment view count"""
        self.view_count = (self.view_count or 0) + 1
        db.session.commit()
    
    def to_dict(self):
        """Convert tutorial to dictionary"""
        return {
            'id': self.id,
            'topic': self.topic,
            'expertise': self.expertise,
            'duration': self.duration,
            'content': self.content,
            'created_at': self.created_at.isoformat(),
            'is_premium': True,  # All content is premium
            'concepts': self.get_concepts(),
            'packages': self.get_packages(),
            'learning_objectives': self.get_learning_objectives(),
            'audio_url': self.audio_url,
            'audio_duration': self.audio_duration,
            'audio_voice': self.audio_voice,
            'view_count': self.view_count,
            'status': self.status,
            'models_used': {
                'text': self.text_model,
                'audio': self.audio_model,
                'voice': self.audio_voice
            },
            'generated_via': self.generated_via
        }

class UsageLog(db.Model):
    """Usage logging for analytics"""
    __tablename__ = 'usage_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    action = db.Column(db.String(100), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Action metadata
    metadata_json = db.Column(db.Text)  # JSON string for additional data
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    
    # Resource tracking
    resource_type = db.Column(db.String(50))  # tutorial, audio, pdf, etc.
    resource_id = db.Column(db.Integer)
    
    # OpenRouter specific tracking
    model_used = db.Column(db.String(100))  # Model used for the action
    tokens_used = db.Column(db.Integer)  # Tokens consumed
    cost_estimate = db.Column(db.Float)  # Estimated cost in USD
    
    def __repr__(self):
        return f'<UsageLog {self.action} by {self.user.email}>'
    
    def get_metadata(self):
        """Get metadata as dictionary"""
        return json.loads(self.metadata_json) if self.metadata_json else {}
    
    def set_metadata(self, metadata_dict):
        """Set metadata from dictionary"""
        self.metadata_json = json.dumps(metadata_dict)
    
    @classmethod
    def log_action(cls, user_id, action, **kwargs):
        """Helper method to log user actions"""
        log = cls(
            user_id=user_id,
            action=action,
            ip_address=kwargs.get('ip_address'),
            user_agent=kwargs.get('user_agent'),
            resource_type=kwargs.get('resource_type'),
            resource_id=kwargs.get('resource_id'),
            model_used=kwargs.get('model_used'),
            tokens_used=kwargs.get('tokens_used'),
            cost_estimate=kwargs.get('cost_estimate')
        )
        
        # Set metadata
        metadata = {k: v for k, v in kwargs.items() 
                   if k not in ['ip_address', 'user_agent', 'resource_type', 'resource_id', 
                               'model_used', 'tokens_used', 'cost_estimate']}
        if metadata:
            log.set_metadata(metadata)
        
        db.session.add(log)
        db.session.commit()
        return log

class APIKey(db.Model):
    """API keys for users (all users can have API access now)"""
    __tablename__ = 'api_keys'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    key_hash = db.Column(db.String(255), nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_used_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Permissions - all users get full permissions
    permissions = db.Column(db.Text)  # JSON array of allowed actions
    
    def __repr__(self):
        return f'<APIKey {self.name} for {self.user.email}>'
    
    def get_permissions(self):
        """Get permissions as list - all users get all permissions"""
        if self.permissions:
            return json.loads(self.permissions)
        # Default permissions for all users
        return [
            'create_tutorial',
            'read_tutorial',
            'update_tutorial',
            'delete_tutorial',
            'regenerate_tutorial',
            'generate_audio',
            'export_data',
            'analytics'
        ]
    
    def set_permissions(self, permissions_list):
        """Set permissions from list"""
        self.permissions = json.dumps(permissions_list)
    
    def has_permission(self, action):
        """Check if API key has specific permission - always True for all users"""
        return True  # All users have all permissions
    
    def update_last_used(self):
        """Update last used timestamp"""
        self.last_used_at = datetime.utcnow()
        db.session.commit()

# Database initialization function
def init_db(app):
    """Initialize database with app context"""
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        
        # Create indexes for better performance
        try:
            # Create composite indexes if they don't exist
            db.engine.execute(
                'CREATE INDEX IF NOT EXISTS idx_usage_user_action_date ON usage_logs(user_id, action, created_at)'
            )
            db.engine.execute(
                'CREATE INDEX IF NOT EXISTS idx_tutorials_user_date ON tutorials(user_id, created_at)'
            )
            print("✅ Database indexes created successfully")
        except Exception as e:
            print(f"⚠️ Index creation skipped: {e}")
        
        print("✅ Database initialized successfully - OpenRouter integration enabled")

# Helper function to upgrade existing users to full access
def upgrade_all_users_to_full_access():
    """Upgrade all existing users to have full access"""
    try:
        # Update all users to have premium-level access while keeping 'free' plan
        users = User.query.all()
        for user in users:
            user.subscription_status = 'active'
            user.is_active = True
            user.email_verified = True
            # Set default OpenRouter preferences if not set
            if not user.preferred_text_model:
                user.preferred_text_model = 'anthropic/claude-3.5-sonnet'
            if not user.preferred_audio_model:
                user.preferred_audio_model = 'openai/tts-1'
            if not user.preferred_voice:
                user.preferred_voice = 'alloy'
        
        # Update all tutorials to be premium
        tutorials = Tutorial.query.all()
        for tutorial in tutorials:
            tutorial.is_premium = True
            tutorial.generated_via = 'openrouter'
        
        db.session.commit()
        print(f"✅ Upgraded {len(users)} users and {len(tutorials)} tutorials to full access")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Failed to upgrade users: {e}")

# Function to create sample data for demonstration
def create_sample_data():
    """Create sample data for demonstration"""
    try:
        # Check if sample data already exists
        if User.query.filter_by(email='demo@rtutorpro.com').first():
            print("⚠️ Sample data already exists")
            return
        
        # Create sample users
        demo_user = User(
            email='demo@rtutorpro.com',
            name='Demo User',
            plan='free',  # Free plan with full access
            preferred_text_model='anthropic/claude-3.5-sonnet',
            preferred_audio_model='openai/tts-1',
            preferred_voice='alloy'
        )
        demo_user.set_password('s')
        
        advanced_user = User(
            email='advanced@rtutorpro.com',
            name='Advanced User',
            plan='free',  # Free plan with full access
            preferred_text_model='openai/gpt-4-turbo',
            preferred_audio_model='openai/tts-1-hd',
            preferred_voice='nova'
        )
        advanced_user.set_password('s')
        
        db.session.add(demo_user)
        db.session.add(advanced_user)
        db.session.commit()
        
        # Create sample tutorials
        sample_tutorials = [
            {
                'topic': 'ggplot2 Data Visualization with OpenRouter AI',
                'expertise': 'intermediate',
                'duration': 15,
                'content': '# Advanced ggplot2 Tutorial\n\nLearn to create stunning visualizations with AI assistance...',
                'concepts': ['grammar of graphics', 'layers', 'aesthetics', 'AI-generated examples'],
                'packages': ['ggplot2', 'dplyr'],
                'objectives': ['Master ggplot2 syntax', 'Create professional plots', 'Use AI for visualization ideas'],
                'text_model': 'anthropic/claude-3.5-sonnet',
                'generated_via': 'openrouter'
            },
            {
                'topic': 'Machine Learning with tidymodels - AI Enhanced',
                'expertise': 'expert',
                'duration': 30,
                'content': '# Machine Learning in R\n\nBuild predictive models with tidymodels and AI guidance...',
                'concepts': ['supervised learning', 'model evaluation', 'feature engineering', 'AI optimization'],
                'packages': ['tidymodels', 'ranger', 'glmnet'],
                'objectives': ['Understand ML workflow', 'Build production models', 'Leverage AI for model selection'],
                'text_model': 'openai/gpt-4-turbo',
                'generated_via': 'openrouter'
            }
        ]
        
        for tutorial_data in sample_tutorials:
            tutorial = Tutorial(
                user_id=demo_user.id,
                topic=tutorial_data['topic'],
                expertise=tutorial_data['expertise'],
                duration=tutorial_data['duration'],
                content=tutorial_data['content'],
                is_premium=True,
                text_model=tutorial_data['text_model'],
                generated_via=tutorial_data['generated_via']
            )
            tutorial.set_concepts(tutorial_data['concepts'])
            tutorial.set_packages(tutorial_data['packages'])
            tutorial.set_learning_objectives(tutorial_data['objectives'])
            
            db.session.add(tutorial)
        
        db.session.commit()
        print("✅ Sample data created successfully with OpenRouter integration")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Failed to create sample data: {e}")