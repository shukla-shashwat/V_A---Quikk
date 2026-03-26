# tools/system_tools.py
"""
System-level tools for controlling Windows.
Handles apps, power, screenshots, and system info.
"""

import os
import subprocess
import platform
import ctypes
from typing import Dict, List, Optional, Tuple
from datetime import datetime


# Windows-specific imports (safe import)
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


def system_info() -> Dict[str, str]:
    """Get basic system information."""
    info = {
        "platform": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "hostname": platform.node()
    }
    
    if HAS_PSUTIL:
        # CPU
        info["cpu_percent"] = f"{psutil.cpu_percent(interval=0.5)}%"
        info["cpu_count"] = str(psutil.cpu_count())
        
        # Memory
        mem = psutil.virtual_memory()
        info["ram_total"] = f"{mem.total / (1024**3):.1f} GB"
        info["ram_used"] = f"{mem.used / (1024**3):.1f} GB"
        info["ram_percent"] = f"{mem.percent}%"
        
        # Disk
        disk = psutil.disk_usage('/')
        info["disk_total"] = f"{disk.total / (1024**3):.1f} GB"
        info["disk_used"] = f"{disk.used / (1024**3):.1f} GB"
        info["disk_percent"] = f"{disk.percent}%"
        
        # Battery
        battery = psutil.sensors_battery()
        if battery:
            info["battery_percent"] = f"{battery.percent}%"
            info["battery_plugged"] = "Yes" if battery.power_plugged else "No"
            if not battery.power_plugged and battery.secsleft > 0:
                hours = battery.secsleft // 3600
                mins = (battery.secsleft % 3600) // 60
                info["battery_time_left"] = f"{hours}h {mins}m"
    
    return info


def get_battery_status() -> Dict:
    """Get battery status."""
    if not HAS_PSUTIL:
        return {"error": "psutil not installed"}
    
    battery = psutil.sensors_battery()
    if not battery:
        return {"error": "No battery detected (desktop PC?)"}
    
    return {
        "percent": battery.percent,
        "plugged": battery.power_plugged,
        "time_left_seconds": battery.secsleft if not battery.power_plugged else None
    }


def get_cpu_usage() -> Dict:
    """Get CPU usage information."""
    if not HAS_PSUTIL:
        return {"error": "psutil not installed"}
    
    return {
        "percent": psutil.cpu_percent(interval=0.5),
        "count": psutil.cpu_count(),
        "count_logical": psutil.cpu_count(logical=True)
    }


def get_memory_usage() -> Dict:
    """Get memory usage information."""
    if not HAS_PSUTIL:
        return {"error": "psutil not installed"}
    
    mem = psutil.virtual_memory()
    return {
        "total_gb": round(mem.total / (1024**3), 2),
        "used_gb": round(mem.used / (1024**3), 2),
        "available_gb": round(mem.available / (1024**3), 2),
        "percent": mem.percent
    }


def get_disk_usage(path: str = "C:/") -> Dict:
    """Get disk usage information."""
    if not HAS_PSUTIL:
        return {"error": "psutil not installed"}
    
    try:
        disk = psutil.disk_usage(path)
        return {
            "path": path,
            "total_gb": round(disk.total / (1024**3), 2),
            "used_gb": round(disk.used / (1024**3), 2),
            "free_gb": round(disk.free / (1024**3), 2),
            "percent": disk.percent
        }
    except Exception as e:
        return {"error": str(e)}


# Application control
APP_PATHS: Dict[str, str] = {
    "chrome": "chrome",
    "firefox": "firefox",
    "msedge": "msedge",
    "notepad": "notepad",
    "calc": "calc",
    "explorer": "explorer",
    "cmd": "cmd",
    "powershell": "powershell",
    "wt": "wt",  # Windows Terminal
    "code": "code",
    "discord": "discord",
    "slack": "slack",
    "winword": "winword",
    "excel": "excel",
    "powerpnt": "powerpnt",
    "outlook": "outlook",
    "mspaint": "mspaint",
    "taskmgr": "taskmgr",
    "control": "control",
    "zoom": "zoom",
    "vlc": "vlc",
    "obs64": "obs64",
    "postman": "postman",
}

# UWP App Package Names (for Microsoft Store apps)
UWP_APPS: Dict[str, str] = {
    "notion": "Notion.Notion",
    "whatsapp": "5319275A.WhatsAppDesktop",
    "spotify": "SpotifyAB.SpotifyMusic",
    "telegram": "TelegramMessengerLLP.TelegramDesktop",
    "netflix": "4DF9E0F8.Netflix",
    "twitter": "9E2F88E3.Twitter",
    "instagram": "Facebook.InstagramBeta",
    "messenger": "Facebook.Messenger",
    "teams": "Microsoft.Teams",
    "xbox": "Microsoft.XboxApp",
    "photos": "Microsoft.Windows.Photos",
    "mail": "microsoft.windowscommunicationsapps",
    "calendar": "microsoft.windowscommunicationsapps",
    "store": "Microsoft.WindowsStore",
    "camera": "Microsoft.WindowsCamera",
    "clock": "Microsoft.WindowsAlarms",
    "maps": "Microsoft.WindowsMaps",
    "weather": "Microsoft.BingWeather",
    "news": "Microsoft.BingNews",
    "calculator": "Microsoft.WindowsCalculator",
}


def _find_uwp_app(app_keyword: str) -> Optional[str]:
    """
    Find UWP app's full name using PowerShell.
    Returns the AppUserModelId that can be used to launch the app.
    """
    try:
        # Use PowerShell to find the app
        cmd = f'powershell -Command "Get-AppxPackage | Where-Object {{$_.Name -like \'*{app_keyword}*\'}} | Select-Object -First 1 -ExpandProperty PackageFamilyName"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and result.stdout.strip():
            package_family = result.stdout.strip()
            # Most apps use "App" as the application ID
            return f"shell:AppsFolder\\{package_family}!App"
        return None
    except Exception:
        return None


def _try_uwp_launch(app_name: str) -> Tuple[bool, str]:
    """
    Try to launch an app as a UWP/Store app.
    """
    # Check if we have a known package name
    uwp_package = UWP_APPS.get(app_name.lower())
    
    if uwp_package:
        # Try to find and launch
        app_id = _find_uwp_app(uwp_package)
        if app_id:
            try:
                subprocess.Popen(f'explorer.exe "{app_id}"', shell=True)
                return True, f"Opened {app_name}"
            except Exception as e:
                return False, f"Failed to open {app_name}: {e}"
    
    # Try searching by name directly
    app_id = _find_uwp_app(app_name)
    if app_id:
        try:
            subprocess.Popen(f'explorer.exe "{app_id}"', shell=True)
            return True, f"Opened {app_name}"
        except Exception as e:
            return False, f"Failed to open {app_name}: {e}"
    
    return False, f"Could not find UWP app: {app_name}"


def open_application(app_name: str) -> Tuple[bool, str]:
    """
    Open an application by name.
    Supports regular desktop apps and UWP/Microsoft Store apps.
    
    Returns:
        Tuple of (success, message)
    """
    app_name_clean = app_name.lower().strip()
    
    # Handle special URI schemes (settings, spotify:, etc.)
    if app_name_clean.endswith(':') or app_name_clean == "settings":
        uri = "ms-settings:" if app_name_clean == "settings" else app_name_clean
        try:
            os.startfile(uri)
            return True, f"Opened {app_name}"
        except Exception as e:
            return False, f"Failed to open {app_name}: {e}"
    
    # Check if it's a known UWP app first
    if app_name_clean in UWP_APPS:
        success, msg = _try_uwp_launch(app_name_clean)
        if success:
            return success, msg
        # If UWP launch fails, try regular method below
    
    # Get executable name from known apps
    executable = APP_PATHS.get(app_name_clean, app_name_clean)
    
    try:
        # Try using start command (works for most desktop apps)
        result = subprocess.run(
            f'start "" "{executable}"',
            shell=True,
            capture_output=True,
            timeout=5
        )
        
        # Check if command seemed to work
        if result.returncode == 0:
            return True, f"Opened {app_name}"
        
        # If start failed, try UWP as fallback
        success, msg = _try_uwp_launch(app_name_clean)
        if success:
            return success, msg
            
        # Try one more method - where.exe to find the app
        where_result = subprocess.run(
            f'where {executable}',
            shell=True,
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if where_result.returncode == 0 and where_result.stdout.strip():
            # Found the executable path
            exe_path = where_result.stdout.strip().split('\n')[0]
            subprocess.Popen(exe_path, shell=True)
            return True, f"Opened {app_name}"
        
        # Final fallback - try UWP with original name
        return _try_uwp_launch(app_name)
        
    except subprocess.TimeoutExpired:
        return True, f"Opening {app_name}..."
    except Exception as e:
        # Final attempt - try as UWP app
        success, msg = _try_uwp_launch(app_name_clean)
        if success:
            return success, msg
        return False, f"Application not found: {app_name}"


def close_application(app_name: str) -> Tuple[bool, str]:
    """
    Close an application by name.
    
    Returns:
        Tuple of (success, message)
    """
    if not HAS_PSUTIL:
        return False, "psutil not installed - cannot manage processes"
    
    app_name = app_name.lower().strip()
    executable = APP_PATHS.get(app_name, app_name)
    
    # Find and terminate matching processes
    closed_count = 0
    for proc in psutil.process_iter(['name', 'pid']):
        try:
            proc_name = proc.info['name'].lower()
            if executable.lower() in proc_name or app_name in proc_name:
                proc.terminate()
                closed_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    if closed_count > 0:
        return True, f"Closed {closed_count} instance(s) of {app_name}"
    else:
        return False, f"No running instances of {app_name} found"


def list_running_apps() -> List[Dict]:
    """Get list of running applications."""
    if not HAS_PSUTIL:
        return []
    
    apps = []
    seen = set()
    
    for proc in psutil.process_iter(['name', 'pid', 'memory_percent']):
        try:
            name = proc.info['name']
            if name not in seen and proc.info['memory_percent'] > 0.1:
                apps.append({
                    "name": name,
                    "pid": proc.info['pid'],
                    "memory_percent": round(proc.info['memory_percent'], 2)
                })
                seen.add(name)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    # Sort by memory usage
    apps.sort(key=lambda x: x['memory_percent'], reverse=True)
    return apps[:20]  # Top 20


# Power controls
def lock_screen() -> Tuple[bool, str]:
    """Lock the Windows screen."""
    try:
        ctypes.windll.user32.LockWorkStation()
        return True, "Screen locked"
    except Exception as e:
        return False, f"Failed to lock screen: {e}"


def shutdown_computer(delay: int = 0) -> Tuple[bool, str]:
    """Shutdown the computer."""
    try:
        os.system(f"shutdown /s /t {delay}")
        return True, f"Shutting down in {delay} seconds..."
    except Exception as e:
        return False, f"Failed to shutdown: {e}"


def restart_computer(delay: int = 0) -> Tuple[bool, str]:
    """Restart the computer."""
    try:
        os.system(f"shutdown /r /t {delay}")
        return True, f"Restarting in {delay} seconds..."
    except Exception as e:
        return False, f"Failed to restart: {e}"


def sleep_computer() -> Tuple[bool, str]:
    """Put computer to sleep."""
    try:
        # Using powercfg for sleep
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
        return True, "Going to sleep..."
    except Exception as e:
        return False, f"Failed to sleep: {e}"


def cancel_shutdown() -> Tuple[bool, str]:
    """Cancel pending shutdown/restart."""
    try:
        os.system("shutdown /a")
        return True, "Shutdown cancelled"
    except Exception as e:
        return False, f"Failed to cancel: {e}"


# Screenshot
def take_screenshot(save_path: str = None) -> Tuple[bool, str]:
    """Take a screenshot and save it."""
    try:
        # Check for PIL/Pillow first
        try:
            from PIL import Image
        except ImportError:
            return False, "Pillow not installed. Run: pip install Pillow"
        
        import pyautogui
        
        if save_path is None:
            # Get path from config
            try:
                from config.loader import get_screenshot_path
                pictures = get_screenshot_path()
            except ImportError:
                pictures = os.path.join(os.path.expanduser("~"), "Pictures", "Screenshots")
            
            os.makedirs(pictures, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = os.path.join(pictures, f"screenshot_{timestamp}.png")
        
        screenshot = pyautogui.screenshot()
        screenshot.save(save_path)
        return True, f"Screenshot saved to {save_path}"
    except ImportError:
        return False, "pyautogui not installed. Run: pip install pyautogui Pillow"
    except Exception as e:
        return False, f"Failed to take screenshot: {e}"


# Time and date
def get_current_time() -> str:
    """Get current time."""
    return datetime.now().strftime("%I:%M %p")


def get_current_date() -> str:
    """Get current date."""
    return datetime.now().strftime("%A, %B %d, %Y")
