# 🔀 Controller Flow

The controller (`core/controller.py`) is the brain switchboard. All input flows through here.

---

## Flow Diagram

```
┌─────────────────────────────────────────────┐
│            handle_input(text)               │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│      Check for pending clarification?       │
│                                             │
│  YES → _handle_clarification_response()    │
│  NO  → Continue                             │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│           detect_intent(text)               │
│                                             │
│  Returns: (intent, confidence, entities)    │
│  Example: ("OPEN_APP", 0.9, {app: "chrome"})│
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│         check_clarification()               │
│                                             │
│  confidence < 0.6?  → Ask clarification     │
│  missing_params?    → Ask for param         │
│  multiple_intents?  → Ask which one         │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│          _execute_intent()                  │
│                                             │
│  Routes to appropriate tool function        │
│  OPEN_APP → system_tools.open_application() │
│  VOLUME_UP → audio_tools.volume_up()        │
│  etc.                                       │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│           Update Memory                     │
│                                             │
│  short_term.update(intent, entities)        │
│  long_term.log_command(...)                 │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│           Return Response                   │
└─────────────────────────────────────────────┘
```

---

## Key Functions

### `handle_input(text: str) -> str`
Main entry point. Receives user input, returns response.

### `_execute_intent(intent: str, entities: dict) -> str`
Routes intent to appropriate tool function.

### `_handle_clarification_response(text: str, pending: dict) -> str`
Handles user's response to a clarification question.

### `_get_help_text() -> str`
Returns the full help/command guide.

---

## Example Flow

```python
# User says: "open chrome"

handle_input("open chrome")
    │
    ├─ detect_intent("open chrome")
    │      → ("OPEN_APP", 0.9, {"app_name": "chrome"})
    │
    ├─ check_clarification() → No clarification needed
    │
    ├─ _execute_intent("OPEN_APP", {"app_name": "chrome"})
    │      → system_tools.open_application("chrome")
    │      → (True, "Opened chrome")
    │
    ├─ Update memory
    │
    └─ Return "Opened chrome"
```

---

## Clarification Example

```python
# User says: "open file"

handle_input("open file")
    │
    ├─ detect_intent("open file")
    │      → ("OPEN_FILE", 0.8, {})  # No file name!
    │
    ├─ check_clarification()
    │      → Missing "target" parameter
    │      → Set pending clarification
    │
    └─ Return "Which file should I open?"

# User says: "report.pdf"

handle_input("report.pdf")
    │
    ├─ Pending clarification exists!
    │
    ├─ _handle_clarification_response("report.pdf", pending)
    │      → Update entities: {"target": "report.pdf"}
    │
    ├─ _execute_intent("OPEN_FILE", {"target": "report.pdf"})
    │
    └─ Return "Opening report.pdf..."
```
