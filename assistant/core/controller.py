"""controller.py
Brain switchboard: routes inputs to intent, clarifier, memory, tools and llm.
This is a small, safe stub for initial project structure.
"""

from typing import Any


def handle_input(text: str) -> dict:
    """Very small stub that demonstrates the controller API.

    Returns a dict with keys: "intent", "response".
    """
    # Lazy imports to avoid circulars in the stub
    from assistant.core import intent as intent_mod

    detected = intent_mod.detect_intent(text)
    return {
        "intent": detected,
        "response": f"Received input with intent '{detected.get('name')}'"
    }
