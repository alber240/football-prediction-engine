"""
Meta-Learner - Aggregates and weights predictions
"""

from app.meta_learner.simple_scraper import SimpleScraper
from typing import Dict, List
import logging
import numpy as np

logger = logging.getLogger(__name__)

class MetaLearner:
    def __init__(self):
        self.scraper = SimpleScraper()
        self.weights = {
            'fivethirtyeight': 0.50,
            'forebet': 0.30,
            'whoscored': 0.20
        }
        self.brier_scores = {}
        
    def get_all_predictions(self, league: str = 'premier-league') -> Dict:
        results = {}
        try:
            results['fivethirtyeight'] = self.scraper.get_538_predictions(league)
        except Exception as e:
            logger.error(f"Error fetching from 538: {e}")
            results['fivethirtyeight'] = []
        
        results['forebet'] = []
        results['whoscored'] = []
        return results
    
    def calculate_weighted_prediction(self, predictions: List[Dict]) -> Dict:
        if not predictions:
            return {'home_win': 0.33, 'draw': 0.33, 'away_win': 0.33}
        
        total_weight = 0
        weighted_probs = {'home_win': 0, 'draw': 0, 'away_win': 0}
        
        for pred in predictions:
            source = pred.get('source', 'unknown')
            weight = self.weights.get(source, 0.1)
            
            weighted_probs['home_win'] += pred['home_win'] * weight
            weighted_probs['draw'] += pred['draw'] * weight
            weighted_probs['away_win'] += pred['away_win'] * weight
            total_weight += weight
        
        if total_weight > 0:
            weighted_probs['home_win'] /= total_weight
            weighted_probs['draw'] /= total_weight
            weighted_probs['away_win'] /= total_weight
        
        return weighted_probs