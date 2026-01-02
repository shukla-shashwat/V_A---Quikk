# Controller Flow

This document explains how `core/controller.py` routes an incoming text input.

1. Receive raw text input.
2. Call `intent.detect_intent(text)` to get a predicted intent and confidence.
3. If confidence is low, call `clarifier.clarify_if_needed(intent)` to produce a follow-up question.
4. Otherwise, select an appropriate tool or LLM path and return the response.

In the stub, the controller returns a small dictionary with detected intent and a textual response.
