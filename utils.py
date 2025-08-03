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

class AudioGenerator:
    def __init__(self):
        self.audio_queue = Queue()
        self.processing = False
    
    def generate_tutorial_script(self, topic, expertise, duration, learning_objectives, concepts, code_examples):
        """Generate a comprehensive tutorial script using local generation"""
        
        return self._generate_local_script(topic, expertise, duration, concepts, code_examples)
    
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
                'service': 'local_tts'
            }
        
        # Clean text for TTS
        clean_text = self._clean_text_for_tts(text)
        
        # Try different TTS services in order of preference
        for service in ['local_tts']:
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
        
        if service == 'local_tts':
            return self._local_tts(text, voice_settings)
        
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
