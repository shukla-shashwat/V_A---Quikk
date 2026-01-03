# core/clarifier.py

def clarify(intent):
    if intent == "CALCULATE":
        return "What should I calculate?"
    if intent == "OPEN_FILE":
        return "Which file should I open?"
    return "Can you clarify what you want?"
