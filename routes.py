# routes.py - Modified for OpenRouter integration
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json
import re
import os

from models import db, User, Tutorial, UsageLog
from openrouter_service import openrouter_service
from utils import (
    track_usage, rate_limit, validate_tutorial_input, sanitize_input, 
    validate_email, calculate_usage_analytics, check_system_health
)
from config import PLANS, MODEL_CONFIGS, AUDIO_MODEL_CONFIGS

# Create blueprints
main_bp = Blueprint('main', __name__)
auth_bp = Blueprint('auth', __name__)
api_bp = Blueprint('api', __name__)

# ==================== MAIN ROUTES ====================

@main_bp.route('/')
def index():
    """Landing page or dashboard based on authentication status"""
    if current_user.is_authenticated:
        # Get user statistics for dashboard
        total_tutorials = Tutorial.query.filter_by(user_id=current_user.id).count()
        monthly_usage = current_user.get_monthly_usage()
        
        # Get OpenRouter status
        openrouter_status = openrouter_service.get_model_status()
        
        user_stats = {
            'total_tutorials': total_tutorials,
            'monthly_usage': monthly_usage,
            'monthly_limit': 999,  # Essentially unlimited
            'plan': 'free',  # Everyone is on free plan with full access
            'can_create_tutorial': True,  # Always true now
            'openrouter_connected': openrouter_status['status'] == 'connected'
        }
        
        return render_template('dashboard.html', 
                             stats=user_stats, 
                             plans=PLANS,
                             models=MODEL_CONFIGS,
                             audio_models=AUDIO_MODEL_CONFIGS,
                             openrouter_status=openrouter_status)
    
    # Landing page for non-authenticated users
    return render_template('landing.html', plans=PLANS)

@main_bp.route('/tutorial/<int:tutorial_id>')
@login_required
def view_tutorial(tutorial_id):
    """View a specific tutorial with audio playback"""
    tutorial = Tutorial.query.get_or_404(tutorial_id)
    
    # Check if user owns this tutorial
    if tutorial.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    # Track tutorial view
    tutorial.increment_view()
    
    return render_template('tutorial.html', tutorial=tutorial)

# ==================== AUTHENTICATION ROUTES ====================

def is_valid_email_format(email):
    """Very permissive email validation for demo purposes"""
    if not email or len(email.strip()) == 0:
        return False
    
    email = email.strip().lower()
    
    if '@' not in email:
        return False
    
    parts = email.split('@')
    if len(parts) != 2:
        return False
    
    local_part, domain_part = parts
    
    if len(local_part) == 0:
        return False
    
    if len(domain_part) == 0 or '.' not in domain_part:
        return False
    
    return True

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        name = request.form.get('name', '').strip()
        
        if not is_valid_email_format(email):
            error_msg = 'Please enter a valid email format (e.g., user@domain.com)'
            if request.headers.get('Content-Type') == 'application/json':
                return jsonify({'success': False, 'error': error_msg})
            flash(error_msg, 'error')
            return render_template('auth.html', mode='register')
        
        if password != "s":
            error_msg = 'Password must be "s" for demo access'
            if request.headers.get('Content-Type') == 'application/json':
                return jsonify({'success': False, 'error': error_msg})
            flash(error_msg, 'error')
            return render_template('auth.html', mode='register')
        
        try:
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                login_user(existing_user)
            else:
                user = User(
                    email=email,
                    password_hash=generate_password_hash(password),
                    name=name if name else email.split('@')[0],
                    plan='free'
                )
                db.session.add(user)
                db.session.commit()
                login_user(user)
            
            if request.headers.get('Content-Type') == 'application/json':
                return jsonify({'success': True, 'redirect': url_for('main.index')})
            return redirect(url_for('main.index'))
            
        except Exception as e:
            db.session.rollback()
            error_msg = 'Registration failed. Please try again.'
            if request.headers.get('Content-Type') == 'application/json':
                return jsonify({'success': False, 'error': error_msg})
            flash(error_msg, 'error')
    
    return render_template('auth.html', mode='register')

@auth_bp.route('/login', methods=['GET', 'POST'])
@rate_limit(requests_per_minute=20)
def login():
    """User login"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember_me = request.form.get('remember_me', False)
        
        if not is_valid_email_format(email):
            error_msg = 'Please enter a valid email format (e.g., user@domain.com)'
            if request.headers.get('Content-Type') == 'application/json':
                return jsonify({'success': False, 'error': error_msg})
            flash(error_msg, 'error')
            return render_template('auth.html', mode='login')
        
        if password != "s":
            error_msg = 'Password must be "s" for demo access'
            if request.headers.get('Content-Type') == 'application/json':
                return jsonify({'success': False, 'error': error_msg})
            flash(error_msg, 'error')
            return render_template('auth.html', mode='login')
        
        try:
            user = User.query.filter_by(email=email).first()
            if not user:
                user = User(
                    email=email,
                    password_hash=generate_password_hash(password),
                    name=email.split('@')[0],
                    plan='free'
                )
                db.session.add(user)
                db.session.commit()
            
            login_user(user, remember=bool(remember_me))
            
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('main.index')
            
            if request.headers.get('Content-Type') == 'application/json':
                return jsonify({'success': True, 'redirect': next_page})
            return redirect(next_page)
            
        except Exception as e:
            db.session.rollback()
            error_msg = 'Login failed. Please try again.'
            if request.headers.get('Content-Type') == 'application/json':
                return jsonify({'success': False, 'error': error_msg})
            flash(error_msg, 'error')
    
    return render_template('auth.html', mode='login')

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    try:
        UsageLog.log_action(
            user_id=current_user.id,
            action='user_logout',
            ip_address=request.remote_addr
        )
    except Exception as e:
        pass
    
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('main.index'))

# ==================== TUTORIAL GENERATION ROUTES ====================

@main_bp.route('/generate-tutorial', methods=['POST'])
@login_required
@rate_limit(requests_per_minute=15)
@track_usage('tutorial_created')
def generate_tutorial():
    """Generate a new tutorial using OpenRouter"""
    
    # Get and validate input
    topic = sanitize_input(request.form.get('topic', ''), 200)
    expertise = request.form.get('expertise', '').strip()
    duration = request.form.get('duration', type=int)
    text_model = request.form.get('text_model', '').strip()
    audio_model = request.form.get('audio_model', '').strip()
    voice = request.form.get('voice', '').strip()
    generate_audio = request.form.get('generate_audio', 'false').lower() == 'true'
    
    # Validate input
    is_valid, error_message = validate_tutorial_input(topic, expertise, duration)
    if not is_valid:
        return jsonify({'success': False, 'error': error_message}), 400
    
    # Set reasonable maximum duration
    max_duration = min(duration, 60)
    
    try:
        # Get user preferences for better content generation
        user_preferences = {
            'focus_areas': request.form.getlist('focus_areas'),
            'learning_style': request.form.get('learning_style', ''),
            'industry_context': request.form.get('industry_context', '')
        }
        
        # Generate tutorial content via OpenRouter
        tutorial_data = openrouter_service.generate_tutorial_content(
            topic=topic,
            expertise=expertise,
            duration=max_duration,
            text_model=text_model or None,
            user_preferences=user_preferences
        )
        
        # Save tutorial to database
        tutorial = Tutorial(
            user_id=current_user.id,
            topic=topic,
            expertise=expertise,
            duration=max_duration,
            content=tutorial_data['content'],
            is_premium=True,  # Everyone gets premium content
            status='completed'
        )
        
        # Set JSON fields
        tutorial.set_concepts(tutorial_data['concepts'])
        tutorial.set_packages(tutorial_data['packages'])
        tutorial.set_learning_objectives(tutorial_data['objectives'])
        
        db.session.add(tutorial)
        db.session.commit()
        
        # Generate audio if requested
        audio_data = None
        if generate_audio and tutorial_data['content']:
            audio_result = openrouter_service.generate_audio(
                text=tutorial_data['content'],
                audio_model=audio_model or None,
                voice=voice or None,
                speed=1.0,
                format='mp3'
            )
            
            if audio_result['success']:
                tutorial.audio_url = audio_result['audio_url']
                tutorial.audio_duration = int(audio_result.get('duration_estimate', max_duration * 60))
                db.session.commit()
                audio_data = audio_result
        
        # Get updated usage count
        monthly_usage = current_user.get_monthly_usage()
        
        response_data = {
            'success': True,
            'tutorial_id': tutorial.id,
            'content': tutorial_data['content'],
            'concepts': tutorial_data['concepts'],
            'packages': tutorial_data['packages'],
            'objectives': tutorial_data['objectives'],
            'is_premium': True,
            'topic': topic,
            'expertise': expertise,
            'duration': max_duration,
            'estimated_reading_time': tutorial_data.get('estimated_reading_time', 5),
            'difficulty_score': tutorial_data.get('difficulty_score', 5),
            'monthly_usage_after': monthly_usage,
            'monthly_limit': 999,
            'model_used': tutorial_data.get('model_used', 'unknown'),
            'generated_via': tutorial_data.get('generated_via', 'openrouter'),
            'character_count': tutorial_data.get('character_count', 0),
            'word_count': tutorial_data.get('word_count', 0)
        }
        
        # Add audio data if generated
        if audio_data:
            response_data.update({
                'audio_generated': True,
                'audio_url': audio_data['audio_url'],
                'audio_model_used': audio_data.get('model_used', 'unknown'),
                'audio_voice_used': audio_data.get('voice_used', 'default'),
                'audio_duration': audio_data.get('duration_estimate', 0),
                'audio_character_count': audio_data.get('character_count', 0)
            })
        else:
            response_data['audio_generated'] = False
        
        return jsonify(response_data)
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Tutorial generation failed. Please try again.',
            'error_details': str(e)
        }), 500

@main_bp.route('/generate-audio/<int:tutorial_id>', methods=['POST'])
@login_required
def generate_audio(tutorial_id):
    """Generate audio for an existing tutorial"""
    tutorial = Tutorial.query.get_or_404(tutorial_id)
    
    # Check ownership
    if tutorial.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    try:
        # Get audio generation parameters
        audio_model = request.form.get('audio_model', '').strip()
        voice = request.form.get('voice', '').strip()
        speed = float(request.form.get('speed', 1.0))
        
        # Generate audio
        audio_result = openrouter_service.generate_audio(
            text=tutorial.content,
            audio_model=audio_model or None,
            voice=voice or None,
            speed=speed,
            format='mp3'
        )
        
        if audio_result['success']:
            # Update tutorial with audio information
            tutorial.audio_url = audio_result['audio_url']
            tutorial.audio_duration = int(audio_result.get('duration_estimate', tutorial.duration * 60))
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Audio generated successfully!',
                'audio_url': audio_result['audio_url'],
                'audio_duration': audio_result.get('duration_estimate', 0),
                'model_used': audio_result.get('model_used', 'unknown'),
                'voice_used': audio_result.get('voice_used', 'default')
            })
        else:
            return jsonify({
                'success': False,
                'error': audio_result.get('error', 'Audio generation failed')
            })
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== API ROUTES ====================

@api_bp.route('/models/text')
@login_required
def get_text_models():
    """Get available text generation models"""
    models = openrouter_service.get_available_models('text')
    return jsonify({
        'success': True,
        'models': models,
        'current_model': openrouter_service.default_text_model,
        'model_configs': MODEL_CONFIGS
    })

@api_bp.route('/models/audio')
@login_required
def get_audio_models():
    """Get available audio generation models"""
    models = openrouter_service.get_available_models('audio')
    return jsonify({
        'success': True,
        'models': models,
        'current_model': openrouter_service.default_audio_model,
        'model_configs': AUDIO_MODEL_CONFIGS
    })

@api_bp.route('/openrouter/status')
@login_required
def openrouter_status():
    """Get OpenRouter connection status"""
    status = openrouter_service.get_model_status()
    return jsonify(status)

@api_bp.route('/usage-stats')
@login_required
def usage_stats():
    """Get user usage statistics"""
    monthly_usage = current_user.get_monthly_usage()
    plan_info = current_user.get_plan_info()
    
    # Get recent tutorials
    recent_tutorials = Tutorial.query.filter_by(user_id=current_user.id)\
        .order_by(Tutorial.created_at.desc()).limit(5).all()
    
    return jsonify({
        'monthly_usage': monthly_usage,
        'monthly_limit': 999,
        'plan': 'free',
        'plan_info': plan_info,
        'recent_tutorials': [
            {
                'id': t.id,
                'topic': t.topic,
                'expertise': t.expertise,
                'created_at': t.created_at.isoformat(),
                'is_premium': True,
                'view_count': t.view_count,
                'has_audio': bool(t.audio_url),
                'model_used': getattr(t, 'model_used', 'unknown')
            } for t in recent_tutorials
        ],
        'can_create_tutorial': True,
        'openrouter_enabled': bool(openrouter_service.api_key)
    })

@api_bp.route('/tutorials')
@login_required
def list_tutorials():
    """List user's tutorials with pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 50)
    
    tutorials = Tutorial.query.filter_by(user_id=current_user.id)\
        .order_by(Tutorial.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'tutorials': [tutorial.to_dict() for tutorial in tutorials.items],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': tutorials.total,
            'pages': tutorials.pages,
            'has_next': tutorials.has_next,
            'has_prev': tutorials.has_prev
        }
    })

@api_bp.route('/tutorial/<int:tutorial_id>')
@login_required
def get_tutorial(tutorial_id):
    """Get a specific tutorial"""
    tutorial = Tutorial.query.get_or_404(tutorial_id)
    
    # Check ownership
    if tutorial.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    return jsonify(tutorial.to_dict())

@api_bp.route('/tutorial/<int:tutorial_id>', methods=['DELETE'])
@login_required
def delete_tutorial(tutorial_id):
    """Delete a tutorial"""
    tutorial = Tutorial.query.get_or_404(tutorial_id)
    
    # Check ownership
    if tutorial.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        db.session.delete(tutorial)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Tutorial deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Delete failed'}), 500

@api_bp.route('/tutorial/<int:tutorial_id>/view', methods=['POST'])
@login_required
def track_tutorial_view(tutorial_id):
    """Track tutorial view"""
    tutorial = Tutorial.query.get_or_404(tutorial_id)
    
    # Check ownership
    if tutorial.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        tutorial.view_count = (tutorial.view_count or 0) + 1
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== SYSTEM ROUTES ====================

@main_bp.route('/health')
def health_check():
    """System health check including OpenRouter status"""
    health_status = check_system_health()
    
    # Add OpenRouter status
    openrouter_status = openrouter_service.get_model_status()
    health_status['openrouter'] = {
        'status': openrouter_status['status'],
        'api_key_configured': bool(openrouter_service.api_key),
        'models_available': openrouter_status.get('model_count', 0)
    }
    
    status_code = 200
    if health_status['status'] == 'unhealthy':
        status_code = 503
    elif health_status['status'] == 'warning':
        status_code = 200
    
    return jsonify(health_status), status_code

@main_bp.route('/version')
def version_info():
    """API version information"""
    return jsonify({
        'version': '2.0.0',
        'api_version': 'v2',
        'features': {
            'openrouter_integration': True,
            'ai_generation': True,
            'audio_generation': True,
            'model_selection': True,
            'unlimited_tutorials': True,
            'advanced_topics': True
        },
        'openrouter': {
            'enabled': bool(openrouter_service.api_key),
            'base_url': openrouter_service.base_url,
            'default_text_model': openrouter_service.default_text_model,
            'default_audio_model': openrouter_service.default_audio_model
        },
        'limits': PLANS
    })

# ==================== ERROR HANDLERS ====================

@main_bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Resource not found'}), 404
    return render_template('error.html', error_code=404, error_message='Page not found'), 404

@main_bp.errorhandler(403)
def forbidden(error):
    """Handle 403 errors"""
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Access denied'}), 403
    return render_template('error.html', error_code=403, error_message='Access denied'), 403

@main_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    db.session.rollback()
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Internal server error'}), 500
    return render_template('error.html', error_code=500, error_message='Internal server error'), 500

@main_bp.errorhandler(429)
def rate_limit_exceeded(error):
    """Handle rate limit errors"""
    return jsonify({
        'error': 'Rate limit exceeded',
        'message': 'Too many requests. Please try again later.',
        'retry_after': 60
    }), 429