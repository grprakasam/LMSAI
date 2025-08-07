# settings_manager.py - Manage user learning settings
import json
import os
from pathlib import Path
from flask_login import current_user
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SettingsManager:
    """Manage user settings for personalized learning experience"""
    
    DEFAULT_SETTINGS = {
        # Content Generation Settings
        'shortWordCount': 400,
        'mediumWordCount': 700,
        'lengthyWordCount': 1000,
        'minDuration': 2,
        'maxDuration': 60,
        'defaultDuration': 5,
        
        # Interactive Learning Settings
        'quizQuestions': 3,
        'quizDifficulty': 'adaptive',
        'quizTimeout': 60,
        'animationSlides': 5,
        'slideTransition': 3,
        'animationStyle': 'slide',
        
        # AI Model Settings
        'defaultTextModel': 'anthropic/claude-3.5-sonnet',
        'temperature': 0.7,
        'maxTokens': 4000,
        'audioModel': 'openai/tts-1',
        'audioVoice': 'alloy',
        'audioSpeed': 1.0,
        
        # Learning Preferences
        'topicSuggestions': [
            'Data Structures',
            'ggplot2 Visualization', 
            'Machine Learning',
            'Data Analysis',
            'Statistical Modeling',
            'Shiny Applications'
        ],
        'trackProgress': True,
        'saveHistory': True,
        'enableRecommendations': True,
        
        # Export & Sharing Settings
        'exportFormat': 'txt',
        
        # Advanced Settings (not shown in UI but configurable)
        'cacheResults': True,
        'autoSave': True,
        'sessionTimeout': 30,  # minutes
        'maxHistoryItems': 100,
        'enableAnalytics': True
    }
    
    @staticmethod
    def get_settings_file_path(user_id=None):
        """Get the path to user settings file"""
        if user_id is None and current_user.is_authenticated:
            user_id = current_user.id
        elif user_id is None:
            user_id = 'default'
        
        settings_dir = Path('data/user_settings')
        settings_dir.mkdir(parents=True, exist_ok=True)
        return settings_dir / f'user_{user_id}_settings.json'
    
    @classmethod
    def load_settings(cls, user_id=None):
        """Load user settings from file, return defaults if not found"""
        try:
            settings_file = cls.get_settings_file_path(user_id)
            
            if settings_file.exists():
                with open(settings_file, 'r', encoding='utf-8') as f:
                    user_settings = json.load(f)
                
                # Merge with defaults to ensure all keys exist
                settings = cls.DEFAULT_SETTINGS.copy()
                settings.update(user_settings)
                
                logger.info(f"Loaded settings for user {user_id or 'current'}")
                return settings
            else:
                logger.info(f"No settings file found for user {user_id or 'current'}, using defaults")
                return cls.DEFAULT_SETTINGS.copy()
                
        except Exception as e:
            logger.error(f"Error loading settings for user {user_id}: {e}")
            return cls.DEFAULT_SETTINGS.copy()
    
    @classmethod
    def save_settings(cls, settings, user_id=None):
        """Save user settings to file"""
        try:
            settings_file = cls.get_settings_file_path(user_id)
            
            # Add metadata
            settings_with_meta = settings.copy()
            settings_with_meta['_metadata'] = {
                'last_updated': datetime.now().isoformat(),
                'version': '1.0',
                'user_id': user_id or (current_user.id if current_user.is_authenticated else 'default')
            }
            
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings_with_meta, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved settings for user {user_id or 'current'}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving settings for user {user_id}: {e}")
            return False
    
    @classmethod
    def get_content_word_count(cls, content_length, user_id=None):
        """Get word count based on content length setting"""
        settings = cls.load_settings(user_id)
        
        word_count_map = {
            'short': settings.get('shortWordCount', cls.DEFAULT_SETTINGS['shortWordCount']),
            'medium': settings.get('mediumWordCount', cls.DEFAULT_SETTINGS['mediumWordCount']),
            'lengthy': settings.get('lengthyWordCount', cls.DEFAULT_SETTINGS['lengthyWordCount'])
        }
        
        return word_count_map.get(content_length, word_count_map['medium'])
    
    @classmethod
    def get_quiz_settings(cls, user_id=None):
        """Get quiz-specific settings"""
        settings = cls.load_settings(user_id)
        
        return {
            'questions': settings.get('quizQuestions', cls.DEFAULT_SETTINGS['quizQuestions']),
            'difficulty': settings.get('quizDifficulty', cls.DEFAULT_SETTINGS['quizDifficulty']),
            'timeout': settings.get('quizTimeout', cls.DEFAULT_SETTINGS['quizTimeout'])
        }
    
    @classmethod
    def get_animation_settings(cls, user_id=None):
        """Get animation-specific settings"""
        settings = cls.load_settings(user_id)
        
        return {
            'slides': settings.get('animationSlides', cls.DEFAULT_SETTINGS['animationSlides']),
            'transition_time': settings.get('slideTransition', cls.DEFAULT_SETTINGS['slideTransition']),
            'style': settings.get('animationStyle', cls.DEFAULT_SETTINGS['animationStyle'])
        }
    
    @classmethod
    def get_model_settings(cls, user_id=None):
        """Get AI model settings"""
        settings = cls.load_settings(user_id)
        
        return {
            'text_model': settings.get('defaultTextModel', cls.DEFAULT_SETTINGS['defaultTextModel']),
            'temperature': settings.get('temperature', cls.DEFAULT_SETTINGS['temperature']),
            'max_tokens': settings.get('maxTokens', cls.DEFAULT_SETTINGS['maxTokens']),
            'audio_model': settings.get('audioModel', cls.DEFAULT_SETTINGS['audioModel']),
            'audio_voice': settings.get('audioVoice', cls.DEFAULT_SETTINGS['audioVoice']),
            'audio_speed': settings.get('audioSpeed', cls.DEFAULT_SETTINGS['audioSpeed'])
        }
    
    @classmethod
    def get_topic_suggestions(cls, user_id=None):
        """Get user's topic suggestions"""
        settings = cls.load_settings(user_id)
        return settings.get('topicSuggestions', cls.DEFAULT_SETTINGS['topicSuggestions'])
    
    @classmethod
    def get_duration_limits(cls, user_id=None):
        """Get duration limits"""
        settings = cls.load_settings(user_id)
        
        return {
            'min': settings.get('minDuration', cls.DEFAULT_SETTINGS['minDuration']),
            'max': settings.get('maxDuration', cls.DEFAULT_SETTINGS['maxDuration']),
            'default': settings.get('defaultDuration', cls.DEFAULT_SETTINGS['defaultDuration'])
        }
    
    @classmethod
    def validate_settings(cls, settings):
        """Validate settings data"""
        errors = []
        
        # Validate word counts
        for key, min_val, max_val in [
            ('shortWordCount', 100, 800),
            ('mediumWordCount', 400, 1200),
            ('lengthyWordCount', 600, 2000)
        ]:
            if key in settings:
                try:
                    value = int(settings[key])
                    if not (min_val <= value <= max_val):
                        errors.append(f"{key} must be between {min_val} and {max_val}")
                except (ValueError, TypeError):
                    errors.append(f"{key} must be a valid number")
        
        # Validate durations
        for key, min_val, max_val in [
            ('minDuration', 1, 5),
            ('maxDuration', 30, 120),
            ('defaultDuration', 1, 15)
        ]:
            if key in settings:
                try:
                    value = int(settings[key])
                    if not (min_val <= value <= max_val):
                        errors.append(f"{key} must be between {min_val} and {max_val}")
                except (ValueError, TypeError):
                    errors.append(f"{key} must be a valid number")
        
        # Validate quiz settings
        if 'quizQuestions' in settings:
            try:
                value = int(settings['quizQuestions'])
                if not (1 <= value <= 20):
                    errors.append("Quiz questions must be between 1 and 20")
            except (ValueError, TypeError):
                errors.append("Quiz questions must be a valid number")
        
        # Validate temperature
        if 'temperature' in settings:
            try:
                value = float(settings['temperature'])
                if not (0.1 <= value <= 1.0):
                    errors.append("Temperature must be between 0.1 and 1.0")
            except (ValueError, TypeError):
                errors.append("Temperature must be a valid number")
        
        # Validate audio speed
        if 'audioSpeed' in settings:
            try:
                value = float(settings['audioSpeed'])
                if not (0.5 <= value <= 2.0):
                    errors.append("Audio speed must be between 0.5 and 2.0")
            except (ValueError, TypeError):
                errors.append("Audio speed must be a valid number")
        
        return errors
    
    @classmethod
    def reset_to_defaults(cls, user_id=None):
        """Reset user settings to defaults"""
        try:
            return cls.save_settings(cls.DEFAULT_SETTINGS.copy(), user_id)
        except Exception as e:
            logger.error(f"Error resetting settings for user {user_id}: {e}")
            return False