"""
WebSocket Server for Live Match Updates
"""

import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from app.services.live_matches import LiveMatchService
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Total: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Broadcast error: {e}")

manager = ConnectionManager()
live_service = LiveMatchService()

async def live_match_updater():
    while True:
        try:
            matches = live_service.get_live_matches()
            if matches:
                await manager.broadcast({
                    "type": "live_update",
                    "matches": matches,
                    "timestamp": str(datetime.now())
                })
        except Exception as e:
            logger.error(f"Live update error: {e}")
        await asyncio.sleep(30)

async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        matches = live_service.get_live_matches()
        await websocket.send_json({
            "type": "initial",
            "matches": matches,
            "timestamp": str(datetime.now())
        })
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)