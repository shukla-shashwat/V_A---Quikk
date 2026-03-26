# 🏗️ Qwikk Architecture

## Overview

Qwikk is a **text-first, offline-capable** AI assistant. The core logic works without any LLM - the LLM is only used for optional response polishing.

```
┌─────────────────────────────────────────────────────────────┐
│                        USER INPUT                           │
│         (Voice / Text / Web UI / Hotkey)                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     ENTRY POINTS                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │run_web.py│ │run_voice │ │run_back- │ │ main.py  │       │
│  │  :8000   │ │   .py    │ │ground.py │ │  (CLI)   │       │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘       │
└───────┼────────────┼────────────┼────────────┼──────────────┘
        │            │            │            │
        └────────────┴─────┬──────┴────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    CORE (Brain)                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              controller.py (Switchboard)             │   │
│  │   • Receives all input                              │   │
│  │   • Routes to appropriate handler                   │   │
│  │   • Returns response                                │   │
│  └──────────────────────┬──────────────────────────────┘   │
│                         │                                   │
│    ┌────────────────────┼────────────────────┐             │
│    │                    │                    │             │
│    ▼                    ▼                    ▼             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│  │intent.py │    │clarifier │    │memory.py │             │
│  │ Detect   │    │  .py     │    │ Store    │             │
│  │ intent   │    │ Ask if   │    │ context  │             │
│  │ Extract  │    │ unclear  │    │ history  │             │
│  │ entities │    │          │    │          │             │
│  └──────────┘    └──────────┘    └──────────┘             │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                       TOOLS                                 │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐  │
│  │ system_   │ │ file_     │ │ audio_    │ │ display_  │  │
│  │ tools.py  │ │ tools.py  │ │ tools.py  │ │ tools.py  │  │
│  │ • Apps    │ │ • Search  │ │ • Volume  │ │ • Bright  │  │
│  │ • Power   │ │ • Open    │ │ • Mute    │ │   ness    │  │
│  │ • Screen  │ │ • Browse  │ │           │ │           │  │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘  │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐                │
│  │ timer_    │ │ network_  │ │ math_     │                │
│  │ tools.py  │ │ tools.py  │ │ tools.py  │                │
│  │ • Timer   │ │ • WiFi    │ │ • Calc    │                │
│  │ • Alarm   │ │ • BT      │ │           │                │
│  │ • Remind  │ │ • Status  │ │           │                │
│  └───────────┘ └───────────┘ └───────────┘                │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    RESPONSE                                 │
│         (Text / Voice / Web UI)                            │
└─────────────────────────────────────────────────────────────┘
```

---

## Design Principles

### 1. Text-First
All logic works with text. Voice is just input/output.

### 2. No LLM Dependency
Core functionality works 100% offline without any AI model.

### 3. Single Entry Point
All input goes through `controller.py` - the "brain switchboard".

### 4. Tool Separation
Each tool module handles one domain:
- `system_tools.py` → Apps, power, screenshots
- `file_tools.py` → Files, folders
- `audio_tools.py` → Volume
- etc.

### 5. Intent-Based Routing
```
User says: "open chrome"
    ↓
intent.py detects: OPEN_APP, entities: {app_name: "chrome"}
    ↓
controller.py routes to: system_tools.open_application("chrome")
    ↓
Response: "Opened chrome"
```

---

## File Reference

| File | Purpose |
|------|---------|
| `controller.py` | Brain - routes intents to tools |
| `intent.py` | Detects intent + extracts entities |
| `clarifier.py` | Asks follow-up questions |
| `memory.py` | Stores context (JSON + SQLite) |
| `system_tools.py` | App control, power, screenshot |
| `file_tools.py` | File/folder search and open |
| `audio_tools.py` | Volume control (pycaw) |
| `display_tools.py` | Brightness control |
| `timer_tools.py` | Timers, alarms, reminders |
| `network_tools.py` | WiFi/Bluetooth status |
| `math_tools.py` | Calculator |

---

## Data Flow

```
1. User speaks/types command
2. Entry point (web/voice/CLI) receives input
3. controller.handle_input(text) is called
4. intent.detect_intent(text) → (intent, confidence, entities)
5. If confidence < 0.6: clarifier asks question
6. If confident: controller routes to appropriate tool
7. Tool executes action (subprocess, API call, etc.)
8. Response returned to user
9. Memory updated with interaction
```
