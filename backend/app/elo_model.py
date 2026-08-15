"""
Elo Rating System for Football Teams
Tracks team strength dynamically over time
"""

from sqlalchemy import text
from app.models import get_db, Team, Match
import numpy as np
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class EloRatingSystem:
    def __init__(self):
        self.db = next(get_db())
        self.base_elo = 1500
        self.k_factor = 30
        self.home_advantage = 50
        
    def calculate_elo(self, team_id: int, season: str = "2024") -> float:
        """Calculate current Elo for a team based on all matches"""
        # Get all matches for this team
        query = text("""
        SELECT 
            m.home_team_id,
            m.away_team_id,
            m.home_score,
            m.away_score,
            m.result,
            m.match_date
        FROM matches m
        WHERE (m.home_team_id = :team_id OR m.away_team_id = :team_id)
        AND m.season = :season
        AND m.status = 'FT'
        AND m.home_score IS NOT NULL
        AND m.away_score IS NOT NULL
        ORDER BY m.match_date ASC
        """)
        
        matches = self.db.execute(query, {"team_id": team_id, "season": season}).fetchall()
        
        if not matches:
            return self.base_elo
        
        elo = self.base_elo
        
        for match in matches:
            is_home = match.home_team_id == team_id
            
            # Determine opponent
            opponent_id = match.away_team_id if is_home else match.home_team_id
            
            # Get opponent Elo (simplified - in production, we'd have a lookup)
            opponent_elo = self.get_team_elo(opponent_id)
            
            # Add home advantage
            if is_home:
                elo_adjusted = elo + self.home_advantage
            else:
                elo_adjusted = elo - self.home_advantage
            
            # Expected result
            expected = 1 / (1 + 10 ** ((opponent_elo - elo_adjusted) / 400))
            
            # Actual result
            if is_home:
                if match.home_score > match.away_score:
                    actual = 1
                elif match.home_score < match.away_score:
                    actual = 0
                else:
                    actual = 0.5
            else:
                if match.away_score > match.home_score:
                    actual = 1
                elif match.away_score < match.home_score:
                    actual = 0
                else:
                    actual = 0.5
            
            # Update Elo
            k = self.get_k_factor(team_id, elo)
            elo = elo + k * (actual - expected)
        
        return elo
    
    def get_team_elo(self, team_id: int) -> float:
        """Get Elo from database or calculate if not exists"""
        team = self.db.query(Team).filter_by(id=team_id).first()
        if team and team.elo_rating:
            return float(team.elo_rating)
        return self.base_elo
    
    def get_k_factor(self, team_id: int, elo: float) -> float:
        """Dynamic K-factor based on team strength"""
        if elo > 1600:
            return 20  # Top teams
        elif elo > 1400:
            return 30  # Mid-table
        else:
            return 40  # Lower teams
    
    def update_all_elos(self, season: str = "2024"):
        """Update Elo ratings for all teams in a season"""
        teams = self.db.query(Team).all()
        for team in teams:
            new_elo = self.calculate_elo(team.id, season)
            team.elo_rating = new_elo
        self.db.commit()
        logger.info(f"Updated Elo ratings for {len(teams)} teams")