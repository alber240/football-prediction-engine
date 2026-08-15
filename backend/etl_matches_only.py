import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.api_football import APIFootballService
from app.models import League, Team, Match, get_db, engine, Base
from datetime import datetime
import time

print("=" * 60)
print("ETL PIPELINE - FETCHING MATCHES ONLY")
print("=" * 60)

service = APIFootballService()
db = next(get_db())

# Get all leagues
leagues = db.query(League).all()
print(f"\nProcessing {len(leagues)} leagues...")

total_match_count = 0

# Process each league
for league in leagues:
    print(f"\n?? {league.name} (ID: {league.api_id})")
    
    # Get teams for this league
    teams = {t.api_id: t for t in db.query(Team).filter_by(league_id=league.id).all()}
    print(f"   Teams in DB: {len(teams)}")
    
    # Fetch matches from API
    matches_data = service.fetch_matches(league.api_id, "2024")
    print(f"   Matches from API: {len(matches_data)}")
    
    match_count = 0
    for match_data in matches_data:
        fixture = match_data.get("fixture", {})
        teams_data = match_data.get("teams", {})
        goals = match_data.get("goals", {})
        
        # Check if match already exists
        existing = db.query(Match).filter_by(api_id=fixture.get("id")).first()
        if existing:
            continue
            
        # Find teams
        home_api_id = teams_data.get("home", {}).get("id")
        away_api_id = teams_data.get("away", {}).get("id")
        
        home_team = teams.get(home_api_id)
        away_team = teams.get(away_api_id)
        
        if home_team and away_team:
            try:
                match_date = datetime.strptime(fixture.get("date", ""), "%Y-%m-%dT%H:%M:%S+00:00")
            except:
                match_date = datetime.utcnow()
                
            home_score = goals.get("home")
            away_score = goals.get("away")
            
            if home_score is not None and away_score is not None:
                if home_score > away_score:
                    result = "H"
                elif home_score < away_score:
                    result = "A"
                else:
                    result = "D"
            else:
                result = None
                
            match = Match(
                api_id=fixture.get("id"),
                league_id=league.id,
                home_team_id=home_team.id,
                away_team_id=away_team.id,
                match_date=match_date,
                season="2024",
                round=fixture.get("round", ""),
                venue=fixture.get("venue", {}).get("name", ""),
                status=fixture.get("status", {}).get("short", "NS"),
                home_score=home_score,
                away_score=away_score,
                result=result
            )
            db.add(match)
            match_count += 1
            total_match_count += 1
        else:
            if not home_team:
                print(f"      ??  Home team not found: {teams_data.get('home', {}).get('name')} (api_id: {home_api_id})")
            if not away_team:
                print(f"      ??  Away team not found: {teams_data.get('away', {}).get('name')} (api_id: {away_api_id})")
    
    db.commit()
    print(f"   ? Saved {match_count} new matches for {league.name}")

print("\n" + "=" * 60)
print("? ETL COMPLETE!")
print("=" * 60)
print(f"   Leagues: {db.query(League).count()}")
print(f"   Teams: {db.query(Team).count()}")
print(f"   Matches: {db.query(Match).count()}")

# Show sample matches
if db.query(Match).count() > 0:
    print("\n?? Sample Matches:")
    matches = db.query(Match).limit(5).all()
    for m in matches:
        home = db.query(Team).filter_by(id=m.home_team_id).first()
        away = db.query(Team).filter_by(id=m.away_team_id).first()
        print(f"   {home.name if home else 'Unknown'} vs {away.name if away else 'Unknown'} - {m.home_score}:{m.away_score} ({m.status})")
