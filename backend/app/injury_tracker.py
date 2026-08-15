"""
Injury and Suspension Tracker
"""

from sqlalchemy import text
from app.models import get_db, Team
import logging

logger = logging.getLogger(__name__)

class InjuryTracker:
    def __init__(self):
        self.db = next(get_db())
        
    def get_injury_impact(self, team_id: int) -> dict:
        # Simplified version without Player model
        return {
            'impact_score': 0,
            'injured_players': [],
            'total_value_lost': 0,
            'total_value_team': 0
        }
    
    def get_suspensions(self, team_id: int) -> list:
        return []
    
    def get_team_availability(self, team_id: int) -> dict:
        return {
            'availability_score': 100,
            'injury_impact': {'impact_score': 0},
            'suspensions': [],
            'missing_players': [],
            'total_missing': 0
        }