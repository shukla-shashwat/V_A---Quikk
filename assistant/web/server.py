# web/server.py
"""
FastAPI server for Qwikk Assistant
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import json

from core.controller import handle_input, get_all_intents_info
from core.memory import get_short_term_memory, get_long_term_memory

# Create FastAPI app
app = FastAPI(
    title="Qwikk Assistant",
    description="Your Gen-Z AI Assistant",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
STATIC_DIR = Path(__file__).parent / "static"
TEMPLATES_DIR = Path(__file__).parent / "templates"

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# Models
class CommandRequest(BaseModel):
    text: str


class CommandResponse(BaseModel):
    response: str
    intent: Optional[str] = None
    success: bool = True


# WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


# Routes
@app.get("/", response_class=HTMLResponse)
async def get_index():
    """Serve the main UI"""
    index_file = TEMPLATES_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return HTMLResponse("<h1>Qwikk Assistant</h1><p>UI not found</p>")


@app.post("/api/command", response_model=CommandResponse)
async def process_command(request: CommandRequest):
    """Process a text command"""
    try:
        response = handle_input(request.text)
        return CommandResponse(response=response, success=True)
    except Exception as e:
        return CommandResponse(response=f"Error: {str(e)}", success=False)


@app.get("/api/help")
async def get_help():
    """Get all available commands and intents"""
    try:
        intents_info = get_all_intents_info()
        return {
            "success": True,
            "intents": intents_info,
            "categories": list(intents_info.keys())
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/history")
async def get_history():
    """Get command history"""
    try:
        long_term = get_long_term_memory()
        commands = long_term.get_recent_commands(limit=20)
        return {"commands": commands}
    except Exception as e:
        return {"commands": [], "error": str(e)}


@app.get("/api/stats")
async def get_stats():
    """Get usage statistics"""
    try:
        long_term = get_long_term_memory()
        stats = long_term.get_command_stats()
        return {"stats": stats}
    except Exception as e:
        return {"stats": {}, "error": str(e)}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time communication"""
    await manager.connect(websocket)
    
    # Send welcome message
    await manager.send_message(json.dumps({
        "type": "welcome",
        "message": "Connected to Qwikk ⚡"
    }), websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            
            try:
                payload = json.loads(data)
                command = payload.get("text", "")
            except json.JSONDecodeError:
                command = data
            
            # Process command with error handling
            try:
                response = handle_input(command)
            except Exception as e:
                response = f"Error processing command: {str(e)}"
                print(f"❌ Error: {e}")
            
            # Send response immediately
            try:
                await manager.send_message(json.dumps({
                    "type": "response",
                    "message": response,
                    "command": command
                }), websocket)
            except Exception as e:
                print(f"❌ Failed to send response: {e}")
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        manager.disconnect(websocket)


def run_server(host: str = "127.0.0.1", port: int = 8000):
    """Run the server"""
    import uvicorn
    print(f"\n⚡ Qwikk is starting at http://{host}:{port}\n")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
