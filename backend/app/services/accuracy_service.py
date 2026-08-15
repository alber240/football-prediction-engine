"""
Accuracy Service - Tracks prediction accuracy
"""

from app.models import get_db, Match, OurPrediction, Team, League
from datetime import datetime, timedelta
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

class AccuracyService:
    def __init__(self):
        self.db = next(get_db())
    
    def check_prediction_accuracy(self, match_id: int) -> dict:
        """Check if a prediction was correct"""
        match = self.db.query(Match).filter_by(id=match_id).first()
        if not match or match.home_score is None:
            return {'error': 'Match not finished or not found'}
        
        prediction = self.db.query(OurPrediction).filter_by(match_id=match_id).first()
        if not prediction:
            return {'error': 'No prediction found'}
        
        # Determine actual result
        if match.home_score > match.away_score:
            actual = 'H'
            actual_index = 0
        elif match.home_score < match.away_score:
            actual = 'A'
            actual_index = 2
        else:
            actual = 'D'
            actual_index = 1
        
        # Determine predicted result
        pred_probs = [prediction.home_prob, prediction.draw_prob, prediction.away_prob]
        predicted_index = max(range(len(pred_probs)), key=pred_probs.__getitem__)
        predicted = ['H', 'D', 'A'][predicted_index]
        
        correct = actual == predicted
        
        return {
            'match_id': match_id,
            'home_team': self.db.query(Team).filter_by(id=match.home_team_id).first().name,
            'away_team': self.db.query(Team).filter_by(id=match.away_team_id).first().name,
            'actual_score': f"{match.home_score}-{match.away_score}",
            'actual_result': actual,
            'predicted_result': predicted,
            'correct': correct,
            'predicted_home_prob': float(prediction.home_prob),
            'predicted_draw_prob': float(prediction.draw_prob),
            'predicted_away_prob': float(prediction.away_prob)
        }
    
    def calculate_daily_accuracy(self, date: str = None) -> dict:
        """Calculate accuracy for a specific day"""
        if not date:
            date = datetime.utcnow().strftime('%Y-%m-%d')
        
        query = text("""
        SELECT m.id
        FROM matches m
        WHERE DATE(m.match_date) = :date
        AND m.status = 'FT'
        AND m.home_score IS NOT NULL
        AND m.away_score IS NOT NULL
        """)
        
        matches = self.db.execute(query, {"date": date}).fetchall()
        
        results = []
        correct_count = 0
        
        for match in matches:
            result = self.check_prediction_accuracy(match.id)
            if 'error' not in result:
                results.append(result)
                if result['correct']:
                    correct_count += 1
        
        total = len(results)
        accuracy = (correct_count / total * 100) if total > 0 else 0
        
        return {
            'date': date,
            'total_predictions': total,
            'correct_predictions': correct_count,
            'accuracy_percentage': round(accuracy, 2),
            'results': results
        }
    
    def get_league_accuracy(self, league_id: int) -> dict:
        """Get accuracy for a specific league"""
        query = text("""
        SELECT m.id
        FROM matches m
        WHERE m.league_id = :league_id
        AND m.status = 'FT'
        AND m.home_score IS NOT NULL
        AND m.away_score IS NOT NULL
        """)
        
        matches = self.db.execute(query, {"league_id": league_id}).fetchall()
        
        results = []
        correct_count = 0
        
        for match in matches:
            result = self.check_prediction_accuracy(match.id)
            if 'error' not in result:
                results.append(result)
                if result['correct']:
                    correct_count += 1
        
        total = len(results)
        accuracy = (correct_count / total * 100) if total > 0 else 0
        
        league = self.db.query(League).filter_by(id=league_id).first()
        
        return {
            'league': league.name if league else 'Unknown',
            'total_predictions': total,
            'correct_predictions': correct_count,
            'accuracy_percentage': round(accuracy, 2)
        }