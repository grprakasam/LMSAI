from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model for authentication and subscription management"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    plan = db.Column(db.String(20), default='free', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    
    # Stripe integration
    stripe_customer_id = db.Column(db.String(100), unique=True)
    stripe_subscription_id = db.Column(db.String(100), unique=True)
    subscription_status = db.Column(db.String(50), default='inactive')
    
    # User preferences
    preferred_expertise = db.Column(db.String(20), default='beginner')
    preferred_duration = db.Column(db.Integer, default=5)
    timezone = db.Column(db.String(50), default='UTC')
    
    # Relationships
    tutorials = db.relationship('Tutorial', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    usage_logs = db.relationship('UsageLog', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    team_memberships = db.relationship('TeamMember', backref='user', lazy='dynamic')
    
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
        """Check if user can create more tutorials this month"""
        from config import PLANS
        monthly_usage = self.get_monthly_usage()
        monthly_limit = PLANS[self.plan]['tutorials_per_month']
        return monthly_usage < monthly_limit
    
    def get_plan_info(self):
        """Get current plan information"""
        from config import PLANS
        return PLANS.get(self.plan, PLANS['free'])
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'plan': self.plan,
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active,
            'monthly_usage': self.get_monthly_usage()
        }

class Tutorial(db.Model):
    """Tutorial model for storing generated content"""
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
    is_premium = db.Column(db.Boolean, default=False, nullable=False)
    concepts = db.Column(db.Text)  # JSON array of concepts
    packages = db.Column(db.Text)  # JSON array of R packages
    learning_objectives = db.Column(db.Text)  # JSON array of objectives
    
    # Media files
    audio_url = db.Column(db.String(500))
    audio_duration = db.Column(db.Integer)  # in seconds
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
        self.view_count += 1
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
            'is_premium': self.is_premium,
            'concepts': self.get_concepts(),
            'packages': self.get_packages(),
            'learning_objectives': self.get_learning_objectives(),
            'audio_url': self.audio_url,
            'view_count': self.view_count,
            'status': self.status
        }

class UsageLog(db.Model):
    """Usage logging for analytics and billing"""
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
            resource_id=kwargs.get('resource_id')
        )
        
        # Set metadata
        metadata = {k: v for k, v in kwargs.items() 
                   if k not in ['ip_address', 'user_agent', 'resource_type', 'resource_id']}
        if metadata:
            log.set_metadata(metadata)
        
        db.session.add(log)
        db.session.commit()
        return log

class Team(db.Model):
    """Team model for organizational accounts"""
    __tablename__ = 'teams'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Team settings
    plan = db.Column(db.String(20), default='team', nullable=False)
    max_members = db.Column(db.Integer, default=10)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Billing
    stripe_subscription_id = db.Column(db.String(100), unique=True)
    billing_email = db.Column(db.String(120))
    
    # Relationships
    members = db.relationship('TeamMember', backref='team', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Team {self.name}>'
    
    def get_active_members(self):
        """Get active team members"""
        return self.members.filter_by(is_active=True).all()
    
    def get_member_count(self):
        """Get number of active members"""
        return self.members.filter_by(is_active=True).count()
    
    def can_add_member(self):
        """Check if team can add more members"""
        return self.get_member_count() < self.max_members
    
    def get_monthly_usage(self, year=None, month=None):
        """Get total team usage for a month"""
        member_ids = [m.user_id for m in self.get_active_members()]
        if not member_ids:
            return 0
        
        if year is None or month is None:
            now = datetime.now()
            year, month = now.year, now.month
        
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        return UsageLog.query.filter(
            UsageLog.user_id.in_(member_ids),
            UsageLog.action == 'tutorial_created',
            UsageLog.created_at >= start_date,
            UsageLog.created_at < end_date
        ).count()

class TeamMember(db.Model):
    """Team membership model"""
    __tablename__ = 'team_members'
    
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.String(20), default='member', nullable=False)  # admin, member
    joined_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Unique constraint
    __table_args__ = (db.UniqueConstraint('team_id', 'user_id', name='unique_team_member'),)
    
    def __repr__(self):
        return f'<TeamMember {self.user.email} in {self.team.name}>'
    
    def is_admin(self):
        """Check if member is admin"""
        return self.role == 'admin'

class APIKey(db.Model):
    """API keys for team plan users"""
    __tablename__ = 'api_keys'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    key_hash = db.Column(db.String(255), nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_used_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Permissions
    permissions = db.Column(db.Text)  # JSON array of allowed actions
    
    def __repr__(self):
        return f'<APIKey {self.name} for {self.user.email}>'
    
    def get_permissions(self):
        """Get permissions as list"""
        return json.loads(self.permissions) if self.permissions else []
    
    def set_permissions(self, permissions_list):
        """Set permissions from list"""
        self.permissions = json.dumps(permissions_list)
    
    def has_permission(self, action):
        """Check if API key has specific permission"""
        return action in self.get_permissions()
    
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
            # Create composite indexes
            db.engine.execute(
                'CREATE INDEX IF NOT EXISTS idx_usage_user_action_date ON usage_logs(user_id, action, created_at)'
            )
            db.engine.execute(
                'CREATE INDEX IF NOT EXISTS idx_tutorials_user_date ON tutorials(user_id, created_at)'
            )
            print("✅ Database indexes created successfully")
        except Exception as e:
            print(f"⚠️ Index creation skipped: {e}")
        
        print("✅ Database initialized successfully")
