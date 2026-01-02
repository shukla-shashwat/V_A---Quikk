"""clarifier.py
Asks follow-up questions when intent confidence is low.
Stub implementation: returns None or a clarifying question.
"""

from typing import Optional


def clarify_if_needed(intent: dict) -> Optional[str]:
    """Return a clarifying question when confidence < 0.7.

    Otherwise return None.
    """
    if intent.get("confidence", 1.0) < 0.7:
        return "Can you tell me more about what you mean?"
    return None
