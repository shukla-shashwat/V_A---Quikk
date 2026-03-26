# interface/voice_stt.py
"""
Speech-to-Text module using offline recognition.
Supports: Vosk (offline) or SpeechRecognition with offline mode.
"""

import os
import json
import wave
import queue
import threading
from typing import Optional, Callable, Generator

# Try importing speech recognition libraries
try:
    import speech_recognition as sr
    HAS_SR = True
except ImportError:
    HAS_SR = False

try:
    from vosk import Model, KaldiRecognizer
    HAS_VOSK = True
except ImportError:
    HAS_VOSK = False

try:
    import pyaudio
    HAS_PYAUDIO = True
except ImportError:
    HAS_PYAUDIO = False


# Configuration
VOSK_MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "vosk-model-small-en-us-0.15")
WAKE_WORDS = ["hey qwikk", "qwikk", "hey quick", "quick"]
SAMPLE_RATE = 16000


class SpeechToText:
    """
    Offline speech recognition using Vosk or SpeechRecognition.
    """
    
    def __init__(self, use_vosk: bool = True):
        """
        Initialize STT engine.
        
        Args:
            use_vosk: Use Vosk for offline recognition (recommended)
        """
        self.use_vosk = use_vosk and HAS_VOSK
        self.recognizer = None
        self.model = None
        self.is_listening = False
        self._audio_queue = queue.Queue()
        
        self._init_engine()
    
    def _init_engine(self):
        """Initialize the speech recognition engine."""
        if self.use_vosk and HAS_VOSK:
            try:
                if os.path.exists(VOSK_MODEL_PATH):
                    self.model = Model(VOSK_MODEL_PATH)
                    print("✓ Vosk model loaded")
                else:
                    print(f"⚠ Vosk model not found at {VOSK_MODEL_PATH}")
                    print("  Download from: https://alphacephei.com/vosk/models")
                    self.use_vosk = False
            except Exception as e:
                print(f"⚠ Vosk init failed: {e}")
                self.use_vosk = False
        
        if not self.use_vosk and HAS_SR:
            self.recognizer = sr.Recognizer()
            self.recognizer.energy_threshold = 300
            self.recognizer.dynamic_energy_threshold = True
            print("✓ Using SpeechRecognition (may need internet for some backends)")
    
    def check_microphone(self) -> bool:
        """Check if microphone is available."""
        if not HAS_PYAUDIO:
            return False
        
        try:
            p = pyaudio.PyAudio()
            device_count = p.get_device_count()
            p.terminate()
            return device_count > 0
        except:
            return False
    
    def listen_once(self, timeout: float = 5.0) -> Optional[str]:
        """
        Listen for a single utterance and return the text.
        
        Args:
            timeout: Maximum time to wait for speech
        
        Returns:
            Recognized text or None
        """
        if self.use_vosk and HAS_VOSK and HAS_PYAUDIO:
            return self._listen_vosk(timeout)
        elif HAS_SR:
            return self._listen_sr(timeout)
        else:
            return None
    
    def _listen_vosk(self, timeout: float) -> Optional[str]:
        """Listen using Vosk."""
        if not self.model:
            return None
        
        try:
            p = pyaudio.PyAudio()
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=SAMPLE_RATE,
                input=True,
                frames_per_buffer=8000
            )
            
            rec = KaldiRecognizer(self.model, SAMPLE_RATE)
            
            print("🎤 Listening...")
            
            import time
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                data = stream.read(4000, exception_on_overflow=False)
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    text = result.get("text", "").strip()
                    if text:
                        stream.stop_stream()
                        stream.close()
                        p.terminate()
                        return text
            
            # Get final result
            result = json.loads(rec.FinalResult())
            text = result.get("text", "").strip()
            
            stream.stop_stream()
            stream.close()
            p.terminate()
            
            return text if text else None
            
        except Exception as e:
            print(f"⚠ Vosk error: {e}")
            return None
    
    def _listen_sr(self, timeout: float) -> Optional[str]:
        """Listen using SpeechRecognition."""
        if not self.recognizer:
            return None
        
        try:
            with sr.Microphone() as source:
                print("🎤 Listening...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=10)
            
            # Try offline first (Sphinx), then online as fallback
            try:
                # Sphinx is offline but less accurate
                text = self.recognizer.recognize_sphinx(audio)
                return text
            except sr.UnknownValueError:
                return None
            except sr.RequestError:
                # Sphinx not available, try Google (requires internet)
                try:
                    text = self.recognizer.recognize_google(audio)
                    return text
                except:
                    return None
                    
        except sr.WaitTimeoutError:
            return None
        except Exception as e:
            print(f"⚠ SR error: {e}")
            return None
    
    def listen_continuous(self, callback: Callable[[str], None], 
                          stop_event: threading.Event = None):
        """
        Continuously listen and call callback with recognized text.
        
        Args:
            callback: Function to call with recognized text
            stop_event: Event to signal when to stop listening
        """
        self.is_listening = True
        stop_event = stop_event or threading.Event()
        
        while not stop_event.is_set() and self.is_listening:
            text = self.listen_once(timeout=5.0)
            if text:
                callback(text)
    
    def detect_wake_word(self, text: str) -> bool:
        """Check if text contains a wake word."""
        text_lower = text.lower()
        return any(wake in text_lower for wake in WAKE_WORDS)
    
    def stop(self):
        """Stop continuous listening."""
        self.is_listening = False


# Convenience functions
_stt_instance: Optional[SpeechToText] = None


def get_stt() -> SpeechToText:
    """Get or create STT instance."""
    global _stt_instance
    if _stt_instance is None:
        _stt_instance = SpeechToText()
    return _stt_instance


def listen_once(timeout: float = 5.0) -> Optional[str]:
    """Listen for a single utterance."""
    return get_stt().listen_once(timeout)


def listen_continuous(callback: Callable[[str], None]):
    """Continuously listen and process speech."""
    get_stt().listen_continuous(callback)


def check_voice_available() -> dict:
    """Check what voice capabilities are available."""
    return {
        "vosk": HAS_VOSK,
        "speech_recognition": HAS_SR,
        "pyaudio": HAS_PYAUDIO,
        "microphone": get_stt().check_microphone() if HAS_PYAUDIO else False
    }
