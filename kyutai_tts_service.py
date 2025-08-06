# kyutai_tts_service.py - Kyutai TTS Streaming Integration
import asyncio
import aiohttp
import json
import uuid
import logging
from typing import Optional, Dict, Any, AsyncGenerator
from pathlib import Path
import tempfile
import time

logger = logging.getLogger(__name__)

class KyutaiTTSService:
    """
    Kyutai TTS Service for streaming text-to-speech without file storage
    
    This service integrates with Kyutai Labs' streaming TTS model to generate
    real-time audio without creating temporary files.
    """
    
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.kyutai.org"):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.session: Optional[aiohttp.ClientSession] = None
        self.active_streams = {}
        
    async def init_session(self):
        """Initialize async HTTP session"""
        if not self.session:
            headers = {}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
            timeout = aiohttp.ClientTimeout(total=120, connect=30)
            
            self.session = aiohttp.ClientSession(
                headers=headers,
                connector=connector,
                timeout=timeout
            )
    
    async def close_session(self):
        """Close async HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def stream_tts(
        self,
        text: str,
        voice: str = "default",
        language: str = "en",
        speed: float = 1.0,
        format: str = "mp3"
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream TTS audio chunks in real-time
        
        Args:
            text: Text to convert to speech
            voice: Voice model to use
            language: Language code
            speed: Speech speed multiplier
            format: Audio format (mp3, wav, ogg)
            
        Yields:
            Audio chunk bytes
        """
        await self.init_session()
        
        # Prepare streaming request
        stream_data = {
            "text": text,
            "voice": voice,
            "language": language,
            "speed": speed,
            "format": format,
            "stream": True,
            "chunk_size": 1024
        }
        
        try:
            url = f"{self.base_url}/v1/tts/stream"
            
            async with self.session.post(url, json=stream_data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Kyutai TTS API error {response.status}: {error_text}")
                
                # Stream audio chunks
                async for chunk in response.content.iter_chunked(1024):
                    if chunk:
                        yield chunk
                        
        except aiohttp.ClientError as e:
            logger.error(f"Kyutai TTS streaming error: {str(e)}")
            raise Exception(f"Streaming failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during streaming: {str(e)}")
            raise
    
    async def create_stream_session(self, text: str, **kwargs) -> str:
        """
        Create a streaming session and return stream ID
        
        Args:
            text: Text to convert to speech
            **kwargs: Additional TTS parameters
            
        Returns:
            Stream session ID
        """
        stream_id = str(uuid.uuid4())
        
        # Store stream configuration
        self.active_streams[stream_id] = {
            'text': text,
            'voice': kwargs.get('voice', 'default'),
            'language': kwargs.get('language', 'en'),
            'speed': kwargs.get('speed', 1.0),
            'format': kwargs.get('format', 'mp3'),
            'created_at': time.time(),
            'status': 'ready'
        }
        
        return stream_id
    
    async def get_stream_url(self, stream_id: str) -> str:
        """
        Get streaming URL for a session
        
        Args:
            stream_id: Stream session ID
            
        Returns:
            Streaming URL
        """
        if stream_id not in self.active_streams:
            raise ValueError(f"Stream session {stream_id} not found")
        
        return f"/api/kyutai-stream/{stream_id}"
    
    def get_stream_info(self, stream_id: str) -> Dict[str, Any]:
        """Get information about a streaming session"""
        return self.active_streams.get(stream_id, {})
    
    def cleanup_expired_streams(self, max_age_seconds: int = 3600):
        """Remove expired streaming sessions"""
        current_time = time.time()
        expired_ids = []
        
        for stream_id, info in self.active_streams.items():
            if current_time - info['created_at'] > max_age_seconds:
                expired_ids.append(stream_id)
        
        for stream_id in expired_ids:
            del self.active_streams[stream_id]
        
        logger.info(f"Cleaned up {len(expired_ids)} expired stream sessions")
    
    async def prepare_text_for_tts(self, content: str) -> str:
        """
        Optimize text content for TTS streaming
        
        Args:
            content: Raw tutorial content
            
        Returns:
            TTS-optimized text
        """
        # Remove HTML tags
        import re
        text = re.sub(r'<[^>]+>', '', content)
        
        # Add natural pauses
        text = text.replace('. ', '. ... ')
        text = text.replace('! ', '! ... ')
        text = text.replace('? ', '? ... ')
        
        # Improve pronunciation of R terms
        replacements = {
            'ggplot2': 'G G plot 2',
            'dplyr': 'D plier',
            'tidyr': 'tidy R',
            '%>%': 'pipe operator',
            'data.frame': 'data frame'
        }
        
        for original, replacement in replacements.items():
            text = text.replace(original, replacement)
        
        return text.strip()

# Global service instance
kyutai_service = KyutaiTTSService()

async def init_kyutai_service(api_key: Optional[str] = None):
    """Initialize the global Kyutai service"""
    if api_key:
        kyutai_service.api_key = api_key
    await kyutai_service.init_session()

async def cleanup_kyutai_service():
    """Cleanup the global Kyutai service"""
    await kyutai_service.close_session()