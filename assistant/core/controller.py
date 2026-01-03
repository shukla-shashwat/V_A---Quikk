# core/controller.py

from core.intent import detect_intent
from core.clarifier import clarify
from core.memory import load_memory, update_memory
from tools.math_tools import calculate

CONFIDENCE_THRESHOLD = 0.6

memory = load_memory()

def handle_input(text):
    intent, confidence = detect_intent(text)

    if confidence < CONFIDENCE_THRESHOLD:
        return clarify(intent)

    if intent == "CALCULATE":
        expression = extract_expression(text)
        if not expression:
            return "What should I calculate?"

        result = calculate(expression)
        update_memory(memory, intent, {"expression": expression})
        return f"Result: {result}"

    if intent == "GREETING":
        return "Hello."

    return "I cannot handle that yet."

def extract_expression(text):
    # VERY basic version
    for char in text:
        if char.isdigit():
            return text
    return None
