"""
Real-time news monitoring service for AI Market Insight Bot.
Continuously monitors for hot/important news and posts immediately.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from news_fetcher import NewsFetcher
from services.news_service import NewsService
from services.posting_service import PostingService
from repositories.news_repository import NewsRepository
from repositories.group_repository import GroupRepository
from config import NEWS_CHECK_INTERVAL_MINUTES, MIN_IMPORTANCE_SCORE, ENABLE_REALTIME_POSTING

logger = logging.getLogger(__name__)


class RealtimeNewsService:
    """
    Service for real-time hot news monitoring and posting.
    
    Features:
    - Continuous monitoring for hot/important news
    - Immediate posting when high-impact news is detected
    - Duplicate detection to avoid reposting
    - Market impact analysis for each news item
    - 24/7 operation independent of scheduled posting
    """
    
    def __init__(
        self,
        news_fetcher: NewsFetcher,
        news_service: NewsService,
        posting_service: PostingService,
        news_repo: NewsRepository,
        group_repo: GroupRepository
    ):
        """Initialize real-time news service."""
        self.news_fetcher = news_fetcher
        self.news_service = news_service
        self.posting_service = posting_service
        self.news_repo = news_repo
        self.group_repo = group_repo
        self.is_running = False
        self.check_interval = NEWS_CHECK_INTERVAL_MINUTES * 60  # Convert to seconds
        self.min_importance = MIN_IMPORTANCE_SCORE
        self.posted_urls = set()  # Track posted URLs to avoid duplicates
        
    async def start_monitoring(self):
        """Start continuous monitoring for hot news."""
        if not ENABLE_REALTIME_POSTING:
            logger.info("Real-time posting is disabled in configuration")
            return
        
        if self.is_running:
            logger.warning("Real-time monitoring is already running")
            return
        
        self.is_running = True
        logger.info(f"🔥 Starting real-time hot news monitoring (checking every {NEWS_CHECK_INTERVAL_MINUTES} minutes)")
        logger.info(f"📊 Minimum importance score: {self.min_importance}/10")
        
        # Load previously posted URLs from database
        await self._load_posted_urls()
        
        while self.is_running:
            try:
                await self._check_and_post_hot_news()
                
                # Wait for next check
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error in real-time monitoring loop: {e}", exc_info=True)
                # Wait a bit before retrying
                await asyncio.sleep(60)
    
    def stop_monitoring(self):
        """Stop the monitoring loop."""
        logger.info("Stopping real-time news monitoring...")
        self.is_running = False
    
    async def _load_posted_urls(self):
        """Load recently posted URLs from database to avoid duplicates."""
        try:
            # Get articles posted in the last 24 hours
            recent_articles = await self.news_repo.find_recent(limit=100)
            self.posted_urls = {article["url"] for article in recent_articles if article.get("url")}
            logger.info(f"Loaded {len(self.posted_urls)} recently posted URLs")
        except Exception as e:
            logger.error(f"Error loading posted URLs: {e}")
    
    async def _check_and_post_hot_news(self):
        """Check for hot news and post immediately if found."""
        logger.info("=" * 60)
        logger.info("🔍 Starting hot news check cycle...")
        logger.info(f"⏰ Check time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")

        try:
            # Fetch hot/important news
            logger.info("📡 Fetching hot news from CryptoPanic API...")
            hot_articles = self.news_fetcher.fetch_hot_news(limit=10)

            if not hot_articles:
                logger.info("❌ No hot news found in this check")
                logger.info("=" * 60)
                return

            logger.info(f"✅ Found {len(hot_articles)} hot articles from CryptoPanic")

            # Log details of each article
            for idx, article in enumerate(hot_articles, 1):
                importance = article.get("importance_score", 0)
                is_hot = article.get("hot", False)
                is_important = article.get("important", False)
                logger.info(f"  [{idx}] Score: {importance}/10 | Hot: {is_hot} | Important: {is_important} | {article['title'][:60]}...")

            # Get all active groups
            active_groups = await self.group_repo.find_active()

            if not active_groups:
                logger.warning("⚠️ No active groups to post to")
                logger.info("=" * 60)
                return

            logger.info(f"📢 Found {len(active_groups)} active groups for posting")

            # Process each hot article
            new_posts_count = 0
            filtered_already_posted = 0
            filtered_low_importance = 0

            for article in hot_articles:
                # Skip if already posted
                if article["url"] in self.posted_urls:
                    filtered_already_posted += 1
                    logger.debug(f"⏭️ Skipping already posted: {article['title'][:50]}...")
                    continue

                # Check importance score
                importance_score = article.get("importance_score", 0)
                if importance_score < self.min_importance:
                    filtered_low_importance += 1
                    logger.info(f"⏭️ Filtered out (score {importance_score} < {self.min_importance}): {article['title'][:50]}...")
                    continue

                logger.info(f"🔥 POSTING hot news (score: {importance_score}/10): {article['title'][:60]}...")

                # Post to all active groups
                success = await self._post_to_groups(article, active_groups)

                if success:
                    # Mark as posted
                    self.posted_urls.add(article["url"])
                    new_posts_count += 1
                    logger.info(f"✅ Successfully posted to all groups!")

                    # Small delay between posts to avoid rate limiting
                    await asyncio.sleep(2)
                else:
                    logger.error(f"❌ Failed to post article to groups")

            # Summary
            logger.info("-" * 60)
            logger.info(f"📊 Check Summary:")
            logger.info(f"   • Total articles fetched: {len(hot_articles)}")
            logger.info(f"   • Already posted (skipped): {filtered_already_posted}")
            logger.info(f"   • Low importance (filtered): {filtered_low_importance}")
            logger.info(f"   • New posts sent: {new_posts_count}")

            if new_posts_count > 0:
                logger.info(f"🎯 Successfully posted {new_posts_count} hot news articles!")
            else:
                logger.info("ℹ️ No new hot news qualified for posting this cycle")

            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"❌ Error checking hot news: {e}", exc_info=True)
            logger.info("=" * 60)
    
    async def _post_to_groups(self, article: Dict[str, Any], groups: List[Dict[str, Any]]) -> bool:
        """
        Post article to all active groups with AI analysis.

        Args:
            article: Article data
            groups: List of active groups

        Returns:
            True if posted successfully to at least one group
        """
        posted_count = 0

        logger.info(f"   📤 Posting to {len(groups)} active groups...")

        for group in groups:
            try:
                group_id = group["group_id"]
                group_name = group.get("group_name", f"Group {group_id}")
                trader_type = group.get("trader_type", "investor")

                logger.info(f"   → Group: {group_name} (trader_type: {trader_type})")

                # Get AI analysis for this trader type
                logger.info(f"      🤖 Requesting AI analysis from Gemini...")
                analysis = await self.news_service.analyze_article(
                    url=article["url"],
                    title=article["title"],
                    summary=article.get("description", ""),
                    trader_type=trader_type
                )

                if not analysis:
                    logger.warning(f"      ⚠️ Failed to get AI analysis for group {group_name}")
                    continue

                logger.info(f"      ✅ AI analysis received: {analysis[:100]}...")

                # Format message with hot news indicator
                importance_score = article.get("importance_score", 0)
                hot_indicator = "🔥 HOT NEWS" if article.get("hot") else "⚡ IMPORTANT"

                # ✅ FIX: Include full news content in the message
                message = f"{hot_indicator} (Impact: {importance_score}/10)\n\n"
                message += f"📰 {article['title']}\n\n"

                # Add full news content if available
                description = article.get("description", "")
                if description:
                    message += f"📄 Full Story:\n{description}\n\n"

                message += f"📊 Market Impact Analysis ({trader_type.replace('_', ' ').title()}):\n"
                message += f"{analysis}\n\n"
                message += f"🔗 Source: {article['url']}\n"
                message += f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}"

                # Post to group
                logger.info(f"      📨 Sending message to Telegram...")
                success = await self.posting_service.post_to_group(
                    group_id=group_id,
                    message=message
                )

                if success:
                    posted_count += 1
                    logger.info(f"      ✅ Posted successfully to {group_name}")

                    # Update group's last_post timestamp
                    await self.group_repo.update_last_post(group_id)

                    # Cache the analysis
                    await self.news_repo.create(
                        url=article["url"],
                        title=article["title"],
                        summary=article.get("description", ""),
                        analysis=analysis,
                        trader_type=trader_type,
                        ttl_hours=24
                    )
                else:
                    logger.error(f"      ❌ Failed to post to {group_name}")

                # Small delay between group posts
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"   ❌ Error posting to group {group.get('group_id')}: {e}", exc_info=True)
                continue

        logger.info(f"   ✅ Posted to {posted_count}/{len(groups)} groups")
        return posted_count > 0
    
    async def manual_check(self) -> Dict[str, Any]:
        """
        Manually trigger a hot news check (for testing/admin commands).
        
        Returns:
            Status dictionary with results
        """
        logger.info("Manual hot news check triggered")
        
        try:
            hot_articles = self.news_fetcher.fetch_hot_news(limit=5)
            
            return {
                "success": True,
                "articles_found": len(hot_articles),
                "articles": [
                    {
                        "title": a["title"],
                        "importance": a.get("importance_score", 0),
                        "hot": a.get("hot", False),
                        "important": a.get("important", False)
                    }
                    for a in hot_articles
                ]
            }
        except Exception as e:
            logger.error(f"Error in manual check: {e}")
            return {
                "success": False,
                "error": str(e)
            }

