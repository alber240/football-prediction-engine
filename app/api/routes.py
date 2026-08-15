from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="AI Football Prediction Engine",
    description="Meta-prediction platform for Top 5 European Leagues + UCL",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "AI Football Prediction Engine API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/api/matches")
async def get_matches():
    return {"message": "Matches endpoint coming soon"}

@app.get("/api/predictions")
async def get_predictions():
    return {"message": "Predictions endpoint coming soon"}
