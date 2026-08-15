#!/usr/bin/env python
"""
Initialize the database - create tables and load initial data.
Run with: python scripts/init_db.py
"""

import sys
import os
from pathlib import Path

# Add the backend directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection - using port 5434 to avoid conflicts
DATABASE_URL = "postgresql://football_admin:football_pass_123@localhost:5434/football_prediction"

engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def check_db_connection():
    """Check if database connection is working"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✅ Database connection successful")
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False

def create_schema():
    """Create all tables and schema"""
    logger.info("📌 Creating database schema...")
    
    # Read and execute schema.sql
    schema_path = Path(__file__).parent.parent / "app" / "models" / "schema.sql"
    
    if not schema_path.exists():
        logger.error(f"❌ Schema file not found at: {schema_path}")
        return False
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    
    # Split into individual statements
    statements = [s.strip() for s in schema_sql.split(';') if s.strip()]
    
    with engine.connect() as conn:
        for stmt in statements:
            if not stmt:
                continue
            try:
                conn.execute(text(stmt))
                logger.debug(f"Executed: {stmt[:50]}...")
            except Exception as e:
                if "already exists" in str(e).lower():
                    logger.debug(f"Skipping (already exists): {stmt[:30]}...")
                else:
                    logger.error(f"❌ Error executing: {stmt[:50]}...")
                    logger.error(f"   Error: {e}")
                    return False
        conn.commit()
    
    logger.info("✅ Database schema created successfully")
    return True

def load_initial_data():
    """Load initial data (leagues, etc.)"""
    logger.info("📌 Loading initial data...")
    
    # Insert leagues if not present
    leagues = [
        {"api_id": 39, "name": "Premier League", "country": "England"},
        {"api_id": 140, "name": "La Liga", "country": "Spain"},
        {"api_id": 78, "name": "Bundesliga", "country": "Germany"},
        {"api_id": 135, "name": "Serie A", "country": "Italy"},
        {"api_id": 61, "name": "Ligue 1", "country": "France"},
        {"api_id": 2, "name": "UEFA Champions League", "country": "Europe"},
    ]
    
    with engine.connect() as conn:
        for league in leagues:
            try:
                result = conn.execute(
                    text("""
                        INSERT INTO leagues (api_id, name, country, is_active)
                        VALUES (:api_id, :name, :country, true)
                        ON CONFLICT (api_id) DO NOTHING
                        RETURNING id
                    """),
                    league
                )
                if result.first():
                    logger.info(f"   Inserted league: {league['name']}")
            except Exception as e:
                logger.error(f"❌ Error inserting league {league['name']}: {e}")
        conn.commit()
    
    logger.info("✅ Initial data loaded successfully")

def main():
    """Main initialization function"""
    logger.info("=" * 60)
    logger.info("DATABASE INITIALIZATION")
    logger.info("=" * 60)
    
    # Check connection
    if not check_db_connection():
        logger.error("❌ Database connection failed. Please check your DATABASE_URL.")
        logger.info("   Make sure PostgreSQL is running on port 5434")
        return False
    
    # Create schema
    if not create_schema():
        logger.error("❌ Failed to create schema")
        return False
    
    # Load initial data
    load_initial_data()
    
    logger.info("=" * 60)
    logger.info("✅ Database initialization complete!")
    logger.info("=" * 60)
    logger.info("")
    logger.info("📍 Next steps:")
    logger.info("   1. Start the backend: uvicorn app.api.routes:app --reload")
    logger.info("   2. Start the frontend: cd frontend && npm run dev")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)