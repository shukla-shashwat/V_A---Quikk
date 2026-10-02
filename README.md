# ⚡ Qwikk - Your Personal AI Assistant

A Jarvis-like voice assistant for Windows that controls your laptop via voice or text commands.

![Qwikk](https://img.shields.io/badge/Qwikk-v1.0-purple?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge)
![Windows](https://img.shields.io/badge/Windows-10%2F11-0078D6?style=for-the-badge)

---

## 🚀 Quick Start

### Installation

```bash
# Clone or navigate to the project
cd D:\V_A\assistant

# Install dependencies
pip install -r requirement.txt
```

---

## 🎯 Three Ways to Run Qwikk

### 1️⃣ Web Interface (Recommended)
Beautiful Gen-Z styled UI with voice support in browser.

```bash
python run_web.py
```
Then open: **http://localhost:8000**

**Features:**
- 🎤 Click mic button to speak
- ⌨️ Type commands
- 🔊 Voice responses (when using mic)
- 🎨 Dark theme with animations

---

### 2️⃣ Background Hotkey Mode
Press **Ctrl+Shift+Q** from anywhere to activate!

```bash
# Run as Administrator (required for global hotkey)
python run_background.py
```

**Features:**
- ⌨️ Global hotkey works in any app
- 🎤 Speak command after pressing hotkey
- 🔊 Voice responses
- 🖥️ Runs in background

---

### 3️⃣ Terminal Voice Mode
Full voice assistant in terminal with wake word support.

```bash
# Always listening mode
python run_voice.py

# Wake word mode (say "Hey Qwikk")
python run_voice.py --wake-word
```

**Features:**
- 🎤 Continuous listening
- 🗣️ Wake word: "Hey Qwikk"
- 🔊 Voice responses
- 💻 Terminal output

---

## 📋 Available Commands

### 📱 App Control
- `open chrome` / `open spotify` / `open notepad`
- `close chrome`
- `open settings`

### 🔊 Volume
- `volume up` / `volume down`
- `set volume to 50`
- `mute` / `unmute`

### ☀️ Brightness
- `brightness up` / `brightness down`
- `set brightness to 70`

### 📶 Network
- `wifi status` / `bluetooth status`
- `network status`
- `list wifi` / `scan wifi`

### 📸 Screenshot
- `take a screenshot`
- `screenshot`

### 🔒 Power
- `lock screen`
- `shutdown` / `restart` / `sleep`

### 📁 Files & Folders
- `open file report.pdf`
- `find file budget`
- `open folder projects`
- `open downloads`

### ⏱️ Timer, Alarm & Reminder
- `set timer for 5 minutes`
- `set alarm for 7:30 AM`
- `remind me to call mom in 1 hour`
- `show timers` / `show alarms` / `show reminders`
- `cancel timer` / `cancel alarm`

### 💻 System Info
- `system info`
- `battery status`

### 🧮 Calculator
- `calculate 25 * 4`
- `what is 100 / 5`

### ⏰ Time & Date
- `what time is it`
- `what's the date`

### 💬 General
- `help` - Show all commands
- `hello` - Greet
- `exit` / `goodbye` - Quit

---

## 📁 Project Structure

```
assistant/
├── core/                   # Brain of the assistant
│   ├── controller.py       # Main routing logic
│   ├── intent.py           # Intent detection
│   ├── clarifier.py        # Clarification system
│   └── memory.py           # Short & long-term memory
│
├── tools/                  # Action executors
│   ├── system_tools.py     # App control, power, screenshot
│   ├── file_tools.py       # File/folder operations
│   ├── audio_tools.py      # Volume control
│   ├── display_tools.py    # Brightness control
│   ├── timer_tools.py      # Timer, alarm, reminder
│   ├── network_tools.py    # WiFi, Bluetooth
│   └── math_tools.py       # Calculator
│
├── interface/              # Input/Output
│   ├── voice_stt.py        # Speech-to-Text
│   └── voice_tts.py        # Text-to-Speech
│
├── web/                    # Web UI
│   ├── server.py           # FastAPI backend
│   ├── templates/          # HTML
│   └── static/             # CSS, JS
│
├── llm/                    # LLM integration (optional)
│   ├── local_llm.py        # Ollama integration
│   └── prompts.py          # Qwikk personality
│
├── config/                 # Configuration
│   └── settings.yaml       # User settings
│
├── docs/                   # Documentation
│
├── run_web.py              # 🌐 Web UI launcher
├── run_background.py       # 🎯 Hotkey mode launcher
├── run_voice.py            # 🎤 Voice mode launcher
├── main.py                 # 💻 CLI launcher
└── requirement.txt         # Dependencies
```

---

## ⚙️ Configuration

Edit `config/settings.yaml`:

```yaml
# Screenshot save location
screenshot_path: "C:/Users/YourName/Pictures/Screenshots"

# Drives to search for files
search_drives:
  - "C:/"
  - "D:/"

# Voice settings
voice_rate: 180
```

---

## 🔧 Troubleshooting

### PyAudio Installation Failed
```bash
pip install pipwin
pipwin install pyaudio
```

### Hotkey Not Working
- Run as **Administrator**
- Check if another app uses Ctrl+Shift+Q

### Microphone Not Detected
- Check Windows Settings → Privacy → Microphone
- Allow apps to access microphone

### Web UI Not Loading
- Check if port 8000 is free
- Try: `python run_web.py --port 8080`

---

## 📜 License

MIT License - Feel free to use and modify!

---

## 🙏 Credits

Built with ❤️ using:
- FastAPI & WebSockets
- SpeechRecognition & pyttsx3
- pycaw & screen-brightness-control
- Python 3.10+

---

**⚡ Qwikk - Fast. Smart. Yours.**
