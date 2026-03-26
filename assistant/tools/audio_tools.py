# tools/audio_tools.py
"""
Audio control tools - volume management using pycaw or fallback methods.
"""

import subprocess
from typing import Tuple, Optional

# Try importing pycaw for precise volume control
try:
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    HAS_PYCAW = True
except ImportError:
    HAS_PYCAW = False


def _get_volume_interface():
    """Get the Windows audio endpoint volume interface."""
    if not HAS_PYCAW:
        return None
    
    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        return cast(interface, POINTER(IAudioEndpointVolume))
    except Exception:
        return None


def get_volume() -> Tuple[bool, int]:
    """
    Get current system volume.
    
    Returns:
        Tuple of (success, volume_percent)
    """
    if HAS_PYCAW:
        try:
            volume = _get_volume_interface()
            if volume:
                current = volume.GetMasterVolumeLevelScalar()
                return True, int(current * 100)
        except Exception:
            pass
    
    return False, 0


def set_volume(level: int) -> Tuple[bool, str]:
    """
    Set system volume to a specific level.
    
    Args:
        level: Volume level (0-100)
    
    Returns:
        Tuple of (success, message)
    """
    level = max(0, min(100, level))  # Clamp to 0-100
    
    if HAS_PYCAW:
        try:
            volume = _get_volume_interface()
            if volume:
                volume.SetMasterVolumeLevelScalar(level / 100.0, None)
                return True, f"Volume set to {level}%"
        except Exception as e:
            return False, f"Failed to set volume: {e}"
    
    # Fallback: Use nircmd or PowerShell
    try:
        # PowerShell fallback
        ps_script = f'''
        $volume = [Audio]::Volume
        [Audio]::Volume = {level / 100.0}
        '''
        # Alternative: Use nircmd if available
        subprocess.run(
            f'powershell -Command "(New-Object -ComObject WScript.Shell).SendKeys([char]173)"',
            shell=True, capture_output=True
        )
        return True, f"Volume set to {level}% (fallback method)"
    except Exception as e:
        return False, f"Volume control not available. Install pycaw: pip install pycaw"


def volume_up(step: int = 10) -> Tuple[bool, str]:
    """Increase volume by step percent."""
    success, current = get_volume()
    if success:
        new_level = min(100, current + step)
        return set_volume(new_level)
    
    # Fallback: send media key
    try:
        subprocess.run(
            'powershell -Command "(New-Object -ComObject WScript.Shell).SendKeys([char]175)"',
            shell=True, capture_output=True
        )
        return True, "Volume increased"
    except:
        return False, "Could not increase volume"


def volume_down(step: int = 10) -> Tuple[bool, str]:
    """Decrease volume by step percent."""
    success, current = get_volume()
    if success:
        new_level = max(0, current - step)
        return set_volume(new_level)
    
    # Fallback: send media key
    try:
        subprocess.run(
            'powershell -Command "(New-Object -ComObject WScript.Shell).SendKeys([char]174)"',
            shell=True, capture_output=True
        )
        return True, "Volume decreased"
    except:
        return False, "Could not decrease volume"


def mute() -> Tuple[bool, str]:
    """Mute system audio."""
    if HAS_PYCAW:
        try:
            volume = _get_volume_interface()
            if volume:
                volume.SetMute(1, None)
                return True, "Audio muted"
        except Exception as e:
            return False, f"Failed to mute: {e}"
    
    # Fallback
    try:
        subprocess.run(
            'powershell -Command "(New-Object -ComObject WScript.Shell).SendKeys([char]173)"',
            shell=True, capture_output=True
        )
        return True, "Audio muted (toggle)"
    except:
        return False, "Could not mute"


def unmute() -> Tuple[bool, str]:
    """Unmute system audio."""
    if HAS_PYCAW:
        try:
            volume = _get_volume_interface()
            if volume:
                volume.SetMute(0, None)
                return True, "Audio unmuted"
        except Exception as e:
            return False, f"Failed to unmute: {e}"
    
    # Fallback
    try:
        subprocess.run(
            'powershell -Command "(New-Object -ComObject WScript.Shell).SendKeys([char]173)"',
            shell=True, capture_output=True
        )
        return True, "Audio unmuted (toggle)"
    except:
        return False, "Could not unmute"


def is_muted() -> Tuple[bool, bool]:
    """Check if audio is muted."""
    if HAS_PYCAW:
        try:
            volume = _get_volume_interface()
            if volume:
                return True, bool(volume.GetMute())
        except:
            pass
    
    return False, False
