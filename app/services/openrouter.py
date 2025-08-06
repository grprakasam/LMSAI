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
        
        # Simple cache for model status
        self._model_status_cache = None
        self._model_status_cache_time = 0
        self._cache_duration = 300  # 5 minutes
        
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
                                text_model: str = None, user_preferences: Dict = None, content_length: str = 'medium'):
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
                return self._generate_fallback_content(topic, expertise, duration, content_length)
            
            # Parse and enhance the generated content
            tutorial_data = self._parse_tutorial_content(content, topic, expertise, duration)
            
            return tutorial_data
            
        except Exception as e:
            logger.error(f"Error generating tutorial content: {e}")
            return self._generate_fallback_content(topic, expertise, duration, content_length)
    
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
        """Create a comprehensive prompt for tutorial generation optimized for audio"""
        
        # Calculate approximate word count for duration
        words_per_minute_spoken = 140  # Average speaking rate for educational content
        target_words = duration * words_per_minute_spoken
        
        # Base prompt with enhanced audio-friendly structure
        prompt = f"""Create a high-quality R programming tutorial on "{topic}" for {expertise} level users that will be converted to audio narration.

**CRITICAL REQUIREMENTS FOR AUDIO-OPTIMIZED CONTENT:**

🎯 **Target Specifications:**
- Duration: {duration} minutes (approximately {target_words} words)
- Expertise: {expertise} level
- Format: Markdown with audio-friendly prose
- Tone: Conversational, engaging, professional

📖 **Content Structure (Must Follow):**
1. **Welcome & Introduction** (2-3 minutes)
   - Warm greeting and topic introduction
   - Clear preview of what listeners will learn
   - Context about why this topic matters

2. **Core Learning Content** ({duration-4} minutes)
   - Conceptual explanations with clear examples
   - Step-by-step R code walkthroughs
   - Practical applications and real-world scenarios

3. **Summary & Next Steps** (1-2 minutes)
   - Key takeaways recap
   - Suggested practice exercises
   - Resources for continued learning

🎙️ **Audio-Friendly Writing Style:**
- Use CONVERSATIONAL language like you're teaching a friend
- Include natural pauses with phrases like "Now, let's move on to..."
- Use "Let's" instead of "We will" for engagement
- Explain code line-by-line in simple terms
- Add verbal signposts: "First," "Next," "Here's the key point," "Remember that"
- Avoid jargon without explanation - define technical terms clearly
- Use active voice and shorter sentences
- Include encouraging phrases: "Great job!" "You're getting it!" "This is important"

💻 **Code Presentation for Audio:**
- Always introduce code blocks: "Let's look at this code example"
- Explain each line in plain English after showing it
- Use descriptive variable names that are easy to pronounce
- Add pronunciation guides for difficult terms: "ggplot (G-G-plot)"
- Mention common errors and how to fix them

📝 **Markdown Structure Required:**
```
# R Tutorial: [Topic Title]

## Introduction
[Engaging welcome and overview]

## What You'll Learn
[Clear bullet points of outcomes]

## Core Concepts
### [Concept 1]
[Clear explanation with examples]

### [Concept 2]
[Clear explanation with examples]

## Hands-On Practice
### Step 1: [Action]
[Detailed walkthrough]

```r
# Code with comments
[working R code here]
```

[Explanation of what this code does]

## Real-World Applications
[Practical examples and use cases]

## Summary
[Key takeaways and next steps]

## Resources for Further Learning
[Additional materials]
```

🎯 **Specific Requirements for "{topic}":**
- Ensure all content directly relates to "{topic}" as requested by the user
- Include practical R examples specific to this topic
- Address common challenges beginners/intermediates/experts face with this topic
- Provide working code that users can copy and execute
- Explain WHY things work, not just HOW

**Expertise Level Guidelines:**"""

        if expertise == 'beginner':
            prompt += """
- Assume NO prior knowledge of this topic
- Define ALL technical terms clearly
- Use simple, step-by-step explanations
- Include more encouragement and reassurance
- Provide basic troubleshooting tips
- Focus on fundamental concepts before advanced applications"""
        elif expertise == 'intermediate':
            prompt += """
- Assume basic R knowledge but not necessarily this specific topic
- Build on fundamental R concepts
- Include intermediate techniques and best practices
- Show multiple ways to solve problems
- Discuss when to use different approaches
- Include performance considerations"""
        else:  # expert
            prompt += """
- Assume solid R foundation and some topic knowledge
- Focus on advanced techniques and optimization
- Discuss edge cases and complex scenarios
- Include performance benchmarking
- Show integration with advanced workflows
- Discuss latest developments in this area"""

        # Add user preferences if provided
        if user_preferences:
            prompt += "\n\n**User Preferences:**"
            if user_preferences.get('focus_areas'):
                prompt += f"\n- Focus areas: {', '.join(user_preferences['focus_areas'])}"
            if user_preferences.get('learning_style'):
                prompt += f"\n- Learning style: {user_preferences['learning_style']}"
            if user_preferences.get('industry_context'):
                prompt += f"\n- Industry context: {user_preferences['industry_context']}"
        
        prompt += f"""

**FINAL INSTRUCTIONS:**
Generate a complete, engaging tutorial that:
1. Follows the exact markdown structure shown above
2. Uses conversational, audio-friendly language throughout
3. Includes working R code examples with clear explanations
4. Stays focused on "{topic}" as the main subject
5. Is appropriate for {expertise} level learners
6. Will sound natural and engaging when read aloud
7. Provides genuine educational value in {duration} minutes

Begin the tutorial now with a warm, engaging introduction:"""
        
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
                    'content': 'You are an expert R programming instructor with 15+ years of experience teaching data science, statistics, and R programming. You specialize in creating audio-friendly tutorials that will be converted to speech. Write in a conversational, engaging tone as if you\'re speaking directly to a student. Use clear explanations, natural transitions, and encourage the learner throughout. Your tutorials should sound warm and professional when read aloud. Include working R code examples with clear verbal explanations of what each part does.'
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
        """Parse and enhance the generated tutorial content with audio optimization"""
        
        # Apply audio-specific optimizations
        audio_optimized_content = self._optimize_for_audio(content)
        
        # Extract concepts (look for key terms and topics)
        concepts = self._extract_concepts(audio_optimized_content, topic)
        
        # Extract R packages mentioned
        packages = self._extract_packages(audio_optimized_content)
        
        # Generate learning objectives
        objectives = self._extract_objectives(audio_optimized_content, topic, expertise)
        
        # Estimate reading time
        reading_time = self._estimate_reading_time(audio_optimized_content)
        
        # Calculate difficulty score
        difficulty_score = self._calculate_difficulty_score(audio_optimized_content, expertise)
        
        return {
            'content': audio_optimized_content,
            'concepts': concepts,
            'packages': packages,
            'objectives': objectives,
            'is_premium': True,
            'estimated_reading_time': reading_time,
            'difficulty_score': difficulty_score,
            'character_count': len(audio_optimized_content),
            'word_count': len(audio_optimized_content.split()),
            'topic_category': self._categorize_topic(topic),
            'generated_via': 'openrouter',
            'model_used': self.default_text_model,
            'audio_optimized': True
        }
    
    def _optimize_for_audio(self, content: str):
        """Optimize content for audio narration by improving readability and flow"""
        import re
        
        # Apply audio-specific optimizations
        optimized = content
        
        # 1. Add pronunciation guides for common R terms
        pronunciation_map = {
            'ggplot2': 'ggplot2 (G-G-plot-two)',
            'dplyr': 'dplyr (D-plier)',
            'tidyr': 'tidyr (tidy-R)',
            '%>%': 'pipe operator (percent greater-than percent)',
            'data.frame': 'data frame',
            'str()': 'str function',
            'summary()': 'summary function',
            'c()': 'c function',
            'length()': 'length function',
            'names()': 'names function'
        }
        
        for term, pronunciation in pronunciation_map.items():
            if term in optimized and pronunciation not in optimized:
                # Only add pronunciation guide on first occurrence
                optimized = optimized.replace(term, pronunciation, 1)
        
        # 2. Add natural pauses and transitions
        section_transitions = {
            '## ': '## ',  # Keep headers as is, but add mental note for pause
            '### ': '### ',
            '\n\n```r': '\n\nNow, let\'s look at this code example:\n\n```r',
            '```\n\n': '```\n\nLet me explain what this code does. ',
            '\n- ': '\n- ',  # Keep bullet points clean
        }
        
        # 3. Enhance code block introductions
        code_block_pattern = r'```r\n(.*?)\n```'
        
        def enhance_code_block(match):
            code = match.group(1)
            lines = code.split('\n')
            
            # Add brief intro if not already present
            intro_phrases = ['let\'s', 'here\'s', 'now', 'look at', 'example']
            needs_intro = True
            
            # Check preceding text for intro phrases
            start_pos = match.start()
            preceding_text = optimized[max(0, start_pos-100):start_pos].lower()
            if any(phrase in preceding_text for phrase in intro_phrases):
                needs_intro = False
            
            enhanced_code = code
            
            # Add explanatory comments for complex lines if missing
            for i, line in enumerate(lines):
                line_stripped = line.strip()
                if line_stripped and not line_stripped.startswith('#'):
                    # Check if line needs explanation
                    if any(complex_term in line_stripped for complex_term in ['%>%', 'mutate', 'filter', 'group_by', 'summarise']):
                        # Look for existing comment
                        if '#' not in line:
                            # Could add inline comment, but keep it simple for now
                            pass
            
            return f'```r\n{enhanced_code}\n```'
        
        optimized = re.sub(code_block_pattern, enhance_code_block, optimized, flags=re.DOTALL)
        
        # 4. Improve readability of complex sentences
        # Split overly long sentences (>25 words) at logical break points
        sentences = optimized.split('. ')
        improved_sentences = []
        
        for sentence in sentences:
            words = sentence.split()
            if len(words) > 25:
                # Look for natural break points
                break_points = [' and ', ' but ', ' however ', ' therefore ', ' which ']
                for break_point in break_points:
                    if break_point in sentence:
                        parts = sentence.split(break_point, 1)
                        if len(parts) == 2:
                            sentence = f"{parts[0]}. {break_point.strip().capitalize()} {parts[1]}"
                            break
            improved_sentences.append(sentence)
        
        optimized = '. '.join(improved_sentences)
        
        # 5. Add verbal cues for emphasis
        emphasis_patterns = {
            'Important:': 'This is important:',
            'Note:': 'Please note:',
            'Warning:': 'Here\'s a warning:',
            'Tip:': 'Here\'s a helpful tip:',
            'Remember:': 'Remember this:'
        }
        
        for pattern, replacement in emphasis_patterns.items():
            optimized = optimized.replace(pattern, replacement)
        
        # 6. Improve list introductions for audio
        list_intro_pattern = r'\n\n([A-Z][^:\n]*:)\n\n((?:\n?[*\-] .+)+)'
        
        def improve_list_intro(match):
            intro = match.group(1)
            list_items = match.group(2)
            return f'\n\n{intro}\n\n{list_items}'
        
        optimized = re.sub(list_intro_pattern, improve_list_intro, optimized)
        
        # 7. Add natural speech markers
        optimized = optimized.replace('\n\n## ', '\n\nNow, let\'s move on to ')
        optimized = optimized.replace('In conclusion', 'To wrap up')
        optimized = optimized.replace('Finally', 'And finally')
        
        return optimized
    
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
    
    def _get_topic_specific_content(self, topic: str, expertise: str, config: Dict):
        """Generate topic-specific content details"""
        topic_lower = topic.lower()
        
        # Topic-specific introductions and content
        if 'ggplot' in topic_lower or 'visualization' in topic_lower:
            return {
                'intro': 'data visualization with ggplot2',
                'packages': ['ggplot2', 'dplyr', 'scales', 'RColorBrewer'],
                'concepts': ['Grammar of Graphics', 'Aesthetic mappings', 'Layers and geoms', 'Themes and customization'],
                'code_example': '''# Creating a scatter plot with ggplot2
library(ggplot2)

# Sample data
data(mtcars)

# Create visualization
ggplot(mtcars, aes(x = wt, y = mpg, color = factor(cyl))) +
  geom_point(size = 3) +
  geom_smooth(method = "lm", se = FALSE) +
  labs(title = "Car Weight vs Fuel Efficiency",
       x = "Weight (1000 lbs)",
       y = "Miles per gallon",
       color = "Cylinders") +
  theme_minimal()''',
                'use_cases': ['Business dashboards', 'Scientific publications', 'Exploratory data analysis'],
                'common_issues': ['Overplotting with large datasets', 'Color accessibility', 'Aspect ratio optimization']
            }
        elif 'machine learning' in topic_lower or 'ml' in topic_lower:
            return {
                'intro': 'machine learning techniques in R',
                'packages': ['caret', 'randomForest', 'e1071', 'glmnet'],
                'concepts': ['Training and testing', 'Cross-validation', 'Feature selection', 'Model evaluation'],
                'code_example': '''# Building a simple classification model
library(caret)
library(randomForest)

# Load and prepare data
data(iris)
set.seed(123)

# Split data
trainIndex <- createDataPartition(iris$Species, p = 0.7, list = FALSE)
train_data <- iris[trainIndex, ]
test_data <- iris[-trainIndex, ]

# Train random forest model
model <- randomForest(Species ~ ., data = train_data)

# Make predictions
predictions <- predict(model, test_data)

# Evaluate performance
confusionMatrix(predictions, test_data$Species)''',
                'use_cases': ['Predictive analytics', 'Classification tasks', 'Feature importance analysis'],
                'common_issues': ['Overfitting', 'Class imbalance', 'Feature scaling']
            }
        elif 'data' in topic_lower and ('manipulation' in topic_lower or 'wrangling' in topic_lower):
            return {
                'intro': 'data manipulation with dplyr and tidyr',
                'packages': ['dplyr', 'tidyr', 'readr', 'stringr'],
                'concepts': ['Filtering and selecting', 'Grouping and summarizing', 'Joins and merging', 'Reshaping data'],
                'code_example': '''# Data manipulation with dplyr
library(dplyr)
library(tidyr)

# Sample data manipulation
data(mtcars)

# Add car names as column
mtcars_clean <- mtcars %>%
  rownames_to_column("car_name") %>%
  # Filter for cars with good fuel efficiency
  filter(mpg > 20) %>%
  # Group by number of cylinders
  group_by(cyl) %>%
  # Calculate summary statistics
  summarise(
    avg_mpg = mean(mpg),
    avg_hp = mean(hp),
    car_count = n(),
    .groups = "drop"
  ) %>%
  # Arrange by average MPG
  arrange(desc(avg_mpg))

print(mtcars_clean)''',
                'use_cases': ['Data cleaning', 'Exploratory data analysis', 'Report generation'],
                'common_issues': ['Missing values handling', 'Data type conversions', 'Memory efficiency']
            }
        elif 'shiny' in topic_lower or 'app' in topic_lower:
            return {
                'intro': 'interactive web applications with Shiny',
                'packages': ['shiny', 'shinydashboard', 'DT', 'plotly'],
                'concepts': ['UI and Server logic', 'Reactivity', 'Input widgets', 'Output rendering'],
                'code_example': '''# Simple Shiny app
library(shiny)

# Define UI
ui <- fluidPage(
  titlePanel("Simple Data Explorer"),
  
  sidebarLayout(
    sidebarPanel(
      selectInput("variable", "Choose variable:",
                  choices = names(mtcars)),
      sliderInput("bins", "Number of bins:",
                  min = 5, max = 50, value = 30)
    ),
    
    mainPanel(
      plotOutput("histogram")
    )
  )
)

# Define server logic
server <- function(input, output) {
  output$histogram <- renderPlot({
    hist(mtcars[[input$variable]], 
         breaks = input$bins,
         main = paste("Histogram of", input$variable))
  })
}

# Run the application
shinyApp(ui = ui, server = server)''',
                'use_cases': ['Interactive dashboards', 'Data exploration tools', 'Decision support systems'],
                'common_issues': ['Performance optimization', 'User input validation', 'Deployment considerations']
            }
        elif 'statistic' in topic_lower or 'analysis' in topic_lower:
            return {
                'intro': 'statistical analysis and modeling in R',
                'packages': ['stats', 'car', 'lmtest', 'broom'],
                'concepts': ['Hypothesis testing', 'Linear modeling', 'ANOVA', 'Model diagnostics'],
                'code_example': '''# Statistical analysis example
# Load built-in dataset
data(mtcars)

# Exploratory analysis
summary(mtcars)

# Correlation analysis
cor_matrix <- cor(mtcars[, c("mpg", "hp", "wt")])
print(cor_matrix)

# Linear regression
model <- lm(mpg ~ hp + wt + factor(cyl), data = mtcars)
summary(model)

# Model diagnostics
plot(model)  # Diagnostic plots

# ANOVA
anova(model)

# Confidence intervals
confint(model)''',
                'use_cases': ['Research analysis', 'Quality control', 'A/B testing'],
                'common_issues': ['Assumption violations', 'Multicollinearity', 'Sample size considerations']
            }
        else:
            # Generic content for other topics
            return {
                'intro': f'{topic} in R programming',
                'packages': ['base', 'utils', 'stats'],
                'concepts': ['Basic concepts', 'Implementation', 'Best practices', 'Troubleshooting'],
                'code_example': f'''# Working with {topic}
# Basic setup
library(base)

# Sample data
sample_data <- c(1, 2, 3, 4, 5)

# Basic operations
result <- mean(sample_data)
print(paste("Result:", result))''',
                'use_cases': ['General analysis', 'Data processing', 'Custom solutions'],
                'common_issues': ['Syntax errors', 'Data type mismatches', 'Performance optimization']
            }
    
    def _generate_fallback_content(self, topic: str, expertise: str, duration: int, content_length: str = 'medium'):
        """Generate high-quality fallback content optimized for audio when API is unavailable"""
        
        # Configure content based on length preference
        length_config = {
            'short': {'target_words': 400, 'sections': 3, 'detail_level': 'concise'},
            'medium': {'target_words': 800, 'sections': 5, 'detail_level': 'balanced'},
            'lengthy': {'target_words': 1500, 'sections': 8, 'detail_level': 'comprehensive'}
        }
        config = length_config.get(content_length, length_config['medium'])
        
        # Create topic-specific content based on common R topics
        topic_specifics = self._get_topic_specific_content(topic, expertise, config)
        
        # Generate audio-friendly content based on expertise level
        if expertise == 'beginner':
            intro_text = f"Hello and welcome! I'm excited to guide you through your first steps with {topic_specifics['intro']}. Don't worry if you're new to this - we'll take it step by step, and by the end of this {content_length} tutorial, you'll have a solid foundation to build upon."
            explanation_depth = "Let me explain this carefully, step by step."
            encouragement = "You're doing great! This is exactly how learning works - one step at a time."
        elif expertise == 'intermediate':
            intro_text = f"Welcome back to R programming! Today, we're diving into {topic_specifics['intro']}, building on the foundational knowledge you already have. This {content_length} tutorial will help you take your skills to the next level."
            explanation_depth = "Now that you understand the basics of R, let's explore how this works."
            encouragement = "Great! You can see how this connects to what you already know."
        else:  # expert
            intro_text = f"Welcome to this advanced tutorial on {topic_specifics['intro']}. In this {content_length} guide, we'll explore sophisticated techniques and optimizations that will enhance your R programming expertise."
            explanation_depth = "Let's examine the implementation details and performance considerations."
            encouragement = "Excellent! You can see the powerful applications of this approach."

        content = f"""# R Tutorial: {topic}

## Introduction

{intro_text}

## What You'll Learn

By the end of this tutorial, you'll be able to:
- Understand the core concepts of {topic} in R
- Implement practical solutions using {topic}
- Apply best practices for {expertise}-level development
- Recognize common pitfalls and how to avoid them

## Getting Started

Let's begin by setting up our R environment. First, we'll load the packages we need for this tutorial.

```r
# Let's load the essential packages for {topic}
library(tidyverse)  # For data manipulation and visualization
library(here)       # For project organization

# Let's also check our R version to ensure compatibility
R.version.string
```

{explanation_depth} The tidyverse package gives us access to powerful tools like dplyr for data manipulation and ggplot2 for visualization. These will be essential for our work with {topic}.

## Core Concepts

### Understanding {topic}

{topic} is a fundamental concept in R that allows us to work more effectively with data. Let me walk you through the key principles.

The most important thing to understand about {topic} is how it fits into your overall R workflow. Think of it as a bridge between your raw data and the insights you want to extract.

### Key Components

Let's break down the essential components:

1. **Data Structure**: How {topic} organizes information
2. **Functions**: The tools we use to work with {topic}
3. **Applications**: Real-world uses in data analysis

## Hands-On Practice

Now, let's put this into practice with a concrete example. I'll walk you through each step.

### Step 1: Creating Sample Data

```r
# Let's create some sample data to work with
sample_data <- data.frame(
  category = c("A", "B", "C", "A", "B", "C"),
  values = c(10, 15, 12, 18, 22, 14),
  dates = seq(as.Date("2024-01-01"), by = "month", length.out = 6)
)

# Let's take a look at what we've created
print(sample_data)
```

Perfect! Now we have a dataset that demonstrates the key principles of {topic}. Notice how each row represents an observation, and each column represents a different variable.

### Step 2: Basic Implementation

```r
# Now let's apply {topic} concepts to our data
result <- sample_data %>%
  group_by(category) %>%
  summarise(
    mean_value = mean(values),
    total_observations = n(),
    .groups = "drop"
  )

print(result)
```

{encouragement} You can see how we've transformed our original data into meaningful insights using {topic} principles.

## Real-World Applications

Let me share some practical scenarios where {topic} becomes incredibly valuable:

### Business Analytics
In business settings, {topic} helps analysts understand customer behavior, sales patterns, and market trends. For example, you might use these techniques to segment customers or identify seasonal patterns in sales data.

### Research Applications
Researchers across many fields use {topic} to analyze experimental data, survey responses, and observational studies. The ability to systematically examine patterns makes it an essential tool in the research toolkit.

### Data Science Projects
In data science, {topic} forms the foundation for more advanced techniques like machine learning and predictive modeling. Understanding these fundamentals is crucial for building robust analytical solutions.

## Best Practices and Tips

Here are some important guidelines to keep in mind:

### Code Organization
Always write clear, well-commented code. Your future self will thank you! Use meaningful variable names that describe what the data represents.

### Data Validation
Before applying {topic} techniques, always check your data quality. Look for missing values, outliers, and inconsistencies that might affect your results.

### Reproducibility
Make your work reproducible by setting random seeds, documenting your process, and organizing your files systematically.

## Common Pitfalls to Avoid

Let me highlight some mistakes I often see:

1. **Rushing the exploration phase**: Take time to understand your data before jumping into analysis
2. **Ignoring data types**: Make sure your variables are properly formatted (numeric, factor, date, etc.)
3. **Forgetting to validate results**: Always sense-check your outputs

## Summary and Next Steps

Congratulations! You've learned the essentials of {topic} in R. Let's recap the key points:

- We explored the fundamental concepts and terminology
- You learned practical implementation techniques
- We covered real-world applications and use cases
- You now understand common pitfalls and how to avoid them

### Recommended Practice
To reinforce what you've learned, try applying these concepts to your own datasets. Start with simple examples and gradually work up to more complex scenarios.

### Further Learning
Consider exploring these related topics:
- Advanced R programming techniques
- Statistical modeling in R
- Data visualization best practices
- R package development

### Resources
- R documentation and help files (use `?function_name`)
- RStudio community forums
- Online R courses and tutorials
- Local R user groups and meetups

## Final Thoughts

Remember, learning R is a journey, not a destination. Each concept you master opens doors to new possibilities in data analysis and statistical computing.

Keep practicing, stay curious, and don't hesitate to experiment with different approaches. The R community is incredibly supportive, so don't be afraid to ask questions and share your discoveries.

Thank you for joining me in this exploration of {topic}. Happy coding!

---

*This tutorial provides foundational knowledge to get you started. For more advanced content and personalized learning paths, consider upgrading to access AI-powered tutorials with OpenRouter integration.*"""

        return {
            'content': content,
            'concepts': topic_specifics['concepts'],
            'packages': topic_specifics['packages'],
            'objectives': [
                f'Understand core concepts of {topic} in R',
                f'Implement practical {topic} solutions',
                'Apply best practices for clean, readable code',
                'Recognize and avoid common pitfalls'
            ],
            'is_premium': False,
            'estimated_reading_time': max(1, duration),
            'difficulty_score': {'beginner': 3, 'intermediate': 6, 'expert': 9}[expertise],
            'character_count': len(content),
            'word_count': len(content.split()),
            'topic_category': self._categorize_topic(topic),
            'generated_via': 'enhanced_fallback',
            'model_used': 'local_generation'
        }
    
    def get_model_status(self):
        """Get status of OpenRouter connection and available models with caching"""
        current_time = time.time()
        
        # Return cached result if still valid
        if (self._model_status_cache and 
            current_time - self._model_status_cache_time < self._cache_duration):
            return self._model_status_cache
        
        try:
            headers = self._get_headers()
            response = requests.get(f"{self.base_url}/models", headers=headers, timeout=10)
            
            if response.status_code == 200:
                models = response.json()
                status = {
                    'status': 'connected',
                    'model_count': len(models.get('data', [])),
                    'api_key_valid': True,
                    'last_check': datetime.now().isoformat()
                }
            else:
                status = {
                    'status': 'error',
                    'error': f"HTTP {response.status_code}",
                    'api_key_valid': False,
                    'last_check': datetime.now().isoformat()
                }
                
        except Exception as e:
            status = {
                'status': 'error',
                'error': str(e),
                'api_key_valid': False,
                'last_check': datetime.now().isoformat()
            }
        
        # Cache the result
        self._model_status_cache = status
        self._model_status_cache_time = current_time
        return status

# Initialize global service instance
openrouter_service = OpenRouterService()