"""memory.py
Short and long term memory stubs.
"""

from typing import List

_short_term: List[str] = []


def remember_short(item: str) -> None:
    _short_term.append(item)


def recall_short() -> List[str]:
    return list(_short_term)
