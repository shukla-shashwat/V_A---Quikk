# 📝 Decision Log

Track of important design decisions and their rationale.

---

## 2026-03 - Major Decisions

### Text-First Architecture
**Decision:** Build core logic without LLM dependency.
**Rationale:** 
- Easier to debug (no AI unpredictability)
- Works offline
- LLM can be added later for polish only

### Intent-Based Routing
**Decision:** Use keyword/regex matching instead of ML for intent detection.
**Rationale:**
- Fast and predictable
- No model files needed
- Easy to add new intents

### Three Entry Points
**Decision:** Create separate launchers (web, voice, background).
**Rationale:**
- Different use cases need different interfaces
- Keep each launcher simple and focused
- All share the same controller

### SQLite for Long-Term Memory
**Decision:** Use SQLite instead of JSON for command history.
**Rationale:**
- Better for queries (stats, search)
- Handles concurrent access
- Scales better than JSON

### UWP App Support
**Decision:** Add special handling for Microsoft Store apps.
**Rationale:**
- Many modern apps are UWP (WhatsApp, Spotify, etc.)
- Normal `start` command doesn't work
- Use `shell:AppsFolder` approach

### Browser Speech API for Web
**Decision:** Use Web Speech API instead of backend STT for web UI.
**Rationale:**
- No extra server-side dependencies
- Works in modern browsers
- Lower latency

### Global Hotkey Mode
**Decision:** Create background assistant with Ctrl+Shift+Q.
**Rationale:**
- Faster than opening browser
- Works from any app
- True "always available" assistant

---

## Technical Choices

| Component | Choice | Alternative Considered |
|-----------|--------|------------------------|
| Web Framework | FastAPI | Flask (less async support) |
| TTS | pyttsx3 | gTTS (needs internet) |
| STT | SpeechRecognition | Vosk (more complex setup) |
| Volume Control | pycaw | pyaudio (more limited) |
| Config Format | YAML | JSON (less readable) |
| Memory DB | SQLite | JSON files (doesn't scale) |

---

## Future Considerations

- [ ] Add Vosk for fully offline STT
- [ ] System tray icon for background mode
- [ ] Plugin system for custom tools
- [ ] Multi-language support
- [ ] Conversation context (multi-turn)
- [ ] LLM integration for complex queries
