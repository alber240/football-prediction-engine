from app.services.api_football import APIFootballService
from app.models import League, Team, Match, get_db
from datetime import datetime

service = APIFootballService()
db = next(get_db())

# Get Premier League
premier_league = db.query(League).filter_by(name="Premier League").first()
print(f"Premier League ID: {premier_league.id}")

# Get a sample match from API
matches = service.fetch_matches(39, "2024")
print(f"API returned {len(matches)} matches")

# Try to save the first match
if matches:
    match_data = matches[0]
    fixture = match_data.get('fixture', {})
    teams_data = match_data.get('teams', {})
    goals = match_data.get('goals', {})
    
    print(f"\nMatch API ID: {fixture.get('id')}")
    print(f"Home team: {teams_data.get('home', {}).get('name')} (api_id: {teams_data.get('home', {}).get('id')})")
    print(f"Away team: {teams_data.get('away', {}).get('name')} (api_id: {teams_data.get('away', {}).get('id')})")
    
    # Find teams in database
    home_team = db.query(Team).filter_by(api_id=teams_data.get('home', {}).get('id')).first()
    away_team = db.query(Team).filter_by(api_id=teams_data.get('away', {}).get('id')).first()
    
    print(f"\nHome team in DB: {home_team.name if home_team else 'NOT FOUND'}")
    print(f"Away team in DB: {away_team.name if away_team else 'NOT FOUND'}")
    
    # Check if match already exists
    existing = db.query(Match).filter_by(api_id=fixture.get('id')).first()
    print(f"Match already exists: {existing is not None}")
