"""
Fix all Python files with proper encoding
"""

import os

def write_file(filepath, content):
    """Write file with proper encoding"""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Created: {filepath}")

# Create directories if needed
os.makedirs("app/websocket", exist_ok=True)
os.makedirs("app/services", exist_ok=True)
os.makedirs("app/scheduler", exist_ok=True)

# WebSocket file
write_file("app/websocket/live_updates.py", '''
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from app.services.live_matches import LiveMatchService
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections = []
    
    async def connect(self, websocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def broadcast(self, message):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()
live_service = LiveMatchService()

async def websocket_endpoint(websocket):
    await manager.connect(websocket)
    try:
        matches = live_service.get_live_matches()
        await websocket.send_json({
            'type': 'initial',
            'matches': matches,
            'timestamp': str(datetime.now())
        })
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
''')

# Live matches service
write_file("app/services/live_matches.py", '''
import requests
import os
from dotenv import load_dotenv
import time
from typing import List, Dict
import logging

load_dotenv()
logger = logging.getLogger(__name__)

class LiveMatchService:
    def __init__(self):
        self.api_key = os.getenv("API_FOOTBALL_KEY")
        self.base_url = "https://v3.football.api-sports.io"
        self.headers = {
            "x-apisports-key": self.api_key,
            "Content-Type": "application/json"
        }
        
    def get_live_matches(self) -> List[Dict]:
        if not self.api_key:
            return []
        try:
            response = requests.get(
                f"{self.base_url}/fixtures",
                headers=self.headers,
                params={"live": "all"}
            )
            time.sleep(0.5)
            if response.status_code == 200:
                data = response.json()
                return data.get("response", [])
            return []
        except Exception as e:
            logger.error(f"Error: {e}")
            return []
''')

# Scheduler
write_file("app/scheduler/etl_scheduler.py", '''
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

def start_scheduler():
    try:
        scheduler.add_job(
            lambda: logger.info("ETL job running..."),
            trigger=IntervalTrigger(hours=6),
            id="etl_job"
        )
        scheduler.start()
        logger.info("Scheduler started")
    except Exception as e:
        logger.error(f"Scheduler error: {e}")
''')

print("All files created successfully!")