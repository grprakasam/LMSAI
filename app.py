from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
import uuid
import requests
import json
import tempfile
import base64
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///r_tutor_saas.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Configuration
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

# Subscription Plans
PLANS = {
    'free': {'tutorials_per_month': 3, 'price': 0, 'features': ['Basic R topics', 'Standard voice']},
    'pro': {'tutorials_per_month': 50, 'price': 9, 'features': ['All R topics', 'Premium voice', 'Code execution', 'Export options']},
    'team': {'tutorials_per_month': 200, 'price': 29, 'features': ['Team management', 'Usage analytics', 'Priority support', 'Custom topics']}
}

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    plan = db.Column(db.String(20), default='free')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    stripe_customer_id = db.Column(db.String(100))
    
    # Relationships
    tutorials = db.relationship('Tutorial', backref='user', lazy=True)
    usage_logs = db.relationship('UsageLog', backref='user', lazy=True)

class Tutorial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    topic = db.Column(db.String(200), nullable=False)
    expertise = db.Column(db.String(50), nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    audio_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_premium = db.Column(db.Boolean, default=False)

class UsageLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)  # 'tutorial_created', 'audio_generated', etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    metadata = db.Column(db.Text)  # JSON string for additional data

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Enhanced R Content with Premium Features
R_TOPICS_CONTENT = {
    'free_topics': {
        'data structures': {
            'beginner': {
                'concepts': ['vectors', 'lists', 'data frames'],
                'code_examples': ['# Creating vectors\nnumeric_vector <- c(1, 2, 3, 4, 5)'],
                'packages': ['base'],
                'learning_objectives': ['Understanding R data types', 'Creating basic structures']
            }
        },
        'basic plotting': {
            'beginner': {
                'concepts': ['plot function', 'basic charts'],
                'code_examples': ['plot(x, y, main="My Plot")'],
                'packages': ['graphics'],
                'learning_objectives': ['Creating simple plots']
            }
        }
    },
    'premium_topics': {
        'advanced ggplot2': {
            'expert': {
                'concepts': ['custom themes', 'complex layouts', 'animations'],
                'code_examples': ['# Advanced ggplot with custom theme\nggplot(data) + geom_point() + theme_custom()'],
                'packages': ['ggplot2', 'gganimate', 'patchwork'],
                'learning_objectives': ['Master advanced visualization', 'Create publication-ready plots']
            }
        },
        'machine learning': {
            'expert': {
                'concepts': ['caret', 'random forests', 'neural networks'],
                'code_examples': ['# ML model training\nmodel <- train(y ~ ., data = train_data, method = "rf")'],
                'packages': ['caret', 'randomForest', 'nnet'],
                'learning_objectives': ['Implement ML algorithms', 'Model evaluation and tuning']
            }
        },
        'shiny dashboards': {
            'intermediate': {
                'concepts': ['reactive programming', 'dashboard layouts', 'deployment'],
                'code_examples': ['# Advanced Shiny app\nshinyDashboard(...)'],
                'packages': ['shiny', 'shinydashboard', 'DT'],
                'learning_objectives': ['Build interactive dashboards', 'Deploy Shiny apps']
            }
        }
    }
}

class AITutorialGenerator:
    def __init__(self):
        self.deepseek_url = "https://api.deepseek.com/v1/chat/completions"
        self.openai_url = "https://api.openai.com/v1/chat/completions"
    
    def generate_tutorial_content(self, topic, expertise, duration, user_plan='free'):
        """Generate tutorial content based on user's subscription plan"""
        
        # Determine content access based on plan
        if user_plan == 'free':
            content_pool = R_TOPICS_CONTENT['free_topics']
            max_duration = min(duration, 5)  # Limit free users to 5 minutes
        else:
            content_pool = {**R_TOPICS_CONTENT['free_topics'], **R_TOPICS_CONTENT['premium_topics']}
            max_duration = duration
        
        # Get topic content
        topic_data = self._get_topic_data(topic, expertise, content_pool)
        
        # Generate script using AI
        if user_plan != 'free' and DEEPSEEK_API_KEY:
            script = self._generate_ai_script(topic, expertise, max_duration, topic_data)
        else:
            script = self._generate_basic_script(topic, expertise, max_duration, topic_data)
        
        return {
            'content': script,
            'concepts': topic_data['concepts'],
            'packages': topic_data['packages'],
            'objectives': topic_data['learning_objectives'],
            'is_premium': user_plan != 'free'
        }
    
    def _generate_ai_script(self, topic, expertise, duration, topic_data):
        """Generate high-quality content using AI (Premium feature)"""
        prompt = f"""Create a comprehensive {duration}-minute R programming tutorial on "{topic}" for {expertise} level.

Structure:
1. Welcome and overview (30 seconds)
2. Core concepts explanation (60% of time)
3. Practical examples with code (30% of time)  
4. Summary and next steps (10% of time)

Include:
- Clear explanations for {expertise} level
- Practical R code examples
- Best practices and common pitfalls
- Relevant packages: {', '.join(topic_data['packages'])}

Make it conversational and engaging. Include natural pauses [PAUSE] and emphasis [EMPHASIS] markers."""

        try:
            if DEEPSEEK_API_KEY:
                response = self._call_deepseek_api(prompt)
                if response:
                    return response
        except Exception as e:
            print(f"AI generation failed: {e}")
        
        return self._generate_basic_script(topic, expertise, duration, topic_data)
    
    def _call_deepseek_api(self, prompt):
        """Call DeepSeek API for premium content generation"""
        headers = {
            'Authorization': f'Bearer {DEEPSEEK_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': 'deepseek-chat',
            'messages': [
                {'role': 'system', 'content': 'You are an expert R programming instructor.'},
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': 2000,
            'temperature': 0.7
        }
        
        try:
            response = requests.post(self.deepseek_url, headers=headers, json=data, timeout=30)
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
        except Exception as e:
            print(f"DeepSeek API error: {e}")
        
        return None
    
    def _generate_basic_script(self, topic, expertise, duration, topic_data):
        """Generate basic content for free users"""
        return f"""Welcome to this {duration}-minute R tutorial on {topic}!

[PAUSE] Today we'll cover {', '.join(topic_data['concepts'][:2])}.

Key concepts:
- {topic_data['concepts'][0] if topic_data['concepts'] else 'Basic concepts'}
- Practical applications in R

[PAUSE] Here's a code example:
{topic_data['code_examples'][0] if topic_data['code_examples'] else '# R code example'}

[EMPHASIS] Remember to practice these concepts regularly.

Thank you for using R Tutor! Upgrade to Pro for advanced topics and longer tutorials."""

    def _get_topic_data(self, topic, expertise, content_pool):
        """Get topic-specific data from content pool"""
        # Search for matching topic
        for topic_key, topic_content in content_pool.items():
            if topic_key.lower() in topic.lower():
                if expertise in topic_content:
                    return topic_content[expertise]
        
        # Default fallback
        return {
            'concepts': ['fundamental concepts', 'practical applications'],
            'code_examples': [f'# {topic} example\n# Basic R code'],
            'packages': ['base'],
            'learning_objectives': [f'Understanding {topic}']
        }

# Usage tracking decorators
def track_usage(action):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.is_authenticated:
                log = UsageLog(
                    user_id=current_user.id,
                    action=action,
                    metadata=json.dumps({
                        'endpoint': request.endpoint,
                        'ip': request.remote_addr
                    })
                )
                db.session.add(log)
                db.session.commit()
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def check_usage_limits():
    """Check if user has exceeded their plan limits"""
    if not current_user.is_authenticated:
        return False
    
    # Get current month usage
    start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    usage_count = UsageLog.query.filter(
        UsageLog.user_id == current_user.id,
        UsageLog.action == 'tutorial_created',
        UsageLog.created_at >= start_of_month
    ).count()
    
    plan_limit = PLANS[current_user.plan]['tutorials_per_month']
    return usage_count >= plan_limit

# Initialize AI generator
ai_generator = AITutorialGenerator()

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        # Get user stats
        total_tutorials = Tutorial.query.filter_by(user_id=current_user.id).count()
        start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_usage = UsageLog.query.filter(
            UsageLog.user_id == current_user.id,
            UsageLog.action == 'tutorial_created',
            UsageLog.created_at >= start_of_month
        ).count()
        
        user_stats = {
            'total_tutorials': total_tutorials,
            'monthly_usage': monthly_usage,
            'monthly_limit': PLANS[current_user.plan]['tutorials_per_month'],
            'plan': current_user.plan
        }
        return render_template('dashboard.html', stats=user_stats, plans=PLANS)
    
    return render_template('landing.html', plans=PLANS)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email'].lower().strip()
        password = request.form['password']
        name = request.form['name'].strip()
        
        # Bypass registration - any password "s" works
        if password == "s":
            # Create a dummy user if one doesn't exist for this email
            user = User.query.filter_by(email=email).first()
            if not user:
                user = User(
                    email=email,
                    password_hash=generate_password_hash(password),
                    name=name if name else email.split('@')[0]
                )
                db.session.add(user)
                db.session.commit()
            
            login_user(user)
            return redirect(url_for('index'))
        
        return jsonify({'success': False, 'error': 'Invalid credentials'})
    
    return render_template('auth.html', mode='register')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].lower().strip()
        password = request.form['password']
        
        # Bypass login - any email with password "s" works
        if password == "s":
            # Find or create user
            user = User.query.filter_by(email=email).first()
            if not user:
                user = User(
                    email=email,
                    password_hash=generate_password_hash(password),
                    name=email.split('@')[0]
                )
                db.session.add(user)
                db.session.commit()
            
            login_user(user)
            return jsonify({'success': True, 'redirect': url_for('index')})
        
        return jsonify({'success': False, 'error': 'Invalid credentials'})
    
    return render_template('auth.html', mode='login')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/generate-tutorial', methods=['POST'])
@login_required
@track_usage('tutorial_created')
def generate_tutorial():
    # Check usage limits
    if check_usage_limits():
        return jsonify({
            'success': False,
            'error': 'Monthly limit reached. Please upgrade your plan.',
            'upgrade_required': True
        })
    
    try:
        topic = request.form.get('topic', '').strip()
        expertise = request.form.get('expertise', '').strip()
        duration = int(request.form.get('duration', 5))
        
        if not topic or not expertise:
            return jsonify({'success': False, 'error': 'Please fill all required fields'})
        
        # Generate tutorial content
        tutorial_data = ai_generator.generate_tutorial_content(
            topic, expertise, duration, current_user.plan
        )
        
        # Save tutorial to database
        tutorial = Tutorial(
            user_id=current_user.id,
            topic=topic,
            expertise=expertise,
            duration=duration,
            content=tutorial_data['content'],
            is_premium=tutorial_data['is_premium']
        )
        
        db.session.add(tutorial)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'tutorial_id': tutorial.id,
            'content': tutorial_data['content'],
            'concepts': tutorial_data['concepts'],
            'packages': tutorial_data['packages'],
            'objectives': tutorial_data['objectives'],
            'is_premium': tutorial_data['is_premium'],
            'topic': topic,
            'expertise': expertise,
            'duration': duration
        })
        
    except Exception as e:
        print(f"Error generating tutorial: {e}")
        return jsonify({'success': False, 'error': 'Tutorial generation failed'})

@app.route('/upgrade/<plan>')
@login_required
def upgrade_plan(plan):
    if plan not in PLANS:
        return jsonify({'success': False, 'error': 'Invalid plan'})
    
    # Here you would integrate with Stripe for payment processing
    # For MVP, we'll just update the plan directly
    current_user.plan = plan
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Successfully upgraded to {plan.title()} plan!',
        'redirect': url_for('index')
    })

@app.route('/api/usage-stats')
@login_required
def usage_stats():
    """API endpoint for usage analytics"""
    start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Monthly usage
    monthly_tutorials = UsageLog.query.filter(
        UsageLog.user_id == current_user.id,
        UsageLog.action == 'tutorial_created',
        UsageLog.created_at >= start_of_month
    ).count()
    
    # Recent tutorials
    recent_tutorials = Tutorial.query.filter_by(user_id=current_user.id)\
        .order_by(Tutorial.created_at.desc()).limit(5).all()
    
    return jsonify({
        'monthly_usage': monthly_tutorials,
        'monthly_limit': PLANS[current_user.plan]['tutorials_per_month'],
        'plan': current_user.plan,
        'recent_tutorials': [
            {
                'topic': t.topic,
                'expertise': t.expertise,
                'created_at': t.created_at.isoformat(),
                'is_premium': t.is_premium
            } for t in recent_tutorials
        ]
    })

@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'database': 'connected',
        'ai_services': {
            'deepseek': bool(DEEPSEEK_API_KEY),
            'openai': bool(OPENAI_API_KEY)
        }
    })

# Initialize database
@app.before_first_request
def create_tables():
    db.create_all()
    
    # Create sample free content if no users exist
    if User.query.count() == 0:
        print("Initializing database with sample data...")

if __name__ == '__main__':
    print("🚀 Starting R Tutor SaaS MVP...")
    print("💰 Monetization: Freemium model with usage limits")
    print("🔧 Set environment variables:")
    print("   - DEEPSEEK_API_KEY for premium content")
    print("   - DATABASE_URL for production database")
    print("   - SECRET_KEY for session security")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
