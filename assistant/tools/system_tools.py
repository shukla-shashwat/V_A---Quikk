"""system_tools.py
System-level helpers, kept minimal and safe in the stub.
"""

import platform
from typing import Dict


def system_info() -> Dict[str, str]:
    return {"platform": platform.system(), "release": platform.release()}
