# utils.py - Modified to remove premium restrictions
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
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def track_usage(action: str, resource_type: str = None, resource_id: int = None):
    """
    Decorator to track user actions for analytics
    
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
                        'user_plan': 'premium',  # Everyone gets premium treatment
                        'full_access': True
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
    Check if user has exceeded their plan limits - DISABLED (no limits)
    
    Args:
        action: Action to check limits for
        
    Returns:
        tuple: (is_over_limit, current_usage, limit) - always returns unlimited access
    """
    if not current_user.is_authenticated:
        return False, 0, 999  # Allow anonymous users too
    
    # Get current month usage for statistics only
    start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    current_usage = UsageLog.query.filter(
        UsageLog.user_id == current_user.id,
        UsageLog.action == action,
        UsageLog.created_at >= start_of_month
    ).count()
    
    # No limits - everyone has unlimited access
    return False, current_usage, 999

def require_plan(required_plan: str):
    """
    Decorator to require specific subscription plan - DISABLED (no restrictions)
    
    Args:
        required_plan: Plan requirement (ignored)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({'success': False, 'error': 'Authentication required'}), 401
            
            # Everyone has access to all features now
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def rate_limit(requests_per_minute: int = 60):
    """
    Rate limiting decorator - Generous limits for all users
    
    Args:
        requests_per_minute: Maximum requests per minute (generous default)
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
            
            # Check current usage - very generous limits
            client_requests = [
                v for k, v in current_app.rate_limit_storage.items()
                if k.startswith(client_id)
            ]
            
            # Generous rate limiting - unlikely to be hit in normal usage
            if len(client_requests) >= requests_per_minute * 2:  # Double the limit
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

def validate_email(email: str):
    """
    Very permissive email validation for demo purposes
    Only checks for basic @ symbol and domain structure
    """
    if not email or len(email.strip()) == 0:
        return False
    
    email = email.strip().lower()
    
    # Very basic check - just needs @ and at least one dot after @
    if '@' not in email:
        return False
    
    parts = email.split('@')
    if len(parts) != 2:
        return False
    
    local_part, domain_part = parts
    
    # Local part should not be empty
    if len(local_part) == 0:
        return False
    
    # Domain should have at least one dot and not be empty
    if len(domain_part) == 0 or '.' not in domain_part:
        return False
    
    # Allow all common formats for maximum accessibility
    return True

def is_valid_email_format(email: str):
    """
    Alternative email validation function with same logic as validate_email
    for consistency across the application
    """
    return validate_email(email)

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

def validate_tutorial_input(topic: str, expertise: str, duration: int):
    """
    Validate tutorial input parameters - relaxed validation
    
    Args:
        topic: Tutorial topic
        expertise: Expertise level
        duration: Tutorial duration in minutes
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not topic or len(topic.strip()) < 2:  # More lenient
        return False, "Topic must be at least 2 characters long"
    
    if expertise not in ['beginner', 'intermediate', 'expert']:
        return False, "Invalid expertise level. Must be 'beginner', 'intermediate', or 'expert'"
    
    if not isinstance(duration, int) or duration < 1 or duration > 60:
        return False, "Duration must be between 1 and 60 minutes"
    
    # Additional validation for topic content - very permissive
    if len(topic.strip()) > 300:  # Increased limit
        return False, "Topic must be less than 300 characters"
    
    # Check for suspicious content - minimal restrictions
    suspicious_patterns = ['<script', 'javascript:']  # Reduced list
    topic_lower = topic.lower()
    if any(pattern in topic_lower for pattern in suspicious_patterns):
        return False, "Topic contains invalid characters"
    
    return True, None

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
    
    # Calculate comprehensive analytics
    analytics = {
        'total_actions': len(usage_logs),
        'total_tutorials': len(tutorials),
        'unique_topics': len(set(t.topic for t in tutorials)),
        'average_duration': sum(t.duration for t in tutorials) / len(tutorials) if tutorials else 0,
        'expertise_distribution': {},
        'topic_categories': {},
        'daily_usage': {},
        'most_active_day': None,
        'most_popular_topic': None,
        'advanced_features_used': len(tutorials),  # All tutorials are now advanced
        'total_learning_time': sum(t.duration for t in tutorials),
        'topics_mastered': len(set(t.topic for t in tutorials)),
        'skill_progression': 'Advancing'  # Everyone is progressing!
    }
    
    # Expertise distribution
    for tutorial in tutorials:
        expertise = tutorial.expertise
        analytics['expertise_distribution'][expertise] = analytics['expertise_distribution'].get(expertise, 0) + 1
    
    # Daily usage patterns
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
        'user_info': {
            'id': user.id,
            'email': user.email,
            'name': user.name,
            'plan': 'premium',  # Everyone effectively has premium
            'created_at': user.created_at.isoformat(),
            'is_active': user.is_active,
            'features_access': 'full'
        },
        'tutorials': [
            {
                'id': t.id,
                'topic': t.topic,
                'expertise': t.expertise,
                'duration': t.duration,
                'created_at': t.created_at.isoformat(),
                'is_premium': True,  # All content is premium quality
                'view_count': getattr(t, 'view_count', 0),
                'concepts': t.get_concepts(),
                'packages': t.get_packages(),
                'objectives': t.get_learning_objectives()
            } for t in tutorials
        ],
        'usage_logs': [
            {
                'id': log.id,
                'action': log.action,
                'created_at': log.created_at.isoformat(),
                'metadata': log.metadata
            } for log in usage_logs
        ],
        'analytics': calculate_usage_analytics(user_id),
        'export_note': 'All features and content were available during your learning journey.'
    }
    
    return export_data

def check_system_health():
    """
    Check system health status
    
    Returns:
        Dictionary with health status
    """
    health_status = {
        'status': 'healthy',
        'checks': {
            'database': 'unknown',
            'ai_services': 'unknown',
            'file_system': 'unknown',
            'user_access': 'unlimited'
        },
        'timestamp': datetime.utcnow().isoformat(),
        'features_enabled': {
            'unlimited_tutorials': True,
            'advanced_topics': True,
            'ai_generation': True,
            'all_expertise_levels': True
        }
    }
    
    # Check database connection
    try:
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        health_status['checks']['database'] = 'healthy'
    except Exception as e:
        health_status['checks']['database'] = 'unhealthy'
        health_status['status'] = 'unhealthy'
        logger.error(f"Database health check failed: {e}")
    
    # Check AI services
    try:
        deepseek_key = os.environ.get('DEEPSEEK_API_KEY', '')
        openai_key = os.environ.get('OPENAI_API_KEY', '')
        
        if deepseek_key or openai_key:
            health_status['checks']['ai_services'] = 'healthy'
        else:
            health_status['checks']['ai_services'] = 'warning'
            if health_status['status'] == 'healthy':
                health_status['status'] = 'warning'
    except Exception as e:
        health_status['checks']['ai_services'] = 'degraded'
        logger.error(f"AI services health check failed: {e}")
    
    # Check file system (basic check)
    try:
        import tempfile
        with tempfile.NamedTemporaryFile(delete=True) as tmp_file:
            tmp_file.write(b'health check')
            tmp_file.flush()
        health_status['checks']['file_system'] = 'healthy'
    except Exception as e:
        health_status['checks']['file_system'] = 'unhealthy'
        health_status['status'] = 'unhealthy'
        logger.error(f"File system health check failed: {e}")
    
    return health_status

def create_demo_user(email: str, name: str = None):
    """
    Create a demo user with full access
    
    Args:
        email: User email
        name: User name (optional)
        
    Returns:
        User object or None if creation fails
    """
    try:
        from models import User
        from werkzeug.security import generate_password_hash
        
        # Validate email format first
        if not validate_email(email):
            return None
        
        user = User(
            email=email.lower().strip(),
            password_hash=generate_password_hash('s'),
            name=name or email.split('@')[0],
            plan='free',  # Free plan now has full access
            is_active=True,
            email_verified=True,  # Auto-verify for demo
            created_at=datetime.utcnow()
        )
        
        db.session.add(user)
        db.session.commit()
        
        logger.info(f"User created with full access: {email}")
        return user
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to create user {email}: {e}")
        return None

def get_feature_availability(user_plan: str = None):
    """
    Get feature availability for any user - ALL FEATURES AVAILABLE
    
    Args:
        user_plan: User's plan (ignored)
        
    Returns:
        Dictionary of available features
    """
    return {
        'unlimited_tutorials': True,
        'advanced_topics': True,
        'ai_generation': True,
        'machine_learning_topics': True,
        'shiny_development': True,
        'statistical_modeling': True,
        'data_visualization': True,
        'package_development': True,
        'all_expertise_levels': True,
        'regenerate_tutorials': True,
        'export_content': True,
        'share_tutorials': True,
        'analytics_dashboard': True,
        'custom_durations': True,
        'max_duration': 60,
        'troubleshooting_tips': True,
        'best_practices': True,
        'real_world_examples': True
    }

def check_feature_access(feature_name: str, user_plan: str = None):
    """
    Check if user has access to a specific feature - ALWAYS TRUE
    
    Args:
        feature_name: Name of the feature to check
        user_plan: User's plan (ignored)
        
    Returns:
        Boolean - always True
    """
    return True

def get_learning_recommendations(user_id: int):
    """
    Get personalized learning recommendations for user
    
    Args:
        user_id: User ID
        
    Returns:
        List of recommended topics and next steps
    """
    from models import Tutorial
    
    # Get user's tutorial history
    user_tutorials = Tutorial.query.filter_by(user_id=user_id).all()
    
    if not user_tutorials:
        # New user recommendations
        return [
            {
                'topic': 'R Data Structures',
                'expertise': 'beginner',
                'reason': 'Great starting point for R programming',
                'estimated_time': 15
            },
            {
                'topic': 'ggplot2 Visualization',
                'expertise': 'beginner',
                'reason': 'Learn to create beautiful data visualizations',
                'estimated_time': 20
            },
            {
                'topic': 'dplyr Data Manipulation',
                'expertise': 'beginner',
                'reason': 'Essential for working with data in R',
                'estimated_time': 25
            }
        ]
    
    # Analyze user's learning pattern
    topics_covered = set(t.topic.lower() for t in user_tutorials)
    expertise_levels = [t.expertise for t in user_tutorials]
    most_common_expertise = max(set(expertise_levels), key=expertise_levels.count) if expertise_levels else 'beginner'
    
    recommendations = []
    
    # Advanced recommendations based on progress
    if 'data structure' not in ' '.join(topics_covered):
        recommendations.append({
            'topic': 'Advanced Data Structures',
            'expertise': most_common_expertise,
            'reason': 'Build on your R foundation',
            'estimated_time': 30
        })
    
    if 'machine learning' not in ' '.join(topics_covered):
        recommendations.append({
            'topic': 'Machine Learning with tidymodels',
            'expertise': 'intermediate' if most_common_expertise == 'beginner' else most_common_expertise,
            'reason': 'Expand into predictive modeling',
            'estimated_time': 45
        })
    
    if 'shiny' not in ' '.join(topics_covered):
        recommendations.append({
            'topic': 'Interactive Shiny Applications',
            'expertise': 'intermediate' if most_common_expertise == 'beginner' else most_common_expertise,
            'reason': 'Create interactive web applications',
            'estimated_time': 40
        })
    
    return recommendations[:3]  # Return top 3 recommendations