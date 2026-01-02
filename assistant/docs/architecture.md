# Architecture Overview

This project is a small assistant prototype organized into logical packages:

- `core/` - controller, intent detection, clarifier, and memory management.
- `llm/` - local LLM interface and prompt templates.
- `tools/` - utility helpers (file, system, math).
- `io/` - input and output helpers.
- `config/` - YAML configuration.
- `docs/` - design and decision artifacts.

The system is intentionally modular so components can be replaced independently.
