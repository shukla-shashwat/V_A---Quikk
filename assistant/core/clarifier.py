# core/clarifier.py
"""
Clarification engine - asks follow-up questions when intent/parameters are unclear.
No LLM dependency - pure rule-based logic.
"""

from typing import Dict, Optional, List

# Required parameters for each intent
INTENT_REQUIREMENTS: Dict[str, Dict] = {
    "OPEN_APP": {
        "required": ["app_name"],
        "prompts": {
            "app_name": "Which application should I open? (e.g., Chrome, Notepad, VS Code)"
        }
    },
    "CLOSE_APP": {
        "required": ["app_name"],
        "prompts": {
            "app_name": "Which application should I close?"
        }
    },
    "VOLUME_SET": {
        "required": ["level"],
        "prompts": {
            "level": "What volume level? (0-100)"
        }
    },
    "BRIGHTNESS_SET": {
        "required": ["level"],
        "prompts": {
            "level": "What brightness level? (0-100)"
        }
    },
    "OPEN_FILE": {
        "required": ["target"],
        "prompts": {
            "target": "Which file or folder should I open? (provide path or name)"
        }
    },
    "SEARCH_FILE": {
        "required": ["target"],
        "prompts": {
            "target": "What file are you looking for? (e.g., report.pdf, notes.txt)"
        }
    },
    "CALCULATE": {
        "required": ["expression"],
        "prompts": {
            "expression": "What should I calculate? (e.g., 25 * 4)"
        }
    }
}

# Confidence thresholds
LOW_CONFIDENCE_THRESHOLD = 0.4
MEDIUM_CONFIDENCE_THRESHOLD = 0.6


class ClarificationResult:
    """Result of clarification check."""
    def __init__(self, needs_clarification: bool, question: str = None, 
                 missing_params: List[str] = None, reason: str = None):
        self.needs_clarification = needs_clarification
        self.question = question
        self.missing_params = missing_params or []
        self.reason = reason


def check_clarification(intent: str, confidence: float, entities: Dict, 
                        context: Dict = None) -> ClarificationResult:
    """
    Check if clarification is needed based on intent, confidence, and entities.
    
    Args:
        intent: Detected intent name
        confidence: Confidence score (0-1)
        entities: Extracted entities
        context: Optional conversation context for follow-up handling
    
    Returns:
        ClarificationResult indicating if clarification is needed
    """
    # Handle unknown intent
    if intent == "UNKNOWN" or confidence < LOW_CONFIDENCE_THRESHOLD:
        return ClarificationResult(
            needs_clarification=True,
            question="I didn't understand that. Could you rephrase? Say 'help' to see what I can do.",
            reason="unknown_intent"
        )
    
    # Check for missing required parameters
    if intent in INTENT_REQUIREMENTS:
        requirements = INTENT_REQUIREMENTS[intent]
        missing = []
        
        for param in requirements["required"]:
            if param not in entities or entities[param] is None:
                missing.append(param)
        
        if missing:
            # Ask for the first missing parameter
            param = missing[0]
            question = requirements["prompts"].get(param, f"Please provide: {param}")
            return ClarificationResult(
                needs_clarification=True,
                question=question,
                missing_params=missing,
                reason="missing_parameter"
            )
    
    # Low confidence but has parameters - ask for confirmation
    if confidence < MEDIUM_CONFIDENCE_THRESHOLD:
        confirmation = _build_confirmation_question(intent, entities)
        return ClarificationResult(
            needs_clarification=True,
            question=confirmation,
            reason="low_confidence"
        )
    
    # No clarification needed
    return ClarificationResult(needs_clarification=False)


def _build_confirmation_question(intent: str, entities: Dict) -> str:
    """Build a confirmation question for low-confidence intents."""
    intent_descriptions = {
        "OPEN_APP": f"open {entities.get('app_name', 'an application')}",
        "CLOSE_APP": f"close {entities.get('app_name', 'an application')}",
        "VOLUME_SET": f"set volume to {entities.get('level', 'a level')}",
        "VOLUME_UP": "increase the volume",
        "VOLUME_DOWN": "decrease the volume",
        "MUTE": "mute the audio",
        "UNMUTE": "unmute the audio",
        "BRIGHTNESS_SET": f"set brightness to {entities.get('level', 'a level')}",
        "BRIGHTNESS_UP": "increase brightness",
        "BRIGHTNESS_DOWN": "decrease brightness",
        "SCREENSHOT": "take a screenshot",
        "LOCK_SCREEN": "lock the screen",
        "SHUTDOWN": "shut down the computer",
        "RESTART": "restart the computer",
        "SLEEP": "put the computer to sleep",
        "SYSTEM_INFO": "show system information",
        "CALCULATE": f"calculate {entities.get('expression', 'something')}",
    }
    
    action = intent_descriptions.get(intent, intent.lower().replace("_", " "))
    return f"Did you want me to {action}? (yes/no)"


def handle_clarification_response(response: str, pending_intent: str, 
                                  pending_entities: Dict, missing_param: str) -> Dict:
    """
    Handle user's response to a clarification question.
    
    Args:
        response: User's response text
        pending_intent: The intent waiting for clarification
        pending_entities: Entities collected so far
        missing_param: The parameter we asked for
    
    Returns:
        Updated entities dict
    """
    response = response.strip()
    
    # Handle yes/no confirmations
    if response.lower() in ("yes", "y", "yeah", "yep", "sure", "ok", "okay"):
        return {"confirmed": True, **pending_entities}
    if response.lower() in ("no", "n", "nope", "cancel", "nevermind"):
        return {"confirmed": False}
    
    # Handle parameter values
    updated_entities = pending_entities.copy()
    
    if missing_param == "app_name":
        updated_entities["app_name"] = response
    elif missing_param == "level":
        # Extract number from response
        import re
        numbers = re.findall(r'\d+', response)
        if numbers:
            updated_entities["level"] = int(numbers[0])
        else:
            updated_entities["level"] = response
    elif missing_param == "target":
        updated_entities["target"] = response
    elif missing_param == "expression":
        updated_entities["expression"] = response
    else:
        updated_entities[missing_param] = response
    
    return updated_entities


# Legacy function for backward compatibility
def clarify(intent: str) -> str:
    """Simple clarification - returns a question for the given intent."""
    result = check_clarification(intent, 0.5, {})
    return result.question or "Can you clarify what you want?"
