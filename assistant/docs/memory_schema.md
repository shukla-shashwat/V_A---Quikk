# 💾 Memory Schema

Qwikk uses two memory systems: short-term (session) and long-term (persistent).

---

## Short-Term Memory (JSON)

Stored in: `data/short_term.json`

Holds context for the current session:

```json
{
    "last_intent": "OPEN_APP",
    "last_entities": {
        "app_name": "chrome"
    },
    "last_response": "Opened chrome",
    "pending_clarification": null,
    "context": {
        "last_file": "report.pdf",
        "last_folder": "Documents"
    },
    "timestamp": "2024-01-15T10:30:00"
}
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `last_intent` | string | Most recent detected intent |
| `last_entities` | object | Entities from last command |
| `last_response` | string | Last response given |
| `pending_clarification` | object/null | If waiting for clarification |
| `context` | object | Accumulated context |
| `timestamp` | string | Last update time |

---

## Long-Term Memory (SQLite)

Stored in: `data/memory.db`

### Tables

#### `commands` - Command History
```sql
CREATE TABLE commands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    intent TEXT NOT NULL,
    entities TEXT,          -- JSON string
    success INTEGER,        -- 1 or 0
    response TEXT
);
```

#### `app_usage` - App Usage Stats
```sql
CREATE TABLE app_usage (
    app_name TEXT PRIMARY KEY,
    open_count INTEGER DEFAULT 0,
    last_opened TEXT
);
```

#### `preferences` - User Preferences
```sql
CREATE TABLE preferences (
    key TEXT PRIMARY KEY,
    value TEXT
);
```

---

## Usage Examples

### Get Recent Commands
```python
from core.memory import get_long_term_memory

ltm = get_long_term_memory()
commands = ltm.get_recent_commands(limit=10)
```

### Track App Usage
```python
ltm.track_app_usage("chrome")  # Increments count
```

### Get Most Used Apps
```python
stats = ltm.get_command_stats()
# Returns: {"most_used_apps": [...], "command_count": 150}
```

---

## Memory Flow

```
User says command
       │
       ▼
┌──────────────────┐
│ Process command  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐     ┌──────────────────┐
│ Update short-    │     │ Log to long-     │
│ term memory      │     │ term memory      │
│ (JSON)           │     │ (SQLite)         │
└──────────────────┘     └──────────────────┘
```

---

## Data Location

```
assistant/
└── data/
    ├── short_term.json    # Current session context
    ├── memory.db          # SQLite database
    └── reminders.json     # Alarms & reminders
```
