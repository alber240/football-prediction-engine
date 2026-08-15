from app.services.api_football import APIFootballService

print("=" * 60)
print("TESTING API CONNECTION")
print("=" * 60)

service = APIFootballService()

print("\n1. Fetching Leagues...")
leagues = service.fetch_leagues()
if leagues:
    print(f"   Found {len(leagues)} leagues:")
    for league in leagues:
        name = league.get("league", {}).get("name", "Unknown")
        country = league.get("country", {}).get("name", "Unknown")
        print(f"      - {name} ({country})")
else:
    print("   No leagues found")

print("\n2. Fetching Premier League Teams...")
teams = service.fetch_teams(39, "2024")
if teams:
    print(f"   Found {len(teams)} teams:")
    for team in teams[:10]:
        name = team.get("team", {}).get("name", "Unknown")
        print(f"      - {name}")
else:
    print("   No teams found (try season 2023)")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
