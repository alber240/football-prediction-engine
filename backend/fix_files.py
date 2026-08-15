"""
This script regenerates all Python files with proper ASCII encoding
Run once to fix all files
"""

import os

# Define all files with their content
files = {
    "app/websocket/live_updates.py": '''
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
''',

    "app/services/live_matches.py": '''
"""
Live Match Service - Fetches real-time match data
"""

import requests
import os
from dotenv import load_dotenv
import time
from typing import List, Dict
from datetime import datetime
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
            else:
                logger.error(f"Failed to fetch live matches: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error fetching live matches: {e}")
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
            logger.error(f"Error fetching events: {e}")
            return []
''',

    "app/scheduler/etl_scheduler.py": '''
"""
Scheduled ETL Pipeline - Runs automatically
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
import logging

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

def fetch_upcoming_matches():
    logger.info("Fetching upcoming matches...")

def fetch_injuries():
    logger.info("Fetching injury data...")

def start_scheduler():
    try:
        scheduler.add_job(
            fetch_upcoming_matches,
            trigger=IntervalTrigger(hours=6),
            id="fetch_matches"
        )
        
        scheduler.add_job(
            fetch_injuries,
            trigger=IntervalTrigger(hours=12),
            id="fetch_injuries"
        )
        
        scheduler.add_job(
            lambda: logger.info("Daily ETL job running..."),
            trigger=CronTrigger(hour=2, minute=0),
            id="daily_etl"
        )
        
        scheduler.start()
        logger.info("Scheduler started successfully")
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
'''
}

# Write all files with proper encoding
for filepath, content in files.items():
    with open(filepath, 'w', encoding='ascii') as f:
        f.write(content)
    print(f"Created: {filepath}")

print("\nAll files created successfully!")