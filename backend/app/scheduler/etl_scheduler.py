"""
Scheduled ETL Pipeline - Runs automatically
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
import logging

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

def fetch_upcoming_matches():
    """Fetch upcoming matches for all leagues"""
    logger.info("Fetching upcoming matches...")

def fetch_injuries():
    """Fetch current injuries for all leagues"""
    logger.info("Fetching injury data...")

def start_scheduler():
    """Start the background scheduler"""
    try:
        scheduler.add_job(
            fetch_upcoming_matches,
            trigger=IntervalTrigger(hours=6),
            id="fetch_matches"
        )
        
        scheduler.add_job(
            fetch_injuries,
            trigger=IntervalTrigger(hours=12),
            id="fetch_injuries"
        )
        
        scheduler.add_job(
            lambda: logger.info("Daily ETL job running..."),
            trigger=CronTrigger(hour=2, minute=0),
            id="daily_etl"
        )
        
        scheduler.start()
        logger.info("Scheduler started successfully")
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")