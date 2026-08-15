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