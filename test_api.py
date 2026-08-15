import requests
import json

print('Testing API endpoints...')
base_url = 'http://127.0.0.1:8000'

# Test health
try:
    response = requests.get(f'{base_url}/health', timeout=5)
    print(f'Health: {response.status_code} - {response.json()}')
except Exception as e:
    print(f'Health error: {e}')

# Test root
try:
    response = requests.get(f'{base_url}/', timeout=5)
    print(f'Root: {response.status_code} - {response.json()}')
except Exception as e:
    print(f'Root error: {e}')

# Test prediction
try:
    response = requests.get(f'{base_url}/api/predictions/match/1', timeout=10)
    if response.status_code == 200:
        data = response.json()
        print(f'Match Prediction: {data.get("home_team")} vs {data.get("away_team")}')
        print(f'   Home Win: {data.get("home_win", 0)*100:.1f}%')
        print(f'   Draw: {data.get("draw", 0)*100:.1f}%')
        print(f'   Away Win: {data.get("away_win", 0)*100:.1f}%')
    else:
        print(f'Prediction error: {response.status_code}')
except Exception as e:
    print(f'Prediction error: {e}')
