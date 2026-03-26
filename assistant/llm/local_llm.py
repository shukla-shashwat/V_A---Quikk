# llm/local_llm.py
"""
Local LLM integration using Ollama.
Provides natural language responses without sending data to cloud.
"""

import requests
import json
from typing import Dict, Optional, Generator
from llm.prompts import get_system_prompt, get_response_prompt


# Ollama API configuration
OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "llama3.2"  # Can also use "mistral", "llama2", "phi3"


def check_ollama_running() -> bool:
    """Check if Ollama is running locally."""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=2)
        return response.status_code == 200
    except:
        return False


def list_models() -> list:
    """List available Ollama models."""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return [m["name"] for m in data.get("models", [])]
    except:
        pass
    return []


def generate(prompt: str, model: str = None, context: list = None) -> Dict[str, str]:
    """
    Generate a response using local Ollama.
    
    Args:
        prompt: User message or full prompt
        model: Model name (default: llama3.2)
        context: Previous conversation context
    
    Returns:
        Dict with 'text' key containing response
    """
    if not check_ollama_running():
        return {"text": None, "error": "Ollama not running. Start with: ollama serve"}
    
    model = model or DEFAULT_MODEL
    
    try:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "num_predict": 150  # Keep responses concise
            }
        }
        
        if context:
            payload["context"] = context
        
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "text": data.get("response", ""),
                "context": data.get("context"),
                "model": model
            }
        else:
            return {"text": None, "error": f"Ollama error: {response.status_code}"}
            
    except requests.exceptions.Timeout:
        return {"text": None, "error": "LLM timeout - try a smaller model"}
    except Exception as e:
        return {"text": None, "error": str(e)}


def generate_stream(prompt: str, model: str = None) -> Generator[str, None, None]:
    """
    Stream response tokens from Ollama.
    Useful for real-time display.
    """
    if not check_ollama_running():
        yield "[Ollama not running]"
        return
    
    model = model or DEFAULT_MODEL
    
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": True
            },
            stream=True,
            timeout=60
        )
        
        for line in response.iter_lines():
            if line:
                data = json.loads(line)
                if "response" in data:
                    yield data["response"]
                if data.get("done"):
                    break
                    
    except Exception as e:
        yield f"[Error: {e}]"


def chat(messages: list, model: str = None) -> Dict[str, str]:
    """
    Chat with conversation history using Ollama's chat API.
    
    Args:
        messages: List of {"role": "user"|"assistant", "content": "..."}
        model: Model name
    
    Returns:
        Dict with response
    """
    if not check_ollama_running():
        return {"text": None, "error": "Ollama not running"}
    
    model = model or DEFAULT_MODEL
    
    # Add system prompt
    full_messages = [
        {"role": "system", "content": get_system_prompt()}
    ] + messages
    
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": model,
                "messages": full_messages,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 150
                }
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "text": data.get("message", {}).get("content", ""),
                "model": model
            }
        else:
            return {"text": None, "error": f"Chat error: {response.status_code}"}
            
    except Exception as e:
        return {"text": None, "error": str(e)}


def polish_response(raw_response: str, context: str = "") -> str:
    """
    Use LLM to make a response more natural and friendly.
    Falls back to raw response if LLM unavailable.
    """
    if not check_ollama_running():
        return raw_response
    
    prompt = get_response_prompt(raw_response, context)
    result = generate(prompt)
    
    if result.get("text"):
        return result["text"].strip()
    return raw_response


def pull_model(model_name: str) -> bool:
    """Download a model if not already available."""
    if not check_ollama_running():
        return False
    
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/pull",
            json={"name": model_name},
            timeout=300  # Models can take a while to download
        )
        return response.status_code == 200
    except:
        return False
