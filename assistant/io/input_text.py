"""input_text.py
Handles text input. Stub that returns passed text.
"""

from typing import Callable


def get_input(prompt: str = "> ") -> str:
    try:
        return input(prompt)
    except EOFError:
        return ""
