"""
Football News Service - Fetches daily football news
"""

import requests
import os
from datetime import datetime, timedelta
import logging
from typing import List, Dict
from bs4 import BeautifulSoup
import feedparser
from app.models import get_db, text

logger = logging.getLogger(__name__)

class FootballNewsService:
    def __init__(self):
        self.api_key = os.getenv("NEWS_API_KEY")
        self.db = next(get_db())
        
    def fetch_and_store_news(self) -> List[Dict]:
        """Fetch news and store in database"""
        all_news = self.fetch_football_news()
        
        stored = 0
        for news in all_news:
            try:
                # Check if already exists
                existing = self.db.execute(
                    text("SELECT id FROM football_news WHERE url = :url"),
                    {"url": news['url']}
                ).fetchone()
                
                if not existing:
                    self.db.execute(
                        text("""
                        INSERT INTO football_news (title, summary, source, url, image_url, published_at, category)
                        VALUES (:title, :summary, :source, :url, :image_url, :published_at, :category)
                        """),
                        news
                    )
                    stored += 1
            except Exception as e:
                logger.error(f"Error storing news: {e}")
        
        self.db.commit()
        logger.info(f"Stored {stored} new news articles")
        return all_news[:20]
    
    def fetch_football_news(self) -> List[Dict]:
        """Fetch football news from multiple sources"""
        all_news = []
        
        # Source 1: NewsAPI (if key available)
        if self.api_key:
            newsapi_news = self._fetch_from_newsapi()
            all_news.extend(newsapi_news)
        
        # Source 2: BBC Sport RSS
        bbc_news = self._fetch_from_bbc()
        all_news.extend(bbc_news)
        
        # Source 3: Sky Sports RSS
        sky_news = self._fetch_from_sky()
        all_news.extend(sky_news)
        
        # Sort by date
        all_news.sort(key=lambda x: x['published_at'], reverse=True)
        return all_news[:30]
    
    def _fetch_from_newsapi(self) -> List[Dict]:
        """Fetch from NewsAPI"""
        if not self.api_key:
            return []
            
        try:
            response = requests.get(
                "https://newsapi.org/v2/everything",
                params={
                    "q": "football OR soccer",
                    "language": "en",
                    "sortBy": "publishedAt",
                    "pageSize": 20,
                    "apiKey": self.api_key
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                news = []
                for article in data.get('articles', []):
                    if article.get('title') and '[Removed]' not in article.get('title', ''):
                        news.append({
                            'title': article.get('title', ''),
                            'summary': article.get('description', '') or article.get('content', '')[:200],
                            'source': article.get('source', {}).get('name', 'NewsAPI'),
                            'url': article.get('url', ''),
                            'image_url': article.get('urlToImage', ''),
                            'published_at': article.get('publishedAt', datetime.utcnow().isoformat()),
                            'category': 'general'
                        })
                return news
        except Exception as e:
            logger.error(f"Error fetching from NewsAPI: {e}")
        return []
    
    def _fetch_from_bbc(self) -> List[Dict]:
        """Fetch from BBC Sport RSS"""
        try:
            feed = feedparser.parse('http://feeds.bbci.co.uk/sport/football/rss.xml')
            news = []
            for entry in feed.entries[:15]:
                news.append({
                    'title': entry.get('title', ''),
                    'summary': entry.get('summary', '')[:300],
                    'source': 'BBC Sport',
                    'url': entry.get('link', ''),
                    'image_url': '',
                    'published_at': entry.get('published', datetime.utcnow().isoformat()),
                    'category': 'general'
                })
            return news
        except Exception as e:
            logger.error(f"Error fetching from BBC: {e}")
        return []
    
    def _fetch_from_sky(self) -> List[Dict]:
        """Fetch from Sky Sports RSS"""
        try:
            feed = feedparser.parse('https://www.skysports.com/rss/12040')
            news = []
            for entry in feed.entries[:15]:
                news.append({
                    'title': entry.get('title', ''),
                    'summary': entry.get('summary', '')[:300],
                    'source': 'Sky Sports',
                    'url': entry.get('link', ''),
                    'image_url': '',
                    'published_at': entry.get('published', datetime.utcnow().isoformat()),
                    'category': 'general'
                })
            return news
        except Exception as e:
            logger.error(f"Error fetching from Sky: {e}")
        return []
    
    def get_news(self, limit: int = 20) -> List[Dict]:
        """Get news from database"""
        result = self.db.execute(
            text("""
            SELECT * FROM football_news
            ORDER BY published_at DESC
            LIMIT :limit
            """),
            {"limit": limit}
        ).fetchall()
        
        return [dict(row._mapping) for row in result]