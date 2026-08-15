"""
Fetch UCL matches from API
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.api_football import APIFootballService
from app.models import get_db, League, Match, Team
from datetime import datetime
import time

print("=" * 60)
print("📊 FETCHING UCL MATCHES")
print("=" * 60)

api = APIFootballService()
db = next(get_db())

# Get UCL league
ucl = db.query(League).filter_by(id=6).first()
if not ucl:
    print("❌ UCL league not found!")
    exit()

print(f"UCL League ID: {ucl.id}, API ID: {ucl.api_id}")

# Fetch UCL matches for recent seasons
seasons = ['2024', '2023', '2022', '2021']
total = 0

for season in seasons:
    print(f"\n📅 Fetching season {season}...")
    matches = api.fetch_matches(2, season)
    print(f"   Found {len(matches)} matches")
    total += len(matches)
    
    # Show sample
    for match_data in matches[:3]:
        fixture = match_data.get('fixture', {})
        teams = match_data.get('teams', {})
        home_name = teams.get('home', {}).get('name', 'Unknown')
        away_name = teams.get('away', {}).get('name', 'Unknown')
        print(f"      {home_name} vs {away_name}")
    
    time.sleep(0.5)

print(f"\n✅ Total UCL matches found: {total}")