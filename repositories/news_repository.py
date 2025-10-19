"""
News repository for AI Market Insight Bot.
Handles news caching and retrieval with connection pooling.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class NewsRepository(BaseRepository):
    """
    Repository for news data operations.
    
    Provides methods for:
    - News article caching
    - AI analysis storage
    - Duplicate detection
    - Cache expiration
    """
    
    async def find_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Find cached news article by URL.
        
        Args:
            url: Article URL
            
        Returns:
            News data dictionary or None
        """
        query = """
            SELECT url, title, summary, analysis, trader_type,
                   created_at, expires_at
            FROM news_cache
            WHERE url = ? AND expires_at > ?
        """
        
        now = datetime.now().isoformat()
        result = await self.execute_query(query, (url, now), fetch_one=True)
        
        if result:
            self.logger.debug(f"Cache hit for URL: {url}")
        
        return result
    
    async def find_recent(
        self,
        trader_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get recent cached news articles.
        
        Args:
            trader_type: Filter by trader type (optional)
            limit: Maximum number of articles
            
        Returns:
            List of news dictionaries
        """
        if trader_type:
            query = """
                SELECT url, title, summary, analysis, trader_type,
                       created_at, expires_at
                FROM news_cache
                WHERE trader_type = ? AND expires_at > ?
                ORDER BY created_at DESC
                LIMIT ?
            """
            now = datetime.now().isoformat()
            return await self.execute_query(
                query,
                (trader_type, now, limit),
                fetch_all=True
            )
        else:
            query = """
                SELECT url, title, summary, analysis, trader_type,
                       created_at, expires_at
                FROM news_cache
                WHERE expires_at > ?
                ORDER BY created_at DESC
                LIMIT ?
            """
            now = datetime.now().isoformat()
            return await self.execute_query(query, (now, limit), fetch_all=True)
    
    async def create(
        self,
        url: str,
        title: str,
        summary: str,
        analysis: str,
        trader_type: str,
        ttl_hours: int = 24
    ) -> bool:
        """
        Cache news article with AI analysis.
        
        Args:
            url: Article URL
            title: Article title
            summary: Article summary
            analysis: AI analysis result
            trader_type: Trader type for analysis
            ttl_hours: Cache TTL in hours
            
        Returns:
            True if successful
        """
        query = """
            INSERT INTO news_cache (url, title, summary, analysis, trader_type,
                                   created_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        now = datetime.now()
        expires_at = now + timedelta(hours=ttl_hours)
        
        try:
            await self.execute_query(
                query,
                (url, title, summary, analysis, trader_type,
                 now.isoformat(), expires_at.isoformat())
            )
            self.logger.info(f"Cached news article: {url}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to cache article {url}: {e}")
            return False
    
    async def update_analysis(self, url: str, analysis: str) -> bool:
        """
        Update AI analysis for cached article.
        
        Args:
            url: Article URL
            analysis: New AI analysis
            
        Returns:
            True if successful
        """
        query = "UPDATE news_cache SET analysis = ? WHERE url = ?"
        
        try:
            await self.execute_query(query, (analysis, url))
            self.logger.info(f"Updated analysis for: {url}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to update analysis for {url}: {e}")
            return False
    
    async def delete(self, url: str) -> bool:
        """
        Delete cached article.
        
        Args:
            url: Article URL
            
        Returns:
            True if successful
        """
        query = "DELETE FROM news_cache WHERE url = ?"
        
        try:
            await self.execute_query(query, (url,))
            self.logger.info(f"Deleted cached article: {url}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete article {url}: {e}")
            return False
    
    async def delete_expired(self) -> int:
        """
        Delete all expired cache entries.
        
        Returns:
            Number of entries deleted
        """
        query = "DELETE FROM news_cache WHERE expires_at <= ?"
        
        now = datetime.now().isoformat()
        
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (now,))
                count = cursor.rowcount
                self.logger.info(f"Deleted {count} expired cache entries")
                return count
        except Exception as e:
            self.logger.error(f"Failed to delete expired entries: {e}")
            return 0
    
    async def exists(self, url: str) -> bool:
        """
        Check if article is cached and not expired.
        
        Args:
            url: Article URL
            
        Returns:
            True if cached and valid
        """
        article = await self.find_by_url(url)
        return article is not None
    
    async def get_or_none(self, url: str, trader_type: str) -> Optional[str]:
        """
        Get cached analysis or None.
        
        Args:
            url: Article URL
            trader_type: Trader type
            
        Returns:
            Cached analysis or None
        """
        query = """
            SELECT analysis
            FROM news_cache
            WHERE url = ? AND trader_type = ? AND expires_at > ?
        """
        
        now = datetime.now().isoformat()
        result = await self.execute_query(query, (url, trader_type, now), fetch_one=True)
        
        return result['analysis'] if result else None
    
    async def count_cached(self) -> int:
        """
        Get number of cached articles (not expired).
        
        Returns:
            Cache count
        """
        query = "SELECT COUNT(*) as count FROM news_cache WHERE expires_at > ?"
        now = datetime.now().isoformat()
        result = await self.execute_query(query, (now,), fetch_one=True)
        return result['count'] if result else 0
    
    async def cache_many(self, articles: List[Dict[str, Any]]) -> int:
        """
        Cache multiple articles in batch.
        
        Args:
            articles: List of article dictionaries
            
        Returns:
            Number of articles cached
        """
        query = """
            INSERT INTO news_cache (url, title, summary, analysis, trader_type,
                                   created_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        now = datetime.now()
        
        params_list = []
        for article in articles:
            ttl_hours = article.get('ttl_hours', 24)
            expires_at = now + timedelta(hours=ttl_hours)
            
            params_list.append((
                article['url'],
                article['title'],
                article['summary'],
                article['analysis'],
                article['trader_type'],
                now.isoformat(),
                expires_at.isoformat()
            ))
        
        try:
            count = await self.execute_many(query, params_list)
            self.logger.info(f"Cached {count} articles in batch")
            return count
        except Exception as e:
            self.logger.error(f"Failed to cache articles in batch: {e}")
            return 0

