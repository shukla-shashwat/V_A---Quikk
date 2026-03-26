# interface/voice_tts.py
"""
Text-to-Speech module using offline engines.
Supports: pyttsx3 (offline) and edge-tts (Microsoft voices).
"""

import threading
import queue
from typing import Optional

# Try importing TTS libraries
try:
    import pyttsx3
    HAS_PYTTSX3 = True
except ImportError:
    HAS_PYTTSX3 = False


class TextToSpeech:
    """
    Offline text-to-speech using pyttsx3.
    """
    
    def __init__(self, rate: int = 175, volume: float = 1.0, voice_id: str = None):
        """
        Initialize TTS engine.
        
        Args:
            rate: Speech rate (words per minute, default 175)
            volume: Volume 0.0 to 1.0
            voice_id: Specific voice ID to use
        """
        self.engine = None
        self.rate = rate
        self.volume = volume
        self.voice_id = voice_id
        self._speech_queue = queue.Queue()
        self._is_speaking = False
        self._thread = None
        
        self._init_engine()
    
    def _init_engine(self):
        """Initialize the TTS engine."""
        if not HAS_PYTTSX3:
            print("⚠ pyttsx3 not installed. Install with: pip install pyttsx3")
            return
        
        try:
            self.engine = pyttsx3.init()
            
            # Set properties
            self.engine.setProperty('rate', self.rate)
            self.engine.setProperty('volume', self.volume)
            
            # Set voice if specified
            if self.voice_id:
                self.engine.setProperty('voice', self.voice_id)
            
            print("✓ TTS engine initialized")
            
        except Exception as e:
            print(f"⚠ TTS init failed: {e}")
            self.engine = None
    
    def get_voices(self) -> list:
        """Get list of available voices."""
        if not self.engine:
            return []
        
        voices = self.engine.getProperty('voices')
        return [
            {
                "id": v.id,
                "name": v.name,
                "languages": v.languages,
                "gender": v.gender
            }
            for v in voices
        ]
    
    def set_voice(self, voice_id: str):
        """Set the voice by ID."""
        if self.engine:
            self.engine.setProperty('voice', voice_id)
            self.voice_id = voice_id
    
    def set_rate(self, rate: int):
        """Set speech rate (words per minute)."""
        if self.engine:
            self.engine.setProperty('rate', rate)
            self.rate = rate
    
    def set_volume(self, volume: float):
        """Set volume (0.0 to 1.0)."""
        if self.engine:
            self.engine.setProperty('volume', max(0.0, min(1.0, volume)))
            self.volume = volume
    
    def speak(self, text: str, block: bool = True):
        """
        Speak the given text.
        
        Args:
            text: Text to speak
            block: If True, wait for speech to complete
        """
        if not self.engine:
            print(f"[TTS unavailable] {text}")
            return
        
        if block:
            self._speak_sync(text)
        else:
            self._speak_async(text)
    
    def _speak_sync(self, text: str):
        """Speak synchronously (blocking)."""
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            print(f"⚠ TTS error: {e}")
    
    def _speak_async(self, text: str):
        """Speak asynchronously (non-blocking)."""
        self._speech_queue.put(text)
        
        if not self._thread or not self._thread.is_alive():
            self._thread = threading.Thread(target=self._process_queue, daemon=True)
            self._thread.start()
    
    def _process_queue(self):
        """Process speech queue in background."""
        while not self._speech_queue.empty():
            try:
                text = self._speech_queue.get(timeout=0.5)
                self._speak_sync(text)
            except queue.Empty:
                break
    
    def stop(self):
        """Stop current speech."""
        if self.engine:
            try:
                self.engine.stop()
            except:
                pass
    
    def is_speaking(self) -> bool:
        """Check if currently speaking."""
        return self._is_speaking


# Convenience functions
_tts_instance: Optional[TextToSpeech] = None


def get_tts() -> TextToSpeech:
    """Get or create TTS instance."""
    global _tts_instance
    if _tts_instance is None:
        _tts_instance = TextToSpeech()
    return _tts_instance


def speak(text: str, block: bool = False):
    """Speak text using the default TTS engine."""
    get_tts().speak(text, block=block)


def set_voice(voice_id: str):
    """Set the TTS voice."""
    get_tts().set_voice(voice_id)


def set_rate(rate: int):
    """Set speech rate."""
    get_tts().set_rate(rate)


def list_voices() -> list:
    """List available voices."""
    return get_tts().get_voices()


def check_tts_available() -> dict:
    """Check TTS availability."""
    return {
        "pyttsx3": HAS_PYTTSX3,
        "engine_ready": get_tts().engine is not None
    }
