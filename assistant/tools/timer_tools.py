# tools/timer_tools.py
"""
Timer, Alarm, and Reminder tools for Qwikk.
Supports background timers with notifications.
"""

import threading
import time
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path

# Try importing Windows notification library
try:
    from win10toast import ToastNotifier
    HAS_TOAST = True
except ImportError:
    HAS_TOAST = False

# Try importing plyer for cross-platform notifications
try:
    from plyer import notification
    HAS_PLYER = True
except ImportError:
    HAS_PLYER = False


# Storage file for persistent reminders/alarms
DATA_DIR = Path(__file__).parent.parent / "data"
REMINDERS_FILE = DATA_DIR / "reminders.json"


class TimerManager:
    """Manages timers, alarms, and reminders."""
    
    def __init__(self):
        self.active_timers: Dict[str, dict] = {}
        self.active_alarms: Dict[str, dict] = {}
        self.reminders: List[dict] = []
        self._timer_id = 0
        self._load_reminders()
        self._start_reminder_checker()
    
    def _load_reminders(self):
        """Load saved reminders from file."""
        try:
            if REMINDERS_FILE.exists():
                with open(REMINDERS_FILE, 'r') as f:
                    data = json.load(f)
                    self.reminders = data.get("reminders", [])
                    self.active_alarms = data.get("alarms", {})
        except:
            self.reminders = []
            self.active_alarms = {}
    
    def _save_reminders(self):
        """Save reminders to file."""
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            with open(REMINDERS_FILE, 'w') as f:
                json.dump({
                    "reminders": self.reminders,
                    "alarms": self.active_alarms
                }, f, indent=2)
        except Exception as e:
            print(f"Failed to save reminders: {e}")
    
    def _start_reminder_checker(self):
        """Start background thread to check reminders."""
        def check_loop():
            while True:
                self._check_reminders()
                self._check_alarms()
                time.sleep(30)  # Check every 30 seconds
        
        thread = threading.Thread(target=check_loop, daemon=True)
        thread.start()
    
    def _check_reminders(self):
        """Check and trigger due reminders."""
        now = datetime.now()
        triggered = []
        
        for reminder in self.reminders:
            remind_time = datetime.fromisoformat(reminder["time"])
            if now >= remind_time:
                self._notify(f"⏰ Reminder: {reminder['message']}")
                triggered.append(reminder)
        
        # Remove triggered reminders
        for r in triggered:
            self.reminders.remove(r)
        
        if triggered:
            self._save_reminders()
    
    def _check_alarms(self):
        """Check and trigger due alarms."""
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        triggered = []
        
        for alarm_id, alarm in self.active_alarms.items():
            if alarm["time"] == current_time and not alarm.get("triggered_today"):
                self._notify(f"⏰ ALARM: {alarm.get('label', 'Wake up!')}")
                self._play_alarm_sound()
                alarm["triggered_today"] = True
                triggered.append(alarm_id)
        
        # Reset triggered flag at midnight
        if current_time == "00:00":
            for alarm in self.active_alarms.values():
                alarm["triggered_today"] = False
        
        if triggered:
            self._save_reminders()
    
    def _notify(self, message: str):
        """Show a notification."""
        print(f"\n🔔 {message}\n")
        
        if HAS_PLYER:
            try:
                notification.notify(
                    title="Qwikk",
                    message=message,
                    app_icon=None,
                    timeout=10
                )
                return
            except:
                pass
        
        if HAS_TOAST:
            try:
                toaster = ToastNotifier()
                toaster.show_toast("Qwikk", message, duration=10, threaded=True)
                return
            except:
                pass
        
        # Fallback: system beep
        try:
            import winsound
            winsound.Beep(1000, 500)
        except:
            print("\a")  # Terminal bell
    
    def _play_alarm_sound(self):
        """Play alarm sound."""
        try:
            import winsound
            # Play multiple beeps for alarm
            for _ in range(3):
                winsound.Beep(1500, 300)
                time.sleep(0.2)
        except:
            pass
    
    # Timer functions
    def set_timer(self, seconds: int, label: str = "Timer") -> Tuple[bool, str]:
        """
        Set a countdown timer.
        
        Args:
            seconds: Number of seconds
            label: Timer label
        
        Returns:
            (success, message)
        """
        self._timer_id += 1
        timer_id = f"timer_{self._timer_id}"
        
        def timer_callback():
            self._notify(f"⏱️ Timer done: {label}")
            self._play_alarm_sound()
            if timer_id in self.active_timers:
                del self.active_timers[timer_id]
        
        timer = threading.Timer(seconds, timer_callback)
        timer.start()
        
        end_time = datetime.now() + timedelta(seconds=seconds)
        self.active_timers[timer_id] = {
            "label": label,
            "seconds": seconds,
            "end_time": end_time.isoformat(),
            "thread": timer
        }
        
        # Format duration nicely
        if seconds >= 3600:
            duration = f"{seconds // 3600} hour(s) {(seconds % 3600) // 60} min"
        elif seconds >= 60:
            duration = f"{seconds // 60} minute(s)"
        else:
            duration = f"{seconds} second(s)"
        
        return True, f"⏱️ Timer set for {duration}"
    
    def cancel_timer(self, timer_id: str = None) -> Tuple[bool, str]:
        """Cancel a timer."""
        if timer_id and timer_id in self.active_timers:
            self.active_timers[timer_id]["thread"].cancel()
            del self.active_timers[timer_id]
            return True, "Timer cancelled"
        
        # Cancel most recent timer
        if self.active_timers:
            latest = list(self.active_timers.keys())[-1]
            self.active_timers[latest]["thread"].cancel()
            del self.active_timers[latest]
            return True, "Timer cancelled"
        
        return False, "No active timers"
    
    def list_timers(self) -> List[dict]:
        """List active timers."""
        return [
            {
                "id": tid,
                "label": t["label"],
                "end_time": t["end_time"]
            }
            for tid, t in self.active_timers.items()
        ]
    
    # Alarm functions
    def set_alarm(self, time_str: str, label: str = "Alarm") -> Tuple[bool, str]:
        """
        Set an alarm for a specific time.
        
        Args:
            time_str: Time in HH:MM format (24-hour)
            label: Alarm label
        
        Returns:
            (success, message)
        """
        # Parse time
        try:
            # Handle various formats
            time_str = time_str.strip().upper()
            
            # Handle AM/PM
            is_pm = "PM" in time_str
            is_am = "AM" in time_str
            time_str = time_str.replace("AM", "").replace("PM", "").strip()
            
            if ":" in time_str:
                parts = time_str.split(":")
                hour = int(parts[0])
                minute = int(parts[1]) if len(parts) > 1 else 0
            else:
                hour = int(time_str)
                minute = 0
            
            # Convert to 24-hour
            if is_pm and hour < 12:
                hour += 12
            elif is_am and hour == 12:
                hour = 0
            
            alarm_time = f"{hour:02d}:{minute:02d}"
            
        except ValueError:
            return False, "Invalid time format. Use HH:MM (e.g., 7:30 or 14:00)"
        
        alarm_id = f"alarm_{len(self.active_alarms) + 1}"
        self.active_alarms[alarm_id] = {
            "time": alarm_time,
            "label": label,
            "triggered_today": False
        }
        
        self._save_reminders()
        
        return True, f"⏰ Alarm set for {alarm_time}"
    
    def cancel_alarm(self, alarm_id: str = None) -> Tuple[bool, str]:
        """Cancel an alarm."""
        if alarm_id and alarm_id in self.active_alarms:
            del self.active_alarms[alarm_id]
            self._save_reminders()
            return True, "Alarm cancelled"
        
        # Cancel most recent alarm
        if self.active_alarms:
            latest = list(self.active_alarms.keys())[-1]
            del self.active_alarms[latest]
            self._save_reminders()
            return True, "Alarm cancelled"
        
        return False, "No active alarms"
    
    def list_alarms(self) -> List[dict]:
        """List active alarms."""
        return [
            {"id": aid, "time": a["time"], "label": a["label"]}
            for aid, a in self.active_alarms.items()
        ]
    
    # Reminder functions
    def set_reminder(self, message: str, when: str) -> Tuple[bool, str]:
        """
        Set a reminder.
        
        Args:
            message: Reminder message
            when: When to remind (e.g., "in 30 minutes", "at 3pm", "tomorrow")
        
        Returns:
            (success, message)
        """
        remind_time = self._parse_reminder_time(when)
        
        if not remind_time:
            return False, "Couldn't understand the time. Try 'in 30 minutes' or 'at 3pm'"
        
        self.reminders.append({
            "message": message,
            "time": remind_time.isoformat(),
            "created": datetime.now().isoformat()
        })
        
        self._save_reminders()
        
        formatted_time = remind_time.strftime("%I:%M %p on %b %d")
        return True, f"📝 Reminder set for {formatted_time}: {message}"
    
    def _parse_reminder_time(self, when: str) -> Optional[datetime]:
        """Parse reminder time from natural language."""
        when = when.lower().strip()
        now = datetime.now()
        
        # "in X minutes/hours"
        import re
        in_match = re.search(r'in\s+(\d+)\s*(min|minute|hour|hr|sec|second)s?', when)
        if in_match:
            amount = int(in_match.group(1))
            unit = in_match.group(2)
            
            if 'min' in unit:
                return now + timedelta(minutes=amount)
            elif 'hour' in unit or 'hr' in unit:
                return now + timedelta(hours=amount)
            elif 'sec' in unit:
                return now + timedelta(seconds=amount)
        
        # "at X:XX" or "at Xpm"
        at_match = re.search(r'at\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', when)
        if at_match:
            hour = int(at_match.group(1))
            minute = int(at_match.group(2) or 0)
            period = at_match.group(3)
            
            if period == 'pm' and hour < 12:
                hour += 12
            elif period == 'am' and hour == 12:
                hour = 0
            
            remind_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # If time has passed today, set for tomorrow
            if remind_time <= now:
                remind_time += timedelta(days=1)
            
            return remind_time
        
        # "tomorrow"
        if 'tomorrow' in when:
            return now + timedelta(days=1)
        
        # "tonight"
        if 'tonight' in when:
            return now.replace(hour=20, minute=0, second=0, microsecond=0)
        
        return None
    
    def cancel_reminder(self, index: int = None) -> Tuple[bool, str]:
        """Cancel a reminder."""
        if not self.reminders:
            return False, "No active reminders"
        
        if index is not None and 0 <= index < len(self.reminders):
            removed = self.reminders.pop(index)
            self._save_reminders()
            return True, f"Cancelled reminder: {removed['message']}"
        
        # Cancel most recent
        removed = self.reminders.pop()
        self._save_reminders()
        return True, f"Cancelled reminder: {removed['message']}"
    
    def list_reminders(self) -> List[dict]:
        """List active reminders."""
        return self.reminders


# Global instance
_timer_manager: Optional[TimerManager] = None


def get_timer_manager() -> TimerManager:
    """Get or create timer manager instance."""
    global _timer_manager
    if _timer_manager is None:
        _timer_manager = TimerManager()
    return _timer_manager


# Convenience functions
def set_timer(duration: str) -> Tuple[bool, str]:
    """
    Set a timer from natural language duration.
    E.g., "5 minutes", "1 hour 30 minutes", "90 seconds"
    """
    import re
    
    duration = duration.lower()
    total_seconds = 0
    
    # Parse hours
    hours = re.search(r'(\d+)\s*(?:hour|hr)s?', duration)
    if hours:
        total_seconds += int(hours.group(1)) * 3600
    
    # Parse minutes
    minutes = re.search(r'(\d+)\s*(?:min|minute)s?', duration)
    if minutes:
        total_seconds += int(minutes.group(1)) * 60
    
    # Parse seconds
    seconds = re.search(r'(\d+)\s*(?:sec|second)s?', duration)
    if seconds:
        total_seconds += int(seconds.group(1))
    
    # If just a number, assume minutes
    if total_seconds == 0:
        num = re.search(r'(\d+)', duration)
        if num:
            total_seconds = int(num.group(1)) * 60
    
    if total_seconds == 0:
        return False, "Couldn't understand duration. Try '5 minutes' or '1 hour'"
    
    return get_timer_manager().set_timer(total_seconds)


def set_alarm(time_str: str, label: str = "Alarm") -> Tuple[bool, str]:
    """Set an alarm for a specific time."""
    return get_timer_manager().set_alarm(time_str, label)


def set_reminder(message: str, when: str) -> Tuple[bool, str]:
    """Set a reminder."""
    return get_timer_manager().set_reminder(message, when)


def cancel_timer() -> Tuple[bool, str]:
    """Cancel the most recent timer."""
    return get_timer_manager().cancel_timer()


def cancel_alarm() -> Tuple[bool, str]:
    """Cancel the most recent alarm."""
    return get_timer_manager().cancel_alarm()


def cancel_reminder() -> Tuple[bool, str]:
    """Cancel the most recent reminder."""
    return get_timer_manager().cancel_reminder()


def list_timers() -> str:
    """List all active timers."""
    timers = get_timer_manager().list_timers()
    if not timers:
        return "No active timers"
    
    lines = ["Active timers:"]
    for t in timers:
        lines.append(f"  • {t['label']} - ends at {t['end_time'][:19]}")
    return "\n".join(lines)


def list_alarms() -> str:
    """List all active alarms."""
    alarms = get_timer_manager().list_alarms()
    if not alarms:
        return "No active alarms"
    
    lines = ["Active alarms:"]
    for a in alarms:
        lines.append(f"  • {a['time']} - {a['label']}")
    return "\n".join(lines)


def list_reminders() -> str:
    """List all active reminders."""
    reminders = get_timer_manager().list_reminders()
    if not reminders:
        return "No active reminders"
    
    lines = ["Active reminders:"]
    for r in reminders:
        remind_time = datetime.fromisoformat(r['time']).strftime("%I:%M %p, %b %d")
        lines.append(f"  • {remind_time}: {r['message']}")
    return "\n".join(lines)
