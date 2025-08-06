# config.py - Centralized configuration
import os
from datetime import timedelta

class Config:
    """Base configuration with OpenRouter support"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production-r-tutor-pro'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=31)
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # OpenRouter API Configuration
    OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY', '')
    OPENROUTER_BASE_URL = 'https://openrouter.ai/api/v1'
    OPENROUTER_SITE_URL = os.environ.get('OPENROUTER_SITE_URL', 'http://localhost:5000')
    OPENROUTER_SITE_NAME = os.environ.get('OPENROUTER_SITE_NAME', 'R Tutor Pro')
    
    # Default model settings
    DEFAULT_TEXT_MODEL = os.environ.get('OPENROUTER_TEXT_MODEL', 'anthropic/claude-3.5-sonnet')
    DEFAULT_AUDIO_MODEL = os.environ.get('OPENROUTER_AUDIO_MODEL', 'openai/tts-1')
    
    # Available models for selection
    AVAILABLE_TEXT_MODELS = [
        'anthropic/claude-3.5-sonnet',
        'anthropic/claude-3-haiku',
        'openai/gpt-4-turbo',
        'openai/gpt-3.5-turbo',
        'meta-llama/llama-3.1-8b-instruct',
        'google/gemini-pro',
        'mistralai/mistral-7b-instruct'
    ]
    
    AVAILABLE_AUDIO_MODELS = [
        'openai/tts-1',
        'openai/tts-1-hd',
        'elevenlabs/eleven-multilingual-v2'
    ]
    
    # Audio configuration
    AUDIO_OUTPUT_FORMAT = 'mp3'
    AUDIO_VOICE = os.environ.get('OPENROUTER_VOICE', 'alloy')
    AUDIO_SPEED = float(os.environ.get('OPENROUTER_AUDIO_SPEED', '1.0'))
    
    # File Upload Configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'generated_audio')
    
    # Rate Limiting
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL', 'memory://')
    
    # Application Settings
    ITEMS_PER_PAGE = 10
    MAX_TUTORIAL_DURATION = 60
    MIN_TUTORIAL_DURATION = 1

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///r_tutor_dev.db'
    SESSION_COOKIE_SECURE = False
    SQLALCHEMY_ECHO = False
    WTF_CSRF_ENABLED = False
    RATELIMIT_ENABLED = False

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
    RATELIMIT_ENABLED = False
    BCRYPT_LOG_ROUNDS = 4

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///r_tutor_prod.db'
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
    RATELIMIT_ENABLED = True

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# Plans Configuration
PLANS = {
    'free': {
        'tutorials_per_month': 999,
        'price': 0,
        'stripe_price_id': None,
        'features': [
            'Unlimited R tutorials via OpenRouter',
            'AI-generated content with model selection',
            'High-quality audio generation',
            'All R topics and expertise levels',
            'Model customization options',
            'Audio voice selection',
            'Export options'
        ],
        'limits': {
            'max_duration': 60,
            'audio_generation': True,
            'model_selection': True,
            'custom_voices': True,
            'api_access': True,
            'export_options': True
        }
    }
}

# Model Configurations
MODEL_CONFIGS = {
    'anthropic/claude-3.5-sonnet': {
        'name': 'Claude 3.5 Sonnet',
        'description': 'High-quality, balanced model for detailed R tutorials',
        'max_tokens': 4096,
        'temperature': 0.7,
        'cost_per_token': 0.000003
    },
    'anthropic/claude-3-haiku': {
        'name': 'Claude 3 Haiku',
        'description': 'Fast, efficient model for quick R explanations',
        'max_tokens': 4096,
        'temperature': 0.7,
        'cost_per_token': 0.00000025
    },
    'openai/gpt-4-turbo': {
        'name': 'GPT-4 Turbo',
        'description': 'Advanced model with excellent R programming knowledge',
        'max_tokens': 4096,
        'temperature': 0.7,
        'cost_per_token': 0.00001
    },
    'openai/gpt-3.5-turbo': {
        'name': 'GPT-3.5 Turbo',
        'description': 'Cost-effective model for standard R tutorials',
        'max_tokens': 4096,
        'temperature': 0.7,
        'cost_per_token': 0.0000005
    }
}

AUDIO_MODEL_CONFIGS = {
    'openai/tts-1': {
        'name': 'OpenAI TTS Standard',
        'description': 'High-quality text-to-speech',
        'voices': ['alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer'],
        'formats': ['mp3', 'opus', 'aac', 'flac'],
        'cost_per_character': 0.000015
    },
    'openai/tts-1-hd': {
        'name': 'OpenAI TTS HD',
        'description': 'Premium quality text-to-speech',
        'voices': ['alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer'],
        'formats': ['mp3', 'opus', 'aac', 'flac'],
        'cost_per_character': 0.00003
    }
}