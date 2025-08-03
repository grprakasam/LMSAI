# openrouter_service.py - OpenRouter API integration
import os
import requests
import json
import time
import tempfile
import base64
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OpenRouterService:
    """Service for interacting with OpenRouter API for both text and audio generation"""
    
    def __init__(self):
        self.api_key = os.environ.get('OPENROUTER_API_KEY', '')
        self.base_url = 'https://openrouter.ai/api/v1'
        self.site_url = os.environ.get('OPENROUTER_SITE_URL', 'http://localhost:5000')
        self.site_name = os.environ.get('OPENROUTER_SITE_NAME', 'R Tutor Pro')
        
        # Default models
        self.default_text_model = os.environ.get('OPENROUTER_TEXT_MODEL', 'anthropic/claude-3.5-sonnet')
        self.default_audio_model = os.environ.get('OPENROUTER_AUDIO_MODEL', 'openai/tts-1')
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0  # seconds between requests
        
        # Validate configuration
        if not self.api_key:
            logger.warning("OPENROUTER_API_KEY not set. Tutorial generation will be limited.")
    
    def get_available_models(self, model_type='text'):
        """
        Get available models from OpenRouter
        
        Args:
            model_type: 'text' or 'audio'
            
        Returns:
            List of available models
        """
        try:
            headers = self._get_headers()
            response = requests.get(f"{self.base_url}/models", headers=headers, timeout=30)
            
            if response.status_code == 200:
                all_models = response.json()['data']
                
                if model_type == 'text':
                    # Filter for text generation models
                    text_models = [
                        model for model in all_models 
                        if 'chat' in model.get('id', '').lower() or 
                           'instruct' in model.get('id', '').lower() or
                           'claude' in model.get('id', '').lower() or
                           'gpt' in model.get('id', '').lower()
                    ]
                    return text_models
                elif model_type == 'audio':
                    # Filter for audio generation models
                    audio_models = [
                        model for model in all_models 
                        if 'tts' in model.get('id', '').lower() or
                           'speech' in model.get('id', '').lower() or
                           'audio' in model.get('id', '').lower()
                    ]
                    return audio_models
                    
            return []
            
        except Exception as e:
            logger.error(f"Failed to fetch models: {e}")
            return []
    
    def generate_tutorial_content(self, topic: str, expertise: str, duration: int, 
                                text_model: str = None, user_preferences: Dict = None):
        """
        Generate tutorial content using OpenRouter
        
        Args:
            topic: R programming topic
            expertise: beginner, intermediate, expert
            duration: tutorial length in minutes
            text_model: OpenRouter model ID for text generation
            user_preferences: Additional user preferences
            
        Returns:
            Dictionary with generated content and metadata
        """
        try:
            # Use provided model or default
            model = text_model or self.default_text_model
            
            # Create comprehensive prompt
            prompt = self._create_tutorial_prompt(topic, expertise, duration, user_preferences)
            
            # Generate content via OpenRouter
            content = self._call_openrouter_chat(prompt, model)
            
            if not content:
                # Fallback to basic content if API fails
                return self._generate_fallback_content(topic, expertise, duration)
            
            # Parse and enhance the generated content
            tutorial_data = self._parse_tutorial_content(content, topic, expertise, duration)
            
            return tutorial_data
            
        except Exception as e:
            logger.error(f"Error generating tutorial content: {e}")
            return self._generate_fallback_content(topic, expertise, duration)
    
    def generate_audio(self, text: str, audio_model: str = None, voice: str = None, 
                      speed: float = 1.0, format: str = 'mp3'):
        """
        Generate audio from text using OpenRouter
        
        Args:
            text: Text content to convert to speech
            audio_model: OpenRouter model ID for audio generation
            voice: Voice selection (model-dependent)
            speed: Speech speed (0.25 to 4.0)
            format: Audio format (mp3, opus, aac, flac)
            
        Returns:
            Dictionary with audio data and metadata
        """
        try:
            # Use provided model or default
            model = audio_model or self.default_audio_model
            voice = voice or os.environ.get('OPENROUTER_VOICE', 'alloy')
            
            # Rate limiting
            self._rate_limit()
            
            # Prepare audio generation request
            audio_data = self._call_openrouter_audio(text, model, voice, speed, format)
            
            if audio_data:
                # Save audio file
                audio_file_path = self._save_audio_file(audio_data, format)
                
                return {
                    'success': True,
                    'audio_url': f"/static/generated_audio/{os.path.basename(audio_file_path)}",
                    'audio_path': audio_file_path,
                    'audio_base64': base64.b64encode(audio_data).decode('utf-8'),
                    'format': format,
                    'model_used': model,
                    'voice_used': voice,
                    'duration_estimate': len(text) / 200 * 60,  # Rough estimate
                    'character_count': len(text)
                }
            else:
                return {
                    'success': False,
                    'error': 'Audio generation failed',
                    'fallback_available': False
                }
                
        except Exception as e:
            logger.error(f"Error generating audio: {e}")
            return {
                'success': False,
                'error': str(e),
                'fallback_available': False
            }
    
    def _get_headers(self):
        """Get headers for OpenRouter API requests"""
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': self.site_url,
            'X-Title': self.site_name
        }
    
    def _rate_limit(self):
        """Implement rate limiting for API calls"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        self.last_request_time = time.time()
    
    def _create_tutorial_prompt(self, topic: str, expertise: str, duration: int, 
                              user_preferences: Dict = None):
        """Create a comprehensive prompt for tutorial generation"""
        
        # Base prompt with structure
        prompt = f"""Create a comprehensive {duration}-minute R programming tutorial on "{topic}" for {expertise} level users.

**Tutorial Requirements:**

1. **Content Structure:**
   - Introduction and overview (15% of content)
   - Core concepts and theory (40% of content)
   - Hands-on code examples (35% of content)
   - Summary and next steps (10% of content)

2. **Learning Objectives:**
   - Define clear, actionable learning outcomes
   - Ensure objectives match {expertise} level expectations
   - Include both theoretical understanding and practical skills

3. **Code Examples:**
   - Provide working R code that users can execute
   - Include detailed comments explaining each step
   - Progress from simple to more complex examples
   - Cover common use cases and best practices

4. **Expertise Level Guidelines:**
   - **Beginner**: Assume minimal R knowledge, explain basic concepts, use simple examples
   - **Intermediate**: Build on fundamental knowledge, introduce advanced techniques, real-world applications
   - **Expert**: Focus on optimization, edge cases, advanced implementations, performance considerations

5. **Content Format:**
   - Use clear section headers
   - Include practical tips and warnings
   - Provide troubleshooting guidance
   - Suggest further learning resources

6. **Audio-Friendly Writing:**
   - Write in a conversational, spoken style
   - Use natural transitions between sections
   - Include verbal cues like "Now let's look at..." or "Here's an important point..."
   - Avoid overly complex sentences that are hard to follow when spoken

**Specific Topic Focus: {topic}**

Please generate comprehensive tutorial content that covers:
- Essential concepts and terminology
- Practical R code implementations
- Common pitfalls and how to avoid them
- Real-world applications and use cases
- Best practices for {expertise} level practitioners

**Output Format:**
Return the content as a well-structured tutorial that flows naturally when read aloud, with clear sections and smooth transitions between topics.

**Additional Preferences:**"""

        # Add user preferences if provided
        if user_preferences:
            if user_preferences.get('focus_areas'):
                prompt += f"\n- Focus on: {', '.join(user_preferences['focus_areas'])}"
            if user_preferences.get('learning_style'):
                prompt += f"\n- Learning style: {user_preferences['learning_style']}"
            if user_preferences.get('industry_context'):
                prompt += f"\n- Industry context: {user_preferences['industry_context']}"
        
        prompt += "\n\nGenerate the tutorial content now:"
        
        return prompt
    
    def _call_openrouter_chat(self, prompt: str, model: str):
        """Call OpenRouter chat completion API"""
        self._rate_limit()
        
        headers = self._get_headers()
        
        data = {
            'model': model,
            'messages': [
                {
                    'role': 'system',
                    'content': 'You are an expert R programming instructor with 15+ years of experience teaching data science, statistics, and R programming. You create engaging, practical, and comprehensive tutorials for learners at all levels. Your explanations are clear, your code examples are working and well-commented, and you always provide practical, actionable guidance.'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'max_tokens': 4096,
            'temperature': 0.7,
            'top_p': 1,
            'frequency_penalty': 0,
            'presence_penalty': 0
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"OpenRouter chat API call failed: {e}")
            return None
    
    def _call_openrouter_audio(self, text: str, model: str, voice: str, speed: float, format: str):
        """Call OpenRouter audio generation API"""
        self._rate_limit()
        
        headers = self._get_headers()
        headers['Accept'] = f'audio/{format}'
        
        # Prepare request based on model type
        if 'openai' in model.lower():
            # OpenAI TTS format
            data = {
                'model': model,
                'input': text,
                'voice': voice,
                'response_format': format,
                'speed': speed
            }
            endpoint = 'audio/speech'
        else:
            # Generic audio generation format
            data = {
                'model': model,
                'text': text,
                'voice': voice,
                'format': format,
                'speed': speed
            }
            endpoint = 'audio/generations'
        
        try:
            response = requests.post(
                f"{self.base_url}/{endpoint}",
                headers=headers,
                json=data,
                timeout=120
            )
            
            if response.status_code == 200:
                return response.content
            else:
                logger.error(f"OpenRouter audio API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"OpenRouter audio API call failed: {e}")
            return None
    
    def _save_audio_file(self, audio_data: bytes, format: str):
        """Save audio data to file"""
        try:
            # Ensure audio directory exists
            audio_dir = os.path.join(os.getcwd(), 'static', 'generated_audio')
            os.makedirs(audio_dir, exist_ok=True)
            
            # Generate unique filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_id = str(uuid.uuid4())[:8]
            filename = f"tutorial_{timestamp}_{unique_id}.{format}"
            file_path = os.path.join(audio_dir, filename)
            
            # Save audio file
            with open(file_path, 'wb') as f:
                f.write(audio_data)
            
            logger.info(f"Audio file saved: {filename}")
            return file_path
            
        except Exception as e:
            logger.error(f"Failed to save audio file: {e}")
            raise
    
    def _parse_tutorial_content(self, content: str, topic: str, expertise: str, duration: int):
        """Parse and enhance the generated tutorial content"""
        
        # Extract concepts (look for key terms and topics)
        concepts = self._extract_concepts(content, topic)
        
        # Extract R packages mentioned
        packages = self._extract_packages(content)
        
        # Generate learning objectives
        objectives = self._extract_objectives(content, topic, expertise)
        
        # Estimate reading time
        reading_time = self._estimate_reading_time(content)
        
        # Calculate difficulty score
        difficulty_score = self._calculate_difficulty_score(content, expertise)
        
        return {
            'content': content,
            'concepts': concepts,
            'packages': packages,
            'objectives': objectives,
            'is_premium': True,
            'estimated_reading_time': reading_time,
            'difficulty_score': difficulty_score,
            'character_count': len(content),
            'word_count': len(content.split()),
            'topic_category': self._categorize_topic(topic),
            'generated_via': 'openrouter',
            'model_used': self.default_text_model
        }
    
    def _extract_concepts(self, content: str, topic: str):
        """Extract key concepts from the tutorial content"""
        content_lower = content.lower()
        
        # Common R concepts to look for
        r_concepts = [
            'data frames', 'vectors', 'lists', 'matrices', 'factors',
            'functions', 'packages', 'libraries', 'visualization',
            'ggplot2', 'dplyr', 'tidyr', 'statistical analysis',
            'machine learning', 'data manipulation', 'data cleaning',
            'regression', 'classification', 'clustering', 'hypothesis testing',
            'loops', 'conditionals', 'apply functions', 'pipes',
            'tidyverse', 'base r', 'data types', 'indexing'
        ]
        
        found_concepts = []
        for concept in r_concepts:
            if concept in content_lower:
                found_concepts.append(concept.title())
        
        # Add topic-specific concepts
        topic_words = topic.lower().split()
        for word in topic_words:
            if len(word) > 3 and word not in ['with', 'using', 'and', 'the', 'for']:
                found_concepts.append(word.title())
        
        return found_concepts[:8]  # Limit to 8 concepts
    
    def _extract_packages(self, content: str):
        """Extract R packages mentioned in the content"""
        import re
        
        # Look for library() or require() calls
        library_pattern = r'library\(["\']?([^"\')\s]+)["\']?\)'
        require_pattern = r'require\(["\']?([^"\')\s]+)["\']?\)'
        
        packages = set()
        
        # Find library calls
        for match in re.finditer(library_pattern, content, re.IGNORECASE):
            packages.add(match.group(1).strip())
        
        # Find require calls
        for match in re.finditer(require_pattern, content, re.IGNORECASE):
            packages.add(match.group(1).strip())
        
        # Common R packages to check for mentions
        common_packages = [
            'ggplot2', 'dplyr', 'tidyr', 'readr', 'tibble', 'stringr',
            'forcats', 'lubridate', 'tidyverse', 'data.table', 'shiny',
            'plotly', 'caret', 'randomForest', 'e1071', 'cluster',
            'survival', 'nlme', 'lme4', 'glmnet', 'xgboost'
        ]
        
        content_lower = content.lower()
        for package in common_packages:
            if package.lower() in content_lower:
                packages.add(package)
        
        return list(packages)[:6]  # Limit to 6 packages
    
    def _extract_objectives(self, content: str, topic: str, expertise: str):
        """Extract or generate learning objectives"""
        objectives = [
            f"Understand the fundamentals of {topic}",
            f"Apply {topic} concepts in practical R programming",
            f"Implement {topic} solutions for real-world problems"
        ]
        
        if expertise == 'beginner':
            objectives.append(f"Get started with {topic} basics in R")
        elif expertise == 'intermediate':
            objectives.append(f"Master intermediate {topic} techniques")
        else:
            objectives.append(f"Explore advanced {topic} implementations")
        
        return objectives
    
    def _estimate_reading_time(self, content: str):
        """Estimate reading time in minutes"""
        words_per_minute = 200
        word_count = len(content.split())
        return max(1, word_count // words_per_minute)
    
    def _calculate_difficulty_score(self, content: str, expertise: str):
        """Calculate difficulty score (1-10)"""
        base_score = {'beginner': 3, 'intermediate': 6, 'expert': 9}[expertise]
        
        # Adjust based on content complexity
        content_lower = content.lower()
        if any(term in content_lower for term in ['advanced', 'complex', 'optimization', 'algorithm']):
            base_score += 1
        if any(term in content_lower for term in ['simple', 'basic', 'introduction', 'getting started']):
            base_score -= 1
            
        return min(10, max(1, base_score))
    
    def _categorize_topic(self, topic: str):
        """Categorize topic into broader categories"""
        topic_lower = topic.lower()
        
        category_map = {
            'data_structures': ['data frame', 'vector', 'list', 'matrix', 'structure'],
            'visualization': ['plot', 'graph', 'visual', 'chart', 'ggplot'],
            'modeling': ['model', 'regression', 'machine learning', 'statistic', 'analysis'],
            'programming': ['function', 'package', 'library', 'programming', 'code'],
            'data_wrangling': ['dplyr', 'tidyr', 'wrangle', 'clean', 'transform', 'manipul'],
            'web_development': ['shiny', 'web', 'app', 'dashboard', 'interactive']
        }
        
        for category, keywords in category_map.items():
            if any(keyword in topic_lower for keyword in keywords):
                return category
        
        return 'general'
    
    def _generate_fallback_content(self, topic: str, expertise: str, duration: int):
        """Generate fallback content when API is unavailable"""
        return {
            'content': f"""# R Tutorial: {topic} ({expertise.title()} Level)

## Introduction
Welcome to this {duration}-minute tutorial on {topic}! This tutorial is designed for {expertise} level R programmers.

## Learning Objectives
By the end of this tutorial, you will:
- Understand the fundamentals of {topic}
- Be able to implement {topic} in your R projects
- Know the best practices for working with {topic}

## Core Concepts
{topic} is an important concept in R programming. Let's explore the key aspects:

### Getting Started
First, let's load the necessary libraries:
```r
# Load required packages
library(tidyverse)  # For data manipulation and visualization
```

### Basic Implementation
Here's a basic example of {topic}:
```r
# Basic {topic} example
# This is a foundational example for {expertise} level
data <- data.frame(
  x = 1:10,
  y = rnorm(10)
)
print(data)
```

## Practical Applications
{topic} can be used in various scenarios:
- Data analysis projects
- Statistical modeling
- Data visualization
- Research applications

## Best Practices
When working with {topic}, remember to:
- Always validate your data
- Use descriptive variable names
- Comment your code thoroughly
- Test your implementations

## Next Steps
Continue your learning journey by:
- Practicing with real datasets
- Exploring advanced {topic} techniques
- Building projects that use {topic}
- Joining R communities for support

## Summary
You've learned the essentials of {topic} in R. Keep practicing and experimenting to master these concepts!

*Note: This is fallback content. For enhanced tutorials, please configure your OpenRouter API key.*
""",
            'concepts': ['fundamentals', 'implementation', 'best practices'],
            'packages': ['tidyverse', 'base'],
            'objectives': [
                f'Understand {topic} fundamentals',
                f'Implement {topic} in R projects',
                'Apply best practices'
            ],
            'is_premium': False,
            'estimated_reading_time': max(1, duration // 2),
            'difficulty_score': {'beginner': 3, 'intermediate': 6, 'expert': 9}[expertise],
            'character_count': 0,
            'word_count': 0,
            'topic_category': 'general',
            'generated_via': 'fallback',
            'model_used': 'none'
        }
    
    def get_model_status(self):
        """Get status of OpenRouter connection and available models"""
        try:
            headers = self._get_headers()
            response = requests.get(f"{self.base_url}/models", headers=headers, timeout=10)
            
            if response.status_code == 200:
                models = response.json()
                return {
                    'status': 'connected',
                    'model_count': len(models.get('data', [])),
                    'api_key_valid': True,
                    'last_check': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'error',
                    'error': f"HTTP {response.status_code}",
                    'api_key_valid': False,
                    'last_check': datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'api_key_valid': False,
                'last_check': datetime.now().isoformat()
            }

# Initialize global service instance
openrouter_service = OpenRouterService()