from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, DECIMAL, Boolean, Text, CHAR
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://football_admin:football_pass_123@localhost:5434/football_prediction")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class League(Base):
    __tablename__ = "leagues"
    id = Column(Integer, primary_key=True, index=True)
    api_id = Column(Integer, unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    country = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Team(Base):
    __tablename__ = "teams"
    id = Column(Integer, primary_key=True, index=True)
    api_id = Column(Integer, unique=True, nullable=False)
    league_id = Column(Integer, ForeignKey("leagues.id"))
    name = Column(String(100), nullable=False)
    short_name = Column(String(20))
    elo_rating = Column(DECIMAL(10, 2), default=1500.00)
    created_at = Column(DateTime, default=datetime.utcnow)

# Add this after the Team model
class Player(Base):
    __tablename__ = "players"
    id = Column(Integer, primary_key=True, index=True)
    api_id = Column(Integer, unique=True)
    team_id = Column(Integer, ForeignKey("teams.id"))
    name = Column(String(100), nullable=False)
    position = Column(String(20))
    nationality = Column(String(50))
    age = Column(Integer)
    market_value = Column(DECIMAL(15, 2))
    is_injured = Column(Boolean, default=False)
    injury_severity = Column(Integer)
    injury_reason = Column(Text)
    expected_return = Column(DateTime)
    yellow_cards = Column(Integer, default=0)
    red_cards = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Match(Base):
    __tablename__ = "matches"
    id = Column(Integer, primary_key=True, index=True)
    api_id = Column(Integer, unique=True, nullable=False)
    league_id = Column(Integer, ForeignKey("leagues.id"))
    home_team_id = Column(Integer, ForeignKey("teams.id"))
    away_team_id = Column(Integer, ForeignKey("teams.id"))
    match_date = Column(DateTime, nullable=False)
    season = Column(String(10))
    round = Column(String(30))
    venue = Column(String(100))
    status = Column(String(10), default="NS")
    home_score = Column(Integer)
    away_score = Column(Integer)
    result = Column(CHAR(1))
    is_midweek = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
