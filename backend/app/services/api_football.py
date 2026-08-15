import requests
import os
from dotenv import load_dotenv
import time
from typing import List, Dict, Optional
import logging

load_dotenv()

logger = logging.getLogger(__name__)

class APIFootballService:
    def __init__(self):
        self.api_key = os.getenv("API_FOOTBALL_KEY")
        if not self.api_key:
            logger.warning("API_FOOTBALL_KEY not found")
        else:
            logger.info(f"API key loaded: {self.api_key[:8]}...")
        self.base_url = "https://v3.football.api-sports.io"
        self.headers = {
            "x-apisports-key": self.api_key,
            "Content-Type": "application/json"
        }
        self.rate_limit_delay = 1.0

    def fetch_leagues(self) -> List[Dict]:
        league_ids = [39, 140, 78, 135, 61, 2]
        leagues = []
        for lid in league_ids:
            try:
                response = requests.get(
                    f"{self.base_url}/leagues",
                    headers=self.headers,
                    params={"id": lid}
                )
                time.sleep(self.rate_limit_delay)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("response"):
                        leagues.append(data["response"][0])
                    print(f"   Fetched league {lid}")
                else:
                    print(f"   Failed to fetch league {lid}")
            except Exception as e:
                print(f"   Error: {e}")
        return leagues

    def fetch_teams(self, league_id: int, season: str) -> List[Dict]:
        try:
            response = requests.get(
                f"{self.base_url}/teams",
                headers=self.headers,
                params={"league": league_id, "season": season}
            )
            time.sleep(self.rate_limit_delay)
            if response.status_code == 200:
                data = response.json()
                return data.get("response", [])
            return []
        except Exception as e:
            print(f"Error: {e}")
            return []

    def fetch_matches(self, league_id: int, season: str, start_date: Optional[str] = None, end_date: Optional[str] = None, status: Optional[str] = None) -> List[Dict]:
        params = {"league": league_id, "season": season}
        if start_date:
            params["from"] = start_date
        if end_date:
            params["to"] = end_date
        if status:
            params["status"] = status
        try:
            response = requests.get(
                f"{self.base_url}/fixtures",
                headers=self.headers,
                params=params
            )
            time.sleep(self.rate_limit_delay)
            if response.status_code == 200:
                data = response.json()
                return data.get("response", [])
            return []
        except Exception as e:
            print(f"Error: {e}")
            return []
