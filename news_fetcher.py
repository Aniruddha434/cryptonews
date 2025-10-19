"""
News fetcher module for AI Market Insight Bot.
Fetches news from NewsAPI and CryptoPanic APIs.
"""

import requests
import logging
from datetime import datetime, timedelta
from config import (
    NEWSAPI_KEY, CRYPTOPANIC_API_KEY, CRYPTOCOMPARE_API_KEY,
    NEWSAPI_ENDPOINT, CRYPTOPANIC_ENDPOINT, CRYPTOCOMPARE_NEWS_ENDPOINT, COINGECKO_NEWS_ENDPOINT
)
from validators import InputValidator, InputSanitizer

logger = logging.getLogger(__name__)


class NewsFetcher:
    """Fetches news from multiple sources."""
    
    def __init__(self):
        """Initialize news fetcher."""
        self.newsapi_key = NEWSAPI_KEY
        self.cryptopanic_key = CRYPTOPANIC_API_KEY
        self.cryptocompare_key = CRYPTOCOMPARE_API_KEY
    
    def fetch_finance_news(self, query="bitcoin OR ethereum OR crypto OR trading", limit=5):
        """
        Fetch finance news from NewsAPI (last 7 days).

        Args:
            query: Search query
            limit: Number of articles to fetch

        Returns:
            List of articles with title, description, url, source, publishedAt
        """
        if not self.newsapi_key:
            logger.warning("NEWSAPI_KEY not configured. Skipping NewsAPI fetch.")
            return []

        try:
            # Calculate date from 7 days ago (fresh news)
            from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")

            params = {
                "q": query,
                "sortBy": "publishedAt",  # Sort by newest first
                "language": "en",
                "apiKey": self.newsapi_key,
                "from": from_date,
                "pageSize": limit
            }

            response = requests.get(NEWSAPI_ENDPOINT, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if data.get("status") != "ok":
                logger.error(f"NewsAPI error: {data.get('message', 'Unknown error')}")
                return []

            articles = []
            for article in data.get("articles", [])[:limit]:
                # Validate and sanitize article data
                title = InputSanitizer.sanitize_article_title(article.get("title", ""))
                url = InputSanitizer.sanitize_url(article.get("url", ""))

                # Skip invalid articles
                if not title or not url:
                    logger.warning("Skipping article with missing title or URL")
                    continue

                if not InputValidator.validate_url(url):
                    logger.warning(f"Skipping article with invalid URL: {url}")
                    continue

                articles.append({
                    "title": title,
                    "description": InputSanitizer.sanitize_text(article.get("description", "")),
                    "url": url,
                    "source": InputSanitizer.sanitize_text(article.get("source", {}).get("name", "Unknown")),
                    "publishedAt": article.get("publishedAt", ""),
                    "image": InputSanitizer.sanitize_url(article.get("urlToImage", ""))
                })

            logger.info(f"Fetched {len(articles)} fresh articles from NewsAPI (last 7 days)")
            return articles

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching from NewsAPI: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in fetch_finance_news: {e}")
            return []
    
    def fetch_crypto_news(self, limit=5, filter_important=False):
        """
        Fetch crypto news from CryptoPanic API (Developer v2).

        Args:
            limit: Number of articles to fetch
            filter_important: If True, only fetch important/hot news

        Returns:
            List of articles with title, description, url, source, publishedAt, importance
        """
        if not self.cryptopanic_key:
            logger.warning("CRYPTOPANIC_API_KEY not configured. Skipping CryptoPanic fetch.")
            return []

        try:
            params = {
                "auth_token": self.cryptopanic_key,
                "kind": "news",
                "public": "true"
            }

            # Filter for important news only
            if filter_important:
                params["filter"] = "important"

            response = requests.get(CRYPTOPANIC_ENDPOINT, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            # Debug: Log API response structure
            logger.debug(f"CryptoPanic API response keys: {data.keys()}")
            logger.debug(f"CryptoPanic results count: {len(data.get('results', []))}")

            articles = []
            for idx, result in enumerate(data.get("results", [])[:limit]):
                # Debug: Print raw article data to console (temporary debugging)
                if idx == 0:  # Only print first article to avoid spam
                    print(f"\n🔍 DEBUG: First CryptoPanic article raw data:")
                    print(f"   Keys: {list(result.keys())}")
                    print(f"   Full data: {result}")
                    print()

                logger.debug(f"Article {idx} raw keys: {result.keys()}")
                logger.debug(f"Article {idx} title (raw): {result.get('title', 'MISSING')}")
                logger.debug(f"Article {idx} slug (raw): {result.get('slug', 'MISSING')}")
                logger.debug(f"Article {idx} id (raw): {result.get('id', 'MISSING')}")

                # Validate and sanitize article data
                title = InputSanitizer.sanitize_article_title(result.get("title", ""))

                # ✅ FIX: CryptoPanic API v2 doesn't return 'url' field directly
                # Construct URL from id and slug: https://cryptopanic.com/news/{id}/{slug}/
                article_id = result.get("id", "")
                slug = result.get("slug", "")

                if article_id and slug:
                    url = f"https://cryptopanic.com/news/{article_id}/{slug}/"
                else:
                    url = ""

                url = InputSanitizer.sanitize_url(url)

                # Debug: Print what we got after sanitization
                if idx == 0:
                    print(f"🔍 DEBUG: After sanitization:")
                    print(f"   title: '{title}' (length: {len(title)})")
                    print(f"   id: {article_id}")
                    print(f"   slug: {slug}")
                    print(f"   constructed url: '{url}' (length: {len(url)})")
                    print()

                # Skip invalid articles
                if not title or not url:
                    logger.warning(f"Skipping CryptoPanic article {idx} with missing title or URL (title={bool(title)}, url={bool(url)})")
                    continue

                if not InputValidator.validate_url(url):
                    logger.warning(f"Skipping CryptoPanic article with invalid URL: {url}")
                    continue

                # Extract metadata
                metadata = result.get("metadata", {})
                votes = result.get("votes", {})

                articles.append({
                    "title": title,
                    # ✅ FIX: Get full body content, not just first 200 chars
                    "description": InputSanitizer.sanitize_text(result.get("body", "")),
                    "url": url,
                    "source": InputSanitizer.sanitize_text(result.get("source", {}).get("title", "CryptoPanic")),
                    "publishedAt": result.get("published_at", ""),
                    "image": "",
                    "important": metadata.get("important", False),
                    "hot": metadata.get("hot", False),
                    "votes_positive": votes.get("positive", 0),
                    "votes_negative": votes.get("negative", 0),
                    "votes_total": votes.get("positive", 0) + votes.get("negative", 0)
                })

            logger.info(f"Fetched {len(articles)} articles from CryptoPanic (important={filter_important})")
            return articles

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching from CryptoPanic: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in fetch_crypto_news: {e}")
            return []

    def fetch_cryptocompare_news(self, limit=10):
        """
        Fetch crypto news from CryptoCompare API.

        Args:
            limit: Number of articles to fetch

        Returns:
            List of articles with title, description, url, source, publishedAt
        """
        logger.debug(f"🔍 Starting CryptoCompare fetch (limit={limit})...")
        try:
            params = {
                "lang": "EN",
                "sortOrder": "latest"
            }

            # Add API key if available (optional for basic usage)
            if self.cryptocompare_key:
                params["api_key"] = self.cryptocompare_key
                logger.debug("✅ CryptoCompare API key is configured")
            else:
                logger.warning("⚠️ CryptoCompare API key is NOT configured")

            logger.debug(f"Calling CryptoCompare API: {CRYPTOCOMPARE_NEWS_ENDPOINT}")
            response = requests.get(CRYPTOCOMPARE_NEWS_ENDPOINT, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            # Debug: Log API response structure
            logger.debug(f"CryptoCompare API response Type: {data.get('Type')}")
            logger.debug(f"CryptoCompare API response keys: {data.keys()}")
            logger.debug(f"CryptoCompare Data count: {len(data.get('Data', []))}")

            if data.get("Type") != 100:  # Success code
                logger.error(f"CryptoCompare API error: {data.get('Message', 'Unknown error')}")
                logger.error(f"Full response: {data}")
                return []

            articles = []
            for idx, article in enumerate(data.get("Data", [])[:limit]):
                # Debug: Log raw article data
                logger.debug(f"CryptoCompare Article {idx} raw keys: {article.keys()}")
                logger.debug(f"CryptoCompare Article {idx} title (raw): {article.get('title', 'MISSING')}")
                logger.debug(f"CryptoCompare Article {idx} url (raw): {article.get('url', 'MISSING')}")

                # Validate and sanitize article data
                title = InputSanitizer.sanitize_article_title(article.get("title", ""))
                url = InputSanitizer.sanitize_url(article.get("url", ""))

                # Skip invalid articles
                if not title or not url:
                    logger.warning(f"Skipping CryptoCompare article {idx} with missing title or URL (title={bool(title)}, url={bool(url)})")
                    continue

                if not InputValidator.validate_url(url):
                    logger.warning(f"Skipping CryptoCompare article with invalid URL: {url}")
                    continue

                # Convert timestamp to ISO format
                published_at = datetime.fromtimestamp(article.get("published_on", 0)).isoformat() + "Z"

                articles.append({
                    "title": title,
                    # ✅ FIX: Get full body content, not just first 200 chars
                    "description": InputSanitizer.sanitize_text(article.get("body", "")),
                    "url": url,
                    "source": InputSanitizer.sanitize_text(article.get("source", "CryptoCompare")),
                    "publishedAt": published_at,
                    "image": InputSanitizer.sanitize_url(article.get("imageurl", "")),
                    "categories": article.get("categories", "").split("|") if article.get("categories") else [],
                    "upvotes": article.get("upvotes", 0),
                    "downvotes": article.get("downvotes", 0)
                })

            logger.info(f"Fetched {len(articles)} articles from CryptoCompare")
            return articles

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching from CryptoCompare: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in fetch_cryptocompare_news: {e}")
            return []

    def fetch_coingecko_news(self, limit=10):
        """
        Fetch crypto news from CoinGecko API.
        NOTE: CoinGecko removed their public news API endpoint.
        This method is kept for future compatibility but returns empty list.

        Args:
            limit: Number of articles to fetch

        Returns:
            Empty list (endpoint no longer available)
        """
        logger.info("CoinGecko news API is not available (endpoint removed)")
        return []

    def fetch_hot_news(self, limit=10):
        """
        Fetch only hot/important news for real-time posting from ALL sources.
        Aggregates news from CryptoPanic, CryptoCompare, and CoinGecko.

        Args:
            limit: Number of hot articles to fetch

        Returns:
            List of hot/important articles sorted by importance
        """
        logger.info("🔥 Fetching hot/important news from ALL sources for real-time posting...")
        logger.debug(f"fetch_hot_news called with limit={limit}")

        all_hot_articles = []

        # ============================================================
        # SOURCE 1: CryptoPanic (filter=important)
        # ============================================================
        logger.debug("📰 Starting CryptoPanic fetch...")
        try:
            hot_crypto = self.fetch_crypto_news(limit=limit, filter_important=True)

            for article in hot_crypto:
                # Calculate importance score (0-10)
                importance_score = 0

                if article.get("important"):
                    importance_score += 5
                if article.get("hot"):
                    importance_score += 3

                # Add points for engagement
                votes_total = article.get("votes_total", 0)
                if votes_total >= 10:
                    importance_score += 2
                elif votes_total >= 5:
                    importance_score += 1

                article["importance_score"] = importance_score
                article["news_source_api"] = "CryptoPanic"

                # Only include articles with high importance
                if importance_score >= 5:
                    all_hot_articles.append(article)

            logger.info(f"   ✅ CryptoPanic: {len([a for a in all_hot_articles if a['news_source_api'] == 'CryptoPanic'])} hot articles")
        except Exception as e:
            logger.error(f"   ❌ CryptoPanic fetch failed: {e}")

        # ============================================================
        # SOURCE 2: CryptoCompare (latest news with engagement)
        # ============================================================
        logger.debug("📰 Starting CryptoCompare fetch...")
        try:
            cryptocompare_news = self.fetch_cryptocompare_news(limit=limit)
            logger.debug(f"CryptoCompare returned {len(cryptocompare_news)} articles")

            for article in cryptocompare_news:
                # Calculate importance score based on engagement
                importance_score = 3  # Base score for CryptoCompare news

                # ✅ FIX: Convert to int to avoid string subtraction error
                upvotes = int(article.get("upvotes", 0))
                downvotes = int(article.get("downvotes", 0))
                net_votes = upvotes - downvotes

                # Add points for high engagement
                if net_votes >= 50:
                    importance_score += 4
                elif net_votes >= 20:
                    importance_score += 3
                elif net_votes >= 10:
                    importance_score += 2
                elif net_votes >= 5:
                    importance_score += 1

                # Boost for breaking news categories
                categories = article.get("categories", [])
                if any(cat.lower() in ["breaking", "important", "market"] for cat in categories):
                    importance_score += 2

                article["importance_score"] = importance_score
                article["news_source_api"] = "CryptoCompare"

                # Only include articles with decent importance
                if importance_score >= 5:
                    all_hot_articles.append(article)

            logger.info(f"   ✅ CryptoCompare: {len([a for a in all_hot_articles if a['news_source_api'] == 'CryptoCompare'])} hot articles")
        except Exception as e:
            logger.error(f"   ❌ CryptoCompare fetch failed: {e}")

        # ============================================================
        # SOURCE 3: CoinGecko - DISABLED (API endpoint removed)
        # ============================================================
        # CoinGecko removed their public news API endpoint
        logger.info(f"   ⚠️  CoinGecko: Skipped (API endpoint not available)")

        # ============================================================
        # Deduplicate by URL and sort by importance
        # ============================================================
        seen_urls = set()
        unique_articles = []

        for article in all_hot_articles:
            url = article.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_articles.append(article)

        # Sort by importance score (highest first)
        unique_articles.sort(key=lambda x: x.get("importance_score", 0), reverse=True)

        logger.info(f"🎯 Total unique hot articles from all sources: {len(unique_articles)}")
        logger.info(f"   📊 Breakdown: CryptoPanic={len([a for a in unique_articles if a.get('news_source_api') == 'CryptoPanic'])}, "
                   f"CryptoCompare={len([a for a in unique_articles if a.get('news_source_api') == 'CryptoCompare'])}")

        return unique_articles[:limit]

    def fetch_trending_news(self, limit=10):
        """
        Fetch trending news from all sources (fresh data only).

        Args:
            limit: Total number of articles to fetch

        Returns:
            Combined list of trending articles (newest first)
        """
        logger.info("Fetching fresh trending news from all sources...")

        # Fetch from both sources (24 hours only)
        finance_news = self.fetch_finance_news(limit=limit // 2)
        crypto_news = self.fetch_crypto_news(limit=limit // 2)

        # Combine and deduplicate by URL
        all_news = finance_news + crypto_news
        seen_urls = set()
        unique_news = []

        for article in all_news:
            if article["url"] not in seen_urls:
                seen_urls.add(article["url"])
                unique_news.append(article)

        # Sort by published date (newest first)
        try:
            unique_news.sort(
                key=lambda x: datetime.fromisoformat(x["publishedAt"].replace("Z", "+00:00")),
                reverse=True
            )
        except Exception as e:
            logger.warning(f"Could not sort articles by date: {e}")

        logger.info(f"Total unique fresh articles fetched: {len(unique_news)}")
        return unique_news[:limit]

