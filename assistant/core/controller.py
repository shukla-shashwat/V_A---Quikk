# core/controller.py
"""
Main controller - the brain switchboard.
Routes intents to appropriate handlers. No LLM dependency for core logic.
LLM is used only for optional response polishing.
"""

from core.intent import detect_intent, APP_ALIASES
from core.clarifier import check_clarification, handle_clarification_response, ClarificationResult
from core.memory import (
    get_short_term_memory, 
    get_long_term_memory,
)

# Tool imports
from tools.math_tools import calculate
from tools.system_tools import (
    system_info, get_battery_status, get_cpu_usage, get_memory_usage,
    open_application, close_application, list_running_apps,
    lock_screen, shutdown_computer, restart_computer, sleep_computer, cancel_shutdown,
    take_screenshot, get_current_time, get_current_date
)
from tools.file_tools import (
    open_file, open_folder, search_files, search_folders,
    find_and_open_file, find_and_open_folder,
    get_recent_files, get_downloads
)
from tools.audio_tools import (
    get_volume, set_volume, volume_up, volume_down, mute, unmute
)
from tools.display_tools import (
    get_brightness, set_brightness, brightness_up, brightness_down
)
from tools.timer_tools import (
    set_timer, set_alarm, set_reminder,
    cancel_timer, cancel_alarm, cancel_reminder,
    list_timers, list_alarms, list_reminders
)
from tools.network_tools import (
    get_wifi_status, enable_wifi, disable_wifi, toggle_wifi,
    list_wifi_networks, connect_wifi, disconnect_wifi,
    get_bluetooth_status, enable_bluetooth, disable_bluetooth, toggle_bluetooth,
    list_bluetooth_devices, network_status
)

# LLM import (optional - for response polishing)
try:
    from llm.local_llm import polish_response, check_ollama_running
    HAS_LLM = True
except ImportError:
    HAS_LLM = False

CONFIDENCE_THRESHOLD = 0.6
USE_LLM_POLISH = False  # Set to True to use Ollama for natural responses

# Initialize memory
short_term = get_short_term_memory()
long_term = get_long_term_memory()


def handle_input(text: str) -> str:
    """
    Main entry point - process user input and return response.
    
    Flow:
    1. Check for pending clarification
    2. Detect intent
    3. Check if clarification needed
    4. Execute appropriate handler
    5. Update memory
    6. Return response
    """
    text = text.strip()
    
    if not text:
        return "I didn't catch that. Could you repeat?"
    
    # Check for pending clarification
    pending = short_term.get_pending_clarification()
    if pending:
        return _handle_clarification_response(text, pending)
    
    # Detect intent
    intent, confidence, entities = detect_intent(text)
    
    # Check if clarification is needed
    clarify_result = check_clarification(intent, confidence, entities, short_term.get_context())
    
    if clarify_result.needs_clarification:
        # Store pending clarification
        if clarify_result.missing_params:
            short_term.set_pending_clarification(
                intent, entities, clarify_result.missing_params[0]
            )
        return clarify_result.question
    
    # Execute intent
    response = _execute_intent(intent, entities)
    
    # Optional: Polish response with LLM
    if USE_LLM_POLISH and HAS_LLM:
        try:
            if check_ollama_running():
                response = polish_response(response, f"User said: {text}")
        except:
            pass  # Fall back to unpolished response
    
    # Update memory
    short_term.update(intent, entities, response)
    long_term.log_command(intent, entities, True, response)
    
    # Track app usage if applicable
    if intent in ("OPEN_APP", "CLOSE_APP") and "app_name" in entities:
        long_term.track_app_usage(entities["app_name"])
    
    return response


def _handle_clarification_response(text: str, pending: dict) -> str:
    """Handle response to a clarification question."""
    intent = pending["intent"]
    entities = pending["entities"]
    missing_param = pending["missing_param"]
    
    # Clear pending clarification
    short_term.clear_pending_clarification()
    
    # Handle cancellation
    if text.lower() in ("cancel", "nevermind", "forget it", "no"):
        return "Cancelled. What else can I do for you?"
    
    # Update entities with user's response
    updated_entities = handle_clarification_response(text, intent, entities, missing_param)
    
    # Check if confirmed (for yes/no questions)
    if "confirmed" in updated_entities:
        if not updated_entities["confirmed"]:
            return "Cancelled. What else can I do for you?"
        del updated_entities["confirmed"]
    
    # Re-check if we have everything
    clarify_result = check_clarification(intent, 1.0, updated_entities)
    
    if clarify_result.needs_clarification:
        short_term.set_pending_clarification(
            intent, updated_entities, clarify_result.missing_params[0]
        )
        return clarify_result.question
    
    # Execute with complete entities
    response = _execute_intent(intent, updated_entities)
    short_term.update(intent, updated_entities, response)
    long_term.log_command(intent, updated_entities, True, response)
    
    return response


def _execute_intent(intent: str, entities: dict) -> str:
    """Execute the detected intent with extracted entities."""
    
    # === Greetings & Help ===
    if intent == "GREETING":
        return "Hello! I'm your assistant. Say 'help' to see what I can do."
    
    if intent == "HELP":
        return _get_help_text()
    
    if intent == "EXIT":
        return "Goodbye! (Type 'exit' in the terminal to quit)"
    
    # === Time & Date ===
    if intent == "TIME":
        return f"The time is {get_current_time()}"
    
    if intent == "DATE":
        return f"Today is {get_current_date()}"
    
    # === Application Control ===
    if intent == "OPEN_APP":
        app_name = entities.get("app_name")
        app_exec = entities.get("app_executable", app_name)
        success, msg = open_application(app_exec)
        return msg
    
    if intent == "CLOSE_APP":
        app_name = entities.get("app_name")
        success, msg = close_application(app_name)
        return msg
    
    # === Volume Control ===
    if intent == "VOLUME_SET":
        level = entities.get("level", 50)
        success, msg = set_volume(int(level))
        return msg
    
    if intent == "VOLUME_UP":
        success, msg = volume_up()
        return msg
    
    if intent == "VOLUME_DOWN":
        success, msg = volume_down()
        return msg
    
    if intent == "MUTE":
        success, msg = mute()
        return msg
    
    if intent == "UNMUTE":
        success, msg = unmute()
        return msg
    
    # === Brightness Control ===
    if intent == "BRIGHTNESS_SET":
        level = entities.get("level", 50)
        success, msg = set_brightness(int(level))
        return msg
    
    if intent == "BRIGHTNESS_UP":
        success, msg = brightness_up()
        return msg
    
    if intent == "BRIGHTNESS_DOWN":
        success, msg = brightness_down()
        return msg
    
    # === System Controls ===
    if intent == "SCREENSHOT":
        success, msg = take_screenshot()
        return msg
    
    if intent == "LOCK_SCREEN":
        success, msg = lock_screen()
        return msg
    
    if intent == "SHUTDOWN":
        return "⚠️ Are you sure you want to shut down? Say 'yes shutdown' to confirm."
    
    if intent == "RESTART":
        return "⚠️ Are you sure you want to restart? Say 'yes restart' to confirm."
    
    if intent == "SLEEP":
        success, msg = sleep_computer()
        return msg
    
    # === File Operations ===
    if intent == "OPEN_FILE":
        target = entities.get("target")
        if not target:
            return "Which file should I open? Please provide the file path or name."
        
        # First try direct path
        success, msg = open_file(target)
        if success:
            return msg
        
        # If not found, search across all drives
        success, msg = find_and_open_file(target)
        return msg
    
    if intent == "OPEN_FOLDER":
        target = entities.get("target")
        if not target:
            # Ask which folder to open
            return "Which folder should I open? Please provide the folder name."
        
        # First try direct path
        success, msg = open_folder(target)
        if success:
            return msg
        
        # If not found, search across all drives
        success, msg = find_and_open_folder(target)
        return msg
    
    if intent == "SEARCH_FILE":
        query = entities.get("target", "")
        if not query:
            return "What file are you looking for?"
        
        # Search across all drives
        results = search_files(query, max_results=10)
        if results:
            files_list = "\n".join([f"  • {r['name']} ({r['path']})" for r in results[:5]])
            return f"Found {len(results)} file(s):\n{files_list}"
        return f"No files found matching '{query}'"
    
    if intent == "SEARCH_FOLDER":
        query = entities.get("target", "")
        if not query:
            return "What folder are you looking for?"
        
        # Search across all drives
        results = search_folders(query, max_results=10)
        if results:
            folders_list = "\n".join([f"  • {r['name']} ({r['path']})" for r in results[:5]])
            return f"Found {len(results)} folder(s):\n{folders_list}"
        return f"No folders found matching '{query}'"
    
    # === Timer, Alarm, Reminder ===
    if intent == "SET_TIMER":
        duration = entities.get("duration", "")
        if not duration:
            return "How long should I set the timer for? (e.g., '5 minutes')"
        success, msg = set_timer(duration)
        return msg
    
    if intent == "SET_ALARM":
        alarm_time = entities.get("time", "")
        if not alarm_time:
            return "What time should I set the alarm for? (e.g., '7:30 AM')"
        success, msg = set_alarm(alarm_time)
        return msg
    
    if intent == "SET_REMINDER":
        message = entities.get("message", "")
        when = entities.get("when", "in 30 minutes")
        if not message:
            return "What should I remind you about?"
        success, msg = set_reminder(message, when)
        return msg
    
    if intent == "CANCEL_TIMER":
        success, msg = cancel_timer()
        return msg
    
    if intent == "CANCEL_ALARM":
        success, msg = cancel_alarm()
        return msg
    
    if intent == "CANCEL_REMINDER":
        success, msg = cancel_reminder()
        return msg
    
    if intent == "LIST_TIMERS":
        return list_timers()
    
    if intent == "LIST_ALARMS":
        return list_alarms()
    
    if intent == "LIST_REMINDERS":
        return list_reminders()
    
    # === System Info ===
    if intent == "SYSTEM_INFO":
        info = system_info()
        parts = []
        if "cpu_percent" in info:
            parts.append(f"CPU: {info['cpu_percent']}")
        if "ram_percent" in info:
            parts.append(f"RAM: {info['ram_percent']} ({info['ram_used']}/{info['ram_total']})")
        if "battery_percent" in info:
            battery = f"Battery: {info['battery_percent']}"
            if info.get("battery_plugged") == "Yes":
                battery += " (charging)"
            elif "battery_time_left" in info:
                battery += f" ({info['battery_time_left']} remaining)"
            parts.append(battery)
        if "disk_percent" in info:
            parts.append(f"Disk: {info['disk_percent']} used")
        
        if parts:
            return " | ".join(parts)
        return f"System: {info.get('platform', 'Unknown')} {info.get('release', '')}"
    
    # === WiFi Control ===
    if intent == "WIFI_ON":
        success, msg = enable_wifi()
        return msg
    
    if intent == "WIFI_OFF":
        success, msg = disable_wifi()
        return msg
    
    if intent == "WIFI_STATUS":
        status = get_wifi_status()
        if status.get("connected"):
            return f"📶 WiFi is connected to '{status.get('ssid', 'Unknown')}' ({status.get('signal', '?')} signal)"
        elif status.get("enabled"):
            return "📶 WiFi is on but not connected to any network"
        else:
            return "📴 WiFi is disabled"
    
    if intent == "WIFI_LIST":
        success, msg = list_wifi_networks()
        return msg
    
    if intent == "WIFI_CONNECT":
        ssid = entities.get("ssid", "")
        if not ssid:
            return "Which WiFi network should I connect to? Please provide the network name."
        success, msg = connect_wifi(ssid)
        return msg
    
    # === Bluetooth Control ===
    if intent == "BLUETOOTH_ON":
        success, msg = enable_bluetooth()
        return msg
    
    if intent == "BLUETOOTH_OFF":
        success, msg = disable_bluetooth()
        return msg
    
    if intent == "BLUETOOTH_STATUS":
        status = get_bluetooth_status()
        if status.get("enabled"):
            return "🔵 Bluetooth is enabled"
        elif status.get("available"):
            return "⚫ Bluetooth is disabled"
        else:
            return "⚪ Bluetooth is not available on this device"
    
    if intent == "BLUETOOTH_DEVICES":
        success, msg = list_bluetooth_devices()
        return msg
    
    # === Network Status ===
    if intent == "NETWORK_STATUS":
        return network_status()
    
    # === Calculator ===
    if intent == "CALCULATE":
        expression = entities.get("expression", "")
        if not expression:
            return "What should I calculate?"
        success, result = calculate(expression)
        if success:
            return f"= {result}"
        return result
    
    # === Unknown ===
    return "I'm not sure how to help with that. Say 'help' to see what I can do."


def _get_help_text() -> str:
    """Return comprehensive help text with all available commands."""
    return """╔══════════════════════════════════════════════════════════════╗
║                    QWIKK COMMAND GUIDE                       ║
╚══════════════════════════════════════════════════════════════╝

📱 APPLICATION CONTROL
  • "open chrome"           - Open Google Chrome
  • "open spotify"          - Open Spotify (works with Store apps!)
  • "open notion"           - Open Notion
  • "open whatsapp"         - Open WhatsApp
  • "open vscode"           - Open Visual Studio Code
  • "open calculator"       - Open Calculator
  • "open settings"         - Open Windows Settings
  • "close notepad"         - Close Notepad
  
🔊 VOLUME CONTROL
  • "volume up"             - Increase volume by 10%
  • "volume down"           - Decrease volume by 10%
  • "set volume to 50"      - Set volume to 50%
  • "mute"                  - Mute audio
  • "unmute"                - Unmute audio

☀️ BRIGHTNESS CONTROL
  • "brightness up"         - Increase brightness by 10%
  • "brightness down"       - Decrease brightness by 10%
  • "set brightness to 70"  - Set brightness to 70%

📶 WIFI CONTROL
  • "wifi on"               - Enable WiFi
  • "wifi off"              - Disable WiFi
  • "wifi status"           - Check WiFi connection status
  • "list wifi"             - Show available WiFi networks
  • "scan wifi"             - Same as above

🔵 BLUETOOTH CONTROL
  • "bluetooth on"          - Enable Bluetooth
  • "bluetooth off"         - Disable Bluetooth
  • "bluetooth status"      - Check if Bluetooth is enabled
  • "bluetooth devices"     - List paired Bluetooth devices

📡 NETWORK STATUS
  • "network status"        - Show WiFi and Bluetooth status

📸 SCREENSHOTS
  • "take a screenshot"     - Capture and save screenshot
  • "screenshot"            - Same as above

🔒 POWER & SECURITY
  • "lock screen"           - Lock the computer
  • "shutdown"              - Shutdown computer (will ask confirmation)
  • "restart"               - Restart computer (will ask confirmation)
  • "sleep"                 - Put computer to sleep

📁 FILE OPERATIONS (searches ENTIRE PC!)
  • "open file report.pdf"  - Find and open a file
  • "find file budget"      - Search for files containing 'budget'
  • "search file invoice"   - Same as find file
  • "open folder projects"  - Find and open a folder
  • "find folder work"      - Search for folders containing 'work'
  • "open documents"        - Open Documents folder
  • "open downloads"        - Open Downloads folder

💻 SYSTEM INFORMATION
  • "system info"           - Show CPU, RAM, battery, disk usage
  • "battery status"        - Show battery percentage
  • "what's my battery"     - Same as above

⏱️ TIMER, ALARM, REMINDER
  • "set timer for 5 minutes"  - Start a countdown timer
  • "timer 30 seconds"         - Quick timer
  • "cancel timer"             - Cancel active timer
  • "set alarm for 7:30 AM"    - Set an alarm
  • "wake me at 8am"           - Same as above
  • "cancel alarm"             - Cancel alarm
  • "remind me to call mom in 1 hour"  - Set a reminder
  • "remind me to check email at 3pm"  - Reminder at specific time
  • "show timers"              - List active timers
  • "show alarms"              - List active alarms
  • "show reminders"           - List active reminders

🧮 CALCULATOR
  • "calculate 25 * 4"      - Perform calculation
  • "what is 100 / 5"       - Same as above
  • "15 + 27"               - Direct calculation

⏰ TIME & DATE
  • "what time is it"       - Show current time
  • "what's the date"       - Show current date
  • "time"                  - Same as above

💬 GENERAL
  • "help"                  - Show this help message
  • "hello"                 - Greet the assistant
  • "exit"                  - Exit the assistant

Tip: Speak naturally! Qwikk understands variations like "launch chrome", 
"open up browser", "turn up the volume", "enable wifi", etc."""


def get_all_intents_info() -> dict:
    """Return detailed info about all supported intents for API use."""
    return {
        "app_control": {
            "intents": ["OPEN_APP", "CLOSE_APP"],
            "examples": ["open chrome", "close notepad", "launch spotify", "open whatsapp"],
            "supported_apps": [
                "chrome", "firefox", "edge", "notepad", "calculator", "vscode",
                "spotify", "discord", "slack", "teams", "notion", "whatsapp",
                "telegram", "word", "excel", "powerpoint", "outlook", "paint",
                "settings", "task manager", "file explorer", "terminal"
            ]
        },
        "volume": {
            "intents": ["VOLUME_SET", "VOLUME_UP", "VOLUME_DOWN", "MUTE", "UNMUTE"],
            "examples": ["volume up", "set volume to 50", "mute", "unmute"]
        },
        "brightness": {
            "intents": ["BRIGHTNESS_SET", "BRIGHTNESS_UP", "BRIGHTNESS_DOWN"],
            "examples": ["brightness up", "set brightness to 70%", "dim screen"]
        },
        "wifi": {
            "intents": ["WIFI_ON", "WIFI_OFF", "WIFI_STATUS", "WIFI_LIST", "WIFI_CONNECT"],
            "examples": ["wifi on", "turn off wifi", "wifi status", "list wifi networks", "scan wifi"]
        },
        "bluetooth": {
            "intents": ["BLUETOOTH_ON", "BLUETOOTH_OFF", "BLUETOOTH_STATUS", "BLUETOOTH_DEVICES"],
            "examples": ["bluetooth on", "turn off bluetooth", "bluetooth status", "show bluetooth devices"]
        },
        "network": {
            "intents": ["NETWORK_STATUS"],
            "examples": ["network status", "am i online", "connection status"]
        },
        "screenshot": {
            "intents": ["SCREENSHOT"],
            "examples": ["take screenshot", "capture screen", "screenshot"]
        },
        "power": {
            "intents": ["LOCK_SCREEN", "SHUTDOWN", "RESTART", "SLEEP"],
            "examples": ["lock screen", "shutdown", "restart", "sleep"]
        },
        "files": {
            "intents": ["OPEN_FILE", "SEARCH_FILE", "OPEN_FOLDER", "SEARCH_FOLDER"],
            "examples": ["open file report.pdf", "find file budget", "open folder projects", "find folder work"]
        },
        "timers": {
            "intents": ["SET_TIMER", "CANCEL_TIMER", "LIST_TIMERS"],
            "examples": ["set timer for 5 minutes", "cancel timer", "show timers"]
        },
        "alarms": {
            "intents": ["SET_ALARM", "CANCEL_ALARM", "LIST_ALARMS"],
            "examples": ["set alarm for 7:30 AM", "wake me at 8am", "cancel alarm", "show alarms"]
        },
        "reminders": {
            "intents": ["SET_REMINDER", "CANCEL_REMINDER", "LIST_REMINDERS"],
            "examples": ["remind me to call mom in 1 hour", "remind me at 3pm to check email", "show reminders"]
        },
        "system": {
            "intents": ["SYSTEM_INFO"],
            "examples": ["system info", "battery status", "how much RAM"]
        },
        "math": {
            "intents": ["CALCULATE"],
            "examples": ["calculate 25 * 4", "what is 100 / 5", "15 + 27"]
        },
        "time": {
            "intents": ["TIME", "DATE"],
            "examples": ["what time is it", "what's the date", "time"]
        }
    }


# Legacy compatibility
def extract_expression(text):
    """Legacy expression extraction."""
    for char in text:
        if char.isdigit():
            return text
    return None
