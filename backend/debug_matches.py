from app.services.api_football import APIFootballService
from app.models import League, Team, get_db

service = APIFootballService()
db = next(get_db())

# Check Premier League teams
premier_league = db.query(League).filter_by(name="Premier League").first()
if premier_league:
    print(f"Premier League ID: {premier_league.id}")
    teams = db.query(Team).filter_by(league_id=premier_league.id).all()
    print(f"Teams in DB: {len(teams)}")
    for team in teams[:5]:
        print(f"   {team.name} (api_id: {team.api_id})")

# Fetch matches from API
print("\nFetching matches from API...")
matches = service.fetch_matches(39, "2024")
print(f"Matches from API: {len(matches)}")

if matches:
    for match in matches[:3]:
        fixture = match.get('fixture', {})
        teams_data = match.get('teams', {})
        home = teams_data.get('home', {}).get('name', 'Unknown')
        away = teams_data.get('away', {}).get('name', 'Unknown')
        print(f"   {home} vs {away} (api_id: {fixture.get('id')})")
