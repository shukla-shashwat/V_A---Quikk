"""file_tools.py
Utility helpers for file operations used by the assistant.
"""

import os
from typing import List


def list_files(path: str) -> List[str]:
    try:
        return [os.path.join(path, p) for p in os.listdir(path)]
    except FileNotFoundError:
        return []
