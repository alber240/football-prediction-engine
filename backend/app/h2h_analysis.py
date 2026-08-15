"""
Head-to-Head Analysis
Historical matchups between two teams
"""

from sqlalchemy import text
from app.models import get_db
import logging

logger = logging.getLogger(__name__)

class H2HAnalyzer:
    def __init__(self):
        self.db = next(get_db())
        
    def get_h2h(self, home_team_id: int, away_team_id: int, num_matches: int = 10) -> dict:
        """
        Get head-to-head record between two teams
        """
        query = text("""
        SELECT 
            m.home_team_id,
            m.away_team_id,
            m.home_score,
            m.away_score,
            m.result,
            m.match_date,
            m.venue,
            t1.name as home_name,
            t2.name as away_name
        FROM matches m
        JOIN teams t1 ON m.home_team_id = t1.id
        JOIN teams t2 ON m.away_team_id = t2.id
        WHERE (m.home_team_id = :home_id AND m.away_team_id = :away_id)
        OR (m.home_team_id = :away_id AND m.away_team_id = :home_id)
        AND m.status = 'FT'
        AND m.home_score IS NOT NULL
        AND m.away_score IS NOT NULL
        ORDER BY m.match_date DESC
        LIMIT :num_matches
        """)
        
        matches = self.db.execute(
            query,
            {"home_id": home_team_id, "away_id": away_team_id, "num_matches": num_matches}
        ).fetchall()
        
        if not matches:
            return {
                'matches': [],
                'home_wins': 0,
                'away_wins': 0,
                'draws': 0,
                'total_goals_home': 0,
                'total_goals_away': 0,
                'most_common_score': None
            }
        
        home_wins = 0
        away_wins = 0
        draws = 0
        total_goals_home = 0
        total_goals_away = 0
        score_counts = {}
        
        for match in matches:
            is_home = match.home_team_id == home_team_id
            
            if is_home:
                goals_for = match.home_score
                goals_against = match.away_score
                total_goals_home += goals_for
                total_goals_away += goals_against
            else:
                goals_for = match.away_score
                goals_against = match.home_score
                total_goals_home += goals_for
                total_goals_away += goals_against
            
            result = 'H' if is_home and match.result == 'H' else 'A' if not is_home and match.result == 'A' else 'D'
            
            if result == 'H':
                home_wins += 1
            elif result == 'A':
                away_wins += 1
            else:
                draws += 1
            
            score = f"{goals_for}-{goals_against}"
            score_counts[score] = score_counts.get(score, 0) + 1
        
        most_common_score = max(score_counts.items(), key=lambda x: x[1]) if score_counts else None
        
        return {
            'matches': [
                {
                    'date': m.match_date.strftime('%Y-%m-%d'),
                    'home_team': m.home_name,
                    'away_team': m.away_name,
                    'score': f"{m.home_score}-{m.away_score}",
                    'venue': m.venue
                }
                for m in matches
            ],
            'home_wins': home_wins,
            'away_wins': away_wins,
            'draws': draws,
            'total_goals_home': total_goals_home,
            'total_goals_away': total_goals_away,
            'avg_goals_home': total_goals_home / len(matches) if matches else 0,
            'avg_goals_away': total_goals_away / len(matches) if matches else 0,
            'most_common_score': most_common_score,
            'matches_analyzed': len(matches)
        }
    
    def get_h2h_summary(self, home_team_id: int, away_team_id: int) -> dict:
        """Get a summary of H2H with advantage indicator"""
        h2h = self.get_h2h(home_team_id, away_team_id)
        
        if h2h['matches_analyzed'] == 0:
            return {
                'summary': "No historical matches found",
                'advantage': 'unknown'
            }
        
        total = h2h['home_wins'] + h2h['away_wins'] + h2h['draws']
        
        if h2h['home_wins'] > h2h['away_wins']:
            advantage = 'home'
            advantage_text = f"{h2h['home_wins']} wins in {total} matches ({(h2h['home_wins']/total)*100:.1f}%)"
        elif h2h['away_wins'] > h2h['home_wins']:
            advantage = 'away'
            advantage_text = f"{h2h['away_wins']} wins in {total} matches ({(h2h['away_wins']/total)*100:.1f}%)"
        else:
            advantage = 'draw'
            advantage_text = f"Even split: {h2h['home_wins']} wins each, {h2h['draws']} draws"
        
        return {
            'summary': f"Historical advantage: {advantage_text}",
            'advantage': advantage,
            'home_wins': h2h['home_wins'],
            'away_wins': h2h['away_wins'],
            'draws': h2h['draws'],
            'avg_goals_home': h2h['avg_goals_home'],
            'avg_goals_away': h2h['avg_goals_away'],
            'most_common_score': h2h['most_common_score']
        }