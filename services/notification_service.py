"""
Notification service for subscription system.
Handles sending automated notifications for trial warnings, payment confirmations, etc.
"""

import logging
from typing import Optional
from datetime import datetime, timedelta
from telegram import Bot
from telegram.error import TelegramError
from core.metrics import MetricsCollector

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service for sending subscription-related notifications.
    
    Features:
    - Trial expiration warnings
    - Payment confirmation messages
    - Subscription renewal reminders
    - Grace period notifications
    - Expiration notices
    """
    
    def __init__(
        self,
        bot: Optional[Bot] = None,
        metrics: Optional[MetricsCollector] = None
    ):
        """Initialize notification service."""
        self.bot = bot
        self.metrics = metrics or MetricsCollector()
    
    def set_bot(self, bot: Bot):
        """Set the bot instance."""
        self.bot = bot
    
    async def send_notification(
        self,
        group_id: int,
        message: str,
        parse_mode: str = "HTML"
    ) -> bool:
        """
        Send a notification message to a group.
        
        Args:
            group_id: Telegram group ID
            message: Message text
            parse_mode: Message parse mode (HTML or Markdown)
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.bot:
            logger.error("Bot instance not set in NotificationService")
            return False
        
        try:
            await self.bot.send_message(
                chat_id=group_id,
                text=message,
                parse_mode=parse_mode,
                disable_web_page_preview=True
            )
            
            self.metrics.inc_counter("notifications_sent_total")
            logger.info(f"Notification sent to group {group_id}")
            return True
            
        except TelegramError as e:
            logger.error(f"Telegram error sending notification to group {group_id}: {e}")
            self.metrics.inc_counter("notifications_failed_total")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending notification to group {group_id}: {e}", exc_info=True)
            self.metrics.inc_counter("notifications_failed_total")
            return False
    
    async def send_trial_started_notification(
        self,
        group_id: int,
        trial_days: int,
        trial_end_date: datetime
    ) -> bool:
        """
        Send notification when trial starts.
        
        Args:
            group_id: Telegram group ID
            trial_days: Number of trial days
            trial_end_date: Trial expiration date
            
        Returns:
            True if sent successfully
        """
        message = (
            f"🎉 <b>Welcome to AI Market Insight Bot!</b>\n\n"
            f"✅ Your {trial_days}-day free trial has started!\n\n"
            f"📅 <b>Trial Period:</b>\n"
            f"   • Starts: {datetime.now().strftime('%B %d, %Y')}\n"
            f"   • Ends: {trial_end_date.strftime('%B %d, %Y')}\n\n"
            f"🚀 <b>What You Get:</b>\n"
            f"   • Real-time crypto news alerts 24/7\n"
            f"   • AI-powered market impact analysis\n"
            f"   • Hot news posted immediately\n"
            f"   • Customized for your trading style\n\n"
            f"💡 <b>Commands:</b>\n"
            f"   • /subscription - Check your trial status\n"
            f"   • /renew - View subscription plans\n\n"
            f"Enjoy your trial! 🎊"
        )
        
        success = await self.send_notification(group_id, message)
        if success:
            self.metrics.inc_counter("trial_started_notifications")
        return success
    
    async def send_trial_warning_notification(
        self,
        group_id: int,
        days_remaining: int,
        trial_end_date: datetime
    ) -> bool:
        """
        Send trial expiration warning.
        
        Args:
            group_id: Telegram group ID
            days_remaining: Days until trial expires
            trial_end_date: Trial expiration date
            
        Returns:
            True if sent successfully
        """
        if days_remaining <= 1:
            urgency = "⚠️ <b>URGENT</b>"
            emoji = "🚨"
        elif days_remaining <= 3:
            urgency = "⚠️ <b>Important</b>"
            emoji = "⏰"
        else:
            urgency = "📢 <b>Reminder</b>"
            emoji = "📅"
        
        message = (
            f"{urgency}\n\n"
            f"{emoji} Your free trial expires in <b>{days_remaining} day{'s' if days_remaining != 1 else ''}</b>!\n\n"
            f"📅 <b>Trial Ends:</b> {trial_end_date.strftime('%B %d, %Y at %I:%M %p UTC')}\n\n"
            f"💰 <b>Continue Receiving News:</b>\n"
            f"   • Subscribe for just $15/month\n"
            f"   • Pay with cryptocurrency (BTC, ETH, USDT, etc.)\n"
            f"   • Instant activation after payment\n\n"
            f"🔄 <b>Renew Now:</b>\n"
            f"   Use /renew to see payment options\n\n"
            f"❓ Questions? Contact support."
        )
        
        success = await self.send_notification(group_id, message)
        if success:
            self.metrics.inc_counter("trial_warning_notifications")
        return success
    
    async def send_trial_expired_notification(
        self,
        group_id: int,
        grace_period_days: int,
        grace_period_end: datetime
    ) -> bool:
        """
        Send notification when trial expires.
        
        Args:
            group_id: Telegram group ID
            grace_period_days: Number of grace period days
            grace_period_end: Grace period end date
            
        Returns:
            True if sent successfully
        """
        message = (
            f"⏰ <b>Trial Period Expired</b>\n\n"
            f"Your {grace_period_days}-day free trial has ended.\n\n"
            f"🎁 <b>Grace Period Active:</b>\n"
            f"   • You have {grace_period_days} days to renew\n"
            f"   • News posting will continue during grace period\n"
            f"   • Grace period ends: {grace_period_end.strftime('%B %d, %Y')}\n\n"
            f"💰 <b>Subscribe Now:</b>\n"
            f"   • Only $15/month\n"
            f"   • Pay with crypto (BTC, ETH, USDT, USDC, BNB, TRX)\n"
            f"   • Instant activation\n\n"
            f"🔄 <b>Renew:</b> Use /renew command\n\n"
            f"⚠️ After grace period, news posting will stop until you subscribe."
        )
        
        success = await self.send_notification(group_id, message)
        if success:
            self.metrics.inc_counter("trial_expired_notifications")
        return success
    
    async def send_grace_period_warning_notification(
        self,
        group_id: int,
        days_remaining: int,
        grace_period_end: datetime
    ) -> bool:
        """
        Send grace period expiration warning.
        
        Args:
            group_id: Telegram group ID
            days_remaining: Days until grace period expires
            grace_period_end: Grace period end date
            
        Returns:
            True if sent successfully
        """
        message = (
            f"🚨 <b>URGENT: Grace Period Ending Soon</b>\n\n"
            f"⏰ Your grace period expires in <b>{days_remaining} day{'s' if days_remaining != 1 else ''}</b>!\n\n"
            f"📅 <b>Grace Period Ends:</b> {grace_period_end.strftime('%B %d, %Y at %I:%M %p UTC')}\n\n"
            f"⚠️ <b>What Happens Next:</b>\n"
            f"   • News posting will STOP after grace period\n"
            f"   • You'll need to subscribe to resume service\n\n"
            f"💰 <b>Subscribe Now - $15/month:</b>\n"
            f"   • Instant activation\n"
            f"   • Pay with cryptocurrency\n"
            f"   • Uninterrupted news delivery\n\n"
            f"🔄 <b>Renew:</b> Use /renew command immediately\n\n"
            f"Don't miss out on critical market updates!"
        )
        
        success = await self.send_notification(group_id, message)
        if success:
            self.metrics.inc_counter("grace_period_warning_notifications")
        return success
    
    async def send_subscription_expired_notification(
        self,
        group_id: int
    ) -> bool:
        """
        Send notification when subscription fully expires.
        
        Args:
            group_id: Telegram group ID
            
        Returns:
            True if sent successfully
        """
        message = (
            f"❌ <b>Subscription Expired</b>\n\n"
            f"Your grace period has ended and news posting has been stopped.\n\n"
            f"💰 <b>Reactivate Your Subscription:</b>\n"
            f"   • Only $15/month\n"
            f"   • Pay with cryptocurrency\n"
            f"   • Instant reactivation\n\n"
            f"🔄 <b>Subscribe:</b> Use /renew command\n\n"
            f"We'll be here when you're ready to resume! 👋"
        )
        
        success = await self.send_notification(group_id, message)
        if success:
            self.metrics.inc_counter("subscription_expired_notifications")
        return success
    
    async def send_payment_received_notification(
        self,
        group_id: int,
        amount_usd: float,
        currency: str
    ) -> bool:
        """
        Send notification when payment is received.
        
        Args:
            group_id: Telegram group ID
            amount_usd: Payment amount in USD
            currency: Cryptocurrency used
            
        Returns:
            True if sent successfully
        """
        message = (
            f"✅ <b>Payment Received!</b>\n\n"
            f"🎉 Your payment has been confirmed!\n\n"
            f"💰 <b>Payment Details:</b>\n"
            f"   • Amount: ${amount_usd:.2f} USD\n"
            f"   • Currency: {currency.upper()}\n"
            f"   • Status: Confirmed\n\n"
            f"⏳ <b>Activation:</b>\n"
            f"   Your subscription is being activated...\n"
            f"   This usually takes a few seconds.\n\n"
            f"Thank you for subscribing! 🙏"
        )
        
        success = await self.send_notification(group_id, message)
        if success:
            self.metrics.inc_counter("payment_received_notifications")
        return success
    
    async def send_subscription_activated_notification(
        self,
        group_id: int,
        subscription_end_date: datetime,
        next_billing_date: datetime
    ) -> bool:
        """
        Send notification when subscription is activated.
        
        Args:
            group_id: Telegram group ID
            subscription_end_date: Subscription end date
            next_billing_date: Next billing date
            
        Returns:
            True if sent successfully
        """
        message = (
            f"🎊 <b>Subscription Activated!</b>\n\n"
            f"✅ Your subscription is now active!\n\n"
            f"📅 <b>Subscription Details:</b>\n"
            f"   • Status: Active\n"
            f"   • Valid Until: {subscription_end_date.strftime('%B %d, %Y')}\n"
            f"   • Next Billing: {next_billing_date.strftime('%B %d, %Y')}\n\n"
            f"🚀 <b>What's Included:</b>\n"
            f"   • Real-time crypto news 24/7\n"
            f"   • AI-powered market analysis\n"
            f"   • Hot news posted immediately\n"
            f"   • Unlimited news updates\n\n"
            f"💡 <b>Commands:</b>\n"
            f"   • /subscription - Check status\n"
            f"   • /renew - Renew subscription\n\n"
            f"Enjoy your premium service! 🎉"
        )
        
        success = await self.send_notification(group_id, message)
        if success:
            self.metrics.inc_counter("subscription_activated_notifications")
        return success

