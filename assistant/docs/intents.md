# 📋 Qwikk Intent Reference

All supported intents with keywords, patterns, and examples.

---

## 📱 App Control

| Intent | Keywords | Examples |
|--------|----------|----------|
| `OPEN_APP` | open, launch, start, run | "open chrome", "launch spotify" |
| `CLOSE_APP` | close, quit, exit, kill | "close notepad", "quit chrome" |

**Supported Apps:** chrome, firefox, edge, notepad, calculator, vscode, spotify, discord, slack, teams, notion, whatsapp, telegram, word, excel, powerpoint, outlook, paint, settings, task manager, file explorer, terminal

---

## 🔊 Volume Control

| Intent | Keywords | Examples |
|--------|----------|----------|
| `VOLUME_UP` | volume up, louder | "volume up", "turn it up" |
| `VOLUME_DOWN` | volume down, quieter | "volume down", "lower" |
| `VOLUME_SET` | set volume, volume to | "set volume to 50" |
| `MUTE` | mute, silence | "mute" |
| `UNMUTE` | unmute, sound on | "unmute" |

---

## ☀️ Brightness Control

| Intent | Keywords | Examples |
|--------|----------|----------|
| `BRIGHTNESS_UP` | brightness up, brighter | "brightness up" |
| `BRIGHTNESS_DOWN` | brightness down, dim | "dim", "brightness down" |
| `BRIGHTNESS_SET` | set brightness | "set brightness to 70" |

---

## 📶 Network Control

| Intent | Keywords | Examples |
|--------|----------|----------|
| `WIFI_ON` | wifi on, enable wifi | "turn on wifi" |
| `WIFI_OFF` | wifi off, disable wifi | "wifi off" |
| `WIFI_STATUS` | wifi status, connected | "wifi status" |
| `WIFI_LIST` | list wifi, scan wifi | "show wifi networks" |
| `BLUETOOTH_ON` | bluetooth on | "bluetooth on" |
| `BLUETOOTH_OFF` | bluetooth off | "bluetooth off" |
| `BLUETOOTH_STATUS` | bluetooth status | "is bluetooth on" |
| `BLUETOOTH_DEVICES` | bluetooth devices | "show bluetooth devices" |
| `NETWORK_STATUS` | network status | "network status" |

---

## 📸 Screenshot

| Intent | Keywords | Examples |
|--------|----------|----------|
| `SCREENSHOT` | screenshot, capture screen | "take a screenshot" |

---

## 🔒 Power Control

| Intent | Keywords | Examples |
|--------|----------|----------|
| `LOCK_SCREEN` | lock, lock screen | "lock screen" |
| `SHUTDOWN` | shutdown, power off | "shutdown" |
| `RESTART` | restart, reboot | "restart" |
| `SLEEP` | sleep, hibernate | "sleep" |

---

## 📁 File Operations

| Intent | Keywords | Examples |
|--------|----------|----------|
| `OPEN_FILE` | open file, open document | "open file report.pdf" |
| `SEARCH_FILE` | find file, locate file | "find file budget" |
| `OPEN_FOLDER` | open folder, open directory | "open folder projects" |
| `SEARCH_FOLDER` | find folder | "find folder work" |

---

## ⏱️ Timer, Alarm, Reminder

| Intent | Keywords | Examples |
|--------|----------|----------|
| `SET_TIMER` | set timer, timer for | "set timer for 5 minutes" |
| `SET_ALARM` | set alarm, wake me | "set alarm for 7:30 AM" |
| `SET_REMINDER` | remind me, reminder | "remind me to call mom in 1 hour" |
| `CANCEL_TIMER` | cancel timer | "cancel timer" |
| `CANCEL_ALARM` | cancel alarm | "cancel alarm" |
| `CANCEL_REMINDER` | cancel reminder | "cancel reminder" |
| `LIST_TIMERS` | show timers | "show timers" |
| `LIST_ALARMS` | show alarms | "show alarms" |
| `LIST_REMINDERS` | show reminders | "show reminders" |

---

## 💻 System Info

| Intent | Keywords | Examples |
|--------|----------|----------|
| `SYSTEM_INFO` | system info, cpu, ram, battery | "system info", "battery status" |

---

## 🧮 Calculator

| Intent | Keywords | Examples |
|--------|----------|----------|
| `CALCULATE` | calculate, what is, compute | "calculate 25 * 4", "what is 100 / 5" |

---

## ⏰ Time & Date

| Intent | Keywords | Examples |
|--------|----------|----------|
| `TIME` | time, what time | "what time is it" |
| `DATE` | date, today | "what's the date" |

---

## 💬 General

| Intent | Keywords | Examples |
|--------|----------|----------|
| `GREETING` | hi, hello, hey | "hello", "hey" |
| `HELP` | help, commands | "help", "what can you do" |
| `EXIT` | exit, quit, bye | "exit", "goodbye" |

---

## Intent Detection Logic

1. **Keyword Match**: Check if any keyword exists in input
2. **Regex Pattern**: Match against defined patterns
3. **Priority Sorting**: Higher priority intents win conflicts
4. **Entity Extraction**: Pull out app names, numbers, file names
5. **Confidence Score**: 0.0 to 1.0 based on matches

**Threshold**: If confidence < 0.6, clarifier asks for clarification.
