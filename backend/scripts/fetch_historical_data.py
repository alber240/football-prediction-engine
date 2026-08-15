"""
PHASE 1: Data Re-fetch Script
Fetches all historical match data from 2020-2021 to 2025-2026
For Top 5 European Leagues + UEFA Champions League
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.api_football import APIFootballService
from app.models import get_db, League, Team, Match
from datetime import datetime, timedelta
import time
import logging
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# League IDs
LEAGUES = {
    'premier_league': {'id': 39, 'name': 'Premier League'},
    'la_liga': {'id': 140, 'name': 'La Liga'},
    'bundesliga': {'id': 78, 'name': 'Bundesliga'},
    'serie_a': {'id': 135, 'name': 'Serie A'},
    'ligue_1': {'id': 61, 'name': 'Ligue 1'},
    'ucl': {'id': 2, 'name': 'UEFA Champions League'}
}

# Seasons to fetch (5 full seasons + current)
SEASONS = ['2020', '2021', '2022', '2023', '2024', '2025']

class DataRefetcher:
    def __init__(self):
        self.api = APIFootballService()
        self.db = next(get_db())
        self.stats = {
            'leagues': 0,
            'teams': 0,
            'matches': 0,
            'errors': 0
        }
    
    def clear_existing_data(self):
        """Clear existing data for a clean refetch"""
        logger.info("🗑️  Clearing existing data...")
        try:
            # Delete in correct order (foreign key constraints)
            self.db.execute(text("DELETE FROM our_predictions"))
            self.db.execute(text("DELETE FROM external_predictions"))
            self.db.execute(text("DELETE FROM team_stats"))
            self.db.execute(text("DELETE FROM matches"))
            self.db.execute(text("DELETE FROM teams"))
            self.db.execute(text("DELETE FROM leagues"))
            self.db.commit()
            logger.info("✅ Data cleared successfully")
        except Exception as e:
            logger.error(f"❌ Error clearing data: {e}")
            self.db.rollback()
    
    def fetch_leagues(self):
        """Fetch all leagues from API"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 FETCHING LEAGUES")
        logger.info("=" * 60)
        
        for key, league_info in LEAGUES.items():
            try:
                # Check if league already exists
                existing = self.db.query(League).filter_by(api_id=league_info['id']).first()
                if existing:
                    logger.info(f"   ⏭️  League already exists: {league_info['name']}")
                    continue
                
                # Fetch from API
                leagues_data = self.api.fetch_leagues()
                for league_data in leagues_data:
                    if league_data.get('league', {}).get('id') == league_info['id']:
                        league = League(
                            api_id=league_info['id'],
                            name=league_info['name'],
                            country=league_data.get('country', {}).get('name', 'Unknown'),
                            is_active=True
                        )
                        self.db.add(league)
                        self.db.commit()
                        logger.info(f"   ✅ Added league: {league_info['name']}")
                        self.stats['leagues'] += 1
                        break
            except Exception as e:
                logger.error(f"   ❌ Error fetching {league_info['name']}: {e}")
                self.stats['errors'] += 1
    
    def fetch_teams(self):
        """Fetch all teams for each league"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 FETCHING TEAMS")
        logger.info("=" * 60)
        
        leagues = self.db.query(League).all()
        
        for league in leagues:
            logger.info(f"\n   📌 {league.name}")
            
            # Try different seasons
            for season in SEASONS:
                try:
                    teams_data = self.api.fetch_teams(league.api_id, season)
                    if teams_data:
                        for team_data in teams_data:
                            team_info = team_data.get('team', {})
                            existing = self.db.query(Team).filter_by(api_id=team_info.get('id')).first()
                            if not existing:
                                team = Team(
                                    api_id=team_info.get('id'),
                                    league_id=league.id,
                                    name=team_info.get('name', 'Unknown'),
                                    short_name=team_info.get('code'),
                                    elo_rating=1500.00
                                )
                                self.db.add(team)
                                self.stats['teams'] += 1
                        self.db.commit()
                        logger.info(f"      ✅ Added {len(teams_data)} teams for {league.name}")
                        break
                except Exception as e:
                    logger.error(f"      ❌ Error fetching teams for {league.name} ({season}): {e}")
                    continue
    
    def fetch_matches_for_league(self, league_id: int, league_name: str, season: str):
        """Fetch matches for a specific league and season"""
        logger.info(f"      📅 Season {season}...")
        
        try:
            matches_data = self.api.fetch_matches(league_id, season)
            
            if not matches_data:
                logger.info(f"         ⚠️  No matches found for {league_name} {season}")
                return 0
            
            match_count = 0
            for match_data in matches_data:
                fixture = match_data.get('fixture', {})
                teams = match_data.get('teams', {})
                goals = match_data.get('goals', {})
                
                # Check if match already exists
                existing = self.db.query(Match).filter_by(api_id=fixture.get('id')).first()
                if existing:
                    continue
                
                # Find teams
                home_team = self.db.query(Team).filter_by(api_id=teams.get('home', {}).get('id')).first()
                away_team = self.db.query(Team).filter_by(api_id=teams.get('away', {}).get('id')).first()
                
                if not home_team or not away_team:
                    continue
                
                # Parse date
                try:
                    match_date = datetime.strptime(fixture.get('date', ''), "%Y-%m-%dT%H:%M:%S+00:00")
                except:
                    match_date = datetime.utcnow()
                
                # Determine result
                home_score = goals.get('home')
                away_score = goals.get('away')
                if home_score is not None and away_score is not None:
                    if home_score > away_score:
                        result = "H"
                    elif home_score < away_score:
                        result = "A"
                    else:
                        result = "D"
                else:
                    result = None
                
                # Get round/group information
                round_info = fixture.get('round', '')
                # For UCL, extract group stage info
                if league_name == 'UEFA Champions League' and 'Group' in round_info:
                    group = round_info.replace('Group Stage - ', '')
                
                match = Match(
                    api_id=fixture.get('id'),
                    league_id=league_id,
                    home_team_id=home_team.id,
                    away_team_id=away_team.id,
                    match_date=match_date,
                    season=season,
                    round=round_info,
                    venue=fixture.get('venue', {}).get('name', ''),
                    status=fixture.get('status', {}).get('short', 'NS'),
                    home_score=home_score,
                    away_score=away_score,
                    result=result,
                    is_derby=False,  # Will be calculated later
                    is_midweek=match_date.weekday() not in [5, 6]  # Not weekend
                )
                self.db.add(match)
                match_count += 1
                
                # Commit every 100 matches to avoid memory issues
                if match_count % 100 == 0:
                    self.db.commit()
                    logger.info(f"         ✅ {match_count} matches saved...")
            
            self.db.commit()
            self.stats['matches'] += match_count
            logger.info(f"         ✅ Added {match_count} matches for {league_name} {season}")
            return match_count
            
        except Exception as e:
            logger.error(f"         ❌ Error fetching matches: {e}")
            self.stats['errors'] += 1
            return 0
    
    def fetch_all_matches(self):
        """Fetch all matches for all leagues and seasons"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 FETCHING MATCHES")
        logger.info("=" * 60)
        
        leagues = self.db.query(League).all()
        total_matches = 0
        
        for league in leagues:
            logger.info(f"\n   📌 {league.name}")
            
            for season in SEASONS:
                # Skip future seasons for some leagues
                if season == '2025':
                    # Only fetch up to current date
                    pass
                
                count = self.fetch_matches_for_league(league.api_id, league.name, season)
                total_matches += count
                time.sleep(0.5)  # Rate limiting
        
        logger.info(f"\n   ✅ Total matches fetched: {total_matches}")
        return total_matches
    
    def run(self):
        """Run the complete data refetch"""
        logger.info("=" * 60)
        logger.info("🚀 PHASE 1: DATA RE-FETCH")
        logger.info("   Seasons: 2020-2021 to 2025-2026")
        logger.info("   Leagues: Top 5 European + UCL")
        logger.info("=" * 60)
        
        # Clear existing data
        # self.clear_existing_data()  # Uncomment to clear existing data
        
        # Fetch leagues
        self.fetch_leagues()
        
        # Fetch teams
        self.fetch_teams()
        
        # Fetch matches
        total_matches = self.fetch_all_matches()
        
        # Final summary
        logger.info("\n" + "=" * 60)
        logger.info("✅ PHASE 1 COMPLETE!")
        logger.info("=" * 60)
        logger.info(f"   Leagues: {self.stats['leagues']}")
        logger.info(f"   Teams: {self.stats['teams']}")
        logger.info(f"   Matches: {total_matches}")
        logger.info(f"   Errors: {self.stats['errors']}")
        logger.info("=" * 60)
        
        return self.stats

if __name__ == "__main__":
    refetcher = DataRefetcher()
    refetcher.run()