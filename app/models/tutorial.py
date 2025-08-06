# tutorial.py - Tutorial model
from datetime import datetime
import json
from ..core.extensions import db

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
    is_premium = db.Column(db.Boolean, default=True, nullable=False)
    concepts = db.Column(db.Text)  # JSON array of concepts
    packages = db.Column(db.Text)  # JSON array of R packages
    learning_objectives = db.Column(db.Text)  # JSON array of objectives
    
    # OpenRouter integration fields
    text_model = db.Column(db.String(100))
    audio_model = db.Column(db.String(100))
    audio_voice = db.Column(db.String(50))
    generated_via = db.Column(db.String(50), default='openrouter')
    
    # Media files
    audio_url = db.Column(db.String(500))
    audio_duration = db.Column(db.Integer)
    audio_format = db.Column(db.String(10), default='mp3')
    pdf_url = db.Column(db.String(500))
    
    # Analytics
    view_count = db.Column(db.Integer, default=0)
    like_count = db.Column(db.Integer, default=0)
    share_count = db.Column(db.Integer, default=0)
    
    # Status
    status = db.Column(db.String(20), default='completed')
    
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
            'is_premium': True,
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