from flask import Flask, render_template, request, jsonify, send_file, url_for
import os
import random
import time
import requests
import json
from datetime import datetime
import tempfile
import base64
from io import BytesIO
import threading
from queue import Queue

app = Flask(__name__)

# Configuration
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"  # Replace with actual DeepSeek API
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', 'your-api-key-here')

TTS_OPTIONS = {
    'local_tts': {
        'enabled': True
    }
}

# Enhanced R-specific content templates
R_TOPICS_CONTENT = {
    'data structures': {
        'beginner': {
            'concepts': ['vectors', 'lists', 'data frames', 'matrices', 'factors'],
            'code_examples': [
                '# Creating vectors\nnumeric_vector <- c(1, 2, 3, 4, 5)\ncharacter_vector <- c("R", "is", "awesome")',
                '# Creating data frames\ndf <- data.frame(\n  name = c("Alice", "Bob", "Charlie"),\n  age = c(25, 30, 35),\n  city = c("NYC", "LA", "Chicago")\n)',
                '# Accessing elements\ndf$name  # Access column\ndf[1, ]  # Access first row\ndf[df$age > 25, ]  # Conditional selection'
            ],
            'packages': ['base', 'utils'],
            'learning_objectives': [
                'Understanding R\'s fundamental data types',
                'Creating and manipulating vectors',
                'Working with data frames effectively',
                'Basic indexing and subsetting techniques'
            ]
        },
        'intermediate': {
            'concepts': ['advanced indexing', 'data manipulation', 'merging datasets', 'data types conversion'],
            'code_examples': [
                '# Advanced indexing with dplyr\nlibrary(dplyr)\ndf %>% \n  filter(age > 25) %>% \n  select(name, city) %>%\n  arrange(desc(age))',
                '# Merging datasets\ndf1 <- data.frame(id = 1:3, value = c(10, 20, 30))\ndf2 <- data.frame(id = 2:4, score = c(85, 90, 95))\nmerged <- merge(df1, df2, by = "id", all = TRUE)'
            ],
            'packages': ['dplyr', 'tidyr', 'data.table'],
            'learning_objectives': [
                'Mastering dplyr for data manipulation',
                'Understanding different types of joins',
                'Efficient data transformation techniques',
                'Working with missing data'
            ]
        },
        'expert': {
            'concepts': ['memory optimization', 'custom data structures', 'S3/S4 classes', 'big data handling'],
            'code_examples': [
                '# Creating S4 class\nsetClass("Person",\n  slots = list(\n    name = "character",\n    age = "numeric",\n    skills = "list"\n  )\n)',
                '# Memory-efficient operations with data.table\nlibrary(data.table)\nDT <- fread("large_file.csv")  # Fast reading\nDT[age > 25, .(avg_score = mean(score)), by = city]'
            ],
            'packages': ['data.table', 'R6', 'methods'],
            'learning_objectives': [
                'Building custom R classes and methods',
                'Optimizing memory usage for large datasets',
                'Advanced data.table operations',
                'Creating reusable R packages'
            ]
        }
    },
    'ggplot2': {
        'beginner': {
            'concepts': ['grammar of graphics', 'basic plots', 'aesthetics', 'geoms'],
            'code_examples': [
                'library(ggplot2)\n# Basic scatter plot\nggplot(mtcars, aes(x = mpg, y = hp)) + \n  geom_point(size = 3, color = "blue") +\n  labs(title = "Car Performance", x = "Miles per Gallon", y = "Horsepower")',
                '# Box plot by category\nggplot(iris, aes(x = Species, y = Sepal.Length, fill = Species)) + \n  geom_boxplot() +\n  theme_minimal()'
            ],
            'packages': ['ggplot2'],
            'learning_objectives': [
                'Understanding the grammar of graphics',
                'Creating basic plots (scatter, box, bar)',
                'Mapping data to visual aesthetics',
                'Adding labels and titles'
            ]
        },
        'intermediate': {
            'concepts': ['faceting', 'themes', 'scales', 'statistical layers'],
            'code_examples': [
                '# Faceted plot with custom theme\nggplot(mtcars, aes(x = mpg, y = hp, color = factor(cyl))) + \n  geom_point() + \n  geom_smooth(method = "lm") +\n  facet_wrap(~cyl) +\n  theme_minimal() +\n  scale_color_brewer(palette = "Set1")',
                '# Advanced histogram with density overlay\nggplot(iris, aes(x = Sepal.Length, fill = Species)) + \n  geom_histogram(alpha = 0.7, position = "identity") +\n  geom_density(alpha = 0.3) +\n  facet_grid(Species ~ .)'
            ],
            'packages': ['ggplot2', 'RColorBrewer', 'scales'],
            'learning_objectives': [
                'Creating multi-panel plots with faceting',
                'Customizing themes and colors',
                'Adding statistical layers and smoothers',
                'Working with scales and transformations'
            ]
        }
    },
    'shiny': {
        'beginner': {
            'concepts': ['reactive programming', 'UI layouts', 'server logic', 'inputs and outputs'],
            'code_examples': [
                '# Basic Shiny app structure\nlibrary(shiny)\n\nui <- fluidPage(\n  titlePanel("My First Shiny App"),\n  sidebarLayout(\n    sidebarPanel(\n      sliderInput("obs", "Number of observations:", min = 1, max = 1000, value = 500)\n    ),\n    mainPanel(\n      plotOutput("distPlot")\n    )\n  )\n)',
                '# Server logic\nserver <- function(input, output) {\n  output$distPlot <- renderPlot({\n    hist(rnorm(input$obs), col = "darkgray", border = "white")\n  })\n}\n\nshinyApp(ui = ui, server = server)'
            ],
            'packages': ['shiny', 'DT'],
            'learning_objectives': [
                'Understanding reactive programming concepts',
                'Building basic user interfaces',
                'Connecting inputs to outputs',
                'Running and deploying Shiny apps'
            ]
        }
    }
}

class AudioGenerator:
    def __init__(self):
        self.audio_queue = Queue()
        self.processing = False
    
    def generate_tutorial_script(self, topic, expertise, duration, learning_objectives, concepts, code_examples):
        """Generate a comprehensive tutorial script using DeepSeek or similar model"""
        
        prompt = f"""You are an expert R programming instructor creating an audio tutorial. Generate a comprehensive, engaging script for a {duration}-minute audio tutorial on "{topic}" for {expertise} level R developers.

REQUIREMENTS:
- Duration: Exactly {duration} minutes of spoken content
- Audience: {expertise.title()} R developers
- Topic: {topic}
- Include natural speech patterns, pauses, and transitions
- Make it conversational and engaging
- Include clear explanations of concepts
- Reference provided code examples naturally
- Add practical tips and best practices

KEY CONCEPTS TO COVER:
{', '.join(concepts)}

LEARNING OBJECTIVES:
{chr(10).join([f"- {obj}" for obj in learning_objectives])}

CODE EXAMPLES TO REFERENCE:
{chr(10).join(code_examples)}

FORMAT:
- Start with a warm welcome and overview
- Break content into logical sections
- Include natural transitions between topics
- Add practical tips and real-world applications
- End with a summary and next steps
- Use conversational tone with appropriate pauses [PAUSE]
- Include emphasis markers for important points [EMPHASIS]

Generate the complete tutorial script now:"""

        try:
            # Try DeepSeek API first
            response = self._call_deepseek_api(prompt)
            if response:
                return response
            
            # Fallback to local generation
            return self._generate_local_script(topic, expertise, duration, concepts, code_examples)
            
        except Exception as e:
            print(f"Error generating script: {e}")
            return self._generate_local_script(topic, expertise, duration, concepts, code_examples)
    
    def _call_deepseek_api(self, prompt):
        """Call DeepSeek API for content generation"""
        try:
            headers = {
                'Authorization': f'Bearer {DEEPSEEK_API_KEY}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': 'deepseek-chat',  # or appropriate model name
                'messages': [
                    {
                        'role': 'system',
                        'content': 'You are an expert R programming instructor specializing in creating engaging audio tutorials.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'max_tokens': 2000,
                'temperature': 0.7
            }
            
            response = requests.post(
                DEEPSEEK_API_URL,
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                print(f"DeepSeek API error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"DeepSeek API call failed: {e}")
            return None
    
    def _generate_local_script(self, topic, expertise, duration, concepts, code_examples):
        """Fallback local script generation"""
        
        intro = f"""Welcome to this {duration}-minute R programming tutorial on {topic}! 
        
[PAUSE] My name is your AI R tutor, and today we'll be exploring {topic} specifically designed for {expertise} level R developers.

[PAUSE] By the end of this tutorial, you'll have a solid understanding of {', '.join(concepts[:3])} and be ready to apply these concepts in your own R projects."""

        main_content = f"""
Let's start with the fundamentals. [PAUSE]

{topic} is a crucial concept in R programming that every {expertise} developer should master. [EMPHASIS] This is particularly important because it forms the foundation for more advanced R programming techniques.

[PAUSE] Let me walk you through some practical examples.

{code_examples[0] if code_examples else "# Example R code would be discussed here"}

[PAUSE] As you can see in this code, we're demonstrating the key principles of {concepts[0] if concepts else topic}. [EMPHASIS] Notice how we structure the code for clarity and efficiency.

[PAUSE] Now, let's explore some best practices that will make your R code more robust and maintainable."""

        conclusion = f"""
[PAUSE] To summarize what we've covered today:

We explored {', '.join(concepts[:2])} and learned how to apply these concepts practically in R.

[EMPHASIS] Remember, the key to mastering {topic} is consistent practice and experimentation.

[PAUSE] For your next steps, I recommend practicing with the code examples we discussed and exploring the {', '.join(["dplyr", "ggplot2"]) if "data" in topic.lower() else ["base R functions"]} packages.

Thank you for joining this R programming tutorial. Keep coding, and happy learning!"""

        return f"{intro}\n\n{main_content}\n\n{conclusion}"
    
    def text_to_speech(self, text, voice_settings=None):
        """Convert text to speech using available TTS services"""
        
        if voice_settings is None:
            voice_settings = {
                'voice': 'alloy',
                'speed': 1.0,
                'service': 'openai'
            }
        
        # Clean text for TTS
        clean_text = self._clean_text_for_tts(text)
        
        # Try different TTS services in order of preference
        for service in ['openai', 'elevenlabs', 'local_tts']:
            try:
                audio_data = self._generate_audio_with_service(clean_text, service, voice_settings)
                if audio_data:
                    return audio_data
            except Exception as e:
                print(f"TTS service {service} failed: {e}")
                continue
        
        # If all services fail, return placeholder
        return self._generate_placeholder_audio()
    
    def _clean_text_for_tts(self, text):
        """Clean text for better TTS pronunciation"""
        # Remove special markers
        text = text.replace('[PAUSE]', '. ')
        text = text.replace('[EMPHASIS]', '')
        
        # Clean up R-specific terms for better pronunciation
        replacements = {
            'ggplot2': 'g g plot two',
            'dplyr': 'd ply r',
            'tidyr': 'tidy r',
            'R programming': 'R programming',
            'data.frame': 'data frame',
            'data.table': 'data table'
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text
    
    def _generate_audio_with_service(self, text, service, voice_settings):
        """Generate audio using specific TTS service"""
        
        if service == 'openai' and TTS_OPTIONS['openai']['key']:
            return self._openai_tts(text, voice_settings)
        elif service == 'elevenlabs' and TTS_OPTIONS['elevenlabs']['key']:
            return self._elevenlabs_tts(text, voice_settings)
        elif service == 'local_tts':
            return self._local_tts(text, voice_settings)
        
        return None
    
    def _openai_tts(self, text, voice_settings):
        """Generate audio using OpenAI TTS"""
        try:
            headers = {
                'Authorization': f'Bearer {TTS_OPTIONS["openai"]["key"]}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': 'tts-1',
                'input': text,
                'voice': voice_settings.get('voice', 'alloy'),
                'speed': voice_settings.get('speed', 1.0)
            }
            
            response = requests.post(
                TTS_OPTIONS['openai']['url'],
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                return response.content
            
        except Exception as e:
            print(f"OpenAI TTS error: {e}")
        
        return None
    
    def _elevenlabs_tts(self, text, voice_settings):
        """Generate audio using ElevenLabs TTS"""
        try:
            voice_id = voice_settings.get('voice_id', TTS_OPTIONS['elevenlabs']['voices'][0])
            
            headers = {
                'Accept': 'audio/mpeg',
                'Content-Type': 'application/json',
                'xi-api-key': TTS_OPTIONS['elevenlabs']['key']
            }
            
            data = {
                'text': text,
                'model_id': 'eleven_monolingual_v1',
                'voice_settings': {
                    'stability': 0.5,
                    'similarity_boost': 0.5,
                    'style': 0.5,
                    'use_speaker_boost': True
                }
            }
            
            response = requests.post(
                f"{TTS_OPTIONS['elevenlabs']['url']}/{voice_id}",
                json=data,
                headers=headers,
                timeout=60
            )
            
            if response.status_code == 200:
                return response.content
                
        except Exception as e:
            print(f"ElevenLabs TTS error: {e}")
        
        return None
    
    def _local_tts(self, text, voice_settings):
        """Generate audio using local TTS (pyttsx3 or similar)"""
        try:
            import pyttsx3
            import io
            import wave
            
            engine = pyttsx3.init()
            
            # Configure voice settings
            rate = engine.getProperty('rate')
            engine.setProperty('rate', int(rate * voice_settings.get('speed', 1.0)))
            
            # Create temporary file for audio
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                engine.save_to_file(text, temp_file.name)
                engine.runAndWait()
                
                # Read the audio file
                with open(temp_file.name, 'rb') as audio_file:
                    audio_data = audio_file.read()
                
                # Clean up
                os.unlink(temp_file.name)
                
                return audio_data
                
        except ImportError:
            print("pyttsx3 not available, install with: pip install pyttsx3")
        except Exception as e:
            print(f"Local TTS error: {e}")
        
        return None
    
    def _generate_placeholder_audio(self):
        """Generate a silent placeholder audio message using pydub"""
        try:
            from pydub import AudioSegment
            import io
            
            # Create a 1-second silent audio segment
            silence = AudioSegment.silent(duration=1000)  # 1000ms = 1 second
            
            # Export to MP3 format in memory
            buf = io.BytesIO()
            silence.export(buf, format="mp3")
            buf.seek(0)
            
            return buf.read()
            
        except ImportError:
            print("pydub not available. Install with: pip install pydub")
            # Fallback to a simple message if pydub is not available
            placeholder_text = "Audio generation failed. Please check your TTS service configuration and ensure pydub is installed."
            return self._local_tts(placeholder_text, {'speed': 1.0})
        except Exception as e:
            print(f"Error generating placeholder audio with pydub: {e}")
            # Fallback to local TTS if pydub fails
            placeholder_text = "Audio generation failed. Please check your TTS service configuration."
            return self._local_tts(placeholder_text, {'speed': 1.0})

# Initialize audio generator
audio_generator = AudioGenerator()

# Ensure the directory for generated audio exists
if not os.path.exists('static/generated_audio'):
    os.makedirs('static/generated_audio')

def get_topic_content(topic, expertise):
    """Get content for a specific topic and expertise level"""
    topic_key = None
    for key in R_TOPICS_CONTENT.keys():
        if key.lower() in topic.lower():
            topic_key = key
            break
    
    if topic_key and expertise in R_TOPICS_CONTENT[topic_key]:
        return R_TOPICS_CONTENT[topic_key][expertise]
    
    # Return default content structure
    return {
        'concepts': ['fundamental concepts', 'practical applications', 'best practices'],
        'code_examples': [f'# {topic} example\n# Code would be specific to the topic'],
        'packages': ['base'],
        'learning_objectives': [
            f'Understanding {topic} fundamentals',
            'Applying concepts in real projects',
            'Following R best practices'
        ]
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit_form():
    try:
        # Get form data
        topic = request.form.get('topic', '').strip()
        expertise = request.form.get('expertise', '').strip()
        duration = request.form.get('duration', '5').strip()
        voice_settings = {
            'voice': request.form.get('voice', 'alloy'),
            'speed': float(request.form.get('speed', 1.0)),
            'service': request.form.get('tts_service', 'openai')
        }
        
        # Validate input
        if not topic or not expertise:
            return jsonify({
                'success': False,
                'error': 'Please fill in all required fields'
            }), 400
        
        # Get topic-specific content
        content_data = get_topic_content(topic, expertise)
        
        # Generate tutorial script
        tutorial_script = audio_generator.generate_tutorial_script(
            topic=topic,
            expertise=expertise,
            duration=int(duration),
            learning_objectives=content_data['learning_objectives'],
            concepts=content_data['concepts'],
            code_examples=content_data['code_examples']
        )
        
        # Generate audio (this might take a while)
        audio_data = audio_generator.text_to_speech(tutorial_script, voice_settings)
        
        # Save audio to temporary file and encode for response
        audio_base64 = None
        stream_url = None
        download_url = None
        
        if audio_data:
            # Save to static/generated_audio
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"r_tutorial_{timestamp}.mp3"
            filepath = os.path.join('static', 'generated_audio', filename)
            
            with open(filepath, 'wb') as f:
                f.write(audio_data)
            
            # Encode for web playback
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            audio_url = url_for('static', filename=f'generated_audio/{filename}', _external=True)
        
        return jsonify({
            'success': True,
            'audio_content': tutorial_script,
            'topic': topic,
            'expertise': expertise,
            'duration': duration,
            'r_packages': content_data['packages'],
            'learning_objectives': content_data['learning_objectives'],
            'estimated_lines_of_code': random.randint(10, 50),
            'difficulty_score': random.randint(1, 10),
            'audio_base64': audio_base64,
            'audio_url': audio_url,
            'audio_available': audio_data is not None
        })
        
    except Exception as e:
        print(f"Error in submit_form: {e}")
        return jsonify({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }), 500


@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'services': {
            'deepseek_api': bool(DEEPSEEK_API_KEY and DEEPSEEK_API_KEY != 'your-api-key-here'),
            'openai_tts': bool(TTS_OPTIONS['openai']['key']),
            'elevenlabs_tts': bool(TTS_OPTIONS['elevenlabs']['key']),
            'local_tts': TTS_OPTIONS['local_tts']['enabled']
        }
    })

if __name__ == '__main__':
    # Install required packages check
    required_packages = ['requests', 'flask']
    try:
        import pyttsx3
        print("✓ pyttsx3 available for local TTS")
    except ImportError:
        print("⚠ pyttsx3 not available. Install with: pip install pyttsx3")
    
    print("🚀 Starting Ephicacy R Tutor with Audio Generation...")
    print("🔧 Configure API keys in environment variables:")
    print("   - DEEPSEEK_API_KEY for content generation")
    print("   - OPENAI_API_KEY for high-quality TTS")
    print("   - ELEVENLABS_API_KEY for premium TTS")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
