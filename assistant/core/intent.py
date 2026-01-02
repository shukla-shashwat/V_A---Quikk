"""intent.py
Detects intent and returns a confidence score.
This is a placeholder implementation.
"""

from typing import Dict


def detect_intent(text: str) -> Dict[str, object]:
    """Return a simple intent prediction for the stub project.

    For now, this function does a naive keyword check.
    """
    lowered = text.lower().strip()
    if not lowered:
        return {"name": "empty", "confidence": 0.0}
    if "help" in lowered or "support" in lowered:
        return {"name": "help_request", "confidence": 0.9}
    if "calculate" in lowered or "math" in lowered:
        return {"name": "calculation", "confidence": 0.8}
    return {"name": "general", "confidence": 0.6}
