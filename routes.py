from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

from models import db, User, Tutorial, UsageLog
from ai_services import ai_generator
from utils import (
    track_usage, check_usage_limits, require_plan, rate_limit,
    validate_tutorial_input, sanitize_input, validate_email,
    calculate_usage_analytics, check_system_health
)
from config import PLANS

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
        
        user_stats = {
            'total_tutorials': total_tutorials,
            'monthly_usage': monthly_usage,
            'monthly_limit': PLANS[current_user.plan]['tutorials_per_month'],
            'plan': current_user.plan,
            'can_create_tutorial': current_user.can_create_tutorial()
        }
        
        return render_template('dashboard.html', stats=user_stats, plans=PLANS)
    
    # Landing page for non-authenticated users
    return render_template('landing.html', plans=PLANS)

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    return redirect(url_for('main.index'))

@main_bp.route('/pricing')
def pricing():
    """Pricing page"""
    return render_template('pricing.html', plans=PLANS)

@main_bp.route('/tutorial/<int:tutorial_id>')
@login_required
def view_tutorial(tutorial_id):
    """View a specific tutorial"""
    tutorial = Tutorial.query.get_or_404(tutorial_id)
    
    # Check if user owns this tutorial or has team access
    if tutorial.user_id != current_user.id:
        # Add team access logic here if needed
        return jsonify({'error': 'Access denied'}), 403
    
    # Track tutorial view
    tutorial.increment_view()
    
    return render_template('tutorial.html', tutorial=tutorial)

# ==================== AUTHENTICATION ROUTES ====================

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        # Get form data
        email = request.form.get('email', '').lower().strip()
        password = request.form.get('password', '')
        name = request.form.get('name', '').strip()
        
        # Validate input
        if not validate_email(email):
            return jsonify({'success': False, 'error': 'Invalid email address'})
        
        if len(password) < 6:
            return jsonify({'success': False, 'error': 'Password must be at least 6 characters'})
        
        if len(name) < 2:
            return jsonify({'success': False, 'error': 'Name must be at least 2 characters'})
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            return jsonify({'success': False, 'error': 'Email already registered'})
        
        # Create new user
        user = User(
            email=email,
            name=sanitize_input(name, 100),
            plan='free'
        )
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            
            # Log the user in
            login_user(user)
            
            # Track registration
            UsageLog.log_action(
                user_id=user.id,
                action='user_registered',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            
            return jsonify({
                'success': True,
                'message': 'Account created successfully!',
                'redirect': url_for('main.index')
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': 'Registration failed. Please try again.'})
    
    return render_template('auth.html', mode='register')

@auth_bp.route('/login', methods=['GET', 'POST'])
@rate_limit(requests_per_minute=10)  # Prevent brute force attacks
def login():
    """User login"""
    if request.method == 'POST':
        email = request.form.get('email', '').lower().strip()
        password = request.form.get('password', '')
        remember_me = request.form.get('remember_me', False)
        
        if not email or not password:
            return jsonify({'success': False, 'error': 'Email and password required'})
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password) and user.is_active:
            login_user(user, remember=bool(remember_me))
            
            # Track login
            UsageLog.log_action(
                user_id=user.id,
                action='user_login',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            
            # Redirect to intended page or dashboard
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('main.index')
            
            return jsonify({
                'success': True,
                'message': 'Login successful!',
                'redirect': next_page
            })
        else:
            # Log failed login attempt
            if user:
                UsageLog.log_action(
                    user_id=user.id,
                    action='login_failed',
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent')
                )
            
            return jsonify({'success': False, 'error': 'Invalid email or password'})
    
    return render_template('auth.html', mode='login')

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    UsageLog.log_action(
        user_id=current_user.id,
        action='user_logout',
        ip_address=request.remote_addr
    )
    
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('main.index'))

# ==================== TUTORIAL GENERATION ROUTES ====================

@main_bp.route('/generate-tutorial', methods=['POST'])
@login_required
@rate_limit(requests_per_minute=10)
@track_usage('tutorial_created')
def generate_tutorial():
    """Generate a new tutorial"""
    
    # Check usage limits
    over_limit, current_usage, limit = check_usage_limits()
    if over_limit:
        return jsonify({
            'success': False,
            'error': f'Monthly limit reached ({current_usage}/{limit}). Please upgrade your plan.',
            'upgrade_required': True,
            'current_plan': current_user.plan
        }), 403
    
    # Get and validate input
    topic = sanitize_input(request.form.get('topic', ''), 200)
    expertise = request.form.get('expertise', '').strip()
    duration = request.form.get('duration', type=int)
    
    # Validate input
    is_valid, error_message = validate_tutorial_input(topic, expertise, duration)
    if not is_valid:
        return jsonify({'success': False, 'error': error_message}), 400
    
    # Check plan limitations
    if current_user.plan == 'free' and duration > 5:
        duration = 5  # Limit free users
    
    try:
        # Generate tutorial content
        tutorial_data = ai_generator.generate_tutorial_content(
            topic=topic,
            expertise=expertise,
            duration=duration,
            user_plan=current_user.plan
        )
        
        # Save tutorial to database
        tutorial = Tutorial(
            user_id=current_user.id,
            topic=topic,
            expertise=expertise,
            duration=duration,
            content=tutorial_data['content'],
            is_premium=tutorial_data['is_premium'],
            status='completed'
        )
        
        # Set JSON fields
        tutorial.set_concepts(tutorial_data['concepts'])
        tutorial.set_packages(tutorial_data['packages'])
        tutorial.set_learning_objectives(tutorial_data['objectives'])
        
        db.session.add(tutorial)
        db.session.commit()
        
        # Prepare response
        response_data = {
            'success': True,
            'tutorial_id': tutorial.id,
            'content': tutorial_data['content'],
            'concepts': tutorial_data['concepts'],
            'packages': tutorial_data['packages'],
            'objectives': tutorial_data['objectives'],
            'is_premium': tutorial_data['is_premium'],
            'topic': topic,
            'expertise': expertise,
            'duration': duration,
            'estimated_reading_time': tutorial_data.get('estimated_reading_time', 5),
            'difficulty_score': tutorial_data.get('difficulty_score', 5),
            'monthly_usage_after': current_usage + 1,
            'monthly_limit': limit
        }
        
        # Add upgrade prompt for free users approaching limit
        if current_user.plan == 'free' and current_usage + 1 >= limit - 1:
            response_data['upgrade_prompt'] = {
                'message': 'You\'re almost at your monthly limit! Upgrade to Pro for unlimited tutorials.',
                'cta': 'Upgrade Now'
            }
        
        return jsonify(response_data)
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Tutorial generation failed. Please try again.',
            'error_details': str(e) if current_user.plan != 'free' else None
        }), 500

@main_bp.route('/tutorial/<int:tutorial_id>/regenerate', methods=['POST'])
@login_required
@require_plan('pro')
def regenerate_tutorial(tutorial_id):
    """Regenerate a tutorial (Pro feature)"""
    tutorial = Tutorial.query.get_or_404(tutorial_id)
    
    # Check ownership
    if tutorial.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    try:
        # Regenerate content
        tutorial_data = ai_generator.generate_tutorial_content(
            topic=tutorial.topic,
            expertise=tutorial.expertise,
            duration=tutorial.duration,
            user_plan=current_user.plan
        )
        
        # Update tutorial
        tutorial.content = tutorial_data['content']
        tutorial.set_concepts(tutorial_data['concepts'])
        tutorial.set_packages(tutorial_data['packages'])
        tutorial.set_learning_objectives(tutorial_data['objectives'])
        tutorial.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Tutorial regenerated successfully!',
            'content': tutorial_data['content']
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Regeneration failed'}), 500

# ==================== SUBSCRIPTION MANAGEMENT ====================

@main_bp.route('/upgrade/<plan>')
@login_required
def upgrade_plan(plan):
    """Upgrade user plan (simplified for MVP)"""
    if plan not in PLANS:
        return jsonify({'success': False, 'error': 'Invalid plan'}), 400
    
    # In production, this would integrate with Stripe
    # For MVP, we'll update the plan directly
    old_plan = current_user.plan
    current_user.plan = plan
    current_user.updated_at = datetime.utcnow()
    
    try:
        db.session.commit()
        
        # Track upgrade
        UsageLog.log_action(
            user_id=current_user.id,
            action='plan_upgraded',
            metadata={
                'old_plan': old_plan,
                'new_plan': plan,
                'upgrade_timestamp': datetime.utcnow().isoformat()
            }
        )
        
        return jsonify({
            'success': True,
            'message': f'Successfully upgraded to {plan.title()} plan!',
            'new_plan': plan,
            'redirect': url_for('main.index')
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Upgrade failed'}), 500

@main_bp.route('/billing')
@login_required
def billing():
    """Billing and subscription management"""
    user_analytics = calculate_usage_analytics(current_user.id)
    
    return render_template('billing.html', 
                         user=current_user, 
                         plans=PLANS,
                         analytics=user_analytics)

# ==================== API ROUTES ====================

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
        'monthly_limit': plan_info['tutorials_per_month'],
        'plan': current_user.plan,
        'plan_info': plan_info,
        'recent_tutorials': [
            {
                'id': t.id,
                'topic': t.topic,
                'expertise': t.expertise,
                'created_at': t.created_at.isoformat(),
                'is_premium': t.is_premium,
                'view_count': t.view_count
            } for t in recent_tutorials
        ],
        'can_create_tutorial': current_user.can_create_tutorial()
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

@api_bp.route('/analytics')
@login_required
def user_analytics():
    """Get detailed user analytics"""
    days = request.args.get('days', 30, type=int)
    analytics = calculate_usage_analytics(current_user.id, days)
    
    return jsonify(analytics)

@api_bp.route('/search-tutorials')
@login_required
def search_tutorials():
    """Search user's tutorials"""
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'tutorials': []})
    
    tutorials = Tutorial.query.filter(
        Tutorial.user_id == current_user.id,
        Tutorial.topic.contains(query)
    ).order_by(Tutorial.created_at.desc()).limit(20).all()
    
    return jsonify({
        'tutorials': [tutorial.to_dict() for tutorial in tutorials],
        'query': query
    })

# ==================== ADMIN ROUTES (Team Plan) ====================

@api_bp.route('/admin/users')
@login_required
@require_plan('team')
def admin_list_users():
    """List all users (team admin only)"""
    # This would include team management logic
    # For now, just return current user
    return jsonify({
        'users': [current_user.to_dict()],
        'message': 'Team management features coming soon!'
    })

# ==================== SYSTEM ROUTES ====================

@main_bp.route('/health')
def health_check():
    """System health check"""
    health_status = check_system_health()
    
    status_code = 200
    if health_status['status'] == 'unhealthy':
        status_code = 503
    elif health_status['status'] == 'warning':
        status_code = 200  # Still operational
    
    return jsonify(health_status), status_code

@main_bp.route('/version')
def version_info():
    """API version information"""
    return jsonify({
        'version': '1.0.0',
        'api_version': 'v1',
        'features': {
            'ai_generation': True,
            'audio_generation': False,  # Coming soon
            'team_management': False,   # Coming soon
            'api_access': True
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

# ==================== UTILITY ROUTES ====================

@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact form"""
    if request.method == 'POST':
        # Handle contact form submission
        name = sanitize_input(request.form.get('name', ''), 100)
        email = request.form.get('email', '').strip()
        message = sanitize_input(request.form.get('message', ''), 1000)
        
        if not validate_email(email):
            flash('Invalid email address', 'error')
            return render_template('contact.html')
        
        # In production, send email or save to database
        flash('Thank you for your message! We\'ll get back to you soon.', 'success')
        return redirect(url_for('main.contact'))
    
    return render_template('contact.html')

@main_bp.route('/privacy')
def privacy_policy():
    """Privacy policy page"""
    return render_template('privacy.html')

@main_bp.route('/terms')
def terms_of_service():
    """Terms of service page"""
    return render_template('terms.html')

@main_bp.route('/export-data')
@login_required
def export_user_data():
    """Export user data (GDPR compliance)"""
    from utils import export_user_data
    
    user_data = export_user_data(current_user.id)
    
    return jsonify({
        'success': True,
        'data': user_data,
        'export_date': datetime.now().isoformat(),
        'note': 'This export contains all your data stored in R Tutor Pro.'
    })

# ==================== WEBHOOK ROUTES (for Stripe integration) ====================

@main_bp.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhooks"""
    # This would handle Stripe payment events
    # For MVP, just return success
    return jsonify({'success': True})

# ==================== DEVELOPMENT/DEBUG ROUTES ====================

@main_bp.route('/debug/user-info')
@login_required
def debug_user_info():
    """Debug endpoint to show user information"""
    from flask import current_app
    
    if not current_app.debug:
        return jsonify({'error': 'Debug mode only'}), 403
    
    return jsonify({
        'user': current_user.to_dict(),
        'session_info': {
            'is_authenticated': current_user.is_authenticated,
            'plan': current_user.plan,
            'monthly_usage': current_user.get_monthly_usage()
        }
    })