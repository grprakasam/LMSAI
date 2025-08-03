import requests
import json
import os
import time
import tempfile
import base64
from typing import Dict, List, Optional, Tuple
from config import R_TOPICS_CONTENT
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AITutorialGenerator:
    """Enhanced AI tutorial generator with multiple service support"""
    
    def __init__(self):
        self.deepseek_url = "https://api.deepseek.com/v1/chat/completions"
        self.openai_url = "https://api.openai.com/v1/chat/completions"
        self.deepseek_key = os.environ.get('DEEPSEEK_API_KEY', '')
        self.openai_key = os.environ.get('OPENAI_API_KEY', '')
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0  # seconds between requests
        
    def generate_tutorial_content(self, topic: str, expertise: str, duration: int, user_plan: str = 'free') -> Dict:
        """
        Generate comprehensive tutorial content based on user's subscription plan
        
        Args:
            topic: R programming topic
            expertise: beginner, intermediate, expert
            duration: tutorial length in minutes
            user_plan: free, pro, team
            
        Returns:
            Dictionary with content, concepts, packages, objectives, etc.
        """
        try:
            # Determine content access and quality based on plan
            content_pool, max_duration = self._get_plan_limitations(user_plan, duration)
            
            # Get topic-specific data
            topic_data = self._get_topic_data(topic, expertise, content_pool)
            
            # Generate script using appropriate method
            if user_plan != 'free' and (self.deepseek_key or self.openai_key):
                script = self._generate_ai_script(topic, expertise, max_duration, topic_data, user_plan)
            else:
                script = self._generate_basic_script(topic, expertise, max_duration, topic_data)
            
            # Enhanced content for premium users
            enhanced_data = self._enhance_content_for_plan(topic_data, user_plan)
            
            return {
                'content': script,
                'concepts': enhanced_data['concepts'],
                'packages': enhanced_data['packages'],
                'objectives': enhanced_data['learning_objectives'],
                'is_premium': user_plan != 'free',
                'estimated_reading_time': self._estimate_reading_time(script),
                'difficulty_score': self._calculate_difficulty_score(expertise, topic),
                'code_examples_count': len(enhanced_data.get('code_examples', [])),
                'topic_category': self._categorize_topic(topic)
            }
            
        except Exception as e:
            logger.error(f"Error generating tutorial content: {e}")
            return self._get_fallback_content(topic, expertise,