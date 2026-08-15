"""
PHASE 1: Data Re-fetch Script (FIXED)
Fetches all historical match data from 2020-2021 to 2025-2026
For Top 5 European Leagues + UEFA Champions League
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.api_football import APIFootballService
from app.models import get_db, League, Team, Match
from datetime import datetime
import time
import logging

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

# Seasons with correct format (API expects season like "2020" for 2020-2021)
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
    
    def fetch_teams_for_league(self, league_id: int, league_name: str):
        """Fetch teams for a specific league"""
        logger.info(f"   📌 {league_name}")
        
        # Try multiple seasons to get all teams
        for season in SEASONS[:3]:  # Try first 3 seasons
            try:
                teams_data = self.api.fetch_teams(league_id, season)
                if teams_data:
                    team_count = 0
                    for team_data in teams_data:
                        team_info = team_data.get('team', {})
                        existing = self.db.query(Team).filter_by(api_id=team_info.get('id')).first()
                        if not existing:
                            team = Team(
                                api_id=team_info.get('id'),
                                league_id=league_id,
                                name=team_info.get('name', 'Unknown'),
                                short_name=team_info.get('code'),
                                elo_rating=1500.00
                            )
                            self.db.add(team)
                            team_count += 1
                    self.db.commit()
                    logger.info(f"      ✅ Added {team_count} teams for {league_name}")
                    self.stats['teams'] += team_count
                    return team_count
            except Exception as e:
                logger.error(f"      ❌ Error fetching teams for {league_name}: {e}")
                continue
        
        logger.warning(f"      ⚠️  No teams found for {league_name}")
        return 0
    
    def fetch_matches_for_league(self, league_id: int, league_name: str, season: str):
        """Fetch matches for a specific league and season"""
        logger.info(f"      📅 Season {season}-{int(season)+1}...")
        
        try:
            # API expects season like "2020" for 2020-2021
            matches_data = self.api.fetch_matches(league_id, season)
            
            if not matches_data:
                logger.info(f"         ⚠️  No matches found for {league_name} {season}-{int(season)+1}")
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
                    date_str = fixture.get('date', '')
                    if date_str:
                        match_date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S+00:00")
                    else:
                        match_date = datetime.utcnow()
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
                
                # Determine if midweek (Tue, Wed, Thu)
                is_midweek = match_date.weekday() in [1, 2, 3]  # Tue, Wed, Thu
                
                match = Match(
                    api_id=fixture.get('id'),
                    league_id=league_id,
                    home_team_id=home_team.id,
                    away_team_id=away_team.id,
                    match_date=match_date,
                    season=season,
                    round=fixture.get('round', ''),
                    venue=fixture.get('venue', {}).get('name', ''),
                    status=fixture.get('status', {}).get('short', 'NS'),
                    home_score=home_score,
                    away_score=away_score,
                    result=result,
                    is_midweek=is_midweek
                )
                self.db.add(match)
                match_count += 1
                
                # Commit every 100 matches
                if match_count % 100 == 0:
                    self.db.commit()
                    logger.info(f"         ✅ {match_count} matches saved...")
            
            self.db.commit()
            self.stats['matches'] += match_count
            logger.info(f"         ✅ Added {match_count} matches for {league_name} {season}-{int(season)+1}")
            return match_count
            
        except Exception as e:
            logger.error(f"         ❌ Error fetching matches: {e}")
            self.stats['errors'] += 1
            import traceback
            traceback.print_exc()
            return 0
    
    def run(self):
        """Run the complete data refetch"""
        logger.info("=" * 60)
        logger.info("🚀 PHASE 1: DATA RE-FETCH (FIXED)")
        logger.info("   Seasons: 2020-2021 to 2025-2026")
        logger.info("   Leagues: Top 5 European + UCL")
        logger.info("=" * 60)
        
        # Get or create leagues
        for key, league_info in LEAGUES.items():
            league = self.db.query(League).filter_by(api_id=league_info['id']).first()
            if not league:
                league = League(
                    api_id=league_info['id'],
                    name=league_info['name'],
                    country=league_info.get('country', 'Europe'),
                    is_active=True
                )
                self.db.add(league)
                self.db.commit()
                self.stats['leagues'] += 1
                logger.info(f"   ✅ Added league: {league_info['name']}")
            else:
                logger.info(f"   ⏭️  League already exists: {league_info['name']}")
        
        # Fetch teams for each league
        logger.info("\n" + "=" * 60)
        logger.info("📊 FETCHING TEAMS")
        logger.info("=" * 60)
        
        for league in self.db.query(League).all():
            self.fetch_teams_for_league(league.api_id, league.name)
            time.sleep(0.5)
        
        # Fetch matches for each league and season
        logger.info("\n" + "=" * 60)
        logger.info("📊 FETCHING MATCHES")
        logger.info("=" * 60)
        
        total_matches = 0
        for league in self.db.query(League).all():
            logger.info(f"\n   📌 {league.name}")
            
            for season in SEASONS:
                count = self.fetch_matches_for_league(league.api_id, league.name, season)
                total_matches += count
                time.sleep(0.5)  # Rate limiting
        
        # Final summary
        logger.info("\n" + "=" * 60)
        logger.info("✅ PHASE 1 COMPLETE!")
        logger.info("=" * 60)
        logger.info(f"   Leagues: {self.db.query(League).count()}")
        logger.info(f"   Teams: {self.db.query(Team).count()}")
        logger.info(f"   Matches: {self.db.query(Match).count()}")
        logger.info(f"   New Matches Added: {total_matches}")
        logger.info(f"   Errors: {self.stats['errors']}")
        logger.info("=" * 60)

if __name__ == "__main__":
    refetcher = DataRefetcher()
    refetcher.run()