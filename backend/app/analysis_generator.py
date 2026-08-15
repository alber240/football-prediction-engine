"""
AI Reasoning Engine - Generates human-readable match analysis
"""

from app.form_analysis import FormAnalyzer
from app.h2h_analysis import H2HAnalyzer
from app.injury_tracker import InjuryTracker
from app.elo_model import EloRatingSystem
from app.models import get_db, Team, Match
import logging

logger = logging.getLogger(__name__)

class AnalysisGenerator:
    def __init__(self):
        self.db = next(get_db())
        self.form_analyzer = FormAnalyzer()
        self.h2h_analyzer = H2HAnalyzer()
        self.injury_tracker = InjuryTracker()
        self.elo_system = EloRatingSystem()
        
    def generate_analysis(self, match_id: int) -> dict:
        match = self.db.query(Match).filter_by(id=match_id).first()
        if not match:
            return {'error': 'Match not found'}
        
        home_team = self.db.query(Team).filter_by(id=match.home_team_id).first()
        away_team = self.db.query(Team).filter_by(id=match.away_team_id).first()
        
        home_elo = self.elo_system.get_team_elo(home_team.id)
        away_elo = self.elo_system.get_team_elo(away_team.id)
        
        home_form = self.form_analyzer.get_form(home_team.id)
        away_form = self.form_analyzer.get_form(away_team.id)
        
        h2h_summary = self.h2h_analyzer.get_h2h_summary(home_team.id, away_team.id)
        
        home_injuries = self.injury_tracker.get_team_availability(home_team.id)
        away_injuries = self.injury_tracker.get_team_availability(away_team.id)
        
        analysis = {
            'match_info': {
                'home_team': home_team.name,
                'away_team': away_team.name,
                'match_id': match_id,
                'venue': match.venue or 'Unknown'
            },
            'factors': {
                'elo': self._analyze_elo(home_elo, away_elo, home_team.name, away_team.name),
                'form': self._analyze_form(home_form, away_form, home_team.name, away_team.name),
                'h2h': self._analyze_h2h(h2h_summary, home_team.name, away_team.name),
                'injuries': self._analyze_injuries(home_injuries, away_injuries, home_team.name, away_team.name)
            },
            'summary': self._generate_summary(home_team.name, away_team.name, h2h_summary, home_injuries, away_injuries),
            'key_battles': self._generate_key_battles(home_team.name, away_team.name),
            'prediction_text': self._generate_prediction_text(home_team.name, away_team.name, h2h_summary),
            'betting_insight': self._generate_betting_insight(home_team.name, away_team.name)
        }
        
        return analysis
    
    def _analyze_elo(self, home_elo, away_elo, home_name, away_name) -> dict:
        diff = home_elo - away_elo
        advantage = 'home' if diff > 0 else 'away'
        return {
            'home_elo': round(home_elo, 1),
            'away_elo': round(away_elo, 1),
            'difference': round(diff, 1),
            'advantage': advantage,
            'text': f"{home_name} ({round(home_elo, 1)}) vs {away_name} ({round(away_elo, 1)})"
        }
    
    def _analyze_form(self, home_form, away_form, home_name, away_name) -> dict:
        return {
            'home_form': home_form['form_score'],
            'away_form': away_form['form_score'],
            'home_streak': home_form['streak'],
            'away_streak': away_form['streak'],
            'advantage': 'home' if home_form['form_score'] > away_form['form_score'] else 'away',
            'text': f"{home_name} form: {home_form['streak']}, {away_name} form: {away_form['streak']}"
        }
    
    def _analyze_h2h(self, h2h_summary, home_name, away_name) -> dict:
        return {
            'advantage': h2h_summary['advantage'],
            'summary': h2h_summary['summary']
        }
    
    def _analyze_injuries(self, home_injuries, away_injuries, home_name, away_name) -> dict:
        return {
            'home_availability': home_injuries['availability_score'],
            'away_availability': away_injuries['availability_score'],
            'home_missing': home_injuries['missing_players'],
            'away_missing': away_injuries['missing_players'],
            'advantage': 'home' if home_injuries['availability_score'] > away_injuries['availability_score'] else 'away',
            'text': f"{home_name} availability: {home_injuries['availability_score']}%, {away_name} availability: {away_injuries['availability_score']}%"
        }
    
    def _generate_summary(self, home_name, away_name, h2h, home_injuries, away_injuries) -> str:
        parts = []
        if h2h['advantage'] == 'home':
            parts.append(f"{home_name} has historically dominated this fixture")
        elif h2h['advantage'] == 'away':
            parts.append(f"{away_name} has historically dominated this fixture")
        else:
            parts.append("This fixture has been evenly contested historically")
        
        if home_injuries['availability_score'] < 80:
            parts.append(f"{home_name} has key players missing")
        if away_injuries['availability_score'] < 80:
            parts.append(f"{away_name} has key players missing")
        
        return ". ".join(parts) if parts else "No clear advantage"
    
    def _generate_key_battles(self, home_name, away_name) -> list:
        return [
            f"{home_name}'s attack vs {away_name}'s defense",
            f"{away_name}'s counter-attacks vs {home_name}'s defensive shape",
            "Midfield battle: control of possession"
        ]
    
    def _generate_prediction_text(self, home_name, away_name, h2h) -> str:
        if h2h['advantage'] == 'home':
            return f"{home_name} have historically dominated this fixture and should be favorites"
        elif h2h['advantage'] == 'away':
            return f"{away_name} have historically dominated this fixture and should be favorites"
        else:
            return "This is an evenly matched fixture with no clear historical advantage"
    
    def _generate_betting_insight(self, home_name, away_name) -> str:
        return f"Value bet: Consider both teams to score"
