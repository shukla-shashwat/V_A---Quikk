# run_voice.py
"""
Voice-enabled Qwikk assistant.
Combines STT → Controller → TTS for full voice interaction.
"""

import sys
import os
import threading
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.controller import handle_input
from interface.voice_stt import SpeechToText, check_voice_available
from interface.voice_tts import TextToSpeech, check_tts_available


class VoiceAssistant:
    """
    Voice-enabled assistant combining STT, processing, and TTS.
    """
    
    def __init__(self, wake_word_mode: bool = False):
        """
        Initialize voice assistant.
        
        Args:
            wake_word_mode: If True, wait for wake word before processing
        """
        self.stt = SpeechToText()
        self.tts = TextToSpeech(rate=180)
        self.wake_word_mode = wake_word_mode
        self.is_running = False
        self.awaiting_command = False
        
        # Wake words
        self.wake_words = ["hey qwikk", "qwikk", "hey quick", "quick"]
    
    def check_setup(self) -> dict:
        """Check if voice components are properly set up."""
        stt_status = check_voice_available()
        tts_status = check_tts_available()
        
        return {
            "stt": stt_status,
            "tts": tts_status,
            "ready": stt_status.get("microphone", False) and tts_status.get("engine_ready", False)
        }
    
    def speak(self, text: str):
        """Speak text using TTS."""
        print(f"🔊 Qwikk: {text}")
        self.tts.speak(text, block=True)
    
    def listen(self, timeout: float = 5.0) -> str:
        """Listen for user speech."""
        text = self.stt.listen_once(timeout=timeout)
        if text:
            print(f"👤 You: {text}")
        return text
    
    def process_command(self, text: str) -> str:
        """Process a command and get response."""
        try:
            response = handle_input(text)
            return response
        except Exception as e:
            return f"Sorry, something went wrong: {e}"
    
    def detect_wake_word(self, text: str) -> bool:
        """Check if text contains a wake word."""
        if not text:
            return False
        text_lower = text.lower()
        return any(wake in text_lower for wake in self.wake_words)
    
    def extract_command_after_wake_word(self, text: str) -> str:
        """Extract command part after wake word."""
        text_lower = text.lower()
        for wake in self.wake_words:
            if wake in text_lower:
                # Get everything after the wake word
                idx = text_lower.find(wake) + len(wake)
                command = text[idx:].strip()
                if command:
                    return command
        return ""
    
    def run_single_interaction(self):
        """Run a single voice interaction cycle."""
        # Listen for command
        text = self.listen(timeout=7.0)
        
        if not text:
            return
        
        # Check for exit commands
        if text.lower() in ["exit", "quit", "goodbye", "bye", "stop"]:
            self.speak("Goodbye!")
            self.is_running = False
            return
        
        # Process command
        response = self.process_command(text)
        
        # Speak response
        self.speak(response)
    
    def run_wake_word_mode(self):
        """Run in wake word mode - waits for "Hey Qwikk" before processing."""
        print("\n🎤 Listening for 'Hey Qwikk'...")
        
        text = self.listen(timeout=10.0)
        
        if not text:
            return
        
        if self.detect_wake_word(text):
            # Check if command was included with wake word
            command = self.extract_command_after_wake_word(text)
            
            if command:
                # Process the command directly
                response = self.process_command(command)
                self.speak(response)
            else:
                # Prompt for command
                self.speak("Yes?")
                self.awaiting_command = True
                
                # Listen for actual command
                command = self.listen(timeout=7.0)
                
                if command:
                    response = self.process_command(command)
                    self.speak(response)
                
                self.awaiting_command = False
    
    def run(self):
        """Main loop - run the voice assistant."""
        # Check setup
        status = self.check_setup()
        
        if not status["stt"].get("microphone"):
            print("❌ No microphone detected!")
            print("   Make sure a microphone is connected and allowed.")
            return
        
        if not status["tts"].get("engine_ready"):
            print("⚠️ TTS not available - responses will be text only")
        
        # Welcome message
        print("\n" + "="*50)
        print("⚡ QWIKK VOICE ASSISTANT")
        print("="*50)
        
        if self.wake_word_mode:
            print("Mode: Wake Word (say 'Hey Qwikk' to activate)")
        else:
            print("Mode: Always Listening (speak anytime)")
        
        print("Say 'exit' or 'goodbye' to quit")
        print("="*50 + "\n")
        
        self.speak("Qwikk is ready! How can I help?")
        
        self.is_running = True
        
        try:
            while self.is_running:
                if self.wake_word_mode:
                    self.run_wake_word_mode()
                else:
                    self.run_single_interaction()
                
                # Small delay between listening cycles
                time.sleep(0.3)
                
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted - shutting down...")
        finally:
            self.is_running = False
            self.speak("Goodbye!")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Qwikk Voice Assistant")
    parser.add_argument("--wake-word", "-w", action="store_true",
                        help="Use wake word mode (say 'Hey Qwikk' to activate)")
    parser.add_argument("--check", "-c", action="store_true",
                        help="Check voice setup and exit")
    
    args = parser.parse_args()
    
    if args.check:
        print("\n🔍 Checking voice setup...\n")
        
        stt_status = check_voice_available()
        tts_status = check_tts_available()
        
        print("Speech-to-Text:")
        print(f"  • Vosk: {'✓' if stt_status['vosk'] else '✗'}")
        print(f"  • SpeechRecognition: {'✓' if stt_status['speech_recognition'] else '✗'}")
        print(f"  • PyAudio: {'✓' if stt_status['pyaudio'] else '✗'}")
        print(f"  • Microphone: {'✓' if stt_status['microphone'] else '✗'}")
        
        print("\nText-to-Speech:")
        print(f"  • pyttsx3: {'✓' if tts_status['pyttsx3'] else '✗'}")
        print(f"  • Engine ready: {'✓' if tts_status['engine_ready'] else '✗'}")
        
        if stt_status['microphone'] and tts_status['engine_ready']:
            print("\n✅ Voice assistant is ready!")
        else:
            print("\n⚠️ Some components missing. Install with:")
            print("   pip install pyttsx3 pyaudio SpeechRecognition")
        
        return
    
    # Run voice assistant
    assistant = VoiceAssistant(wake_word_mode=args.wake_word)
    assistant.run()


if __name__ == "__main__":
    main()
