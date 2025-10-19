"""
Subscription service for AI Market Insight Bot.
Manages subscription lifecycle and validation.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import hashlib

from repositories.subscription_repository import SubscriptionRepository
from repositories.payment_repository import PaymentRepository
from repositories.group_repository import GroupRepository
from core.metrics import MetricsCollector
import config

# TYPE_CHECKING import to avoid circular dependency
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class SubscriptionService:
    """
    Service for subscription operations.

    Provides:
    - Trial subscription creation
    - Subscription validation
    - Trial abuse detection
    - Subscription activation
    - Posting permission checks
    """

    def __init__(
        self,
        subscription_repo: SubscriptionRepository,
        payment_repo: PaymentRepository,
        group_repo: GroupRepository,
        metrics: MetricsCollector,
        notification_service: Optional['NotificationService'] = None
    ):
        """
        Initialize subscription service.

        Args:
            subscription_repo: Subscription repository
            payment_repo: Payment repository
            group_repo: Group repository
            metrics: Metrics collector
            notification_service: Notification service (optional)
        """
        self.subscription_repo = subscription_repo
        self.payment_repo = payment_repo
        self.group_repo = group_repo
        self.notification_service = notification_service
        self.metrics = metrics

        # Configuration from config.py
        self.TRIAL_DAYS = config.TRIAL_DAYS
        self.GRACE_PERIOD_DAYS = config.GRACE_PERIOD_DAYS
        self.SUBSCRIPTION_PRICE_USD = config.SUBSCRIPTION_PRICE_USD
        self.TRIAL_COOLDOWN_DAYS = config.TRIAL_COOLDOWN_DAYS
        self.MAX_TRIALS_PER_CREATOR = config.MAX_TRIALS_PER_CREATOR

        logger.info("SubscriptionService initialized")
    
    async def create_trial_subscription(
        self,
        group_id: int,
        group_name: str,
        creator_user_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new trial subscription for a group.
        
        Checks for trial abuse before creating.
        
        Args:
            group_id: Telegram group ID
            group_name: Group name
            creator_user_id: User ID who added the bot
            
        Returns:
            Subscription data or None if abuse detected
        """
        try:
            # Check if subscription already exists
            existing = await self.subscription_repo.find_by_group_id(group_id)
            
            if existing:
                logger.info(f"Subscription already exists for group {group_id}")
                return existing
            
            # Check for trial abuse
            if creator_user_id:
                is_abuse = await self.check_trial_abuse(
                    group_id,
                    group_name,
                    creator_user_id
                )
                
                if is_abuse:
                    logger.warning(f"Trial abuse detected for group {group_id}")
                    self.metrics.inc_counter("trial_abuse_detected")
                    return None
            
            # Calculate dates
            trial_start = datetime.now()
            trial_end = trial_start + timedelta(days=self.TRIAL_DAYS)
            
            # Create subscription
            subscription = await self.subscription_repo.create({
                'group_id': group_id,
                'subscription_status': 'trial',
                'trial_start_date': trial_start.isoformat(),
                'trial_end_date': trial_end.isoformat()
            })
            
            if not subscription:
                logger.error(f"Failed to create subscription for group {group_id}")
                return None
            
            # Update group with subscription info
            await self.group_repo.update(group_id, {
                'subscription_status': 'trial',
                'trial_ends_at': trial_end.isoformat()
            })
            
            # Log event
            await self.subscription_repo.log_event(
                subscription['subscription_id'],
                group_id,
                'trial_started',
                {'group_name': group_name, 'trial_days': self.TRIAL_DAYS}
            )
            
            # Track trial for abuse detection
            if creator_user_id:
                await self.subscription_repo.track_trial(
                    group_id,
                    group_name,
                    creator_user_id
                )
            
            self.metrics.inc_counter("trials_created")
            logger.info(f"Created trial subscription for group {group_id} ({group_name})")

            # Send trial started notification
            if self.notification_service:
                try:
                    await self.notification_service.send_trial_started_notification(
                        group_id=group_id,
                        trial_days=self.TRIAL_DAYS,
                        trial_end_date=trial_end
                    )
                except Exception as e:
                    logger.error(f"Failed to send trial started notification: {e}")

            return subscription

        except Exception as e:
            logger.error(f"Error creating trial subscription: {e}", exc_info=True)
            return None

    def set_notification_service(self, notification_service: 'NotificationService'):
        """
        Set notification service for sending automated notifications.

        Args:
            notification_service: NotificationService instance
        """
        self.notification_service = notification_service
        logger.info("Notification service set in SubscriptionService")
    
    async def is_posting_allowed(self, group_id: int) -> bool:
        """
        Check if posting is allowed for a group.
        
        Returns True if:
        - Trial is active
        - Subscription is active
        - In grace period
        
        Args:
            group_id: Telegram group ID
            
        Returns:
            True if posting allowed
        """
        try:
            subscription = await self.subscription_repo.find_by_group_id(group_id)
            
            if not subscription:
                # No subscription = no posting
                return False
            
            status = subscription['subscription_status']
            now = datetime.now()
            
            # Active subscription
            if status == 'active':
                if subscription['subscription_end_date']:
                    end_date = datetime.fromisoformat(subscription['subscription_end_date'])
                    if end_date > now:
                        return True
            
            # Active trial
            elif status == 'trial':
                if subscription['trial_end_date']:
                    trial_end = datetime.fromisoformat(subscription['trial_end_date'])
                    if trial_end > now:
                        return True
            
            # Grace period
            elif status == 'grace_period':
                if subscription['grace_period_end']:
                    grace_end = datetime.fromisoformat(subscription['grace_period_end'])
                    if grace_end > now:
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking posting permission for group {group_id}: {e}", exc_info=True)
            return False
    
    async def activate_subscription(
        self,
        subscription_id: int,
        payment_id: int,
        months: int = 1
    ) -> bool:
        """
        Activate a subscription after payment confirmation.
        
        Args:
            subscription_id: Subscription ID
            payment_id: Payment ID
            months: Number of months to activate
            
        Returns:
            True if successful
        """
        try:
            subscription = await self.subscription_repo.find_by_id(subscription_id)
            
            if not subscription:
                logger.error(f"Subscription not found: {subscription_id}")
                return False
            
            # Calculate dates
            now = datetime.now()
            
            # If trial, start from trial end date
            if subscription['subscription_status'] == 'trial':
                if subscription['trial_end_date']:
                    start_date = datetime.fromisoformat(subscription['trial_end_date'])
                else:
                    start_date = now
            else:
                # Renewal - start from current end date or now
                if subscription['subscription_end_date']:
                    current_end = datetime.fromisoformat(subscription['subscription_end_date'])
                    start_date = current_end if current_end > now else now
                else:
                    start_date = now
            
            end_date = start_date + timedelta(days=30 * months)
            next_billing = end_date - timedelta(days=7)  # Remind 7 days before
            
            # Update subscription
            await self.subscription_repo.update(subscription_id, {
                'subscription_status': 'active',
                'subscription_start_date': start_date.isoformat(),
                'subscription_end_date': end_date.isoformat(),
                'next_billing_date': next_billing.isoformat()
            })
            
            # Update group
            await self.group_repo.update(subscription['group_id'], {
                'subscription_status': 'active',
                'is_active': 1
            })
            
            # Log event
            await self.subscription_repo.log_event(
                subscription_id,
                subscription['group_id'],
                'subscription_activated',
                {'payment_id': payment_id, 'months': months, 'end_date': end_date.isoformat()}
            )
            
            self.metrics.inc_counter("subscriptions_activated")
            logger.info(f"Activated subscription {subscription_id} for {months} month(s)")

            # Send subscription activated notification
            if self.notification_service:
                try:
                    await self.notification_service.send_subscription_activated_notification(
                        group_id=subscription['group_id'],
                        subscription_end_date=end_date,
                        next_billing_date=next_billing
                    )
                except Exception as e:
                    logger.error(f"Failed to send subscription activated notification: {e}")

            return True

        except Exception as e:
            logger.error(f"Error activating subscription {subscription_id}: {e}", exc_info=True)
            return False
    
    async def check_trial_abuse(
        self,
        group_id: int,
        group_title: str,
        creator_user_id: int
    ) -> bool:
        """
        Check for trial abuse patterns.
        
        Returns True if abuse detected.
        
        Args:
            group_id: Telegram group ID
            group_title: Group title
            creator_user_id: User ID who created the trial
            
        Returns:
            True if abuse detected
        """
        try:
            # Generate fingerprint
            fingerprint = hashlib.sha256(
                f"{group_id}:{group_title}".encode()
            ).hexdigest()
            
            # Check for existing trials with same fingerprint
            existing = await self.subscription_repo.find_by_fingerprint(fingerprint)
            
            if existing:
                # Check cooldown period
                last_trial_str = existing[0]['trial_started_at']
                last_trial = datetime.fromisoformat(last_trial_str)
                cooldown_end = last_trial + timedelta(days=self.TRIAL_COOLDOWN_DAYS)
                
                if datetime.now() < cooldown_end:
                    logger.warning(f"Trial abuse: Same fingerprint within cooldown period")
                    return True
            
            # Check trials by creator
            creator_trials = await self.subscription_repo.find_by_creator(creator_user_id)
            
            if len(creator_trials) >= self.MAX_TRIALS_PER_CREATOR:
                logger.warning(f"Trial abuse: Creator has {len(creator_trials)} trials")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking trial abuse: {e}", exc_info=True)
            # On error, allow trial (fail open)
            return False
    
    async def get_subscription(self, group_id: int) -> Optional[Dict[str, Any]]:
        """
        Get subscription for a group.
        
        Args:
            group_id: Telegram group ID
            
        Returns:
            Subscription data or None
        """
        try:
            return await self.subscription_repo.find_by_group_id(group_id)
        except Exception as e:
            logger.error(f"Error getting subscription for group {group_id}: {e}", exc_info=True)
            return None
    
    async def get_subscription_status(self, group_id: int) -> Dict[str, Any]:
        """
        Get detailed subscription status for a group.
        
        Args:
            group_id: Telegram group ID
            
        Returns:
            Dictionary with status information
        """
        try:
            subscription = await self.subscription_repo.find_by_group_id(group_id)
            
            if not subscription:
                return {
                    'has_subscription': False,
                    'status': 'none',
                    'posting_allowed': False
                }
            
            now = datetime.now()
            status = subscription['subscription_status']
            
            result = {
                'has_subscription': True,
                'status': status,
                'posting_allowed': await self.is_posting_allowed(group_id)
            }
            
            # Add trial info
            if status == 'trial' and subscription['trial_end_date']:
                trial_end = datetime.fromisoformat(subscription['trial_end_date'])
                days_left = (trial_end - now).days
                result['trial_days_left'] = max(0, days_left)
                result['trial_end_date'] = trial_end.isoformat()
            
            # Add subscription info
            if status == 'active' and subscription['subscription_end_date']:
                sub_end = datetime.fromisoformat(subscription['subscription_end_date'])
                days_left = (sub_end - now).days
                result['subscription_days_left'] = max(0, days_left)
                result['subscription_end_date'] = sub_end.isoformat()
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting subscription status: {e}", exc_info=True)
            return {
                'has_subscription': False,
                'status': 'error',
                'posting_allowed': False
            }

