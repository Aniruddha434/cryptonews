"""
Enterprise AI Market Insight Bot - Clean Version
Modern UI with inline buttons and enterprise features.
"""

import logging
import sys
import asyncio
from datetime import datetime, timedelta, time, timezone
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

from config import (
    TELEGRAM_BOT_TOKEN, validate_config, POSTING_HOUR, POSTING_MINUTE, TIMEZONE,
    ENABLE_REALTIME_POSTING
)
from logging_config import setup_all_loggers, get_logger
from migrations import run_all_migrations

# Enterprise components
from core import (
    init_container,
    shutdown_container,
    setup_correlation_logging
)
from services import NewsService, UserService, AnalyticsService, SchedulerService
from services.realtime_news_service import RealtimeNewsService
from services.posting_service import PostingService
from handlers import UserHandlers, AdminHandlers

# Setup logging
setup_all_loggers()
setup_correlation_logging()
logger = get_logger('bot')


class EnterpriseBot:
    """Enterprise AI Market Insight Bot."""

    def __init__(self):
        """Initialize the bot."""
        if not validate_config():
            logger.error("Configuration validation failed. Check .env file.")
            sys.exit(1)

        # Run migrations
        logger.info("Running database migrations...")
        run_all_migrations()

        # Services (initialized in async init)
        self.services = None
        self.news_service = None
        self.user_service = None
        self.analytics_service = None
        self.scheduler_service = None
        self.posting_service = None
        self.realtime_news_service = None
        self.subscription_service = None
        self.payment_service = None
        self.notification_service = None
        self.subscription_checker_service = None
        self.user_handlers = None
        self.admin_handlers = None
        self.app = None
        self.scheduler = None
        self.realtime_task = None  # Background task for real-time monitoring
        self.subscription_check_task = None  # Background task for subscription checking
        self.webhook_runner = None  # Webhook server runner
        self.webhook_site = None    # Webhook server site

        logger.info("Bot initialized")
    
    async def initialize(self):
        """Initialize async components."""
        logger.info("Initializing enterprise services...")

        # Initialize dependency container
        self.services = await init_container()

        # Create services
        self.news_service = NewsService(
            news_repo=self.services.news_repo,
            news_fetcher=self.services.news_fetcher,
            ai_analyzer=self.services.ai_analyzer,
            cache=self.services.cache,
            metrics=self.services.metrics,
            gemini_circuit_breaker=self.services.gemini_circuit_breaker,
            news_api_circuit_breaker=self.services.news_api_circuit_breaker
        )

        # Create notification service
        from services.notification_service import NotificationService
        self.notification_service = NotificationService(
            bot=None,  # Will be set after app is created
            metrics=self.services.metrics
        )

        # Create subscription service
        from services.subscription_service import SubscriptionService
        self.subscription_service = SubscriptionService(
            subscription_repo=self.services.subscription_repo,
            payment_repo=self.services.payment_repo,
            group_repo=self.services.group_repo,
            metrics=self.services.metrics,
            notification_service=self.notification_service
        )

        # Create payment service
        from services.payment_service import PaymentService
        self.payment_service = PaymentService(
            payment_repo=self.services.payment_repo,
            subscription_repo=self.services.subscription_repo,
            metrics=self.services.metrics
        )

        self.user_service = UserService(
            user_repo=self.services.user_repo,
            group_repo=self.services.group_repo,
            metrics=self.services.metrics,
            subscription_service=self.subscription_service
        )

        self.analytics_service = AnalyticsService(
            analytics_repo=self.services.analytics_repo,
            metrics=self.services.metrics
        )

        # Create posting service
        self.posting_service = PostingService(
            bot=None,  # Will be set after app is created
            posting_manager=self.services.posting_manager,
            metrics=self.services.metrics,
            subscription_service=self.subscription_service
        )

        # Create subscription checker service
        from services.subscription_checker_service import SubscriptionCheckerService
        self.subscription_checker_service = SubscriptionCheckerService(
            subscription_repo=self.services.subscription_repo,
            group_repo=self.services.group_repo,
            notification_service=self.notification_service,
            metrics=self.services.metrics
        )

        # Create real-time news service
        self.realtime_news_service = RealtimeNewsService(
            news_fetcher=self.services.news_fetcher,
            news_service=self.news_service,
            posting_service=self.posting_service,
            news_repo=self.services.news_repo,
            group_repo=self.services.group_repo
        )

        # Create handlers
        self.user_handlers = UserHandlers(
            user_service=self.user_service,
            news_service=self.news_service,
            analytics_service=self.analytics_service,
            subscription_service=self.subscription_service,
            payment_service=self.payment_service
        )

        self.admin_handlers = AdminHandlers(
            user_service=self.user_service,
            analytics_service=self.analytics_service,
            realtime_news_service=self.realtime_news_service,  # For /testnews command
            subscription_service=self.subscription_service  # For subscription stats
        )

        logger.info("✅ Services initialized")

    async def initialize_scheduler(self):
        """Initialize scheduler service and APScheduler."""
        logger.info("Initializing scheduler...")

        # Create scheduler service (needs bot instance, so we do this after app is created)
        self.scheduler_service = SchedulerService(
            bot=self.app.bot,
            group_repo=self.services.group_repo,
            news_service=self.news_service,
            posting_manager=self.services.posting_manager,
            metrics=self.services.metrics
        )

        # Create APScheduler
        self.scheduler = AsyncIOScheduler(timezone=pytz.timezone(TIMEZONE))

        # Add daily posting job
        self.scheduler.add_job(
            self.scheduler_service.run_daily_posting,
            trigger=CronTrigger(hour=POSTING_HOUR, minute=POSTING_MINUTE, timezone=TIMEZONE),
            id='daily_posting',
            name='Daily News Posting',
            replace_existing=True
        )

        logger.info(f"✅ Scheduler configured for {POSTING_HOUR:02d}:{POSTING_MINUTE:02d} {TIMEZONE}")

    def start_scheduler(self):
        """Start the scheduler."""
        if self.scheduler and not self.scheduler.running:
            self.scheduler.start()
            logger.info("✅ Scheduler started")

    def stop_scheduler(self):
        """Stop the scheduler."""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("✅ Scheduler stopped")
    
    def setup_handlers(self):
        """Setup command and callback handlers."""
        logger.info("Setting up handlers...")

        # User commands
        self.app.add_handler(CommandHandler("start", self.user_handlers.handle_start))
        self.app.add_handler(CommandHandler("help", self.user_handlers.handle_help))
        self.app.add_handler(CommandHandler("subscription", self.user_handlers.handle_subscription))
        self.app.add_handler(CommandHandler("renew", self.user_handlers.handle_renew))

        # Channel management commands (private chat only)
        self.app.add_handler(CommandHandler("addchannel", self.user_handlers.handle_add_channel))
        self.app.add_handler(CommandHandler("registerchannel", self.user_handlers.handle_register_channel))
        self.app.add_handler(CommandHandler("mychannels", self.user_handlers.handle_my_channels))
        self.app.add_handler(CommandHandler("channelstatus", self.user_handlers.handle_channel_status))
        self.app.add_handler(CommandHandler("renewchannel", self.user_handlers.handle_renew_channel))
        self.app.add_handler(CommandHandler("deletechannel", self.user_handlers.handle_delete_channel))

        # Admin commands
        self.app.add_handler(CommandHandler("setup", self.admin_handlers.handle_setup))
        self.app.add_handler(CommandHandler("admin", self.admin_handlers.handle_admin))
        self.app.add_handler(CommandHandler("pause", self.admin_handlers.handle_pause))
        self.app.add_handler(CommandHandler("resume", self.admin_handlers.handle_resume))
        self.app.add_handler(CommandHandler("remove", self.admin_handlers.handle_remove))
        self.app.add_handler(CommandHandler("status", self.admin_handlers.handle_status))
        self.app.add_handler(CommandHandler("testnews", self.admin_handlers.handle_testnews))

        # User callbacks (onboarding only - no personal news/stats)
        self.app.add_handler(CallbackQueryHandler(
            self.user_handlers.handle_help_callback,
            pattern="^show_help$"
        ))
        self.app.add_handler(CallbackQueryHandler(
            self.user_handlers.handle_setup_guide_callback,
            pattern="^show_setup_guide$"
        ))
        self.app.add_handler(CallbackQueryHandler(
            self.user_handlers.handle_trader_types_callback,
            pattern="^show_trader_types$"
        ))
        self.app.add_handler(CallbackQueryHandler(
            self.user_handlers.handle_back_to_start_callback,
            pattern="^back_to_start$"
        ))
        self.app.add_handler(CallbackQueryHandler(
            self.user_handlers.handle_preview_sample_news_callback,
            pattern="^preview_sample_news$"
        ))

        # Channel setup callbacks
        self.app.add_handler(CallbackQueryHandler(
            self.user_handlers.handle_channel_setup_callback,
            pattern="^show_channel_setup$"
        ))
        self.app.add_handler(CallbackQueryHandler(
            self.user_handlers.handle_detailed_channel_guide_callback,
            pattern="^show_detailed_channel_guide$"
        ))

        # Onboarding flow callbacks
        self.app.add_handler(CallbackQueryHandler(
            self.user_handlers.handle_onboarding_step_1_callback,
            pattern="^onboarding_step_1$"
        ))
        self.app.add_handler(CallbackQueryHandler(
            self.user_handlers.handle_onboarding_step_2_callback,
            pattern="^onboarding_step_2$"
        ))
        self.app.add_handler(CallbackQueryHandler(
            self.user_handlers.handle_onboarding_step_3_callback,
            pattern="^onboarding_step_3$"
        ))
        self.app.add_handler(CallbackQueryHandler(
            self.user_handlers.handle_onboarding_step_4_callback,
            pattern="^onboarding_step_4$"
        ))

        # Admin callbacks
        self.app.add_handler(CallbackQueryHandler(
            self.admin_handlers.handle_toggle_posting_callback,
            pattern="^admin_toggle_posting$"
        ))
        self.app.add_handler(CallbackQueryHandler(
            self.admin_handlers.handle_configure_traders_callback,
            pattern="^admin_configure_traders$"
        ))
        self.app.add_handler(CallbackQueryHandler(
            self.admin_handlers.handle_set_trader_callback,
            pattern="^admin_set_trader_"
        ))
        self.app.add_handler(CallbackQueryHandler(
            self.admin_handlers.handle_set_schedule_callback,
            pattern="^admin_set_schedule$"
        ))
        self.app.add_handler(CallbackQueryHandler(
            self.admin_handlers.handle_schedule_time_callback,
            pattern="^admin_schedule_"
        ))
        self.app.add_handler(CallbackQueryHandler(
            self.admin_handlers.handle_view_stats_callback,
            pattern="^admin_view_stats$"
        ))
        self.app.add_handler(CallbackQueryHandler(
            self.admin_handlers.handle_view_settings_callback,
            pattern="^admin_view_settings$"
        ))
        self.app.add_handler(CallbackQueryHandler(
            self.admin_handlers.handle_refresh_admin_callback,
            pattern="^admin_refresh$"
        ))

        # Payment callbacks
        self.app.add_handler(CallbackQueryHandler(
            self.user_handlers.handle_payment_callback,
            pattern="^pay_"
        ))
        self.app.add_handler(CallbackQueryHandler(
            self.user_handlers.handle_check_payment_callback,
            pattern="^check_payment_"
        ))

        logger.info("✅ Handlers configured")
    
    async def post_startup(self, application: Application):
        """Post-startup hook."""
        logger.info("🚀 Bot started successfully!")
        logger.info("✅ Enterprise components active")

        # Set bot instance in posting service and notification service
        self.posting_service.bot = application.bot
        self.notification_service.set_bot(application.bot)

        # Start webhook server for payment notifications
        try:
            from handlers.webhook_handler import create_webhook_server
            from config import WEBHOOK_PORT

            webhook_port = WEBHOOK_PORT

            _, self.webhook_runner, self.webhook_site = await create_webhook_server(
                payment_service=self.payment_service,
                subscription_service=self.subscription_service,
                host='0.0.0.0',
                port=webhook_port
            )
            logger.info(f"💳 Payment webhook server started on port {webhook_port}")
        except Exception as e:
            logger.error(f"Failed to start webhook server: {e}", exc_info=True)
            logger.warning("Bot will continue without webhook server")

        # Start subscription checker (runs daily at 9 AM UTC)
        import asyncio
        self.subscription_check_task = asyncio.create_task(
            self._run_subscription_checker()
        )
        logger.info("💳 Subscription checker started (daily at 9:00 AM UTC)")

        # Start real-time news monitoring
        if ENABLE_REALTIME_POSTING:
            self.realtime_task = asyncio.create_task(
                self.realtime_news_service.start_monitoring()
            )
            logger.info("🔥 Real-time hot news monitoring started (24/7)")
            logger.info("📊 Legacy daily scheduler DISABLED (using real-time posting only)")
        else:
            # Only use legacy scheduler if real-time posting is disabled
            await self.initialize_scheduler()
            self.start_scheduler()
            logger.info("⏰ Using scheduled posting only (real-time disabled)")

        # Log circuit breaker states
        gemini_state = self.services.gemini_circuit_breaker.get_state()
        news_state = self.services.news_api_circuit_breaker.get_state()
        logger.info(f"Gemini API: {gemini_state['state']}")
        logger.info(f"News API: {news_state['state']}")

        # Log scheduler status
        logger.info(f"📅 Scheduler: Daily posting at {POSTING_HOUR:02d}:{POSTING_MINUTE:02d} {TIMEZONE}")

    async def pre_shutdown(self, application: Application):
        """Pre-shutdown hook."""
        logger.info("🛑 Shutting down...")

        # Stop webhook server
        if self.webhook_runner:
            try:
                from handlers.webhook_handler import shutdown_webhook_server
                await shutdown_webhook_server(self.webhook_runner)
            except Exception as e:
                logger.error(f"Error shutting down webhook server: {e}", exc_info=True)

        # Stop subscription checker
        if self.subscription_check_task:
            self.subscription_check_task.cancel()
            try:
                await self.subscription_check_task
            except asyncio.CancelledError:
                pass
            logger.info("✅ Subscription checker stopped")

        # Stop real-time monitoring
        if self.realtime_news_service:
            self.realtime_news_service.stop_monitoring()
            if self.realtime_task:
                self.realtime_task.cancel()
                try:
                    await self.realtime_task
                except asyncio.CancelledError:
                    pass
            logger.info("✅ Real-time monitoring stopped")

        # Stop scheduler
        self.stop_scheduler()

        # Get final metrics
        metrics = await self.services.metrics.get_metrics()
        cache_stats = await self.services.cache.get_stats()

        logger.info(f"Cache hit rate: {cache_stats['hit_rate']:.2%}")
        logger.info(f"Total requests: {metrics['counters'].get('bot_requests_total', {}).get('value', 0)}")

        # Shutdown
        await shutdown_container()
        logger.info("✅ Shutdown complete")

    async def _run_subscription_checker(self):
        """
        Background task to run subscription checker daily at 9 AM UTC.
        """
        import asyncio

        logger.info("Subscription checker task started")

        while True:
            try:
                # Calculate next run time (9 AM UTC)
                now = datetime.now(timezone.utc)
                target_time = time(9, 0)  # 9:00 AM UTC

                # Calculate next occurrence
                next_run = datetime.combine(now.date(), target_time, tzinfo=timezone.utc)
                if now.time() >= target_time:
                    # If it's already past 9 AM today, schedule for tomorrow
                    next_run += timedelta(days=1)

                # Calculate sleep duration
                sleep_seconds = (next_run - now).total_seconds()

                logger.info(f"Next subscription check scheduled for: {next_run.isoformat()} UTC")
                logger.info(f"Sleeping for {sleep_seconds / 3600:.2f} hours...")

                # Sleep until next run time
                await asyncio.sleep(sleep_seconds)

                # Run the subscription check
                logger.info("Running daily subscription check...")
                await self.subscription_checker_service.check_all_subscriptions()
                logger.info("Daily subscription check completed")

            except asyncio.CancelledError:
                logger.info("Subscription checker task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in subscription checker task: {e}", exc_info=True)
                # Sleep for 1 hour before retrying on error
                await asyncio.sleep(3600)

    async def run(self):
        """Run the bot."""
        logger.info("Starting Enterprise Bot...")
        
        # Initialize services
        await self.initialize()
        
        # Create application
        self.app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

        # Setup handlers
        self.setup_handlers()

        # Add hooks
        self.app.post_init = self.post_startup
        self.app.post_shutdown = self.pre_shutdown

        # Start bot
        logger.info("Starting polling...")
        await self.app.initialize()
        await self.app.start()

        # Clear any existing webhooks to prevent conflicts
        try:
            logger.info("Clearing any existing webhooks...")
            await self.app.bot.delete_webhook(drop_pending_updates=True)
            logger.info("✅ Webhooks cleared successfully")

            # Wait for any old instances to shut down (deployment race condition fix)
            logger.info("⏳ Waiting 20 seconds for old instances to terminate...")
            await asyncio.sleep(20)
            logger.info("✅ Ready to start polling")
        except Exception as e:
            logger.warning(f"Could not clear webhooks: {e}")

        await self.app.updater.start_polling(allowed_updates=Update.ALL_TYPES)

        logger.info("✅ Bot is running! Press Ctrl+C to stop.")

        # ✅ FIX: Manually call post_startup since we're not using run_polling()
        await self.post_startup(self.app)

        # Keep running
        import asyncio
        try:
            await asyncio.Event().wait()
        except (KeyboardInterrupt, asyncio.CancelledError):
            logger.info("Shutdown signal received")
        finally:
            # ✅ FIX: Stop updater before shutting down
            try:
                await self.app.updater.stop()
                logger.info("Updater stopped")
            except Exception as e:
                logger.warning(f"Error stopping updater: {e}")

            try:
                await self.app.stop()
                logger.info("Application stopped")
            except Exception as e:
                logger.warning(f"Error stopping application: {e}")

            try:
                await self.app.shutdown()
                logger.info("Application shutdown complete")
            except Exception as e:
                logger.warning(f"Error during shutdown: {e}")


def main():
    """Main entry point."""
    import asyncio
    
    bot = EnterpriseBot()
    
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

