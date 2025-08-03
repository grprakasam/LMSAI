import os
import secrets
import hashlib
import json
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from flask_login import current_user
from models import UsageLog, db
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def track_usage(action: str, resource_type: str = None, resource_id: int = None):
    """
    Decorator to track user actions for analytics and billing
    
    Args:
        action: Action being performed (e.g., 'tutorial_created', 'audio_generated')
        resource_type: Type of resource being accessed
        resource_id: ID of the resource
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.is_authenticated:
                try:
                    # Create usage log
                    log = UsageLog(
                        user_id=current_user.id,
                        action=action,
                        resource_type=resource_type,
                        resource_id=resource_id,
                        ip_address=get_client_ip(),
                        user_agent=request.headers.get('User-Agent', '')[:500]
                    )
                    
                    # Add request metadata
                    metadata = {
                        'endpoint': request.endpoint,
                        'method': request.method,
                        'user_plan': current_user.plan
                    }
                    
                    # Add additional context from kwargs if available
                    if 'tutorial_data' in kwargs:
                        metadata.update({
                            'topic': kwargs['tutorial_data'].get('topic'),
                            'expertise': kwargs['tutorial_data'].get('expertise'),
                            'duration': kwargs['tutorial_data'].get('duration')
                        })
                    
                    log.set_metadata(metadata)
                    
                    db.session.add(log)
                    db.session.commit()
                    
                except Exception as e:
                    logger.error(f"Failed to track usage: {e}")
                    # Don't fail the main function if logging fails
                    pass
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def check_usage_limits(action: str = 'tutorial_created'):
    """
    Check if user has exceeded their plan limits
    
    Args:
        action: Action to check limits for
        
    Returns:
        tuple: (is_over_limit, current_usage, limit)
    """
    if not current_user.is_authenticated:
        return True, 0, 0
    
    from config import PLANS
    
    # Get current month usage
    start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    current_usage = UsageLog.query.filter(
        UsageLog.user_id == current_user.id,
        UsageLog.action == action,
        UsageLog.created_at >= start_of_month
    ).count()
    
    plan_limit = PLANS[current_user.plan]['tutorials_per_month']
    is_over_limit = current_usage >= plan_limit
    
    return is_over_limit, current_usage, plan_limit

def require_plan(required_plan: str):
    """
    Decorator to require specific subscription plan
    
    Args:
        required_plan: Minimum plan required (free, pro, team)
    """
    plan_hierarchy = {'free': 0, 'pro': 1, 'team': 2}
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({'success': False, 'error': 'Authentication required'}), 401
            
            user_plan_level = plan_hierarchy.get(current_user.plan, 0)
            required_plan_level = plan_hierarchy.get(required_plan, 0)
            
            if user_plan_level < required_plan_level:
                return jsonify({
                    'success': False,
                    'error': f'{required_plan.title()} plan required for this feature',
                    'upgrade_required': True,
                    'current_plan': current_user.plan,
                    'required_plan': required_plan
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def rate_limit(requests_per_minute: int = 60):
    """
    Rate limiting decorator
    
    Args:
        requests_per_minute: Maximum requests per minute
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                client_id = get_client_ip()
            else:
                client_id = f"user_{current_user.id}"
            
            # Simple in-memory rate limiting (use Redis in production)
            if not hasattr(current_app, 'rate_limit_storage'):
                current_app.rate_limit_storage = {}
            
            now = datetime.now()
            window_start = now - timedelta(minutes=1)
            
            # Clean old entries
            current_app.rate_limit_storage = {
                k: v for k, v in current_app.rate_limit_storage.items()
                if v['timestamp'] > window_start
            }
            
            # Check current usage
            client_requests = [
                v for k, v in current_app.rate_limit_storage.items()
                if k.startswith(client_id)
            ]
            
            if len(client_requests) >= requests_per_minute:
                return jsonify({
                    'success': False,
                    'error': 'Rate limit exceeded. Please try again later.',
                    'retry_after': 60
                }), 429
            
            # Record this request
            request_key = f"{client_id}_{now.timestamp()}"
            current_app.rate_limit_storage[request_key] = {'timestamp': now}
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_client_ip():
    """Get client IP address, handling proxies"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr

def generate_api_key():
    """Generate a secure API key"""
    return secrets.token_urlsafe(32)

def hash_api_key(api_key: str):
    """Hash API key for secure storage"""
    return hashlib.sha256(api_key.encode()).hexdigest()

def validate_email(email: str):
    """Basic email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def sanitize_input(text: str, max_length: int = 1000):
    """Sanitize user input"""
    if not text:
        return ""
    
    # Remove any potentially harmful characters
    import html
    text = html.escape(text.strip())
    
    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length] + "..."
    
    return text

def format_duration(seconds: int):
    """Format duration in seconds to human-readable format"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        if remaining_seconds == 0:
            return f"{minutes}m"
        return f"{minutes}m {remaining_seconds}s"
    else:
        hours = seconds // 3600
        remaining_minutes = (seconds % 3600) // 60
        if remaining_minutes == 0:
            return f"{hours}h"
        return f"{hours}h {remaining_minutes}m"

def calculate_usage_analytics(user_id: int, days: int = 30):
    """
    Calculate usage analytics for a user
    
    Args:
        user_id: User ID
        days: Number of days to analyze
        
    Returns:
        Dictionary with analytics data
    """
    from models import UsageLog, Tutorial
    
    start_date = datetime.now() - timedelta(days=days)
    
    # Get usage logs
    usage_logs = UsageLog.query.filter(
        UsageLog.user_id == user_id,
        UsageLog.created_at >= start_date
    ).all()
    
    # Get tutorials
    tutorials = Tutorial.query.filter(
        Tutorial.user_id == user_id,
        Tutorial.created_at >= start_date
    ).all()
    
    # Calculate analytics
    analytics = {
        'total_actions': len(usage_logs),
        'total_tutorials': len(tutorials),
        'unique_topics': len(set(t.topic for t in tutorials)),
        'average_duration': sum(t.duration for t in tutorials) / len(tutorials) if tutorials else 0,
        'expertise_distribution': {},
        'topic_categories': {},
        'daily_usage': {},
        'most_active_day': None,
        'most_popular_topic': None
    }
    
    # Expertise distribution
    for tutorial in tutorials:
        expertise = tutorial.expertise
        analytics['expertise_distribution'][expertise] = analytics['expertise_distribution'].get(expertise, 0) + 1
    
    # Daily usage
    for log in usage_logs:
        date_key = log.created_at.strftime('%Y-%m-%d')
        analytics['daily_usage'][date_key] = analytics['daily_usage'].get(date_key, 0) + 1
    
    # Most active day
    if analytics['daily_usage']:
        analytics['most_active_day'] = max(analytics['daily_usage'], key=analytics['daily_usage'].get)
    
    # Most popular topic
    topic_counts = {}
    for tutorial in tutorials:
        topic_counts[tutorial.topic] = topic_counts.get(tutorial.topic, 0) + 1
    
    if topic_counts:
        analytics['most_popular_topic'] = max(topic_counts, key=topic_counts.get)
    
    return analytics

def export_user_data(user_id: int):
    """
    Export all user data for GDPR compliance
    
    Args:
        user_id: User ID
        
    Returns:
        Dictionary with all user data
    """
    from models import User, Tutorial, UsageLog
    
    user = User.query.get(user_id)
    if not user:
        return None
    
    # Get all user data
    tutorials = Tutorial.query.filter_by(user_id=user_id).all()
    usage_logs = UsageLog.query.filter_by(user_id=user_id).all()
    
    export_data = {
        'user_info': user.to_dict(),
        'tutorials': [tutorial.to_dict() for tutorial in tutorials],
        'usage_logs': [log.to_dict() for log in usage_logs]
    }
    
    return export_data

def validate_tutorial_input(topic: str, expertise: str, duration: int):
    """
    Validate tutorial input parameters
    
    Args:
        topic: Tutorial topic
        expertise: Expertise level
        duration: Tutorial duration in minutes
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not topic or len(topic.strip()) < 3:
        return False, "Topic must be at least 3 characters long"
    
    if expertise not in ['beginner', 'intermediate', 'expert']:
        return False, "Invalid expertise level"
    
    if not isinstance(duration, int) or duration < 1 or duration > 60:
        return False, "Duration must be between 1 and 60 minutes"
    
    return True, None

def check_system_health():
    """
    Check system health status
    
    Returns:
        Dictionary with health status
    """
    from config import PLANS
    from flask import current_app
    
    health_status = {
        'status': 'healthy',
        'checks': {
            'database': 'unknown',
            'ai_services': 'unknown',
            'file_system': 'unknown'
        },
        'timestamp': datetime.utcnow().isoformat()
    }
    
    # Check database connection
    try:
        db.session.query('1').from_statement(db.text('SELECT 1')).all()
        health_status['checks']['database'] = 'healthy'
    except Exception as e:
        health_status['checks']['database'] = 'unhealthy'
        health_status['status'] = 'unhealthy'
        logger.error(f"Database health check failed: {e}")
    
    # Check AI services
    try:
        from aiservices import ai_generator
        if ai_generator.deepseek_key or ai_generator.openai_key:
            health_status['checks']['ai_services'] = 'healthy'
        else:
            health_status['checks']['ai_services'] = 'warning'
            if health_status['status'] == 'healthy':
                health_status['status'] = 'warning'
    except Exception as e:
        health_status['checks']['ai_services'] = 'unhealthy'
        health_status['status'] = 'unhealthy'
        logger.error(f"AI services health check failed: {e}")
    
    # Check file system (basic check)
    try:
        # Try to create and delete a temporary file
        temp_file = os.path.join(current_app.instance_path, 'health_check.tmp')
        with open(temp_file, 'w') as f:
            f.write('health check')
        os.remove(temp_file)
        health_status['checks']['file_system'] = 'healthy'
    except Exception as e:
        health_status['checks']['file_system'] = 'unhealthy'
        health_status['status'] = 'unhealthy'
        logger.error(f"File system health check failed: {e}")
    
    return health_status
