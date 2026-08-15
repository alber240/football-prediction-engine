"""
Form Analysis - Last 5 matches with weighted importance
"""

from sqlalchemy import text
from app.models import get_db, Team, Match
from datetime import datetime, timedelta
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class FormAnalyzer:
    def __init__(self):
        self.db = next(get_db())
        
    def get_form(self, team_id: int, num_matches: int = 5, season: str = "2024") -> dict:
        """
        Get form data for a team
        Returns: form_points, goals_scored, goals_conceded, wins, draws, losses, streak
        """
        query = text("""
        SELECT 
            m.home_team_id,
            m.away_team_id,
            m.home_score,
            m.away_score,
            m.result,
            m.match_date,
            CASE 
                WHEN m.home_team_id = :team_id THEN 'home'
                ELSE 'away'
            END as venue
        FROM matches m
        WHERE (m.home_team_id = :team_id OR m.away_team_id = :team_id)
        AND m.season = :season
        AND m.status = 'FT'
        AND m.home_score IS NOT NULL
        AND m.away_score IS NOT NULL
        ORDER BY m.match_date DESC
        LIMIT :num_matches
        """)
        
        matches = self.db.execute(
            query, 
            {"team_id": team_id, "season": season, "num_matches": num_matches}
        ).fetchall()
        
        if not matches:
            return {
                'points': 0,
                'goals_scored': 0,
                'goals_conceded': 0,
                'wins': 0,
                'draws': 0,
                'losses': 0,
                'streak': 'No matches',
                'form_score': 0
            }
        
        points = 0
        goals_scored = 0
        goals_conceded = 0
        wins = 0
        draws = 0
        losses = 0
        results = []
        
        for match in matches:
            is_home = match.home_team_id == team_id
            
            if is_home:
                gs = match.home_score
                gc = match.away_score
            else:
                gs = match.away_score
                gc = match.home_score
            
            goals_scored += gs
            goals_conceded += gc
            
            if gs > gc:
                points += 3
                wins += 1
                results.append('W')
            elif gs == gc:
                points += 1
                draws += 1
                results.append('D')
            else:
                losses += 1
                results.append('L')
        
        # Calculate form score (weighted: more recent matches count more)
        weights = [0.3, 0.25, 0.2, 0.15, 0.1]  # Most recent gets highest weight
        form_score = 0
        for i, result in enumerate(results[:5]):
            if result == 'W':
                form_score += 3 * weights[i]
            elif result == 'D':
                form_score += 1 * weights[i]
            # Loss = 0
        
        return {
            'points': points,
            'goals_scored': goals_scored,
            'goals_conceded': goals_conceded,
            'wins': wins,
            'draws': draws,
            'losses': losses,
            'streak': ''.join(results[:5]),
            'form_score': form_score,
            'matches_analyzed': len(matches)
        }
    
    def get_form_difference(self, home_team_id: int, away_team_id: int) -> dict:
        """Compare form between two teams"""
        home_form = self.get_form(home_team_id)
        away_form = self.get_form(away_team_id)
        
        form_diff = {
            'home_form_score': home_form['form_score'],
            'away_form_score': away_form['form_score'],
            'form_advantage': 'home' if home_form['form_score'] > away_form['form_score'] else 'away',
            'home_form_streak': home_form['streak'],
            'away_form_streak': away_form['streak'],
            'home_goals_avg': home_form['goals_scored'] / max(1, home_form['matches_analyzed']),
            'away_goals_avg': away_form['goals_scored'] / max(1, away_form['matches_analyzed']),
            'home_goals_conceded_avg': home_form['goals_conceded'] / max(1, home_form['matches_analyzed']),
            'away_goals_conceded_avg': away_form['goals_conceded'] / max(1, away_form['matches_analyzed'])
        }
        
        return form_diff