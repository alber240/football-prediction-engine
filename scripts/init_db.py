#!/usr/bin/env python
"""
Initialize the database - create tables, indexes, and load initial data.
Run with: python scripts/init_db.py
"""

import sys
import os
from pathlib import Path

# Add the backend directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config.database import init_db, check_db_connection, engine
from app.config.settings import settings
from sqlalchemy import text
from loguru import logger
import pandas as pd

def create_schema():
    """Create all tables and schema"""
    logger.info("Creating database schema...")
    
    # Read and execute schema.sql
    schema_path = Path(__file__).parent.parent / "app" / "models" / "schema.sql"
    with open(schema_path, 'r') as f:
        schema_sql = f.read()
    
    # Split into individual statements
    statements = [s.strip() for s in schema_sql.split(';') if s.strip()]
    
    with engine.connect() as conn:
        for stmt in statements:
            try:
                conn.execute(text(stmt))
            except Exception as e:
                if "already exists" not in str(e).lower():
                    logger.error(f"Error executing: {stmt[:50]}...")
                    logger.error(e)
                    raise
        conn.commit()
    
    logger.info("Database schema created successfully")

def load_initial_data():
    """Load initial data (leagues, etc.)"""
    logger.info("Loading initial data...")
    
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
                conn.execute(
                    text("""
                        INSERT INTO leagues (api_id, name, country, is_active)
                        VALUES (:api_id, :name, :country, true)
                        ON CONFLICT (api_id) DO NOTHING
                    """),
                    league
                )
            except Exception as e:
                logger.error(f"Error inserting league {league['name']}: {e}")
        
        conn.commit()
    
    logger.info("Initial data loaded successfully")

def main():
    """Main initialization function"""
    logger.info("=" * 60)
    logger.info("DATABASE INITIALIZATION")
    logger.info("=" * 60)
    
    # Check connection
    if not check_db_connection():
        logger.error("Database connection failed. Please check your DATABASE_URL.")
        return False
    
    # Create schema
    
    create_schema()
    
    # Load initial data
    load_initial_data()
    
    logger.info("=" * 60)
    logger.info("✅ Database initialization complete!")
    logger.info("=" * 60)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)