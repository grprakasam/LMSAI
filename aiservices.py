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
            return self._get_fallback_content(topic, expertise, duration)
    
    def _get_plan_limitations(self, user_plan: str, duration: int) -> Tuple[Dict, int]:
        """Get content pool and max duration based on user plan"""
        if user_plan == 'free':
            content_pool = R_TOPICS_CONTENT['free_topics']
            max_duration = min(duration, 5)  # Limit free users to 5 minutes
        else:
            content_pool = {**R_TOPICS_CONTENT['free_topics'], **R_TOPICS_CONTENT['premium_topics']}
            max_duration = duration
        return content_pool, max_duration
    
    def _get_topic_data(self, topic: str, expertise: str, content_pool: Dict) -> Dict:
        """Get topic-specific data from content pool"""
        # Search for matching topic
        for topic_key, topic_content in content_pool.items():
            if topic_key.lower() in topic.lower() or topic.lower() in topic_key.lower():
                if expertise in topic_content:
                    return topic_content[expertise]
        
        # Default fallback
        return {
            'concepts': ['fundamental concepts', 'practical applications'],
            'code_examples': [f'# {topic} example\n# Basic R code'],
            'packages': ['base'],
            'learning_objectives': [f'Understanding {topic}']
        }
    
    def _generate_ai_script(self, topic: str, expertise: str, duration: int, topic_data: Dict, user_plan: str) -> str:
        """Generate high-quality content using AI (Premium feature)"""
        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        
        self.last_request_time = time.time()
        
        # Create detailed prompt based on user plan
        prompt = self._create_detailed_prompt(topic, expertise, duration, topic_data, user_plan)
        
        # Try DeepSeek first, then OpenAI as fallback
        if self.deepseek_key:
            response = self._call_deepseek_api(prompt)
            if response:
                return response
        elif self.openai_key:
            response = self._call_openai_api(prompt)
            if response:
                return response
        
        # Fallback to basic script if AI services fail
        return self._generate_basic_script(topic, expertise, duration, topic_data)
    
    def _create_detailed_prompt(self, topic: str, expertise: str, duration: int, topic_data: Dict, user_plan: str) -> str:
        """Create a detailed prompt for AI content generation"""
        # Calculate content proportions
        total_seconds = duration * 60
        intro_seconds = min(30, total_seconds * 0.1)  # 10% or 30 seconds
        core_seconds = total_seconds * 0.6  # 60%
        examples_seconds = total_seconds * 0.2  # 20%
        summary_seconds = total_seconds * 0.1  # 10%
        
        # Determine content depth based on plan
        if user_plan == 'free':
            detail_level = 'Clear and concise explanations for beginners'
            code_complexity = 'Basic examples with detailed comments'
        elif user_plan == 'pro':
            detail_level = 'Detailed explanations with intermediate concepts'
            code_complexity = 'Intermediate examples with best practices'
        else:  # team
            detail_level = 'Comprehensive explanations with advanced concepts'
            code_complexity = 'Advanced examples with optimization techniques'
        
        prompt = f"""Create a comprehensive {duration}-minute R programming tutorial on "{topic}" for {expertise} level users.

Content Structure:
1. Introduction and Overview ({int(intro_seconds)} seconds)
   - Hook the audience with relevance of the topic
   - Brief overview of what will be covered

2. Core Concepts Explanation ({int(core_seconds)} seconds)
   - {detail_level}
   - Key concepts: {', '.join(topic_data['concepts'][:3])}
   - Common pitfalls and how to avoid them

3. Practical Examples with Code ({int(examples_seconds)} seconds)
   - {code_complexity}
   - Relevant packages: {', '.join(topic_data['packages'][:3])}
   - Real-world applications and use cases

4. Summary and Next Steps ({int(summary_seconds)} seconds)
   - Key takeaways
   - Resources for further learning
   - Practice exercises

Additional Requirements:
- Make it conversational and engaging
- Include natural pauses [PAUSE] and emphasis [EMPHASIS] markers
- Add code execution suggestions [EXECUTE]
- Include troubleshooting tips for common errors
- Add pro tips for advanced users (if applicable)

Target Audience: {expertise.capitalize()} level R programmers"""

        return prompt
    
    def _call_deepseek_api(self, prompt: str) -> Optional[str]:
        """Call DeepSeek API for premium content generation"""
        headers = {
            'Authorization': f'Bearer {self.deepseek_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': 'deepseek-chat',
            'messages': [
                {'role': 'system', 'content': 'You are an expert R programming instructor with 10+ years of experience teaching data science.'},
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
            logger.error(f"DeepSeek API error: {e}")
        
        return None
    
    def _call_openai_api(self, prompt: str) -> Optional[str]:
        """Call OpenAI API for premium content generation"""
        headers = {
            'Authorization': f'Bearer {self.openai_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': 'gpt-3.5-turbo',
            'messages': [
                {'role': 'system', 'content': 'You are an expert R programming instructor with 10+ years of experience teaching data science.'},
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': 2000,
            'temperature': 0.7
        }
        
        try:
            response = requests.post(self.openai_url, headers=headers, json=data, timeout=30)
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
        
        return None
    
    def _generate_basic_script(self, topic: str, expertise: str, duration: int, topic_data: Dict) -> str:
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
    
    def _enhance_content_for_plan(self, topic_data: Dict, user_plan: str) -> Dict:
        """Enhance content based on user's subscription plan"""
        enhanced_data = {
            'concepts': topic_data.get('concepts', []),
            'packages': topic_data.get('packages', ['base']),
            'learning_objectives': topic_data.get('learning_objectives', [f'Understanding {topic_data.get("topic", "the concept")}']),
            'code_examples': topic_data.get('code_examples', [])
        }
        
        # Add premium enhancements
        if user_plan != 'free':
            enhanced_data['advanced_tips'] = [
                'Consider using vectorized operations for better performance',
                'Always check your data types before analysis',
                'Use functions to avoid code repetition'
            ]
            
            if user_plan == 'team':
                enhanced_data['enterprise_considerations'] = [
                    'Code review best practices',
                    'Documentation standards',
                    'Performance optimization techniques'
                ]
        
        return enhanced_data
    
    def _estimate_reading_time(self, content: str) -> int:
        """Estimate reading time in minutes"""
        words_per_minute = 200
        word_count = len(content.split())
        return max(1, word_count // words_per_minute)
    
    def _calculate_difficulty_score(self, expertise: str, topic: str) -> int:
        """Calculate difficulty score (1-10)"""
        base_score = {'beginner': 3, 'intermediate': 6, 'expert': 9}[expertise]
        # Adjust based on topic complexity (simplified)
        if any(word in topic.lower() for word in ['advanced', 'machine learning', 'neural', 'bayesian']):
            base_score += 2
        elif any(word in topic.lower() for word in ['basic', 'intro', 'fundamentals']):
            base_score -= 1
        return min(10, max(1, base_score))
    
    def _categorize_topic(self, topic: str) -> str:
        """Categorize topic into broader categories"""
        topic_lower = topic.lower()
        if any(word in topic_lower for word in ['data frame', 'vector', 'list', 'matrix']):
            return 'data_structures'
        elif any(word in topic_lower for word in ['plot', 'graph', 'visual', 'chart']):
            return 'visualization'
        elif any(word in topic_lower for word in ['model', 'regression', 'machine learning', 'statistic']):
            return 'modeling'
        elif any(word in topic_lower for word in ['function', 'package', 'library']):
            return 'programming'
        else:
            return 'general'

# Initialize AI generator instance
ai_generator = AITutorialGenerator()
