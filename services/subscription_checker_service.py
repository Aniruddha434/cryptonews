"""
Subscription Checker Service for AI Market Insight Bot.
Handles automated checking of trial and subscription expiration.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class SubscriptionCheckerService:
    """
    Service for checking subscription and trial expiration.
    
    Provides:
    - Daily trial expiration checks
    - Trial warning notifications (7, 3, 1 days)
    - Grace period monitoring
    - Subscription expiration handling
    - Automatic group disabling
    """
    
    def __init__(
        self,
        subscription_repo,
        group_repo,
        notification_service,
        metrics
    ):
        """
        Initialize subscription checker service.
        
        Args:
            subscription_repo: SubscriptionRepository instance
            group_repo: GroupRepository instance
            notification_service: NotificationService instance
            metrics: MetricsCollector instance
        """
        self.subscription_repo = subscription_repo
        self.group_repo = group_repo
        self.notification_service = notification_service
        self.metrics = metrics
        
        # Grace period duration (days)
        self.GRACE_PERIOD_DAYS = 3
        
        logger.info("SubscriptionCheckerService initialized")
    
    async def check_all_subscriptions(self):
        """
        Main method to check all subscriptions.
        Should be run daily by scheduler.
        """
        try:
            logger.info("Starting daily subscription check...")
            
            # Check trial warnings
            await self.check_trial_warnings()
            
            # Check expired trials
            await self.check_expired_trials()
            
            # Check grace period warnings
            await self.check_grace_period_warnings()
            
            # Check expired subscriptions
            await self.check_expired_subscriptions()
            
            logger.info("Daily subscription check completed")
            self.metrics.inc_counter("subscription_checks_completed")
            
        except Exception as e:
            logger.error(f"Error in daily subscription check: {e}", exc_info=True)
            self.metrics.inc_counter("subscription_checks_failed")
    
    async def check_trial_warnings(self):
        """
        Check for trials expiring soon and send warnings.
        Sends notifications at 7, 3, and 1 days before expiration.
        """
        try:
            logger.info("Checking trial warnings...")
            
            # Warning thresholds (days before expiration)
            warning_days = [7, 3, 1]
            
            for days in warning_days:
                # Calculate target date
                target_date = datetime.now() + timedelta(days=days)
                target_date_str = target_date.date().isoformat()
                
                # Find trials expiring on target date
                trials = await self._find_trials_expiring_on_date(target_date_str)
                
                logger.info(f"Found {len(trials)} trials expiring in {days} day(s)")
                
                for trial in trials:
                    # Check if warning already sent today
                    if await self._was_warning_sent_today(trial['subscription_id'], days):
                        logger.debug(f"Warning already sent for subscription {trial['subscription_id']}")
                        continue
                    
                    # Send warning notification
                    try:
                        trial_end = datetime.fromisoformat(trial['trial_end_date'])
                        
                        await self.notification_service.send_trial_warning_notification(
                            group_id=trial['group_id'],
                            days_remaining=days,
                            trial_end_date=trial_end
                        )
                        
                        # Log event
                        await self.subscription_repo.log_event(
                            trial['subscription_id'],
                            trial['group_id'],
                            f'trial_warning_{days}d',
                            {'days_remaining': days, 'warning_sent': True}
                        )
                        
                        self.metrics.inc_counter(f"trial_warnings_sent_{days}d")
                        logger.info(f"Sent {days}-day warning for group {trial['group_id']}")
                        
                    except Exception as e:
                        logger.error(f"Failed to send trial warning for group {trial['group_id']}: {e}")
            
            logger.info("Trial warnings check completed")
            
        except Exception as e:
            logger.error(f"Error checking trial warnings: {e}", exc_info=True)
    
    async def check_expired_trials(self):
        """
        Check for expired trials and activate grace period.
        """
        try:
            logger.info("Checking expired trials...")
            
            # Find trials that expired today
            now = datetime.now()
            today_str = now.date().isoformat()
            
            expired_trials = await self._find_trials_expired_on_date(today_str)
            
            logger.info(f"Found {len(expired_trials)} expired trials")
            
            for trial in expired_trials:
                try:
                    # Calculate grace period end date
                    grace_end = now + timedelta(days=self.GRACE_PERIOD_DAYS)
                    
                    # Update subscription to grace period
                    await self.subscription_repo.update(trial['subscription_id'], {
                        'subscription_status': 'grace_period',
                        'grace_period_end_date': grace_end.isoformat()
                    })
                    
                    # Update group status
                    await self.group_repo.update(trial['group_id'], {
                        'subscription_status': 'grace_period'
                    })
                    
                    # Send trial expired notification
                    await self.notification_service.send_trial_expired_notification(
                        group_id=trial['group_id'],
                        grace_period_days=self.GRACE_PERIOD_DAYS,
                        grace_period_end=grace_end
                    )
                    
                    # Log event
                    await self.subscription_repo.log_event(
                        trial['subscription_id'],
                        trial['group_id'],
                        'trial_expired',
                        {'grace_period_end': grace_end.isoformat()}
                    )
                    
                    self.metrics.inc_counter("trials_expired")
                    logger.info(f"Activated grace period for group {trial['group_id']}")
                    
                except Exception as e:
                    logger.error(f"Failed to process expired trial for group {trial['group_id']}: {e}")
            
            logger.info("Expired trials check completed")
            
        except Exception as e:
            logger.error(f"Error checking expired trials: {e}", exc_info=True)
    
    async def check_grace_period_warnings(self):
        """
        Check for grace periods ending soon and send urgent warnings.
        Sends warning 1 day before grace period ends.
        """
        try:
            logger.info("Checking grace period warnings...")
            
            # Find grace periods ending tomorrow
            tomorrow = datetime.now() + timedelta(days=1)
            tomorrow_str = tomorrow.date().isoformat()
            
            grace_periods = await self._find_grace_periods_ending_on_date(tomorrow_str)
            
            logger.info(f"Found {len(grace_periods)} grace periods ending tomorrow")
            
            for subscription in grace_periods:
                # Check if warning already sent today
                if await self._was_grace_warning_sent_today(subscription['subscription_id']):
                    logger.debug(f"Grace warning already sent for subscription {subscription['subscription_id']}")
                    continue
                
                try:
                    grace_end = datetime.fromisoformat(subscription['grace_period_end_date'])
                    
                    # Send urgent warning
                    await self.notification_service.send_grace_period_warning_notification(
                        group_id=subscription['group_id'],
                        days_remaining=1,
                        grace_period_end=grace_end
                    )
                    
                    # Log event
                    await self.subscription_repo.log_event(
                        subscription['subscription_id'],
                        subscription['group_id'],
                        'grace_period_warning',
                        {'days_remaining': 1, 'warning_sent': True}
                    )
                    
                    self.metrics.inc_counter("grace_period_warnings_sent")
                    logger.info(f"Sent grace period warning for group {subscription['group_id']}")
                    
                except Exception as e:
                    logger.error(f"Failed to send grace period warning for group {subscription['group_id']}: {e}")
            
            logger.info("Grace period warnings check completed")
            
        except Exception as e:
            logger.error(f"Error checking grace period warnings: {e}", exc_info=True)
    
    async def check_expired_subscriptions(self):
        """
        Check for expired subscriptions and disable posting.
        """
        try:
            logger.info("Checking expired subscriptions...")
            
            # Find grace periods that expired today
            now = datetime.now()
            today_str = now.date().isoformat()
            
            expired_subscriptions = await self._find_grace_periods_expired_on_date(today_str)
            
            logger.info(f"Found {len(expired_subscriptions)} expired subscriptions")
            
            for subscription in expired_subscriptions:
                try:
                    # Update subscription to expired
                    await self.subscription_repo.update(subscription['subscription_id'], {
                        'subscription_status': 'expired'
                    })
                    
                    # Disable group
                    await self.group_repo.update(subscription['group_id'], {
                        'subscription_status': 'expired',
                        'is_active': 0
                    })
                    
                    # Send expiration notification
                    await self.notification_service.send_subscription_expired_notification(
                        group_id=subscription['group_id']
                    )
                    
                    # Log event
                    await self.subscription_repo.log_event(
                        subscription['subscription_id'],
                        subscription['group_id'],
                        'subscription_expired',
                        {'posting_disabled': True}
                    )
                    
                    self.metrics.inc_counter("subscriptions_expired")
                    logger.info(f"Disabled posting for expired group {subscription['group_id']}")
                    
                except Exception as e:
                    logger.error(f"Failed to process expired subscription for group {subscription['group_id']}: {e}")
            
            logger.info("Expired subscriptions check completed")

        except Exception as e:
            logger.error(f"Error checking expired subscriptions: {e}", exc_info=True)

    # Helper methods for database queries

    async def _find_trials_expiring_on_date(self, date_str: str) -> List[Dict]:
        """Find trials expiring on a specific date."""
        try:
            query = """
                SELECT s.*, g.group_name
                FROM subscriptions s
                JOIN groups g ON s.group_id = g.group_id
                WHERE s.subscription_status = 'trial'
                AND DATE(s.trial_end_date) = ?
            """

            results = await self.subscription_repo.execute_query(query, (date_str,), fetch_all=True)
            return results if results else []

        except Exception as e:
            logger.error(f"Error finding trials expiring on {date_str}: {e}")
            return []

    async def _find_trials_expired_on_date(self, date_str: str) -> List[Dict]:
        """Find trials that expired on a specific date."""
        try:
            query = """
                SELECT s.*, g.group_name
                FROM subscriptions s
                JOIN groups g ON s.group_id = g.group_id
                WHERE s.subscription_status = 'trial'
                AND DATE(s.trial_end_date) = ?
            """

            results = await self.subscription_repo.execute_query(query, (date_str,), fetch_all=True)
            return results if results else []

        except Exception as e:
            logger.error(f"Error finding trials expired on {date_str}: {e}")
            return []

    async def _find_grace_periods_ending_on_date(self, date_str: str) -> List[Dict]:
        """Find grace periods ending on a specific date."""
        try:
            query = """
                SELECT s.*, g.group_name
                FROM subscriptions s
                JOIN groups g ON s.group_id = g.group_id
                WHERE s.subscription_status = 'grace_period'
                AND DATE(s.grace_period_end_date) = ?
            """

            results = await self.subscription_repo.execute_query(query, (date_str,), fetch_all=True)
            return results if results else []

        except Exception as e:
            logger.error(f"Error finding grace periods ending on {date_str}: {e}")
            return []

    async def _find_grace_periods_expired_on_date(self, date_str: str) -> List[Dict]:
        """Find grace periods that expired on a specific date."""
        try:
            query = """
                SELECT s.*, g.group_name
                FROM subscriptions s
                JOIN groups g ON s.group_id = g.group_id
                WHERE s.subscription_status = 'grace_period'
                AND DATE(s.grace_period_end_date) = ?
            """

            results = await self.subscription_repo.execute_query(query, (date_str,), fetch_all=True)
            return results if results else []

        except Exception as e:
            logger.error(f"Error finding grace periods expired on {date_str}: {e}")
            return []

    async def _was_warning_sent_today(self, subscription_id: int, days: int) -> bool:
        """Check if a trial warning was already sent today."""
        try:
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

            query = """
                SELECT COUNT(*) as count
                FROM subscription_events
                WHERE subscription_id = ?
                AND event_type = ?
                AND created_at >= ?
            """

            results = await self.subscription_repo.execute_query(
                query,
                (subscription_id, f'trial_warning_{days}d', today_start.isoformat()),
                fetch_all=True
            )

            return results[0]['count'] > 0 if results else False

        except Exception as e:
            logger.error(f"Error checking if warning was sent: {e}")
            return False

    async def _was_grace_warning_sent_today(self, subscription_id: int) -> bool:
        """Check if a grace period warning was already sent today."""
        try:
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

            query = """
                SELECT COUNT(*) as count
                FROM subscription_events
                WHERE subscription_id = ?
                AND event_type = 'grace_period_warning'
                AND created_at >= ?
            """

            results = await self.subscription_repo.execute_query(
                query,
                (subscription_id, today_start.isoformat()),
                fetch_all=True
            )

            return results[0]['count'] > 0 if results else False

        except Exception as e:
            logger.error(f"Error checking if grace warning was sent: {e}")
            return False

