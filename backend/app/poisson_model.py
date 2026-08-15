"""
Poisson Distribution Model for Football Predictions
Layer 1: Mathematical Foundation
"""

import numpy as np
import pandas as pd
from scipy import stats
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv
from typing import Dict, List, Tuple, Optional
import logging

load_dotenv()

logger = logging.getLogger(__name__)

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://football_admin:football_pass_123@localhost:5434/football_prediction")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class PoissonModel:
    def __init__(self):
        self.db = SessionLocal()
        self.league_stats = {}
        self.team_stats = {}
        self.dixon_coles_tau = 0.05  # Will be optimized

    def calculate_league_averages(self, league_id: int, season: str = "2024") -> Dict:
        """Calculate league-wide average goals per game"""
        query = text("""
        SELECT 
            AVG(m.home_score) as avg_home_goals,
            AVG(m.away_score) as avg_away_goals,
            COUNT(*) as matches_count,
            AVG(m.home_score + m.away_score) as avg_total_goals
        FROM matches m
        WHERE m.league_id = :league_id
        AND m.season = :season
        AND m.home_score IS NOT NULL
        AND m.away_score IS NOT NULL
        AND m.status = 'FT'
        """)
        
        result = self.db.execute(query, {"league_id": league_id, "season": season}).fetchone()
        
        if not result or result.matches_count == 0:
            return {
                'avg_home_goals': 1.5,
                'avg_away_goals': 1.2,
                'avg_total_goals': 2.7,
                'matches': 0
            }
        
        league_stats = {
            'avg_home_goals': float(result.avg_home_goals) if result.avg_home_goals else 1.5,
            'avg_away_goals': float(result.avg_away_goals) if result.avg_away_goals else 1.2,
            'avg_total_goals': float(result.avg_total_goals) if result.avg_total_goals else 2.7,
            'matches': result.matches_count
        }
        
        self.league_stats[(league_id, season)] = league_stats
        return league_stats

    def calculate_team_strengths(self, league_id: int, season: str = "2024") -> Dict:
        """
        Calculate attack and defense strengths for each team
        Attack Strength = Team's avg goals scored / League avg goals scored
        Defense Strength = Team's avg goals conceded / League avg goals conceded
        """
        league_avg = self.calculate_league_averages(league_id, season)
        
        # Home stats
        home_query = text("""
        SELECT 
            t.id as team_id,
            t.name as team_name,
            AVG(m.home_score) as avg_goals_for,
            AVG(m.away_score) as avg_goals_against,
            COUNT(*) as matches_played
        FROM matches m
        JOIN teams t ON m.home_team_id = t.id
        WHERE m.league_id = :league_id
        AND m.season = :season
        AND m.home_score IS NOT NULL
        AND m.away_score IS NOT NULL
        AND m.status = 'FT'
        GROUP BY t.id, t.name
        """)
        
        home_stats = self.db.execute(home_query, {"league_id": league_id, "season": season}).fetchall()
        
        # Away stats
        away_query = text("""
        SELECT 
            t.id as team_id,
            t.name as team_name,
            AVG(m.away_score) as avg_goals_for,
            AVG(m.home_score) as avg_goals_against,
            COUNT(*) as matches_played
        FROM matches m
        JOIN teams t ON m.away_team_id = t.id
        WHERE m.league_id = :league_id
        AND m.season = :season
        AND m.home_score IS NOT NULL
        AND m.away_score IS NOT NULL
        AND m.status = 'FT'
        GROUP BY t.id, t.name
        """)
        
        away_stats = self.db.execute(away_query, {"league_id": league_id, "season": season}).fetchall()
        
        # Build team strengths dictionary
        team_strengths = {}
        
        # Process home stats
        for row in home_stats:
            team_id = row.team_id
            avg_goals_for = float(row.avg_goals_for) if row.avg_goals_for else 0.0
            avg_goals_against = float(row.avg_goals_against) if row.avg_goals_against else 0.0
            
            attack_strength = avg_goals_for / float(league_avg['avg_home_goals']) if league_avg['avg_home_goals'] > 0 else 1.0
            defense_strength = avg_goals_against / float(league_avg['avg_away_goals']) if league_avg['avg_away_goals'] > 0 else 1.0
            
            team_strengths[team_id] = {
                'home_attack': attack_strength,
                'home_defense': defense_strength,
                'home_matches': row.matches_played,
                'home_avg_for': avg_goals_for,
                'home_avg_against': avg_goals_against
            }
        
        # Process away stats
        for row in away_stats:
            team_id = row.team_id
            if team_id in team_strengths:
                avg_goals_for = float(row.avg_goals_for) if row.avg_goals_for else 0.0
                avg_goals_against = float(row.avg_goals_against) if row.avg_goals_against else 0.0
                
                attack_strength = avg_goals_for / float(league_avg['avg_away_goals']) if league_avg['avg_away_goals'] > 0 else 1.0
                defense_strength = avg_goals_against / float(league_avg['avg_home_goals']) if league_avg['avg_home_goals'] > 0 else 1.0
                
                team_strengths[team_id]['away_attack'] = attack_strength
                team_strengths[team_id]['away_defense'] = defense_strength
                team_strengths[team_id]['away_matches'] = row.matches_played
                team_strengths[team_id]['away_avg_for'] = avg_goals_for
                team_strengths[team_id]['away_avg_against'] = avg_goals_against
        
        self.team_stats[(league_id, season)] = team_strengths
        return team_strengths

    def predict_match(
        self, 
        home_team_id: int, 
        away_team_id: int,
        league_id: int,
        season: str = "2024",
        apply_dixon_coles: bool = True
    ) -> Dict:
        """
        Predict match probabilities using Poisson distribution
        Returns: Dict with probabilities and expected goals
        """
        # Get team strengths
        team_strengths = self.calculate_team_strengths(league_id, season)
        league_avg = self.calculate_league_averages(league_id, season)
        
        # Get specific team data
        home_data = team_strengths.get(home_team_id, {})
        away_data = team_strengths.get(away_team_id, {})
        
        # Calculate expected goals
        expected_home_goals = (
            league_avg['avg_home_goals'] * 
            home_data.get('home_attack', 1.0) * 
            away_data.get('away_defense', 1.0)
        )
        
        expected_away_goals = (
            league_avg['avg_away_goals'] * 
            away_data.get('away_attack', 1.0) * 
            home_data.get('home_defense', 1.0)
        )
        
        # Apply Dixon-Coles correction for draws
        if apply_dixon_coles:
            expected_home_goals, expected_away_goals = self.apply_dixon_coles(
                expected_home_goals, 
                expected_away_goals
            )
        
        # Generate score probability matrix
        score_matrix = self.generate_score_matrix(
            expected_home_goals, 
            expected_away_goals,
            max_goals=6
        )
        
        # Calculate match result probabilities
        home_prob = 0.0
        draw_prob = 0.0
        away_prob = 0.0
        over_25_prob = 0.0
        
        for i in range(len(score_matrix)):
            for j in range(len(score_matrix[i])):
                prob = score_matrix[i][j]
                
                if i > j:
                    home_prob += prob
                elif i < j:
                    away_prob += prob
                else:
                    draw_prob += prob
                
                if i + j > 2.5:
                    over_25_prob += prob
        
        # Get most likely scores
        most_likely_scores = self.get_most_likely_scores(score_matrix, top_n=5)
        
        return {
            'home_team_id': home_team_id,
            'away_team_id': away_team_id,
            'league_id': league_id,
            'expected_home_goals': expected_home_goals,
            'expected_away_goals': expected_away_goals,
            'home_win': home_prob,
            'draw': draw_prob,
            'away_win': away_prob,
            'over_25': over_25_prob,
            'under_25': 1 - over_25_prob,
            'score_matrix': score_matrix.tolist(),
            'most_likely_scores': most_likely_scores,
            'confidence_score': max(home_prob, draw_prob, away_prob)
        }

    def generate_score_matrix(self, lambda_home: float, lambda_away: float, max_goals: int = 6) -> np.ndarray:
        """Generate probability matrix for all scorelines up to max_goals"""
        matrix = np.zeros((max_goals + 1, max_goals + 1))
        
        # Calculate Poisson probabilities for each goal count
        home_probs = stats.poisson.pmf(range(max_goals + 1), max(0.01, lambda_home))
        away_probs = stats.poisson.pmf(range(max_goals + 1), max(0.01, lambda_away))
        
        # Fill the matrix
        for i in range(max_goals + 1):
            for j in range(max_goals + 1):
                matrix[i][j] = home_probs[i] * away_probs[j]
        
        # Normalize (ensure sum to 1)
        matrix_sum = matrix.sum()
        if matrix_sum > 0:
            matrix = matrix / matrix_sum
        
        return matrix

    def apply_dixon_coles(self, lambda_home: float, lambda_away: float) -> Tuple[float, float]:
        """
        Apply Dixon-Coles correction factor for low-scoring draws
        """
        if lambda_home < 1.2 and lambda_away < 1.2:
            reduction_factor = 1 - (self.dixon_coles_tau * 0.5)
            return max(0.01, lambda_home * reduction_factor), max(0.01, lambda_away * reduction_factor)
        elif lambda_home < 1.5 and lambda_away < 1.5:
            reduction_factor = 1 - (self.dixon_coles_tau * 0.3)
            return max(0.01, lambda_home * reduction_factor), max(0.01, lambda_away * reduction_factor)
        
        return max(0.01, lambda_home), max(0.01, lambda_away)

    def get_most_likely_scores(self, score_matrix: np.ndarray, top_n: int = 5) -> List[Tuple]:
        """Get the most likely exact scores"""
        scores = []
        for i in range(score_matrix.shape[0]):
            for j in range(score_matrix.shape[1]):
                prob = float(score_matrix[i][j])
                if prob > 0.001:
                    scores.append((f"{i}-{j}", prob))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_n]

    def optimize_dixon_coles_tau(self, league_id: int, season: str = "2024") -> float:
        """
        Optimize tau parameter using historical data
        """
        from scipy.optimize import minimize_scalar
        
        def objective(tau):
            self.dixon_coles_tau = tau
            brier_scores = []
            
            query = text("""
            SELECT 
                m.id, m.home_team_id, m.away_team_id,
                m.home_score, m.away_score
            FROM matches m
            WHERE m.league_id = :league_id
            AND m.season = :season
            AND m.home_score IS NOT NULL
            AND m.away_score IS NOT NULL
            AND m.status = 'FT'
            LIMIT 100
            """)
            
            matches = self.db.execute(query, {"league_id": league_id, "season": season}).fetchall()
            
            if len(matches) < 10:
                return 0.05
            
            for match in matches:
                pred = self.predict_match(
                    match.home_team_id,
                    match.away_team_id,
                    league_id,
                    season,
                    apply_dixon_coles=True
                )
                
                actual = self.one_hot_result(match.home_score, match.away_score)
                pred_probs = [pred['home_win'], pred['draw'], pred['away_win']]
                
                brier = np.mean((np.array(pred_probs) - np.array(actual)) ** 2)
                brier_scores.append(brier)
            
            return np.mean(brier_scores) if brier_scores else 0.05
        
        result = minimize_scalar(objective, bounds=(0, 0.2), method='bounded')
        self.dixon_coles_tau = result.x
        logger.info(f"Optimized Dixon-Coles tau: {self.dixon_coles_tau:.4f}")
        return self.dixon_coles_tau

    def one_hot_result(self, home_goals: int, away_goals: int) -> List[int]:
        """Convert actual result to one-hot encoding"""
        if home_goals > away_goals:
            return [1, 0, 0]
        elif home_goals < away_goals:
            return [0, 0, 1]
        else:
            return [0, 1, 0]

    def close(self):
        """Close database connection"""
        self.db.close()
        