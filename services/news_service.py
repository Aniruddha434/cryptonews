"""
News service for AI Market Insight Bot.
Handles news fetching, AI analysis, and caching with circuit breaker protection.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from core.cache import Cache
from core.circuit_breaker import CircuitBreaker, CircuitBreakerError
from core.metrics import MetricsCollector
from repositories.news_repository import NewsRepository
from news_fetcher import NewsFetcher
from ai_analyzer import AIAnalyzer

logger = logging.getLogger(__name__)


class NewsService:
    """
    Service for news operations.
    
    Provides:
    - News fetching with circuit breaker protection
    - AI analysis with caching
    - Trader-specific content filtering
    - Performance metrics tracking
    """
    
    def __init__(
        self,
        news_repo: NewsRepository,
        news_fetcher: NewsFetcher,
        ai_analyzer: AIAnalyzer,
        cache: Cache,
        metrics: MetricsCollector,
        gemini_circuit_breaker: CircuitBreaker,
        news_api_circuit_breaker: CircuitBreaker
    ):
        """
        Initialize news service.
        
        Args:
            news_repo: News repository
            news_fetcher: News fetcher
            ai_analyzer: AI analyzer
            cache: Cache instance
            metrics: Metrics collector
            gemini_circuit_breaker: Circuit breaker for Gemini API
            news_api_circuit_breaker: Circuit breaker for News API
        """
        self.news_repo = news_repo
        self.news_fetcher = news_fetcher
        self.ai_analyzer = ai_analyzer
        self.cache = cache
        self.metrics = metrics
        self.gemini_cb = gemini_circuit_breaker
        self.news_api_cb = news_api_circuit_breaker
        
        logger.info("NewsService initialized")
    
    async def fetch_trending_news(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Fetch trending crypto news with circuit breaker protection.
        
        Args:
            limit: Number of articles to fetch
            
        Returns:
            List of news articles
        """
        cache_key = f"trending_news:{limit}"
        
        # Try cache first
        cached = await self.cache.get(cache_key)
        if cached:
            self.metrics.inc_counter("cache_hits_total")
            logger.debug(f"Cache hit for trending news (limit={limit})")
            return cached
        
        self.metrics.inc_counter("cache_misses_total")
        
        # Fetch from API with circuit breaker
        try:
            with self.metrics.track_api_call("news_api"):
                # Call synchronous function with call_sync
                articles = self.news_api_cb.call_sync(
                    self._fetch_trending_sync,
                    limit
                )

            # Cache result
            await self.cache.set(cache_key, articles, ttl=300)  # 5 minutes

            return articles

        except CircuitBreakerError as e:
            logger.error(f"News API circuit breaker open: {e}")
            # Return cached data even if expired
            return []
        except Exception as e:
            logger.error(f"Error fetching trending news: {e}", exc_info=True)
            return []

    def _fetch_trending_sync(self, limit: int) -> List[Dict[str, Any]]:
        """Synchronous wrapper for news fetching."""
        try:
            return self.news_fetcher.fetch_trending_news(limit=limit)
        except Exception as e:
            logger.error(f"Error in _fetch_trending_sync: {e}", exc_info=True)
            return []
    
    async def fetch_finance_news(
        self,
        query: str = "bitcoin OR ethereum OR crypto OR trading",
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Fetch finance news with circuit breaker protection.
        
        Args:
            query: Search query
            limit: Number of articles
            
        Returns:
            List of news articles
        """
        cache_key = f"finance_news:{query}:{limit}"
        
        # Try cache first
        cached = await self.cache.get(cache_key)
        if cached:
            self.metrics.inc_counter("cache_hits_total")
            return cached
        
        self.metrics.inc_counter("cache_misses_total")
        
        # Fetch from API with circuit breaker
        try:
            with self.metrics.track_api_call("news_api"):
                # Call synchronous function with call_sync
                articles = self.news_api_cb.call_sync(
                    self._fetch_finance_sync,
                    query,
                    limit
                )

            # Cache result
            await self.cache.set(cache_key, articles, ttl=300)

            return articles

        except CircuitBreakerError as e:
            logger.error(f"News API circuit breaker open: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching finance news: {e}", exc_info=True)
            return []

    def _fetch_finance_sync(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Synchronous wrapper for finance news fetching."""
        try:
            return self.news_fetcher.fetch_finance_news(query=query, limit=limit)
        except Exception as e:
            logger.error(f"Error in _fetch_finance_sync: {e}", exc_info=True)
            return []
    
    async def analyze_article(
        self,
        title: str,
        summary: str,
        trader_type: str = "investor",
        url: Optional[str] = None
    ) -> str:
        """
        Analyze article with AI, using cache and circuit breaker.

        Args:
            title: Article title
            summary: Article summary
            trader_type: Type of trader (scalper, day_trader, swing_trader, investor)
            url: Article URL for caching

        Returns:
            AI analysis text for the specific trader type
        """
        # Check database cache first
        if url:
            cached_analysis = await self.news_repo.get_or_none(url, trader_type)
            if cached_analysis:
                self.metrics.inc_counter("cache_hits_total")
                logger.debug(f"Database cache hit for article: {url} (trader_type: {trader_type})")
                return cached_analysis

        # Check memory cache
        cache_key = f"ai_analysis:{trader_type}:{title[:50]}"
        cached = await self.cache.get(cache_key)
        if cached:
            self.metrics.inc_counter("cache_hits_total")
            logger.debug(f"Memory cache hit for article: {title[:50]} (trader_type: {trader_type})")
            return cached

        self.metrics.inc_counter("cache_misses_total")

        # Analyze with AI using circuit breaker
        try:
            logger.info(f"Calling Gemini API for analysis (trader_type: {trader_type})")
            with self.metrics.track_api_call("gemini_api"):
                # ✅ FIX: Use call_sync() for synchronous function
                analysis = self.gemini_cb.call_sync(
                    self._analyze_sync,
                    title,
                    summary,
                    trader_type  # ✅ FIX: Pass trader_type to AI analyzer
                )

            logger.info(f"✅ Successfully received AI analysis for trader_type: {trader_type}")

            # Cache in memory
            await self.cache.set(cache_key, analysis, ttl=3600)  # 1 hour

            # Cache in database if URL provided
            if url:
                await self.news_repo.create(
                    url=url,
                    title=title,
                    summary=summary,
                    analysis=analysis,
                    trader_type=trader_type,
                    ttl_hours=24
                )

            return analysis

        except CircuitBreakerError as e:
            logger.error(f"Gemini API circuit breaker open: {e}")
            return self._fallback_analysis(title, summary)
        except Exception as e:
            logger.error(f"Error analyzing article: {e}", exc_info=True)
            return self._fallback_analysis(title, summary)

    def _analyze_sync(self, title: str, summary: str, trader_type: str = "investor") -> str:
        """
        Synchronous wrapper for AI analysis.

        Args:
            title: Article title
            summary: Article summary
            trader_type: Type of trader (scalper, day_trader, swing_trader, investor)

        Returns:
            Trader-specific analysis text
        """
        result = self.ai_analyzer.analyze_with_gpt(title, summary)

        # ✅ FIX: Extract the correct trader-specific field from the dict
        if isinstance(result, dict):
            # Map trader_type to the correct field in the response
            analysis_text = result.get(trader_type, "")

            if analysis_text:
                logger.debug(f"Extracted {trader_type} analysis: {analysis_text[:100]}...")
                return analysis_text
            else:
                # Fallback: if trader_type field is missing, try to construct from all fields
                logger.warning(f"Trader type '{trader_type}' not found in AI response. Available keys: {result.keys()}")
                return str(result)

        return str(result)
    
    def _fallback_analysis(self, title: str, summary: str) -> str:
        """Fallback analysis when AI is unavailable."""
        return f"📰 {title}\n\n{summary}\n\n⚠️ AI analysis temporarily unavailable."
    
    async def get_trader_specific_news(
        self,
        trader_type: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get news with trader-specific AI analysis.
        
        Args:
            trader_type: Type of trader
            limit: Number of articles
            
        Returns:
            List of articles with analysis
        """
        # Fetch trending news
        articles = await self.fetch_trending_news(limit=limit)
        
        # Add AI analysis to each article
        analyzed_articles = []
        for article in articles:
            analysis = await self.analyze_article(
                title=article.get('title', ''),
                summary=article.get('description', ''),
                trader_type=trader_type,
                url=article.get('url')
            )
            
            analyzed_articles.append({
                **article,
                'analysis': analysis,
                'trader_type': trader_type
            })
        
        return analyzed_articles
    
    async def cleanup_expired_cache(self) -> int:
        """
        Clean up expired news cache entries.
        
        Returns:
            Number of entries deleted
        """
        try:
            count = await self.news_repo.delete_expired()
            logger.info(f"Cleaned up {count} expired news cache entries")
            return count
        except Exception as e:
            logger.error(f"Error cleaning up cache: {e}", exc_info=True)
            return 0

