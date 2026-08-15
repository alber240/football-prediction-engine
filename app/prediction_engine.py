"""
Prediction Engine - Orchestrates all layers
Currently: Layer 1 (Poisson) only
"""

from app.poisson_model import PoissonModel
from app.models import get_db, League, Team, Match
from typing import Dict, Optional
import logging
import time

logger = logging.getLogger(__name__)

class PredictionEngine:
    def __init__(self):
        self.db = next(get_db())
        self.poisson_model = PoissonModel()
        
    def predict_match(self, match_id: int) -> Dict:
        """Predict a single match by ID"""
        start_time = time.time()
        
        match = self.db.query(Match).filter_by(id=match_id).first()
        if not match:
            return {'error': 'Match not found'}
        
        league = self.db.query(League).filter_by(id=match.league_id).first()
        
        prediction = self.poisson_model.predict_match(
            home_team_id=match.home_team_id,
            away_team_id=match.away_team_id,
            league_id=match.league_id
        )
        
        home_team = self.db.query(Team).filter_by(id=match.home_team_id).first()
        away_team = self.db.query(Team).filter_by(id=match.away_team_id).first()
        
        prediction['home_team_name'] = home_team.name if home_team else 'Unknown'
        prediction['away_team_name'] = away_team.name if away_team else 'Unknown'
        prediction['league_name'] = league.name if league else 'Unknown'
        prediction['match_id'] = match_id
        
        elapsed = time.time() - start_time
        logger.info(f"Prediction for match {match_id} took {elapsed:.2f}s")
        
        return prediction
    
    def predict_upcoming_matches(self, league_id: Optional[int] = None) -> list:
        """Predict upcoming or recent matches"""
        try:
            # Check for NS/TBD matches first
            ns_count = self.db.query(Match).filter(Match.status.in_(['NS', 'TBD'])).count()
            
            if ns_count > 0:
                # There are upcoming matches
                query = self.db.query(Match).filter(
                    Match.status.in_(['NS', 'TBD']),
                    Match.home_score.is_(None)
                )
            else:
                # No upcoming matches, return recent matches with scores
                logger.info("No upcoming matches, returning recent matches with predictions")
                query = self.db.query(Match).filter(
                    Match.home_score.isnot(None),
                    Match.away_score.isnot(None)
                ).order_by(Match.match_date.desc()).limit(20)
            
            if league_id:
                query = query.filter_by(league_id=league_id)
            
            matches = query.limit(50).all()
            
            predictions = []
            for match in matches:
                try:
                    pred = self.predict_match(match.id)
                    predictions.append(pred)
                except Exception as e:
                    logger.error(f"Error predicting match {match.id}: {e}")
                    continue
            
            return predictions
        except Exception as e:
            logger.error(f"Error in predict_upcoming_matches: {e}")
            return []
    
    def close(self):
        """Close database connections"""
        self.poisson_model.close()
        self.db.close()
