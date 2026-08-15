"""
Base Scraper - Core scraping functionality
"""

import requests
from bs4 import BeautifulSoup
import time
import random
import logging
from typing import Dict, List, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class BaseScraper(ABC):
    """Abstract base class for all prediction scrapers"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
    def random_delay(self, min_wait: float = 1.0, max_wait: float = 3.0):
        time.sleep(random.uniform(min_wait, max_wait))
    
    def get_soup(self, url: str) -> Optional[BeautifulSoup]:
        try:
            self.random_delay()
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                return BeautifulSoup(response.content, 'html.parser')
            else:
                logger.error(f"Failed to fetch {url}: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    @abstractmethod
    def get_predictions(self, league: str = 'premier-league') -> List[Dict]:
        pass
    
    @abstractmethod
    def get_source_name(self) -> str:
        pass