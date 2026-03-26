# tools/display_tools.py
"""
Display control tools - brightness management.
"""

import subprocess
from typing import Tuple, Optional

# Try importing screen_brightness_control
try:
    import screen_brightness_control as sbc
    HAS_SBC = True
except ImportError:
    HAS_SBC = False


def get_brightness() -> Tuple[bool, int]:
    """
    Get current screen brightness.
    
    Returns:
        Tuple of (success, brightness_percent)
    """
    if HAS_SBC:
        try:
            brightness = sbc.get_brightness()
            # Returns list if multiple monitors
            if isinstance(brightness, list):
                return True, brightness[0]
            return True, brightness
        except Exception:
            pass
    
    # WMI fallback
    try:
        result = subprocess.run(
            ['powershell', '-Command', 
             '(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness).CurrentBrightness'],
            capture_output=True, text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            return True, int(result.stdout.strip())
    except:
        pass
    
    return False, 0


def set_brightness(level: int) -> Tuple[bool, str]:
    """
    Set screen brightness.
    
    Args:
        level: Brightness level (0-100)
    
    Returns:
        Tuple of (success, message)
    """
    level = max(0, min(100, level))  # Clamp to 0-100
    
    if HAS_SBC:
        try:
            sbc.set_brightness(level)
            return True, f"Brightness set to {level}%"
        except Exception as e:
            # Try WMI fallback
            pass
    
    # WMI fallback for laptops
    try:
        result = subprocess.run(
            ['powershell', '-Command', 
             f'(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,{level})'],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            return True, f"Brightness set to {level}%"
        return False, "Brightness control not supported on this display"
    except Exception as e:
        return False, f"Failed to set brightness: {e}"


def brightness_up(step: int = 10) -> Tuple[bool, str]:
    """Increase brightness by step percent."""
    success, current = get_brightness()
    if success:
        new_level = min(100, current + step)
        return set_brightness(new_level)
    
    # Blind increase
    return set_brightness(50 + step)


def brightness_down(step: int = 10) -> Tuple[bool, str]:
    """Decrease brightness by step percent."""
    success, current = get_brightness()
    if success:
        new_level = max(0, current - step)
        return set_brightness(new_level)
    
    # Blind decrease
    return set_brightness(50 - step)
