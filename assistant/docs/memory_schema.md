# Memory Schema

Short-term memory (volatile):
- Stored in `core/memory.py` as a simple in-memory list for the stub.
- Intended to hold recent context items for the current conversation session.

Long-term memory (persistent):
- Not implemented in the stub. In a full system this would be a database or vector store.

Example schema for persistent memory (conceptual):
- id: UUID
- user_id: string
- timestamp: ISO8601
- type: enum (note, preference, fact)
- content: JSON
- embedding: optional vector
