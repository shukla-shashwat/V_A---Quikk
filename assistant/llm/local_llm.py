"""local_llm.py
Simple llama interface placeholder. No external models are loaded here.
"""

from typing import Dict


def generate(prompt: str) -> Dict[str, str]:
    """Return a deterministic, safe response for the stub.

    Real implementations should call a local LLM backend.
    """
    return {"text": f"[stubbed LLM response] for prompt: {prompt}"}
