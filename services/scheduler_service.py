"""
Scheduler service for automated group posting.
Handles daily news posting to registered groups at configured times.
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError, Forbidden, BadRequest

from core.metrics import MetricsCollector
from repositories.group_repository import GroupRepository
from services.news_service import NewsService
from rate_limiter import ConcurrentPostingManager

logger = logging.getLogger(__name__)


class SchedulerService:
    """
    Service for automated news posting to groups.
    
    Provides:
    - Scheduled posting to active groups
    - Permission verification before posting
    - Retry logic with exponential backoff
    - Error handling and logging
    - Metrics tracking
    """
    
    def __init__(
        self,
        bot: Bot,
        group_repo: GroupRepository,
        news_service: NewsService,
        posting_manager: ConcurrentPostingManager,
        metrics: MetricsCollector
    ):
        """
        Initialize scheduler service.
        
        Args:
            bot: Telegram bot instance
            group_repo: Group repository
            news_service: News service for fetching and analyzing news
            posting_manager: Concurrent posting manager for rate limiting
            metrics: Metrics collector
        """
        self.bot = bot
        self.group_repo = group_repo
        self.news_service = news_service
        self.posting_manager = posting_manager
        self.metrics = metrics
        
        logger.info("SchedulerService initialized")
    
    async def check_bot_permissions(self, group_id: int) -> bool:
        """
        Check if bot has permission to post in group.
        
        Args:
            group_id: Telegram group ID
            
        Returns:
            True if bot can post, False otherwise
        """
        try:
            # Get bot's member status in the group
            bot_member = await self.bot.get_chat_member(group_id, self.bot.id)
            
            # Check if bot can send messages
            if bot_member.status == 'left' or bot_member.status == 'kicked':
                logger.warning(f"Bot is not a member of group {group_id}")
                return False
            
            # For administrators, check can_post_messages permission
            if bot_member.status == 'administrator':
                if not bot_member.can_post_messages:
                    logger.warning(f"Bot lacks post permission in group {group_id}")
                    return False
            
            return True
            
        except Forbidden:
            logger.warning(f"Bot was removed from group {group_id}")
            return False
        except BadRequest as e:
            logger.error(f"Error checking permissions for group {group_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error checking permissions for group {group_id}: {e}")
            return False
    
    async def generate_news_for_group(self, group: Dict[str, Any]) -> Optional[str]:
        """
        Generate AI-analyzed news content for a group.
        
        Args:
            group: Group data dictionary
            
        Returns:
            Formatted news message or None if failed
        """
        try:
            trader_type = group.get('trader_type', 'investor')
            group_name = group.get('group_name', 'Unknown')
            
            logger.info(f"Generating news for group {group_name} (trader_type: {trader_type})")
            
            # Fetch trending news
            articles = await self.news_service.fetch_trending_news(limit=5)
            
            if not articles:
                logger.warning(f"No articles fetched for group {group_name}")
                return None
            
            # Analyze articles with AI
            analyzed_articles = []
            for article in articles[:3]:  # Analyze top 3 articles
                try:
                    analysis = await self.news_service.analyze_article(
                        title=article.get('title', ''),
                        summary=article.get('description', ''),
                        url=article.get('url', ''),
                        trader_type=trader_type
                    )
                    
                    analyzed_articles.append({
                        'title': article.get('title', ''),
                        'url': article.get('url', ''),
                        'analysis': analysis
                    })
                    
                except Exception as e:
                    logger.error(f"Error analyzing article: {e}")
                    continue
            
            if not analyzed_articles:
                logger.warning(f"No articles analyzed for group {group_name}")
                return None
            
            # Format message
            message = self._format_news_message(analyzed_articles, trader_type)
            return message
            
        except Exception as e:
            logger.error(f"Error generating news for group {group.get('group_name')}: {e}", exc_info=True)
            return None
    
    def _format_news_message(self, articles: List[Dict[str, Any]], trader_type: str) -> str:
        """
        Format analyzed articles into a message.
        
        Args:
            articles: List of analyzed articles
            trader_type: Trader type for personalization
            
        Returns:
            Formatted message string
        """
        trader_emoji = {
            'scalper': '⚡',
            'day_trader': '🎯',
            'swing_trader': '🌊',
            'investor': '🏛️'
        }
        
        emoji = trader_emoji.get(trader_type, '📰')
        trader_name = trader_type.replace('_', ' ').title()
        
        message = f"{emoji} **Daily AI Market Insights for {trader_name}s**\n\n"
        message += f"📅 {datetime.now().strftime('%B %d, %Y')}\n"
        message += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        for i, article in enumerate(articles, 1):
            message += f"**{i}. {article['title']}**\n\n"
            message += f"🤖 **AI Analysis:**\n{article['analysis']}\n\n"
            message += f"🔗 [Read More]({article['url']})\n\n"
            message += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        message += "💡 *Powered by AI Analysis | Stay Informed, Trade Smart*"
        
        return message
    
    async def post_to_group(self, group: Dict[str, Any]) -> bool:
        """
        Post news to a single group.
        
        Args:
            group: Group data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        group_id = group['group_id']
        group_name = group.get('group_name', 'Unknown')
        
        try:
            # Check bot permissions
            if not await self.check_bot_permissions(group_id):
                logger.warning(f"Skipping group {group_name} - insufficient permissions")
                await self.group_repo.update_active_status(group_id, False)
                return False
            
            # Generate news content
            message = await self.generate_news_for_group(group)
            
            if not message:
                logger.warning(f"No content generated for group {group_name}")
                return False
            
            # Post with rate limiting and retry logic
            async def post_func(gid):
                await self.bot.send_message(
                    chat_id=gid,
                    text=message,
                    parse_mode='Markdown',
                    disable_web_page_preview=False
                )
            
            success = await self.posting_manager.post_with_retry(
                post_func,
                group_id
            )
            
            if success:
                # Update last_post timestamp
                await self.group_repo.update_last_post(group_id)
                self.metrics.inc_counter("scheduled_posts_success")
                logger.info(f"✅ Successfully posted to group {group_name}")
            else:
                self.metrics.inc_counter("scheduled_posts_failed")
                logger.error(f"❌ Failed to post to group {group_name}")
            
            return success
            
        except Forbidden:
            logger.warning(f"Bot was blocked/removed from group {group_name}")
            await self.group_repo.update_active_status(group_id, False)
            return False
        except Exception as e:
            logger.error(f"Error posting to group {group_name}: {e}", exc_info=True)
            self.metrics.inc_counter("scheduled_posts_failed")
            return False
    
    async def run_daily_posting(self):
        """
        Run daily posting job for all active groups.
        This method is called by the scheduler.
        """
        logger.info("🚀 Starting daily posting job...")
        
        try:
            # Get all active groups
            active_groups = await self.group_repo.find_active()
            
            if not active_groups:
                logger.info("No active groups found for posting")
                return
            
            logger.info(f"Found {len(active_groups)} active groups")
            
            # Post to all groups concurrently
            tasks = [self.post_to_group(group) for group in active_groups]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Count successes and failures
            successes = sum(1 for r in results if r is True)
            failures = len(results) - successes
            
            logger.info(f"✅ Daily posting complete: {successes} successful, {failures} failed")
            
            # Update metrics
            self.metrics.inc_counter("daily_posting_jobs_total")
            
        except Exception as e:
            logger.error(f"Error in daily posting job: {e}", exc_info=True)
            self.metrics.inc_counter("daily_posting_jobs_failed")

