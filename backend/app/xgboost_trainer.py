"""
XGBoost Trainer - Layer 3 Neural Network
Trains per-league models on 2020-2025 data
"""

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.metrics import accuracy_score, log_loss, brier_score_loss
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sqlalchemy import text
import joblib
import os
from datetime import datetime
import logging
from typing import Dict, List, Tuple, Optional

from app.models import get_db, League, Team, Match
from app.poisson_model import PoissonModel
from app.elo_model import EloRatingSystem
from app.form_analysis import FormAnalyzer
from app.h2h_analysis import H2HAnalyzer

logger = logging.getLogger(__name__)

class XGBoostTrainer:
    def __init__(self):
        self.db = next(get_db())
        self.poisson = PoissonModel()
        self.elo_system = EloRatingSystem()
        self.form_analyzer = FormAnalyzer()
        self.h2h_analyzer = H2HAnalyzer()
        self.scaler = StandardScaler()
        self.models = {}
        self.feature_columns = []
        self.model_dir = "models/xgboost"
        os.makedirs(self.model_dir, exist_ok=True)
        
        # League IDs for per-league models (database IDs, not API IDs)
        self.leagues = {
            1: 'premier_league',
            2: 'la_liga',
            3: 'bundesliga',
            4: 'serie_a',
            5: 'ligue_1',
            6: 'ucl'
        }
    
    def prepare_features(self, match: Dict) -> np.ndarray:
        """Extract features for a single match"""
        features = []
        
        # Layer 1: Poisson features
        poisson_pred = self.poisson.predict_match(
            home_team_id=match['home_team_id'],
            away_team_id=match['away_team_id'],
            league_id=match['league_id']
        )
        features.extend([
            poisson_pred['expected_home_goals'],
            poisson_pred['expected_away_goals'],
            poisson_pred['home_win'],
            poisson_pred['draw'],
            poisson_pred['away_win'],
            poisson_pred['over_25'],
            poisson_pred['under_25']
        ])
        
        # Elo features
        home_elo = self.elo_system.get_team_elo(match['home_team_id'])
        away_elo = self.elo_system.get_team_elo(match['away_team_id'])
        features.extend([
            home_elo,
            away_elo,
            home_elo - away_elo,
            home_elo + 50 - away_elo  # With home advantage
        ])
        
        # Form features
        home_form = self.form_analyzer.get_form(match['home_team_id'])
        away_form = self.form_analyzer.get_form(match['away_team_id'])
        features.extend([
            home_form['form_score'],
            away_form['form_score'],
            home_form['form_score'] - away_form['form_score'],
            home_form['goals_scored'] / max(1, home_form['matches_analyzed']),
            away_form['goals_scored'] / max(1, away_form['matches_analyzed']),
            home_form['goals_conceded'] / max(1, home_form['matches_analyzed']),
            away_form['goals_conceded'] / max(1, away_form['matches_analyzed'])
        ])
        
        # Head-to-Head features
        h2h = self.h2h_analyzer.get_h2h(match['home_team_id'], match['away_team_id'])
        features.extend([
            h2h['home_wins'] / max(1, h2h['matches_analyzed']),
            h2h['away_wins'] / max(1, h2h['matches_analyzed']),
            h2h['draws'] / max(1, h2h['matches_analyzed']),
            h2h['avg_goals_home'],
            h2h['avg_goals_away']
        ])
        
        # Non-statistical features
        features.extend([
            self._get_days_since_last_match(match['home_team_id'], match['match_date']),
            self._get_days_since_last_match(match['away_team_id'], match['match_date']),
            1 if match.get('is_midweek', False) else 0,
            1 if match.get('is_derby', False) else 0
        ])
        
        return np.array(features)
    
    def _get_days_since_last_match(self, team_id: int, match_date: datetime) -> int:
        """Calculate days since team's last match"""
        query = text("""
        SELECT match_date
        FROM matches
        WHERE (home_team_id = :team_id OR away_team_id = :team_id)
        AND match_date < :match_date
        AND status = 'FT'
        ORDER BY match_date DESC
        LIMIT 1
        """)
        result = self.db.execute(query, {"team_id": team_id, "match_date": match_date}).fetchone()
        if result:
            days = (match_date - result.match_date).days
            return max(0, days)
        return 7  # Default to 7 days
    
    def get_training_data(self, league_id: int, start_season: str = "2020", end_season: str = "2024") -> Tuple[np.ndarray, np.ndarray]:
        """Extract training data for a specific league"""
        query = text("""
        SELECT 
            m.id,
            m.home_team_id,
            m.away_team_id,
            m.league_id,
            m.home_score,
            m.away_score,
            m.result,
            m.match_date,
            m.is_midweek,
            m.season
        FROM matches m
        WHERE m.league_id = :league_id
        AND m.season >= :start_season
        AND m.season <= :end_season
        AND m.status = 'FT'
        AND m.home_score IS NOT NULL
        AND m.away_score IS NOT NULL
        """)
        
        matches = self.db.execute(query, {
            "league_id": league_id,
            "start_season": start_season,
            "end_season": end_season
        }).fetchall()
        
        if not matches:
            logger.warning(f"No matches found for league {league_id}")
            return np.array([]), np.array([])
        
        features = []
        targets = []
        
        for match in matches:
            try:
                match_dict = {
                    'home_team_id': match.home_team_id,
                    'away_team_id': match.away_team_id,
                    'league_id': match.league_id,
                    'match_date': match.match_date,
                    'is_midweek': match.is_midweek
                }
                
                feature_vector = self.prepare_features(match_dict)
                features.append(feature_vector)
                
                # Target: one-hot encoded result [home_win, draw, away_win]
                if match.home_score > match.away_score:
                    targets.append([1, 0, 0])
                elif match.home_score < match.away_score:
                    targets.append([0, 0, 1])
                else:
                    targets.append([0, 1, 0])
                    
            except Exception as e:
                logger.warning(f"Error processing match {match.id}: {e}")
                continue
        
        if not features:
            return np.array([]), np.array([])
        
        return np.array(features), np.array(targets)
    
    def train_model(self, league_id: int, league_name: str) -> Dict:
        """Train XGBoost model for a specific league"""
        logger.info(f"Training model for {league_name} (ID: {league_id})...")
        
        # Get training data
        X, y = self.get_training_data(league_id)
        
        if len(X) == 0:
            logger.warning(f"No training data for {league_name}")
            return {'status': 'failed', 'reason': 'No data'}
        
        logger.info(f"Found {len(X)} matches for {league_name}")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # XGBoost parameters
        params = {
            'n_estimators': 300,
            'max_depth': 6,
            'learning_rate': 0.05,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'min_child_weight': 3,
            'gamma': 0.1,
            'reg_alpha': 0.1,
            'reg_lambda': 1.0,
            'objective': 'multi:softprob',
            'num_class': 3,
            'eval_metric': 'mlogloss',
            'early_stopping_rounds': 30,
            'random_state': 42
        }
        
        # Train model
        model = xgb.XGBClassifier(**params)
        model.fit(
            X_train_scaled,
            np.argmax(y_train, axis=1),
            eval_set=[(X_test_scaled, np.argmax(y_test, axis=1))],
            verbose=False
        )
        
        # Evaluate
        y_pred_proba = model.predict_proba(X_test_scaled)
        y_pred = model.predict(X_test_scaled)
        
        accuracy = accuracy_score(np.argmax(y_test, axis=1), y_pred)
        log_loss_score = log_loss(y_test, y_pred_proba)
        
        # Calculate Brier score (without multi_class parameter)
        brier_scores = []
        for i in range(3):
            brier = brier_score_loss(y_test[:, i], y_pred_proba[:, i])
            brier_scores.append(brier)
        brier_score = np.mean(brier_scores)
        
        # Save model
        model_path = os.path.join(self.model_dir, f"{league_name}_model.pkl")
        joblib.dump({
            'model': model,
            'scaler': self.scaler,
            'feature_columns': self.feature_columns,
            'accuracy': accuracy,
            'brier_score': brier_score
        }, model_path)
        
        self.models[league_name] = model
        
        result = {
            'status': 'success',
            'league': league_name,
            'matches_trained': len(X_train),
            'matches_tested': len(X_test),
            'accuracy': accuracy,
            'brier_score': brier_score,
            'log_loss': log_loss_score,
            'model_path': model_path
        }
        
        logger.info(f"✅ {league_name} - Accuracy: {accuracy:.4f}, Brier: {brier_score:.4f}")
        return result
    
    def train_all_models(self) -> Dict:
        """Train models for all leagues"""
        results = {}
        
        for league_id, league_name in self.leagues.items():
            # Get the league from database
            league = self.db.query(League).filter_by(id=league_id).first()
            if not league:
                logger.warning(f"League ID {league_id} not found in database")
                continue
                
            result = self.train_model(league_id, league_name)
            results[league_name] = result
        
        return results
    
    def predict(self, match_id: int) -> Dict:
        """Predict using the trained XGBoost model"""
        match = self.db.query(Match).filter_by(id=match_id).first()
        if not match:
            return {'error': 'Match not found'}
        
        league = self.db.query(League).filter_by(id=match.league_id).first()
        league_name = self.leagues.get(match.league_id)
        
        if not league_name or league_name not in self.models:
            return {'error': f'Model not found for league {league_name}'}
        
        # Prepare features
        match_dict = {
            'home_team_id': match.home_team_id,
            'away_team_id': match.away_team_id,
            'league_id': match.league_id,
            'match_date': match.match_date,
            'is_midweek': match.is_midweek
        }
        features = self.prepare_features(match_dict).reshape(1, -1)
        
        # Scale features
        model_data = joblib.load(os.path.join(self.model_dir, f"{league_name}_model.pkl"))
        scaler = model_data['scaler']
        model = model_data['model']
        
        features_scaled = scaler.transform(features)
        
        # Predict
        probabilities = model.predict_proba(features_scaled)[0]
        
        return {
            'home_win': probabilities[0],
            'draw': probabilities[1],
            'away_win': probabilities[2]
        }