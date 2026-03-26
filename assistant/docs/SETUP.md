# 🚀 Quick Setup Guide

Get Qwikk running in 5 minutes!

---

## Step 1: Install Python
Make sure you have Python 3.10+ installed.
```bash
python --version
```

---

## Step 2: Install Dependencies
```bash
cd D:\V_A\assistant
pip install -r requirement.txt
```

### If PyAudio Fails:
```bash
pip install pipwin
pipwin install pyaudio
```

---

## Step 3: Choose How to Run

### Option A: Web Interface (Easiest)
```bash
python run_web.py
```
Open http://localhost:8000 in your browser.

### Option B: Background Hotkey
```bash
# Run as Administrator!
python run_background.py
```
Press **Ctrl+Shift+Q** anywhere to speak.

### Option C: Terminal Voice
```bash
python run_voice.py
```
Speak commands directly in terminal.

---

## Step 4: Test It!

Try these commands:
- "open notepad"
- "what time is it"
- "take a screenshot"
- "volume up"
- "set timer for 1 minute"
- "help"

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| PyAudio error | `pip install pipwin && pipwin install pyaudio` |
| Hotkey not working | Run as Administrator |
| No microphone | Check Windows Privacy Settings |
| Web not loading | Check port 8000 is free |

---

## File Locations

| File | Purpose |
|------|---------|
| `run_web.py` | Start web UI |
| `run_background.py` | Start hotkey mode |
| `run_voice.py` | Start voice mode |
| `main.py` | Start CLI mode |
| `config/settings.yaml` | Settings |

---

## Need Help?

Say "help" to Qwikk to see all commands!
