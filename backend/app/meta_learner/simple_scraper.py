"""
Simple Scraper - Alternative method using public APIs
"""

import requests
import json
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class SimpleScraper:
    def __init__(self):
        self.api_key = None

    def get_538_predictions(self, league: str = 'premier-league') -> List[Dict]:
        try:
            url = f"https://projects.fivethirtyeight.com/soccer-predictions/data/{league}.json"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                try:
                    data = response.json()
                    predictions = []

                    if 'matches' in data:
                        matches = data.get('matches', [])
                    elif 'games' in data:
                        matches = data.get('games', [])
                    else:
                        matches = []
                        for key in data:
                            if isinstance(data[key], list) and len(data[key]) > 0:
                                if 'home_team' in data[key][0] or 'team1' in data[key][0]:
                                    matches = data[key]
                                    break

                    for match in matches:
                        home = match.get('home_team') or match.get('team1') or match.get('home') or 'Unknown'
                        away = match.get('away_team') or match.get('team2') or match.get('away') or 'Unknown'

                        home_prob = match.get('home_win_prob') or match.get('win_prob_1') or 0.33
                        draw_prob = match.get('draw_prob') or match.get('tie_prob') or 0.33
                        away_prob = match.get('away_win_prob') or match.get('win_prob_2') or 0.33

                        predictions.append({
                            'home_team': home,
                            'away_team': away,
                            'home_win': float(home_prob),
                            'draw': float(draw_prob),
                            'away_win': float(away_prob),
                            'source': 'fivethirtyeight'
                        })

                    return predictions
                except ValueError as e:
                    logger.error(f"Error parsing JSON: {e}")
                    return []
            else:
                logger.error(f"Failed to fetch 538 data: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error fetching 538 data: {e}")
            return []

    def get_forebet_predictions(self, league: str = 'premier-league') -> List[Dict]:
        return []