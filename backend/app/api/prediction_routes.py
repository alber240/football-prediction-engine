"""
Prediction API Routes
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel
from app.prediction_engine import PredictionEngine
from app.models import get_db, League, Team, Match
from datetime import datetime

router = APIRouter(prefix="/api/predictions", tags=["predictions"])

class ScoreProbability(BaseModel):
    score: str
    probability: float

class MatchPredictionResponse(BaseModel):
    match_id: int
    home_team: str
    away_team: str
    league: str
    expected_home_goals: float
    expected_away_goals: float
    home_win: float
    draw: float
    away_win: float
    over_25: float
    under_25: float
    most_likely_scores: List[ScoreProbability]
    confidence_score: float
    prediction_time: datetime

@router.get("/match/{match_id}")
async def predict_match(match_id: int):
    engine = PredictionEngine()
    try:
        prediction = engine.predict_match(match_id)
        engine.close()
        
        if 'error' in prediction:
            raise HTTPException(status_code=404, detail=prediction['error'])
        
        return MatchPredictionResponse(
            match_id=prediction['match_id'],
            home_team=prediction.get('home_team_name', 'Unknown'),
            away_team=prediction.get('away_team_name', 'Unknown'),
            league=prediction.get('league_name', 'Unknown'),
            expected_home_goals=round(prediction['expected_home_goals'], 3),
            expected_away_goals=round(prediction['expected_away_goals'], 3),
            home_win=round(prediction['home_win'], 4),
            draw=round(prediction['draw'], 4),
            away_win=round(prediction['away_win'], 4),
            over_25=round(prediction['over_25'], 4),
            under_25=round(prediction['under_25'], 4),
            most_likely_scores=[
                ScoreProbability(score=s[0], probability=round(s[1], 4)) 
                for s in prediction.get('most_likely_scores', [])
            ],
            confidence_score=round(prediction['confidence_score'], 4),
            prediction_time=datetime.utcnow()
        )
    except Exception as e:
        engine.close()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/upcoming")
async def predict_upcoming_matches(
    league_id: Optional[int] = None,
    limit: int = Query(default=20, le=100)
):
    engine = PredictionEngine()
    try:
        predictions = engine.predict_upcoming_matches(league_id)
        engine.close()
        
        results = []
        for pred in predictions[:limit]:
            results.append({
                'match_id': pred.get('match_id'),
                'home_team': pred.get('home_team_name', 'Unknown'),
                'away_team': pred.get('away_team_name', 'Unknown'),
                'league': pred.get('league_name', 'Unknown'),
                'home_win': round(pred.get('home_win', 0), 4),
                'draw': round(pred.get('draw', 0), 4),
                'away_win': round(pred.get('away_win', 0), 4),
                'over_25': round(pred.get('over_25', 0), 4),
                'under_25': round(pred.get('under_25', 0), 4),
                'confidence_score': round(pred.get('confidence_score', 0), 4)
            })
        
        return {
            'total': len(results),
            'predictions': results
        }
    except Exception as e:
        engine.close()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/league/{league_id}")
async def predict_league_matches(league_id: int):
    engine = PredictionEngine()
    try:
        db = next(get_db())
        league = db.query(League).filter_by(id=league_id).first()
        if not league:
            raise HTTPException(status_code=404, detail="League not found")
        
        predictions = engine.predict_upcoming_matches(league_id)
        engine.close()
        
        return {
            'league': league.name,
            'total_matches': len(predictions),
            'predictions': predictions
        }
    except Exception as e:
        engine.close()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis/{match_id}")
async def get_match_analysis(match_id: int):
    """Get detailed match analysis with AI reasoning"""
    from app.analysis_generator import AnalysisGenerator
    try:
        gen = AnalysisGenerator()
        analysis = gen.generate_analysis(match_id)
        if 'error' in analysis:
            raise HTTPException(status_code=404, detail=analysis['error'])
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
