# core/memory.py

import json

MEMORY_FILE = "data/memory.json"

def load_memory():
    try:
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)

def update_memory(memory, intent, entities):
    memory["last_intent"] = intent
    memory["last_entities"] = entities
    save_memory(memory)
