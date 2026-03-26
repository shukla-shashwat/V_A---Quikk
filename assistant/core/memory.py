# core/memory.py
"""
Memory system - short-term (JSON) and long-term (SQLite) storage.
Handles conversation context, command history, and user preferences.
"""

import json
import sqlite3
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

# Paths
DATA_DIR = Path(__file__).parent.parent / "data"
MEMORY_FILE = DATA_DIR / "memory.json"
DB_FILE = DATA_DIR / "assistant.db"


class ShortTermMemory:
    """In-memory + JSON storage for current conversation context."""
    
    def __init__(self):
        self.data: Dict = {
            "last_intent": None,
            "last_entities": {},
            "last_response": None,
            "pending_clarification": None,
            "conversation_turns": [],
            "session_start": datetime.now().isoformat()
        }
        self._load()
    
    def _load(self):
        """Load from JSON file."""
        try:
            if MEMORY_FILE.exists():
                with open(MEMORY_FILE, "r") as f:
                    saved = json.load(f)
                    self.data.update(saved)
        except (json.JSONDecodeError, IOError):
            pass  # Start fresh
    
    def save(self):
        """Save to JSON file."""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(MEMORY_FILE, "w") as f:
            json.dump(self.data, f, indent=2, default=str)
    
    def update(self, intent: str, entities: Dict, response: str):
        """Update memory with latest interaction."""
        self.data["last_intent"] = intent
        self.data["last_entities"] = entities
        self.data["last_response"] = response
        self.data["conversation_turns"].append({
            "timestamp": datetime.now().isoformat(),
            "intent": intent,
            "entities": entities,
            "response": response[:200]  # Truncate for storage
        })
        # Keep only last 20 turns in short-term
        self.data["conversation_turns"] = self.data["conversation_turns"][-20:]
        self.save()
    
    def set_pending_clarification(self, intent: str, entities: Dict, missing_param: str):
        """Store pending clarification state."""
        self.data["pending_clarification"] = {
            "intent": intent,
            "entities": entities,
            "missing_param": missing_param,
            "timestamp": datetime.now().isoformat()
        }
        self.save()
    
    def get_pending_clarification(self) -> Optional[Dict]:
        """Get pending clarification if any."""
        return self.data.get("pending_clarification")
    
    def clear_pending_clarification(self):
        """Clear pending clarification."""
        self.data["pending_clarification"] = None
        self.save()
    
    def get_last_intent(self) -> Optional[str]:
        return self.data.get("last_intent")
    
    def get_last_entities(self) -> Dict:
        return self.data.get("last_entities", {})
    
    def get_context(self) -> Dict:
        """Get conversation context for decision making."""
        return {
            "last_intent": self.data.get("last_intent"),
            "last_entities": self.data.get("last_entities"),
            "turns_count": len(self.data.get("conversation_turns", [])),
            "pending": self.data.get("pending_clarification")
        }
    
    def clear(self):
        """Clear short-term memory."""
        self.data = {
            "last_intent": None,
            "last_entities": {},
            "last_response": None,
            "pending_clarification": None,
            "conversation_turns": [],
            "session_start": datetime.now().isoformat()
        }
        self.save()


class LongTermMemory:
    """SQLite storage for command history and preferences."""
    
    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(DB_FILE))
        self.conn.row_factory = sqlite3.Row
        self._init_tables()
    
    def _init_tables(self):
        """Create tables if they don't exist."""
        cursor = self.conn.cursor()
        
        # Command history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS command_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                intent TEXT NOT NULL,
                entities TEXT,
                success INTEGER DEFAULT 1,
                response TEXT
            )
        ''')
        
        # User preferences
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS preferences (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TEXT
            )
        ''')
        
        # Frequently used apps
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS app_usage (
                app_name TEXT PRIMARY KEY,
                use_count INTEGER DEFAULT 0,
                last_used TEXT
            )
        ''')
        
        self.conn.commit()
    
    def log_command(self, intent: str, entities: Dict, success: bool, response: str):
        """Log a command execution."""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO command_history (timestamp, intent, entities, success, response)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            intent,
            json.dumps(entities),
            1 if success else 0,
            response[:500]
        ))
        self.conn.commit()
    
    def get_recent_commands(self, limit: int = 10) -> List[Dict]:
        """Get recent commands."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM command_history 
            ORDER BY timestamp DESC LIMIT ?
        ''', (limit,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def get_command_stats(self) -> Dict:
        """Get command usage statistics."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT intent, COUNT(*) as count 
            FROM command_history 
            GROUP BY intent 
            ORDER BY count DESC
        ''')
        return {row['intent']: row['count'] for row in cursor.fetchall()}
    
    def track_app_usage(self, app_name: str):
        """Track app usage for suggestions."""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO app_usage (app_name, use_count, last_used)
            VALUES (?, 1, ?)
            ON CONFLICT(app_name) DO UPDATE SET
                use_count = use_count + 1,
                last_used = excluded.last_used
        ''', (app_name.lower(), datetime.now().isoformat()))
        self.conn.commit()
    
    def get_frequent_apps(self, limit: int = 5) -> List[str]:
        """Get most frequently used apps."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT app_name FROM app_usage 
            ORDER BY use_count DESC LIMIT ?
        ''', (limit,))
        return [row['app_name'] for row in cursor.fetchall()]
    
    def set_preference(self, key: str, value: Any):
        """Set a user preference."""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO preferences (key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
        ''', (key, json.dumps(value), datetime.now().isoformat()))
        self.conn.commit()
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT value FROM preferences WHERE key = ?', (key,))
        row = cursor.fetchone()
        if row:
            return json.loads(row['value'])
        return default
    
    def close(self):
        """Close database connection."""
        self.conn.close()


# Global memory instances
_short_term: Optional[ShortTermMemory] = None
_long_term: Optional[LongTermMemory] = None


def get_short_term_memory() -> ShortTermMemory:
    """Get or create short-term memory instance."""
    global _short_term
    if _short_term is None:
        _short_term = ShortTermMemory()
    return _short_term


def get_long_term_memory() -> LongTermMemory:
    """Get or create long-term memory instance."""
    global _long_term
    if _long_term is None:
        _long_term = LongTermMemory()
    return _long_term


# Legacy functions for backward compatibility
def load_memory() -> Dict:
    """Load memory (legacy)."""
    return get_short_term_memory().data


def save_memory(memory: Dict):
    """Save memory (legacy)."""
    stm = get_short_term_memory()
    stm.data.update(memory)
    stm.save()


def update_memory(memory: Dict, intent: str, entities: Dict):
    """Update memory (legacy)."""
    stm = get_short_term_memory()
    stm.update(intent, entities, "")
