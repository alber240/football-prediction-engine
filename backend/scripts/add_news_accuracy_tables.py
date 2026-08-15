"""
Add news and accuracy tracking tables to database
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import get_db, engine
from sqlalchemy import text

def add_tables():
    db = next(get_db())
    
    print("Creating football_news table...")
    try:
        db.execute(text("""
        CREATE TABLE IF NOT EXISTS football_news (
            id SERIAL PRIMARY KEY,
            title VARCHAR(500) NOT NULL,
            summary TEXT,
            source VARCHAR(100),
            url VARCHAR(500),
            image_url VARCHAR(500),
            published_at TIMESTAMP,
            category VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """))
        db.commit()
        print("✅ football_news table created")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()

    print("Creating prediction_accuracy table...")
    try:
        db.execute(text("""
        CREATE TABLE IF NOT EXISTS prediction_accuracy (
            id SERIAL PRIMARY KEY,
            match_id INTEGER REFERENCES matches(id),
            predicted_home_win BOOLEAN,
            predicted_draw BOOLEAN,
            predicted_away_win BOOLEAN,
            predicted_home_prob DECIMAL(6,5),
            predicted_draw_prob DECIMAL(6,5),
            predicted_away_prob DECIMAL(6,5),
            correct BOOLEAN,
            accuracy_type VARCHAR(20),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """))
        db.commit()
        print("✅ prediction_accuracy table created")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()

    print("Creating daily_accuracy table...")
    try:
        db.execute(text("""
        CREATE TABLE IF NOT EXISTS daily_accuracy (
            id SERIAL PRIMARY KEY,
            date DATE NOT NULL,
            total_predictions INTEGER,
            correct_predictions INTEGER,
            accuracy_percentage DECIMAL(5,2),
            league_id INTEGER REFERENCES leagues(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(date, league_id)
        );
        """))
        db.commit()
        print("✅ daily_accuracy table created")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()

    print("\n✅ All tables created successfully!")

if __name__ == "__main__":
    add_tables()