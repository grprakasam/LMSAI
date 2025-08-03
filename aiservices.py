# aiservices.py - Modified for free access to all content
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
    """Enhanced AI tutorial generator with free access to all features"""
    
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
        Generate comprehensive tutorial content - all features available to everyone
        
        Args:
            topic: R programming topic
            expertise: beginner, intermediate, expert
            duration: tutorial length in minutes
            user_plan: always treated as having full access
            
        Returns:
            Dictionary with content, concepts, packages, objectives, etc.
        """
        try:
            # Everyone gets access to all content now
            content_pool = R_TOPICS_CONTENT['all_topics']
            max_duration = duration  # No duration limits
            
            # Get topic-specific data
            topic_data = self._get_topic_data(topic, expertise, content_pool)
            
            # Always try to generate AI script for better quality
            if self.deepseek_key or self.openai_key:
                script = self._generate_ai_script(topic, expertise, max_duration, topic_data)
            else:
                script = self._generate_enhanced_script(topic, expertise, max_duration, topic_data)
            
            # Enhanced content for all users
            enhanced_data = self._enhance_content_for_all_users(topic_data)
            
            return {
                'content': script,
                'concepts': enhanced_data['concepts'],
                'packages': enhanced_data['packages'],
                'objectives': enhanced_data['learning_objectives'],
                'is_premium': True,  # Everyone gets premium content
                'estimated_reading_time': self._estimate_reading_time(script),
                'difficulty_score': self._calculate_difficulty_score(expertise, topic),
                'code_examples_count': len(enhanced_data.get('code_examples', [])),
                'topic_category': self._categorize_topic(topic),
                'advanced_tips': enhanced_data.get('advanced_tips', []),
                'real_world_applications': enhanced_data.get('real_world_applications', [])
            }
            
        except Exception as e:
            logger.error(f"Error generating tutorial content: {e}")
            return self._get_fallback_content(topic, expertise, duration)
    
    def _get_topic_data(self, topic: str, expertise: str, content_pool: Dict) -> Dict:
        """Get topic-specific data from content pool"""
        # Search for matching topic (case-insensitive, partial match)
        for topic_key, topic_content in content_pool.items():
            if topic_key.lower() in topic.lower() or any(word.lower() in topic.lower() for word in topic_key.split()):
                if expertise in topic_content:
                    return topic_content[expertise]
                # Fallback to available expertise level
                elif topic_content:
                    return list(topic_content.values())[0]
        
        # Enhanced default fallback based on expertise level
        default_concepts = {
            'beginner': ['fundamental concepts', 'basic syntax', 'practical examples', 'step-by-step approach'],
            'intermediate': ['advanced techniques', 'best practices', 'real-world applications', 'optimization'],
            'expert': ['advanced concepts', 'optimization', 'complex implementations', 'cutting-edge techniques']
        }
        
        default_packages = {
            'beginner': ['base', 'utils'],
            'intermediate': ['base', 'dplyr', 'ggplot2'],
            'expert': ['base', 'tidyverse', 'advanced packages']
        }
        
        return {
            'concepts': default_concepts.get(expertise, ['fundamental concepts', 'practical applications']),
            'code_examples': [f'# {topic} - {expertise} level tutorial\n# Comprehensive R examples\nlibrary(tidyverse)\n\n# Your {topic} journey starts here!'],
            'packages': default_packages.get(expertise, ['base']),
            'learning_objectives': [
                f'Master {topic} fundamentals',
                f'Implement {topic} in real projects',
                f'Apply {topic} best practices',
                f'Troubleshoot common {topic} issues'
            ]
        }
    
    def _generate_ai_script(self, topic: str, expertise: str, duration: int, topic_data: Dict) -> str:
        """Generate high-quality content using AI"""
        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        
        self.last_request_time = time.time()
        
        # Create comprehensive prompt
        prompt = self._create_comprehensive_prompt(topic, expertise, duration, topic_data)
        
        # Try DeepSeek first, then OpenAI as fallback
        if self.deepseek_key:
            response = self._call_deepseek_api(prompt)
            if response:
                return response
        elif self.openai_key:
            response = self._call_openai_api(prompt)
            if response:
                return response
        
        # Fallback to enhanced script if AI services fail
        return self._generate_enhanced_script(topic, expertise, duration, topic_data)
    
    def _create_comprehensive_prompt(self, topic: str, expertise: str, duration: int, topic_data: Dict) -> str:
        """Create a comprehensive prompt for AI content generation"""
        # Calculate content proportions
        total_seconds = duration * 60
        intro_seconds = min(60, total_seconds * 0.15)  # 15% or 60 seconds max
        core_seconds = total_seconds * 0.50  # 50%
        examples_seconds = total_seconds * 0.25  # 25%
        summary_seconds = total_seconds * 0.10  # 10%
        
        prompt = f"""Create a comprehensive {duration}-minute R programming tutorial on "{topic}" for {expertise} level users.

**Tutorial Structure:**
1. Introduction and Overview ({int(intro_seconds)} seconds)
   - Hook the audience with real-world relevance
   - Clear learning objectives
   - Prerequisites and setup

2. Core Concepts Deep Dive ({int(core_seconds)} seconds)
   - Detailed explanations with visual metaphors
   - Key concepts: {', '.join(topic_data['concepts'])}
   - Theory to practice connections
   - Common misconceptions and clarifications

3. Hands-On Code Examples ({int(examples_seconds)} seconds)
   - Multiple practical examples with detailed comments
   - Progressive difficulty building
   - Real-world applications and use cases
   - Relevant packages: {', '.join(topic_data['packages'])}
   - Debugging and troubleshooting tips

4. Summary and Advanced Tips ({int(summary_seconds)} seconds)
   - Key takeaways and recap
   - Pro tips and advanced techniques
   - Next steps for continued learning
   - Resources and further reading

**Content Requirements:**
- Write in a conversational, engaging style
- Include natural pauses [PAUSE] for reflection
- Add emphasis markers [EMPHASIS] for key points
- Include code execution markers [EXECUTE] for hands-on practice
- Provide troubleshooting sections [TROUBLESHOOT]
- Add best practices callouts [BEST_PRACTICE]
- Include real-world examples [REAL_WORLD]

**Quality Standards:**
- Accuracy: All code must be syntactically correct
- Clarity: Explain complex concepts in simple terms
- Engagement: Use analogies and real-world connections
- Practicality: Focus on immediately applicable skills
- Progression: Build knowledge systematically

Target Audience: {expertise.capitalize()} level R programmers seeking practical, actionable knowledge.

Make this tutorial comprehensive, engaging, and immediately useful for learners."""

        return prompt
    
    def _call_deepseek_api(self, prompt: str) -> Optional[str]:
        """Call DeepSeek API for content generation"""
        headers = {
            'Authorization': f'Bearer {self.deepseek_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': 'deepseek-chat',
            'messages': [
                {'role': 'system', 'content': 'You are an expert R programming instructor with 15+ years of experience teaching data science, statistics, and R programming to learners at all levels. You create engaging, practical, and comprehensive tutorials.'},
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': 3000,  # Increased for more comprehensive content
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
        """Call OpenAI API for content generation"""
        headers = {
            'Authorization': f'Bearer {self.openai_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': 'gpt-3.5-turbo',
            'messages': [
                {'role': 'system', 'content': 'You are an expert R programming instructor with 15+ years of experience teaching data science, statistics, and R programming to learners at all levels. You create engaging, practical, and comprehensive tutorials.'},
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': 3000,  # Increased for more comprehensive content
            'temperature': 0.7
        }
        
        try:
            response = requests.post(self.openai_url, headers=headers, json=data, timeout=30)
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
        
        return None
    
    def _generate_enhanced_script(self, topic: str, expertise: str, duration: int, topic_data: Dict) -> str:
        """Generate enhanced content when AI is not available"""
        return f"""# R Tutorial: {topic} ({expertise.title()} Level)

[PAUSE] Welcome to this comprehensive {duration}-minute tutorial on {topic}! 

## Learning Objectives
By the end of this tutorial, you'll be able to:
{chr(10).join(f"- {obj}" for obj in topic_data['learning_objectives'])}

[PAUSE] Let's dive into the fascinating world of {topic}!

## Core Concepts

[EMPHASIS] Key concepts we'll explore today:
{chr(10).join(f"- **{concept.title()}**: Essential for mastering {topic}" for concept in topic_data['concepts'])}

[PAUSE] These concepts form the foundation of effective {topic} usage in R.

## Hands-On Examples

[EXECUTE] Let's start with practical code examples:

```r
{topic_data['code_examples'][0] if topic_data['code_examples'] else f'# {topic} practical example\n# Step-by-step implementation'}
```

[BEST_PRACTICE] **Pro Tip**: Always comment your code for better maintainability and team collaboration.

[TROUBLESHOOT] **Common Issues**:
- Ensure all required packages are installed
- Check data types and structure
- Verify column names and case sensitivity

## R Packages Used

[EMPHASIS] Essential packages for {topic}:
{chr(10).join(f"- **{pkg}**: Core functionality for {topic}" for pkg in topic_data['packages'])}

[EXECUTE] Install packages if needed:
```r
install.packages(c({', '.join(f'"{pkg}"' for pkg in topic_data['packages'])}))
```

## Real-World Applications

[REAL_WORLD] {topic} is widely used in:
- Data analysis and visualization
- Statistical modeling and inference
- Business intelligence and reporting
- Research and academic studies

## Advanced Techniques

[EMPHASIS] For {expertise} level practitioners:
- Optimize performance with vectorized operations
- Implement error handling and validation
- Create reusable functions and workflows
- Document your analysis thoroughly

## Summary and Next Steps

[PAUSE] Congratulations! You've learned the essentials of {topic} in R.

**Key takeaways:**
{chr(10).join(f"✓ {concept}" for concept in topic_data['concepts'][:3])}

**Continue your learning journey:**
- Practice with real datasets
- Explore advanced {topic} techniques
- Join R communities and forums
- Build projects using {topic}

[EMPHASIS] Remember: The best way to master {topic} is through consistent practice and real-world application!

Thank you for learning with R Tutor Pro - where every concept becomes clear and actionable!"""
        
        return script
    
    def _enhance_content_for_all_users(self, topic_data: Dict) -> Dict:
        """Enhance content for all users (no premium restrictions)"""
        enhanced_data = {
            'concepts': topic_data.get('concepts', []),
            'packages': topic_data.get('packages', ['base']),
            'learning_objectives': topic_data.get('learning_objectives', []),
            'code_examples': topic_data.get('code_examples', [])
        }
        
        # Add advanced features for everyone
        enhanced_data['advanced_tips'] = [
            'Use vectorized operations for better performance',
            'Always validate your data before analysis',
            'Write reusable functions to avoid code repetition',
            'Document your code and analysis process',
            'Use version control for your R projects',
            'Follow R style guides for consistent coding'
        ]
        
        enhanced_data['real_world_applications'] = [
            'Business analytics and reporting',
            'Scientific research and data analysis',
            'Machine learning and predictive modeling',
            'Data visualization and storytelling',
            'Statistical analysis and inference'
        ]
        
        enhanced_data['troubleshooting_tips'] = [
            'Check for missing values and handle appropriately',
            'Verify data types match your expectations',
            'Use debugging tools like browser() and debug()',
            'Read error messages carefully for clues',
            'Test with small datasets first'
        ]
        
        enhanced_data['best_practices'] = [
            'Write clean, readable code with meaningful variable names',
            'Use consistent coding style throughout your project',
            'Comment your code to explain the why, not just the what',
            'Break complex problems into smaller, manageable pieces',
            'Test your code with different input scenarios'
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
        # Adjust based on topic complexity
        if any(word in topic.lower() for word in ['advanced', 'machine learning', 'neural', 'bayesian', 'optimization']):
            base_score += 2
        elif any(word in topic.lower() for word in ['basic', 'intro', 'fundamentals', 'getting started']):
            base_score -= 1
        return min(10, max(1, base_score))
    
    def _categorize_topic(self, topic: str) -> str:
        """Categorize topic into broader categories"""
        topic_lower = topic.lower()
        if any(word in topic_lower for word in ['data frame', 'vector', 'list', 'matrix', 'structure']):
            return 'data_structures'
        elif any(word in topic_lower for word in ['plot', 'graph', 'visual', 'chart', 'ggplot']):
            return 'visualization'
        elif any(word in topic_lower for word in ['model', 'regression', 'machine learning', 'statistic', 'analysis']):
            return 'modeling'
        elif any(word in topic_lower for word in ['function', 'package', 'library', 'programming']):
            return 'programming'
        elif any(word in topic_lower for word in ['dplyr', 'tidyr', 'wrangle', 'clean', 'transform']):
            return 'data_wrangling'
        elif any(word in topic_lower for word in ['shiny', 'web', 'app', 'dashboard', 'interactive']):
            return 'web_development'
        else:
            return 'general'
    
    def _get_fallback_content(self, topic: str, expertise: str, duration: int) -> Dict:
        """Provide fallback content if all generation methods fail"""
        return {
            'content': f"""# R Tutorial: {topic}

Welcome to this {duration}-minute tutorial on {topic} for {expertise} level learners!

## Introduction
{topic} is an important concept in R programming that will enhance your data analysis capabilities.

## Key Concepts
- Understanding the fundamentals of {topic}
- Practical applications in real-world scenarios
- Best practices and common pitfalls

## Code Example
```r
# {topic} example
library(tidyverse)

# Your code here
print("Hello, R learners!")
```

## Summary
You've learned the basics of {topic}. Keep practicing to master these concepts!

Thank you for using R Tutor Pro!""",
            'concepts': ['fundamentals', 'applications', 'best practices'],
            'packages': ['base', 'tidyverse'],
            'objectives': [f'Understand {topic}', 'Apply concepts', 'Follow best practices'],
            'is_premium': True,
            'estimated_reading_time': max(1, duration // 2),
            'difficulty_score': 5,
            'code_examples_count': 1,
            'topic_category': 'general'
        }

# Initialize AI generator instance
ai_generator = AITutorialGenerator()