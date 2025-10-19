"""
Posting service for AI Market Insight Bot.
Handles posting messages to Telegram groups with rate limiting.
"""

import logging
from typing import Optional, TYPE_CHECKING
from datetime import datetime, timedelta
from telegram import Bot
from telegram.error import TelegramError
from rate_limiter import ConcurrentPostingManager
from core.metrics import MetricsCollector

if TYPE_CHECKING:
    from services.subscription_service import SubscriptionService

logger = logging.getLogger(__name__)


class PostingService:
    """
    Service for posting messages to Telegram groups.

    Features:
    - Rate limiting to avoid Telegram API limits
    - Concurrent posting management
    - Subscription validation
    - Error handling and retries
    - Metrics tracking
    - Subscription expiration notifications
    """

    def __init__(
        self,
        bot: Optional[Bot],
        posting_manager: ConcurrentPostingManager,
        metrics: MetricsCollector,
        subscription_service: Optional['SubscriptionService'] = None
    ):
        """Initialize posting service."""
        self.bot = bot
        self.posting_manager = posting_manager
        self.metrics = metrics
        self.subscription_service = subscription_service
        # Track when we last sent expiration notifications to avoid spam
        self._last_expiration_notification = {}  # {group_id: datetime}
    
    async def post_to_group(
        self,
        group_id: int,
        message: str,
        parse_mode: str = "HTML"
    ) -> bool:
        """
        Post a message to a Telegram group.

        Checks subscription status before posting.

        Args:
            group_id: Telegram group ID
            message: Message text to post
            parse_mode: Message parse mode (HTML or Markdown)

        Returns:
            True if posted successfully, False otherwise
        """
        if not self.bot:
            logger.error("Bot instance not set in PostingService")
            return False

        # Check subscription status if service is available
        if self.subscription_service:
            posting_allowed = await self.subscription_service.is_posting_allowed(group_id)

            if not posting_allowed:
                logger.warning(f"Posting not allowed for group {group_id} - subscription expired or inactive")
                self.metrics.inc_counter("posts_blocked_subscription")

                # Send expiration notification to the group (once per day)
                await self._send_expiration_notification(group_id)

                return False

        try:
            # ✅ FIX: Use rate limiter directly, not post_context()
            await self.posting_manager.rate_limiter.acquire()

            await self.bot.send_message(
                chat_id=group_id,
                text=message,
                parse_mode=parse_mode,
                disable_web_page_preview=False
            )

            # ✅ FIX: Use inc_counter() not increment_counter()
            self.metrics.inc_counter("posts_sent_total")
            logger.info(f"Posted message to group {group_id}")
            return True

        except TelegramError as e:
            logger.error(f"Telegram error posting to group {group_id}: {e}")
            self.metrics.inc_counter("posts_failed_total")
            return False
        except Exception as e:
            logger.error(f"Unexpected error posting to group {group_id}: {e}", exc_info=True)
            self.metrics.inc_counter("posts_failed_total")
            return False
    
    def set_subscription_service(self, subscription_service: 'SubscriptionService'):
        """
        Set subscription service for posting validation.

        Args:
            subscription_service: SubscriptionService instance
        """
        self.subscription_service = subscription_service
        logger.info("Subscription service set in PostingService")

    async def _send_expiration_notification(self, group_id: int) -> bool:
        """
        Send a notification to the group about subscription expiration.
        Only sends once per day to avoid spam.

        Args:
            group_id: Telegram group ID

        Returns:
            True if notification was sent, False if skipped
        """
        logger.info(f"📧 Attempting to send expiration notification to group {group_id}")

        # Check if we already sent a notification today
        now = datetime.now()
        last_notification = self._last_expiration_notification.get(group_id)

        if last_notification:
            time_since_last = now - last_notification
            if time_since_last < timedelta(hours=24):
                logger.debug(f"Skipping expiration notification for group {group_id} - already sent today")
                return False

        try:
            # Get subscription details to craft appropriate message
            if not self.subscription_service:
                logger.error(f"❌ Cannot send expiration notification - subscription_service not set")
                return False

            logger.debug(f"Fetching subscription details for group {group_id}")
            subscription = await self.subscription_service.subscription_repo.find_by_group_id(group_id)

            if not subscription:
                # No subscription found
                notification_message = (
                    "⚠️ <b>Subscription Required</b>\n\n"
                    "This group doesn't have an active subscription.\n\n"
                    "💰 <b>Get Started:</b>\n"
                    "   • 15-day free trial available\n"
                    "   • Then only $15/month\n"
                    "   • Pay with cryptocurrency\n\n"
                    "🚀 <b>Start Trial:</b> Use /start command\n"
                    "📞 <b>Questions?</b> Contact support"
                )
            else:
                status = subscription.get('subscription_status', 'unknown')

                if status == 'trial':
                    # Trial expired
                    notification_message = (
                        "⏰ <b>Free Trial Expired</b>\n\n"
                        "Your 15-day free trial has ended.\n\n"
                        "💰 <b>Continue Receiving News:</b>\n"
                        "   • Subscribe for just $15/month\n"
                        "   • Pay with crypto (BTC, ETH, USDT, USDC, BNB, TRX)\n"
                        "   • Instant activation after payment\n\n"
                        "🔄 <b>Subscribe Now:</b> Use /renew command\n\n"
                        "❓ Questions? Contact support."
                    )
                elif status == 'expired':
                    # Subscription expired
                    notification_message = (
                        "❌ <b>Subscription Expired</b>\n\n"
                        "Your subscription has ended and news posting has been stopped.\n\n"
                        "💰 <b>Reactivate Your Subscription:</b>\n"
                        "   • Only $15/month\n"
                        "   • Pay with cryptocurrency\n"
                        "   • Instant reactivation\n\n"
                        "🔄 <b>Renew:</b> Use /renew command\n\n"
                        "We'll be here when you're ready to resume! 👋"
                    )
                elif status == 'grace_period':
                    # In grace period but posting blocked (shouldn't happen normally)
                    grace_end = subscription.get('grace_period_end_date')
                    notification_message = (
                        "⚠️ <b>Grace Period Active</b>\n\n"
                        "Your subscription has expired but you're in the grace period.\n\n"
                        "💰 <b>Renew Now to Continue:</b>\n"
                        "   • Only $15/month\n"
                        "   • Pay with cryptocurrency\n"
                        "   • Instant activation\n\n"
                        "🔄 <b>Renew:</b> Use /renew command\n\n"
                        f"⏰ Grace period ends soon. Renew to keep receiving news!"
                    )
                else:
                    # Unknown status
                    notification_message = (
                        "⚠️ <b>Subscription Issue</b>\n\n"
                        "There's an issue with your subscription status.\n\n"
                        "🔄 <b>Renew:</b> Use /renew command\n"
                        "📞 <b>Support:</b> Contact us for assistance"
                    )

            # Send the notification
            await self.bot.send_message(
                chat_id=group_id,
                text=notification_message,
                parse_mode="HTML"
            )

            # Update last notification time
            self._last_expiration_notification[group_id] = now

            logger.info(f"Sent subscription expiration notification to group {group_id}")
            self.metrics.inc_counter("expiration_notifications_sent")
            return True

        except TelegramError as e:
            logger.error(f"Failed to send expiration notification to group {group_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending expiration notification to group {group_id}: {e}", exc_info=True)
            return False

    async def post_to_multiple_groups(
        self,
        group_ids: list[int],
        message: str,
        parse_mode: str = "HTML"
    ) -> dict[int, bool]:
        """
        Post a message to multiple Telegram groups.

        Args:
            group_ids: List of Telegram group IDs
            message: Message text to post
            parse_mode: Message parse mode (HTML or Markdown)

        Returns:
            Dictionary mapping group_id to success status
        """
        results = {}

        for group_id in group_ids:
            success = await self.post_to_group(group_id, message, parse_mode)
            results[group_id] = success

        return results

