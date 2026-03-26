# run_background.py
"""
Background Qwikk assistant with global hotkey and wake word support.
Runs in system tray - always ready to listen!

Usage:
    python run_background.py

Hotkey: Ctrl+Shift+Q - Press to speak a command
Wake word: "Hey Qwikk" or "Qwikk" - Always listening mode
"""

import sys
import os
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.controller import handle_input

# Try importing required libraries
try:
    import keyboard
    HAS_KEYBOARD = True
except ImportError:
    HAS_KEYBOARD = False
    print("⚠️ Install keyboard: pip install keyboard")

try:
    import speech_recognition as sr
    HAS_SR = True
except ImportError:
    HAS_SR = False
    print("⚠️ Install speech_recognition: pip install SpeechRecognition")

try:
    import pyttsx3
    HAS_TTS = True
except ImportError:
    HAS_TTS = False
    print("⚠️ Install pyttsx3: pip install pyttsx3")


class BackgroundAssistant:
    """
    Always-on assistant that listens for hotkey or wake word.
    """
    
    def __init__(self, mode="hotkey"):
        """
        Args:
            mode: "hotkey" (press Ctrl+Shift+Q) or "wake" (say "Hey Qwikk")
        """
        self.mode = mode
        self.running = False
        self.listening = False
        
        # Initialize TTS
        self.tts = None
        if HAS_TTS:
            try:
                self.tts = pyttsx3.init()
                self.tts.setProperty('rate', 180)
            except:
                pass
        
        # Initialize STT
        self.recognizer = None
        self.microphone = None
        if HAS_SR:
            self.recognizer = sr.Recognizer()
            try:
                self.microphone = sr.Microphone()
            except:
                print("❌ No microphone found!")
        
        # Wake words
        self.wake_words = ["hey qwikk", "hey quick", "qwikk", "quick", "quik"]
        
        # Hotkey
        self.hotkey = "ctrl+shift+q"
    
    def speak(self, text: str):
        """Speak text using TTS."""
        print(f"🔊 Qwikk: {text}")
        if self.tts:
            try:
                self.tts.say(text)
                self.tts.runAndWait()
            except:
                pass
    
    def listen(self, timeout: float = 5.0, prompt: bool = True) -> str:
        """Listen for speech and return text."""
        if not self.recognizer or not self.microphone:
            return None
        
        try:
            with self.microphone as source:
                if prompt:
                    print("🎤 Listening...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=10)
            
            # Try Google (needs internet) or Sphinx (offline)
            try:
                text = self.recognizer.recognize_google(audio)
                return text.lower()
            except:
                try:
                    text = self.recognizer.recognize_sphinx(audio)
                    return text.lower()
                except:
                    return None
                    
        except sr.WaitTimeoutError:
            return None
        except Exception as e:
            print(f"⚠️ Listen error: {e}")
            return None
    
    def process_command(self, text: str):
        """Process a voice command."""
        if not text:
            return
        
        print(f"👤 You: {text}")
        
        # Check for exit commands
        if text.lower() in ["exit", "quit", "stop", "goodbye", "bye"]:
            self.speak("Goodbye!")
            self.running = False
            return
        
        # Get response from controller
        try:
            response = handle_input(text)
            self.speak(response)
        except Exception as e:
            self.speak(f"Error: {e}")
    
    def on_hotkey(self):
        """Called when hotkey is pressed."""
        if self.listening:
            return
        
        self.listening = True
        print("\n⚡ Hotkey pressed! Listening...")
        self.speak("Yes?")
        
        text = self.listen(timeout=7.0)
        if text:
            self.process_command(text)
        else:
            print("(No speech detected)")
        
        self.listening = False
    
    def check_wake_word(self, text: str) -> tuple:
        """Check if text contains wake word, return (has_wake, remaining_command)."""
        if not text:
            return False, ""
        
        text_lower = text.lower()
        
        for wake in self.wake_words:
            if wake in text_lower:
                # Extract command after wake word
                idx = text_lower.find(wake) + len(wake)
                remaining = text[idx:].strip()
                return True, remaining
        
        return False, ""
    
    def run_hotkey_mode(self):
        """Run in hotkey mode - press Ctrl+Shift+Q to activate."""
        if not HAS_KEYBOARD:
            print("❌ keyboard library required for hotkey mode")
            print("   Install with: pip install keyboard")
            return
        
        print("\n" + "="*50)
        print("⚡ QWIKK BACKGROUND ASSISTANT")
        print("="*50)
        print(f"🎯 Press {self.hotkey.upper()} to speak a command")
        print("💡 Say 'exit' or 'quit' to stop")
        print("="*50 + "\n")
        
        self.speak("Qwikk ready! Press Control Shift Q to speak.")
        
        # Register hotkey
        keyboard.add_hotkey(self.hotkey, self.on_hotkey)
        
        self.running = True
        try:
            while self.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass
        finally:
            keyboard.unhook_all()
            self.speak("Goodbye!")
    
    def run_wake_word_mode(self):
        """Run in wake word mode - always listening for 'Hey Qwikk'."""
        if not HAS_SR:
            print("❌ SpeechRecognition required for wake word mode")
            return
        
        print("\n" + "="*50)
        print("⚡ QWIKK ALWAYS-LISTENING MODE")
        print("="*50)
        print("🎤 Say 'Hey Qwikk' followed by your command")
        print("💡 Or say 'Hey Qwikk' and wait for the beep")
        print("🛑 Say 'exit' or 'quit' to stop")
        print("="*50 + "\n")
        
        self.speak("Qwikk is listening! Say Hey Qwikk to activate.")
        
        self.running = True
        
        try:
            while self.running:
                # Listen for wake word (longer timeout)
                print("\n🎤 Listening for 'Hey Qwikk'...")
                text = self.listen(timeout=10.0, prompt=False)
                
                if not text:
                    continue
                
                has_wake, command = self.check_wake_word(text)
                
                if has_wake:
                    print("✨ Wake word detected!")
                    
                    if command:
                        # Command was included with wake word
                        self.process_command(command)
                    else:
                        # Wait for command
                        self.speak("Yes?")
                        command = self.listen(timeout=7.0)
                        if command:
                            self.process_command(command)
                
                time.sleep(0.2)
                
        except KeyboardInterrupt:
            pass
        finally:
            self.speak("Goodbye!")
    
    def run(self):
        """Start the assistant."""
        if self.mode == "hotkey":
            self.run_hotkey_mode()
        elif self.mode == "wake":
            self.run_wake_word_mode()
        else:
            print(f"Unknown mode: {self.mode}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Qwikk Background Assistant")
    parser.add_argument("--mode", "-m", choices=["hotkey", "wake"], default="hotkey",
                        help="Mode: 'hotkey' (Ctrl+Shift+Q) or 'wake' (Hey Qwikk)")
    parser.add_argument("--check", "-c", action="store_true",
                        help="Check dependencies and exit")
    
    args = parser.parse_args()
    
    if args.check:
        print("\n🔍 Checking dependencies...\n")
        print(f"  • keyboard: {'✓' if HAS_KEYBOARD else '✗ (pip install keyboard)'}")
        print(f"  • SpeechRecognition: {'✓' if HAS_SR else '✗ (pip install SpeechRecognition)'}")
        print(f"  • pyttsx3: {'✓' if HAS_TTS else '✗ (pip install pyttsx3)'}")
        
        if HAS_SR:
            try:
                mic = sr.Microphone()
                print(f"  • Microphone: ✓")
            except:
                print(f"  • Microphone: ✗ (not found)")
        
        print()
        return
    
    # Check requirements
    if args.mode == "hotkey" and not HAS_KEYBOARD:
        print("❌ Install keyboard library: pip install keyboard")
        return
    
    if not HAS_SR:
        print("❌ Install SpeechRecognition: pip install SpeechRecognition")
        return
    
    # Run assistant
    assistant = BackgroundAssistant(mode=args.mode)
    assistant.run()


if __name__ == "__main__":
    main()
