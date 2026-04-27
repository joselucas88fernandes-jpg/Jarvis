from fastapi import FastAPI, WebSocket
from typing import List
import asyncio
from jarvis_refactored.skills.hud.telemetry_vis import telemetry_vis
from jarvis_refactored.interfaces import SkillInput

app = FastAPI()

class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

ws_manager = WebSocketManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # This is a simple loop to keep the connection alive.
            # In a real application, you would handle incoming messages here.
            await asyncio.sleep(1) 
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        ws_manager.disconnect(websocket)
