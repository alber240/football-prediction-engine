from app.prediction_engine import PredictionEngine

print('Testing Prediction Engine...')
engine = PredictionEngine()

print('Predicting match ID 1...')
try:
    result = engine.predict_match(1)
    print('Success!')
    print(f"Home: {result.get('home_team_name')}")
    print(f"Away: {result.get('away_team_name')}")
    print(f"Home Win: {result.get('home_win', 0)*100:.1f}%")
    print(f"Draw: {result.get('draw', 0)*100:.1f}%")
    print(f"Away Win: {result.get('away_win', 0)*100:.1f}%")
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()

engine.close()
