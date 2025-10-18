# backend/app/services/connection_manager.py

from typing import Dict, List
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, job_id: str):
        await websocket.accept()
        self.active_connections[job_id] = websocket

    def disconnect(self, job_id: str):
        if job_id in self.active_connections:
            del self.active_connections[job_id]

    async def send_event_to_job(self, event_json: str, job_id: str):
        if job_id in self.active_connections:
            websocket = self.active_connections[job_id]
            await websocket.send_text(event_json)

#manager instance
manager = ConnectionManager()