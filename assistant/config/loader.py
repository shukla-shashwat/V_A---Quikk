# config/loader.py
"""
Configuration loader - reads settings.yaml
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict

CONFIG_FILE = Path(__file__).parent / "settings.yaml"

_config: Dict = None


def load_config() -> Dict:
    """Load configuration from settings.yaml"""
    global _config
    
    if _config is not None:
        return _config
    
    try:
        with open(CONFIG_FILE, "r") as f:
            _config = yaml.safe_load(f) or {}
    except FileNotFoundError:
        _config = {}
    except yaml.YAMLError:
        _config = {}
    
    return _config


def get(key: str, default: Any = None) -> Any:
    """
    Get a config value by dot-notation key.
    Example: get("screenshot.save_path")
    """
    config = load_config()
    
    keys = key.split(".")
    value = config
    
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default
    
    return value


def get_screenshot_path() -> str:
    """Get screenshot save path."""
    return get("screenshot.save_path", 
               os.path.join(os.path.expanduser("~"), "Pictures", "Screenshots"))


def get_search_drives() -> list:
    """Get drives to search."""
    return get("file_search.search_drives", ["C:\\", "D:\\"])


def get_skip_folders() -> list:
    """Get folders to skip during search."""
    return get("file_search.skip_folders", [
        "Windows", "Program Files", "Program Files (x86)", 
        "ProgramData", "$Recycle.Bin", "node_modules", 
        "__pycache__", ".git", "venv", "AppData"
    ])


def get_max_results() -> int:
    """Get max search results."""
    return get("file_search.max_results", 20)
