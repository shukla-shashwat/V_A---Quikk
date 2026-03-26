# main.py
"""
Voice Assistant - Main entry point.
Text-first interface with command loop.
Supports TTS (Text-to-Speech) for spoken responses.
"""

import sys
import os
import argparse

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from interface.input_text import get_input
from interface.output_text import send_output
from core.controller import handle_input

# Try to import TTS
try:
    from interface.voice_tts import TextToSpeech
    HAS_TTS = True
except ImportError:
    HAS_TTS = False


class Assistant:
    """Main assistant with optional TTS."""
    
    def __init__(self, speak: bool = False):
        """
        Initialize assistant.
        
        Args:
            speak: Enable TTS to speak all responses
        """
        self.speak_enabled = speak and HAS_TTS
        self.tts = None
        
        if self.speak_enabled:
            try:
                self.tts = TextToSpeech(rate=180)
                print("🔊 TTS enabled - I will speak responses")
            except Exception as e:
                print(f"⚠️ TTS failed to initialize: {e}")
                self.speak_enabled = False
    
    def output(self, text: str):
        """Output text and optionally speak it."""
        send_output(text)
        
        if self.speak_enabled and self.tts:
            # Clean text for speech (remove emojis and special chars)
            clean_text = self._clean_for_speech(text)
            if clean_text:
                self.tts.speak(clean_text, block=True)
    
    def _clean_for_speech(self, text: str) -> str:
        """Clean text for TTS (remove emojis, formatting)."""
        import re
        # Remove emoji and special characters
        clean = re.sub(r'[^\w\s\.\,\!\?\-\:\;\'\"\(\)]', ' ', text)
        # Remove multiple spaces
        clean = re.sub(r'\s+', ' ', clean).strip()
        # Skip very long text (like help)
        if len(clean) > 500:
            return clean[:200] + "... and more. Type help to see full list."
        return clean
    
    def run(self):
        """Main loop."""
        self.output("Qwikk ready! Type 'help' for commands, 'exit' to quit.")
        
        while True:
            try:
                text = get_input()
                
                # Handle exit
                if text.lower() in ("exit", "quit", "bye", "goodbye"):
                    self.output("Goodbye!")
                    break
                
                # Process input
                response = handle_input(text)
                self.output(response)
                
            except KeyboardInterrupt:
                self.output("\nGoodbye!")
                break
            except Exception as e:
                self.output(f"Error: {e}")


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(description="Qwikk Assistant")
    parser.add_argument("--speak", "-s", action="store_true",
                        help="Enable TTS - speak all responses")
    parser.add_argument("--quiet", "-q", action="store_true",
                        help="Text only - no speech")
    
    args = parser.parse_args()
    
    # Run assistant
    assistant = Assistant(speak=args.speak)
    assistant.run()


if __name__ == "__main__":
    main()
