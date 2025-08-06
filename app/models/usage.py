# usage.py - Usage tracking models
from datetime import datetime
import json
from ..core.extensions import db

class UsageLog(db.Model):
    """Usage logging for analytics"""
    __tablename__ = 'usage_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    action = db.Column(db.String(100), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Action metadata
    metadata_json = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    
    # Resource tracking
    resource_type = db.Column(db.String(50))
    resource_id = db.Column(db.Integer)
    
    # OpenRouter specific tracking
    model_used = db.Column(db.String(100))
    tokens_used = db.Column(db.Integer)
    cost_estimate = db.Column(db.Float)
    
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
    """API keys for users"""
    __tablename__ = 'api_keys'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    key_hash = db.Column(db.String(255), nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_used_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Permissions
    permissions = db.Column(db.Text)
    
    def __repr__(self):
        return f'<APIKey {self.name} for {self.user.email}>'
    
    def get_permissions(self):
        """Get permissions as list"""
        if self.permissions:
            return json.loads(self.permissions)
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
        """Check if API key has specific permission"""
        return True
    
    def update_last_used(self):
        """Update last used timestamp"""
        self.last_used_at = datetime.utcnow()
        db.session.commit()