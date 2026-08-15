from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from app.api.prediction_routes import router as prediction_router
from app.websocket.live_updates import websocket_endpoint
import logging

logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Football Prediction Engine",
    description="Meta-prediction platform for Top 5 European Leagues + UCL",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(prediction_router)

@app.websocket("/ws/live")
async def websocket_live(websocket: WebSocket):
    await websocket_endpoint(websocket)

@app.get("/")
async def root():
    return {
        "message": "AI Football Prediction Engine API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "/api/predictions/match/{match_id}": "Get prediction for a match",
            "/api/predictions/upcoming": "Get predictions for upcoming matches",
            "/api/predictions/league/{league_id}": "Get predictions for a league",
            "/api/predictions/analysis/{match_id}": "Get detailed match analysis",
            "/ws/live": "WebSocket for live match updates"
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}