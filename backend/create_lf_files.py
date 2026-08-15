"""
Create all files with LF line endings (no CRLF)
"""

import os

def write_file_lf(filepath, content):
    """Write file with LF only line endings"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    # Replace any existing \r\n with \n
    content = content.replace('\r\n', '\n')
    with open(filepath, 'w', newline='\n') as f:
        f.write(content)
    print(f"Created: {filepath}")

# WebSocket file
write_file_lf("app/websocket/live_updates.py", '''
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
write_file_lf("app/services/live_matches.py", '''
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
    
    def get_match_events(self, fixture_id: int) -> List[Dict]:
        try:
            response = requests.get(
                f"{self.base_url}/fixtures/events",
                headers=self.headers,
                params={"fixture": fixture_id}
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
write_file_lf("app/scheduler/etl_scheduler.py", '''
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

# Test import file
write_file_lf("test_simple.py", '''
print("Testing imports...")

try:
    from app.websocket.live_updates import ConnectionManager
    print("WebSocket OK")
except Exception as e:
    print(f"WebSocket error: {e}")

try:
    from app.services.live_matches import LiveMatchService
    print("LiveMatch OK")
except Exception as e:
    print(f"LiveMatch error: {e}")

try:
    from app.scheduler.etl_scheduler import start_scheduler
    print("Scheduler OK")
except Exception as e:
    print(f"Scheduler error: {e}")

print("Done!")
''')

print("All files created with LF line endings!")