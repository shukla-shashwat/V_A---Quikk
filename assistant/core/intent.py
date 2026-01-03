# core/intent.py

def detect_intent(text):
    text = text.lower()
    scores = {
        "CALCULATE": 0.0,
        "OPEN_FILE": 0.0,
        "GREETING": 0.0
    }

    if any(word in text for word in ["calculate", "add", "sum", "multiply", "calc"]):
        scores["CALCULATE"] += 0.6

    if any(char.isdigit() for char in text):
        scores["CALCULATE"] += 0.3

    if any(word in text for word in ["open", "file"]):
        scores["OPEN_FILE"] += 0.7

    if any(word in text for word in ["hi", "hello", "hey"]):
        scores["GREETING"] += 0.8

    intent = max(scores, key=scores.get)
    confidence = scores[intent]

    return intent, confidence
