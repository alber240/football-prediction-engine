import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.api_football import APIFootballService
from app.models import League, Team, Match, get_db, engine, Base
from datetime import datetime
import time

print("=" * 60)
print("ETL PIPELINE - FETCHING DATA")
print("=" * 60)

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

service = APIFootballService()
db = next(get_db())

# 1. Fetch and save leagues (skip if already exist)
print("\n1. Fetching Leagues...")
leagues_data = service.fetch_leagues()
league_count = 0
for league_data in leagues_data:
    league_info = league_data.get("league", {})
    existing = db.query(League).filter_by(api_id=league_info.get("id")).first()
    if not existing:
        league = League(
            api_id=league_info.get("id"),
            name=league_info.get("name"),
            country=league_data.get("country", {}).get("name", "Unknown"),
            is_active=True
        )
        db.add(league)
        league_count += 1
db.commit()
print(f"   ? Added {league_count} new leagues, {len(leagues_data) - league_count} already exist")

# 2. Fetch and save teams for each league
print("\n2. Fetching Teams...")
total_team_count = 0
for league in db.query(League).all():
    print(f"   Fetching teams for {league.name}...")
    teams_data = service.fetch_teams(league.api_id, "2024")
    team_count = 0
    for team_data in teams_data:
        team_info = team_data.get("team", {})
        existing = db.query(Team).filter_by(api_id=team_info.get("id")).first()
        if not existing:
            team = Team(
                api_id=team_info.get("id"),
                league_id=league.id,
                name=team_info.get("name"),
                short_name=team_info.get("code"),
                elo_rating=1500.00
            )
            db.add(team)
            team_count += 1
            total_team_count += 1
    db.commit()
    print(f"      ? Added {team_count} new teams for {league.name}")

# 3. Fetch matches for each league
print("\n3. Fetching Matches...")
total_match_count = 0
for league in db.query(League).all():
    print(f"   Fetching matches for {league.name}...")
    matches_data = service.fetch_matches(league.api_id, "2024")
    match_count = 0
    for match_data in matches_data:
        fixture = match_data.get("fixture", {})
        teams = match_data.get("teams", {})
        goals = match_data.get("goals", {})
        
        # Check if match already exists
        existing = db.query(Match).filter_by(api_id=fixture.get("id")).first()
        if existing:
            continue
            
        # Find team IDs
        home_team = db.query(Team).filter_by(api_id=teams.get("home", {}).get("id")).first()
        away_team = db.query(Team).filter_by(api_id=teams.get("away", {}).get("id")).first()
        
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
    db.commit()
    print(f"      ? Added {match_count} new matches for {league.name}")

print("\n" + "=" * 60)
print("? ETL COMPLETE!")
print("=" * 60)
print(f"   Leagues: {db.query(League).count()}")
print(f"   Teams: {db.query(Team).count()}")
print(f"   Matches: {db.query(Match).count()}")

# Show sample matches
print("\n?? Sample Matches:")
matches = db.query(Match).limit(5).all()
for m in matches:
    home = db.query(Team).filter_by(id=m.home_team_id).first()
    away = db.query(Team).filter_by(id=m.away_team_id).first()
    print(f"   {home.name if home else 'Unknown'} vs {away.name if away else 'Unknown'} - {m.home_score}:{m.away_score} ({m.status})")
