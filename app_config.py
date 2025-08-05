# app_config.py - Optimized application configuration
import os
import logging
from typing import Dict, Any

def configure_logging():
    """Configure application logging with optimized settings"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/app.log', mode='a') if os.path.exists('logs') else logging.NullHandler()
        ]
    )

def get_app_info() -> Dict[str, Any]:
    """Get application information for startup display"""
    openrouter_key = os.environ.get('OPENROUTER_API_KEY')
    
    return {
        'title': 'R Tutor Pro - OpenRouter AI Integration',
        'version': '2.0.0',
        'features': [
            'AI Features: OpenRouter integration for tutorial generation',
            'Audio: AI-powered audio generation via OpenRouter models',
            'Content: Unlimited AI-generated R programming tutorials',
            'Models: Configurable text and audio generation models'
        ],
        'config': {
            'openrouter_configured': bool(openrouter_key),
            'openrouter_key_preview': f"{openrouter_key[:8]}..." if openrouter_key else None,
            'database': os.environ.get('DATABASE_URL', 'sqlite:///r_tutor_dev.db'),
            'secret_key_secure': bool(os.environ.get('SECRET_KEY')) and 
                                os.environ.get('SECRET_KEY') != 'dev-secret-key-change-in-production-r-tutor-pro'
        },
        'instructions': [
            '1. Get OpenRouter API key from https://openrouter.ai/keys',
            '2. Set OPENROUTER_API_KEY environment variable', 
            '3. Choose models in the dashboard model selection',
            '4. Generate AI-powered R tutorials with audio!'
        ],
        'access_info': {
            'url': f"http://localhost:{os.environ.get('PORT', 5000)}",
            'login': 'Login with any email + password "s"'
        }
    }

def print_startup_info():
    """Print optimized startup information"""
    info = get_app_info()
    
    print(info['title'])
    print("=" * 60)
    
    for feature in info['features']:
        print(feature)
    
    print("=" * 60)
    
    # Configuration status
    config = info['config']
    if config['openrouter_configured']:
        print(f"[OK] OpenRouter API Key: Configured ({config['openrouter_key_preview']})")
    else:
        print("[WARN] OpenRouter API Key: Not configured (limited functionality)")
    
    print(f"Database: {config['database']}")
    
    if config['secret_key_secure']:
        print("[OK] Secret Key: Configured (secure)")
    else:
        print("[WARN] Secret Key: Using default (change for production)")
    
    print("=" * 60)
    print("Setup Instructions:")
    for instruction in info['instructions']:
        print(instruction)
    
    print("=" * 60)
    print(f"Access the app at: {info['access_info']['url']}")
    print(info['access_info']['login'])
    print("=" * 60)