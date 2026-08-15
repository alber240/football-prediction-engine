"""
Prediction Engine - Orchestrates all layers
"""

from app.poisson_model import PoissonModel
from app.elo_model import EloRatingSystem
from app.form_analysis import FormAnalyzer
from app.h2h_analysis import H2HAnalyzer
from app.injury_tracker import InjuryTracker
from app.meta_learner.meta_learner import MetaLearner
from app.models import get_db, League, Team, Match
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class PredictionEngine:
    def __init__(self):
        self.db = next(get_db())
        self.poisson_model = PoissonModel()
        self.elo_system = EloRatingSystem()
        self.form_analyzer = FormAnalyzer()
        self.h2h_analyzer = H2HAnalyzer()
        self.injury_tracker = InjuryTracker()
        self.meta_learner = MetaLearner()
        
    def predict_match(self, match_id: int) -> Dict:
        """Predict a single match using all layers"""
        match = self.db.query(Match).filter_by(id=match_id).first()
        if not match:
            return {'error': 'Match not found'}
        
        league = self.db.query(League).filter_by(id=match.league_id).first()
        
        # Layer 1: Mathematical Foundation
        logger.info("Layer 1: Poisson + Elo...")
        poisson_pred = self.poisson_model.predict_match(
            home_team_id=match.home_team_id,
            away_team_id=match.away_team_id,
            league_id=match.league_id
        )
        
        # Get team names
        home_team = self.db.query(Team).filter_by(id=match.home_team_id).first()
        away_team = self.db.query(Team).filter_by(id=match.away_team_id).first()
        
        # Layer 2: Meta-Learner (if available)
        logger.info("Layer 2: Meta-Learner...")
        meta_predictions = self.meta_learner.get_all_predictions('premier-league')
        # TODO: Match predictions to this specific match
        meta_consensus = {'home_win': 0.33, 'draw': 0.33, 'away_win': 0.33}
        
        # Combine predictions
        final_pred = self._combine_predictions(poisson_pred, meta_consensus)
        
        # Add team names
        final_pred['home_team_name'] = home_team.name if home_team else 'Unknown'
        final_pred['away_team_name'] = away_team.name if away_team else 'Unknown'
        final_pred['league_name'] = league.name if league else 'Unknown'
        final_pred['match_id'] = match_id
        
        return final_pred
    
    def _combine_predictions(self, poisson: Dict, meta: Dict) -> Dict:
        """Combine Poisson and Meta-Learner predictions"""
        poisson_weight = 0.7
        meta_weight = 0.3

        combined = {
            'home_win': (poisson['home_win'] * poisson_weight) + (meta['home_win'] * meta_weight),
            'draw': (poisson['draw'] * poisson_weight) + (meta['draw'] * meta_weight),
            'away_win': (poisson['away_win'] * poisson_weight) + (meta['away_win'] * meta_weight)
        }

        # Normalize
        total = sum(combined.values())
        if total > 0:
            combined['home_win'] /= total
            combined['draw'] /= total
            combined['away_win'] /= total

        combined['expected_home_goals'] = poisson['expected_home_goals']
        combined['expected_away_goals'] = poisson['expected_away_goals']
        combined['over_25'] = poisson['over_25']
        combined['under_25'] = poisson['under_25']
        combined['most_likely_scores'] = poisson['most_likely_scores']
        combined['confidence_score'] = max(combined['home_win'], combined['draw'], combined['away_win'])

        return combined