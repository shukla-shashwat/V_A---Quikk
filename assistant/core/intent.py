# core/intent.py
"""
Intent detection using keyword matching and regex scoring.
No ML/LLM - pure rule-based for reliability.
"""

import re
from typing import Tuple, Dict, List

# Intent definitions with keywords and patterns
INTENT_PATTERNS: Dict[str, Dict] = {
    "OPEN_FILE": {
        "keywords": ["open file", "open the file", "open document", "open the document"],
        "patterns": [r"open\s+(the\s+)?file\s+(.+)", r"open\s+(the\s+)?document\s+(.+)", r"open\s+[\"']([^\"']+)[\"']", r"open\s+([a-zA-Z]:\\[^\s]+)"],
        "weight": 0.9,  # Higher priority than OPEN_APP when "file" mentioned
        "priority": 1
    },
    "OPEN_FOLDER": {
        "keywords": ["open folder", "open the folder", "open directory", "open dir", "go to folder"],
        "patterns": [
            r"open\s+(?:the\s+)?folder\s+(.+)",
            r"open\s+(?:the\s+)?directory\s+(.+)",
            r"go\s+to\s+(?:the\s+)?folder\s+(.+)",
            r"folder\s+(.+)"
        ],
        "weight": 0.9,
        "priority": 1
    },
    "SEARCH_FILE": {
        "keywords": ["find file", "search file", "locate file", "where is file", "look for file"],
        "patterns": [
            r"(?:find|search|locate|look\s+for)\s+(?:the\s+)?file\s+(.+)",
            r"where\s+is\s+(?:the\s+)?file\s+(.+)"
        ],
        "weight": 0.85,
        "priority": 1
    },
    "SEARCH_FOLDER": {
        "keywords": ["find folder", "search folder", "locate folder", "where is folder", "look for folder"],
        "patterns": [
            r"(?:find|search|locate|look\s+for)\s+(?:the\s+)?folder\s+(.+)",
            r"where\s+is\s+(?:the\s+)?folder\s+(.+)"
        ],
        "weight": 0.85,
        "priority": 1
    },
    "OPEN_APP": {
        "keywords": ["open", "launch", "start", "run"],
        "negative": ["file", "folder", "document", "directory", "the file", "the folder"],
        "patterns": [r"open\s+(\w+)", r"launch\s+(\w+)", r"start\s+(\w+)"],
        "weight": 0.7,
        "priority": 2  # Lower priority than OPEN_FILE/OPEN_FOLDER
    },
    "CLOSE_APP": {
        "keywords": ["close", "quit", "exit", "kill", "terminate", "end"],
        "patterns": [r"close\s+(\w+)", r"quit\s+(\w+)", r"kill\s+(\w+)"],
        "weight": 0.7
    },
    "VOLUME_UP": {
        "keywords": ["volume up", "louder", "increase volume", "turn up", "raise volume"],
        "patterns": [r"volume\s*up", r"increase\s*(the\s*)?volume", r"turn\s*(it\s*)?up"],
        "weight": 0.8
    },
    "VOLUME_DOWN": {
        "keywords": ["volume down", "quieter", "decrease volume", "turn down", "lower volume"],
        "patterns": [r"volume\s*down", r"decrease\s*(the\s*)?volume", r"turn\s*(it\s*)?down", r"lower"],
        "weight": 0.8
    },
    "VOLUME_SET": {
        "keywords": ["set volume", "volume to", "volume at"],
        "patterns": [r"(?:set\s+)?volume\s+(?:to\s+)?(\d+)", r"(\d+)\s*%?\s*volume"],
        "weight": 0.85
    },
    "MUTE": {
        "keywords": ["mute", "silence", "quiet"],
        "patterns": [r"\bmute\b", r"silence"],
        "weight": 0.9
    },
    "UNMUTE": {
        "keywords": ["unmute", "sound on"],
        "patterns": [r"unmute", r"sound\s+on"],
        "weight": 0.9
    },
    "BRIGHTNESS_UP": {
        "keywords": ["brightness up", "brighter", "increase brightness"],
        "patterns": [r"brightness\s*up", r"brighter", r"increase\s*brightness"],
        "weight": 0.8
    },
    "BRIGHTNESS_DOWN": {
        "keywords": ["brightness down", "dimmer", "decrease brightness", "dim"],
        "patterns": [r"brightness\s*down", r"dim", r"decrease\s*brightness"],
        "weight": 0.8
    },
    "BRIGHTNESS_SET": {
        "keywords": ["set brightness", "brightness to"],
        "patterns": [r"(?:set\s+)?brightness\s+(?:to\s+)?(\d+)"],
        "weight": 0.85
    },
    "SCREENSHOT": {
        "keywords": ["screenshot", "screen capture", "capture screen", "take a screenshot", "print screen"],
        "patterns": [r"screenshot", r"screen\s*capture", r"capture\s*(the\s*)?screen"],
        "weight": 0.9
    },
    # Timer, Alarm, Reminder
    "SET_TIMER": {
        "keywords": ["set timer", "timer for", "start timer", "countdown"],
        "patterns": [
            r"(?:set\s+)?(?:a\s+)?timer\s+(?:for\s+)?(.+)",
            r"countdown\s+(?:for\s+)?(.+)",
            r"(\d+)\s*(?:min|minute|hour|second)s?\s+timer"
        ],
        "weight": 0.9
    },
    "SET_ALARM": {
        "keywords": ["set alarm", "alarm for", "wake me", "alarm at"],
        "patterns": [
            r"(?:set\s+)?(?:an?\s+)?alarm\s+(?:for\s+|at\s+)?(.+)",
            r"wake\s+me\s+(?:up\s+)?(?:at\s+)?(.+)"
        ],
        "weight": 0.9
    },
    "SET_REMINDER": {
        "keywords": ["remind me", "set reminder", "reminder to", "don't let me forget"],
        "patterns": [
            r"remind\s+me\s+(?:to\s+)?(.+)",
            r"(?:set\s+)?(?:a\s+)?reminder\s+(?:to\s+)?(.+)"
        ],
        "weight": 0.9
    },
    "CANCEL_TIMER": {
        "keywords": ["cancel timer", "stop timer", "delete timer"],
        "patterns": [r"(?:cancel|stop|delete|remove)\s+(?:the\s+)?timer"],
        "weight": 0.85
    },
    "CANCEL_ALARM": {
        "keywords": ["cancel alarm", "stop alarm", "delete alarm", "turn off alarm"],
        "patterns": [r"(?:cancel|stop|delete|remove|turn\s+off)\s+(?:the\s+)?alarm"],
        "weight": 0.85
    },
    "CANCEL_REMINDER": {
        "keywords": ["cancel reminder", "delete reminder", "remove reminder"],
        "patterns": [r"(?:cancel|delete|remove)\s+(?:the\s+)?reminder"],
        "weight": 0.85
    },
    "LIST_TIMERS": {
        "keywords": ["show timers", "list timers", "my timers", "active timers"],
        "patterns": [r"(?:show|list|what\s+are)\s+(?:my\s+)?(?:active\s+)?timers"],
        "weight": 0.8
    },
    "LIST_ALARMS": {
        "keywords": ["show alarms", "list alarms", "my alarms", "active alarms"],
        "patterns": [r"(?:show|list|what\s+are)\s+(?:my\s+)?(?:active\s+)?alarms"],
        "weight": 0.8
    },
    "LIST_REMINDERS": {
        "keywords": ["show reminders", "list reminders", "my reminders"],
        "patterns": [r"(?:show|list|what\s+are)\s+(?:my\s+)?reminders"],
        "weight": 0.8
    },
    "LOCK_SCREEN": {
        "keywords": ["lock", "lock screen", "lock computer", "lock pc"],
        "patterns": [r"lock\s*(the\s*)?(screen|computer|pc|laptop)?"],
        "weight": 0.8
    },
    "SHUTDOWN": {
        "keywords": ["shutdown", "shut down", "power off", "turn off computer"],
        "patterns": [r"shut\s*down", r"power\s+off", r"turn\s+off\s+(the\s+)?(computer|pc|laptop)"],
        "weight": 0.9
    },
    "RESTART": {
        "keywords": ["restart", "reboot"],
        "patterns": [r"restart", r"reboot"],
        "weight": 0.9
    },
    "SLEEP": {
        "keywords": ["sleep", "hibernate", "sleep mode"],
        "patterns": [r"\bsleep\b", r"hibernate"],
        "weight": 0.85
    },
    "OPEN_FILE": {
        "keywords": ["open file", "open document", "open folder"],
        "patterns": [r"open\s+(file|document|folder)\s+(.+)", r"open\s+[\"']?([^\"']+)[\"']?"],
        "weight": 0.7
    },
    "SEARCH_FILE": {
        "keywords": ["find file", "search file", "locate", "where is"],
        "patterns": [r"(?:find|search|locate)\s+(?:file\s+)?(.+)", r"where\s+is\s+(.+)"],
        "weight": 0.75
    },
    "SYSTEM_INFO": {
        "keywords": ["system info", "cpu", "ram", "memory", "disk", "storage", "battery", "status"],
        "patterns": [r"system\s*info", r"how\s+much\s+(ram|memory|storage|disk)", r"cpu\s*(usage)?", r"battery"],
        "weight": 0.8
    },
    "TIME": {
        "keywords": ["time", "what time", "current time"],
        "patterns": [r"what\s*(is\s*)?(the\s*)?time", r"current\s+time", r"tell\s+me\s+the\s+time"],
        "weight": 0.9
    },
    "DATE": {
        "keywords": ["date", "what date", "today", "what day"],
        "patterns": [r"what\s*(is\s*)?(the\s*)?date", r"today", r"what\s+day"],
        "weight": 0.9
    },
    "CALCULATE": {
        "keywords": ["calculate", "compute", "what is", "how much is", "add", "subtract", "multiply", "divide"],
        "patterns": [r"calculate\s+(.+)", r"what\s+is\s+(\d+.+\d+)", r"(\d+\s*[\+\-\*\/\^]\s*\d+)"],
        "weight": 0.75
    },
    "GREETING": {
        "keywords": ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"],
        "patterns": [r"^(hi|hello|hey)\b", r"good\s+(morning|afternoon|evening)"],
        "weight": 0.9
    },
    "HELP": {
        "keywords": ["help", "what can you do", "commands", "how to use"],
        "patterns": [r"\bhelp\b", r"what\s+can\s+you\s+do", r"available\s+commands"],
        "weight": 0.85
    },
    "EXIT": {
        "keywords": ["exit", "quit", "bye", "goodbye", "stop"],
        "patterns": [r"^(exit|quit|bye|goodbye|stop)$"],
        "weight": 0.9
    },
    # WiFi Controls
    "WIFI_ON": {
        "keywords": ["wifi on", "turn on wifi", "enable wifi", "connect wifi", "wifi enable"],
        "patterns": [r"(?:turn\s+)?(?:on\s+)?wifi\s*(?:on)?", r"enable\s+wifi", r"connect\s+wifi"],
        "weight": 0.9
    },
    "WIFI_OFF": {
        "keywords": ["wifi off", "turn off wifi", "disable wifi", "disconnect wifi"],
        "patterns": [r"(?:turn\s+)?(?:off\s+)?wifi\s*(?:off)?", r"disable\s+wifi", r"disconnect\s+wifi"],
        "weight": 0.9
    },
    "WIFI_STATUS": {
        "keywords": ["wifi status", "wifi info", "am i connected", "wifi connected", "check wifi"],
        "patterns": [r"wifi\s+status", r"(?:am\s+i|is\s+wifi)\s+connected", r"check\s+wifi"],
        "weight": 0.85
    },
    "WIFI_LIST": {
        "keywords": ["list wifi", "show wifi", "available wifi", "wifi networks", "scan wifi"],
        "patterns": [r"(?:list|show|scan)\s+wifi", r"(?:available|nearby)\s+wifi", r"wifi\s+networks"],
        "weight": 0.85
    },
    "WIFI_CONNECT": {
        "keywords": ["connect to wifi", "join wifi", "connect to network"],
        "patterns": [r"connect\s+(?:to\s+)?(?:wifi\s+)?(.+)", r"join\s+(?:wifi\s+)?(.+)"],
        "weight": 0.8
    },
    # Bluetooth Controls
    "BLUETOOTH_ON": {
        "keywords": ["bluetooth on", "turn on bluetooth", "enable bluetooth"],
        "patterns": [r"(?:turn\s+)?(?:on\s+)?bluetooth\s*(?:on)?", r"enable\s+bluetooth"],
        "weight": 0.9
    },
    "BLUETOOTH_OFF": {
        "keywords": ["bluetooth off", "turn off bluetooth", "disable bluetooth"],
        "patterns": [r"(?:turn\s+)?(?:off\s+)?bluetooth\s*(?:off)?", r"disable\s+bluetooth"],
        "weight": 0.9
    },
    "BLUETOOTH_STATUS": {
        "keywords": ["bluetooth status", "bluetooth info", "check bluetooth", "is bluetooth on"],
        "patterns": [r"bluetooth\s+status", r"(?:is\s+)?bluetooth\s+(?:on|enabled)", r"check\s+bluetooth"],
        "weight": 0.85
    },
    "BLUETOOTH_DEVICES": {
        "keywords": ["bluetooth devices", "show bluetooth", "list bluetooth", "paired devices"],
        "patterns": [r"(?:show|list)\s+bluetooth", r"bluetooth\s+devices", r"paired\s+devices"],
        "weight": 0.85
    },
    "NETWORK_STATUS": {
        "keywords": ["network status", "connection status", "internet status", "am i online"],
        "patterns": [r"network\s+status", r"connection\s+status", r"(?:am\s+i|are\s+we)\s+online", r"internet\s+status"],
        "weight": 0.85
    }
}

# Common app name aliases
APP_ALIASES: Dict[str, str] = {
    "chrome": "chrome",
    "google": "chrome",
    "browser": "chrome",
    "firefox": "firefox",
    "edge": "msedge",
    "notepad": "notepad",
    "calculator": "calc",
    "calc": "calc",
    "explorer": "explorer",
    "files": "explorer",
    "file explorer": "explorer",
    "cmd": "cmd",
    "command prompt": "cmd",
    "terminal": "wt",  # Windows Terminal
    "powershell": "powershell",
    "vscode": "code",
    "vs code": "code",
    "visual studio code": "code",
    "code": "code",
    "spotify": "spotify:",  # UWP app
    "discord": "discord",
    "slack": "slack",
    "teams": "msteams:",  # UWP app
    "microsoft teams": "msteams:",
    "word": "winword",
    "excel": "excel",
    "powerpoint": "powerpnt",
    "outlook": "outlook",
    "paint": "mspaint",
    "settings": "ms-settings:",
    "control panel": "control",
    "task manager": "taskmgr",
    # UWP / Microsoft Store Apps
    "notion": "notion:",
    "whatsapp": "whatsapp:",
    "telegram": "telegram:",
    "netflix": "netflix:",
    "twitter": "twitter:",
    "instagram": "instagram:",
    "facebook": "facebook:",
    "messenger": "messenger:",
    "zoom": "zoom",
    "vlc": "vlc",
    "obs": "obs64",
    "photoshop": "photoshop",
    "illustrator": "illustrator",
    "premiere": "premiere",
    "blender": "blender",
    "unity": "unity",
    "steam": "steam:",
    "epic games": "com.epicgames.launcher:",
    "github desktop": "github-windows:",
    "postman": "postman",
    "figma": "figma",
    "canva": "canva:",
}

# UWP App IDs (for Microsoft Store apps)
UWP_APPS: Dict[str, str] = {
    "notion": "Notion.Notion_ddwkm3w1by0mj!Notion",
    "whatsapp": "5319275A.WhatsAppDesktop_cv1g1gnamjy7m!App",
    "spotify": "SpotifyAB.SpotifyMusic_zpdnekdrzrea0!Spotify",
    "telegram": "TelegramMessengerLLP.TelegramDesktop_t4vj0pshhgkwm!Telegram",
    "netflix": "4DF9E0F8.Netflix_mcm4njqhnhss8!Netflix.App",
    "twitter": "9E2F88E3.Twitter_wgeqdkkx372wm!Twitter",
    "instagram": "Facebook.InstagramBeta_8xx8rvfyw5nnt!Instagram",
    "messenger": "FACEBOOK.317180B0BB486_8xx8rvfyw5nnt!App",
}


def detect_intent(text: str) -> Tuple[str, float, Dict]:
    """
    Detect intent from user text using keyword matching and regex patterns.
    
    Returns:
        Tuple of (intent_name, confidence_score, extracted_entities)
    """
    text_lower = text.lower().strip()
    scores: Dict[str, float] = {intent: 0.0 for intent in INTENT_PATTERNS}
    entities: Dict[str, any] = {}
    
    for intent, config in INTENT_PATTERNS.items():
        score = 0.0
        
        # Check keywords
        for keyword in config["keywords"]:
            if keyword in text_lower:
                score += config["weight"]
                break
        
        # Check negative keywords (reduce score)
        if "negative" in config:
            for neg in config["negative"]:
                if neg in text_lower:
                    score -= 0.3
        
        # Check regex patterns
        for pattern in config["patterns"]:
            match = re.search(pattern, text_lower)
            if match:
                score += 0.2  # Bonus for pattern match
                # Extract groups as entities
                if match.groups():
                    entities[intent] = match.groups()
                break
        
        scores[intent] = min(score, 1.0)  # Cap at 1.0
    
    # Get best intent
    best_intent = max(scores, key=scores.get)
    confidence = scores[best_intent]
    
    # Extract entities for the winning intent
    final_entities = _extract_entities(best_intent, text_lower, entities.get(best_intent))
    
    # If no clear intent, mark as UNKNOWN
    if confidence < 0.3:
        return "UNKNOWN", confidence, {}
    
    return best_intent, confidence, final_entities


def _extract_entities(intent: str, text: str, regex_groups: tuple = None) -> Dict:
    """Extract relevant entities based on intent type."""
    entities = {}
    
    if intent in ("OPEN_APP", "CLOSE_APP"):
        # Extract app name
        app_name = _extract_app_name(text)
        if app_name:
            entities["app_name"] = app_name
            entities["app_executable"] = APP_ALIASES.get(app_name.lower(), app_name)
    
    elif intent in ("VOLUME_SET", "BRIGHTNESS_SET"):
        # Extract number
        numbers = re.findall(r'\d+', text)
        if numbers:
            entities["level"] = int(numbers[0])
    
    elif intent in ("OPEN_FILE", "SEARCH_FILE", "OPEN_FOLDER", "SEARCH_FOLDER"):
        # Extract file/folder path or name
        target = _extract_file_target(text, regex_groups)
        if target:
            entities["target"] = target
    
    elif intent == "CALCULATE":
        # Extract mathematical expression
        expr = _extract_math_expression(text)
        if expr:
            entities["expression"] = expr
    
    elif intent == "SET_TIMER":
        # Extract duration
        duration = _extract_timer_duration(text)
        if duration:
            entities["duration"] = duration
    
    elif intent == "SET_ALARM":
        # Extract time
        alarm_time = _extract_alarm_time(text)
        if alarm_time:
            entities["time"] = alarm_time
    
    elif intent == "SET_REMINDER":
        # Extract message and time
        message, when = _extract_reminder_info(text)
        if message:
            entities["message"] = message
        if when:
            entities["when"] = when
    
    return entities


def _extract_timer_duration(text: str) -> str:
    """Extract timer duration from text."""
    # Remove command words
    for word in ["set", "timer", "for", "a", "the", "start", "countdown"]:
        text = re.sub(rf'\b{word}\b', '', text, flags=re.IGNORECASE)
    
    return text.strip()


def _extract_alarm_time(text: str) -> str:
    """Extract alarm time from text."""
    # Look for time patterns
    time_match = re.search(r'(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)', text, re.IGNORECASE)
    if time_match:
        return time_match.group(1)
    
    # Remove command words and return remaining
    for word in ["set", "alarm", "for", "at", "an", "a", "the", "wake", "me", "up"]:
        text = re.sub(rf'\b{word}\b', '', text, flags=re.IGNORECASE)
    
    return text.strip()


def _extract_reminder_info(text: str) -> tuple:
    """Extract reminder message and time from text."""
    # Pattern: "remind me to X in/at Y"
    match = re.search(r'remind\s+me\s+(?:to\s+)?(.+?)\s+(in\s+\d+|at\s+\d+|tomorrow|tonight)', text, re.IGNORECASE)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    
    # Pattern: "remind me in X to Y"
    match = re.search(r'remind\s+me\s+(in\s+\d+\s*\w+|at\s+\d+\s*\w*)\s+(?:to\s+)?(.+)', text, re.IGNORECASE)
    if match:
        return match.group(2).strip(), match.group(1).strip()
    
    # Just extract everything after "remind me"
    match = re.search(r'remind\s+me\s+(?:to\s+)?(.+)', text, re.IGNORECASE)
    if match:
        return match.group(1).strip(), "in 30 minutes"
    
    return None, None


def _extract_file_target(text: str, regex_groups: tuple = None) -> str:
    """Extract file/folder path or name from text."""
    # Look for quoted strings first (highest priority)
    quoted = re.search(r'["\']([^"\']+)["\']', text)
    if quoted:
        return quoted.group(1)
    
    # Look for Windows path pattern (C:\path\to\file)
    path_match = re.search(r'([a-zA-Z]:\\[^\s]+)', text)
    if path_match:
        return path_match.group(1)
    
    # Look for Unix-style path (/path/to/file or ~/path)
    unix_path = re.search(r'([~/][^\s]+)', text)
    if unix_path:
        return unix_path.group(1)
    
    # Use regex groups if available
    if regex_groups:
        # Filter out common words and get the actual target
        for group in reversed(regex_groups):
            if group and group.strip() not in ('the', 'file', 'folder', 'document', 'directory', 'a', 'an', ''):
                return group.strip()
    
    # Extract remaining text after removing command words
    cleaned = text
    for word in ["open", "find", "search", "locate", "the", "file", "folder", "directory", 
                 "document", "for", "named", "called", "a", "an", "please", "can you"]:
        cleaned = re.sub(rf'\b{word}\b', '', cleaned, flags=re.IGNORECASE)
    
    cleaned = cleaned.strip()
    if cleaned:
        return cleaned
    
    return None


def _extract_app_name(text: str) -> str:
    """Extract application name from text."""
    # Remove common command words
    for word in ["open", "close", "launch", "start", "quit", "exit", "kill", "run", "please", "the", "app", "application"]:
        text = re.sub(rf'\b{word}\b', '', text, flags=re.IGNORECASE)
    
    text = text.strip()
    
    # Check against known aliases
    for alias in APP_ALIASES:
        if alias in text.lower():
            return alias
    
    # Return remaining text as app name
    words = text.split()
    if words:
        return words[0]
    return None


def _extract_math_expression(text: str) -> str:
    """Extract mathematical expression from text."""
    # Look for explicit expression patterns
    patterns = [
        r'calculate\s+(.+)',
        r'what\s+is\s+(.+)',
        r'compute\s+(.+)',
        r'(\d+[\s\d\+\-\*\/\^\(\)\.]+\d+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            expr = match.group(1).strip()
            # Clean up the expression
            expr = re.sub(r'[^\d\+\-\*\/\^\(\)\.\s]', '', expr)
            expr = expr.strip()
            if expr:
                return expr
    
    return None


def get_all_intents() -> List[str]:
    """Return list of all supported intents."""
    return list(INTENT_PATTERNS.keys())
