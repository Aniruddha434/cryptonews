"""
Subscription repository for AI Market Insight Bot.
Handles all subscription-related database operations.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import hashlib
from repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class SubscriptionRepository(BaseRepository):
    """
    Repository for subscription data operations.
    
    Provides methods for:
    - Subscription creation and retrieval
    - Trial management
    - Subscription status updates
    - Trial abuse tracking
    """
    
    async def find_by_id(self, subscription_id: int) -> Optional[Dict[str, Any]]:
        """
        Find subscription by ID.
        
        Args:
            subscription_id: Subscription ID
            
        Returns:
            Subscription data dictionary or None
        """
        query = """
            SELECT subscription_id, group_id, subscription_status,
                   trial_start_date, trial_end_date, subscription_start_date,
                   subscription_end_date, next_billing_date, grace_period_end,
                   created_at, updated_at
            FROM subscriptions
            WHERE subscription_id = ?
        """
        
        return await self.execute_query(query, (subscription_id,), fetch_one=True)
    
    async def find_by_group_id(self, group_id: int) -> Optional[Dict[str, Any]]:
        """
        Find subscription by group ID.
        
        Args:
            group_id: Telegram group ID
            
        Returns:
            Subscription data dictionary or None
        """
        query = """
            SELECT subscription_id, group_id, subscription_status,
                   trial_start_date, trial_end_date, subscription_start_date,
                   subscription_end_date, next_billing_date, grace_period_end,
                   created_at, updated_at
            FROM subscriptions
            WHERE group_id = ?
        """
        
        return await self.execute_query(query, (group_id,), fetch_one=True)
    
    async def find_all(self) -> List[Dict[str, Any]]:
        """
        Get all subscriptions.
        
        Returns:
            List of subscription dictionaries
        """
        query = """
            SELECT subscription_id, group_id, subscription_status,
                   trial_start_date, trial_end_date, subscription_start_date,
                   subscription_end_date, next_billing_date, grace_period_end,
                   created_at, updated_at
            FROM subscriptions
            ORDER BY created_at DESC
        """
        
        return await self.execute_query(query, fetch_all=True)
    
    async def create(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create new subscription.
        
        Args:
            data: Subscription data
            
        Returns:
            Created subscription data or None
        """
        query = """
            INSERT INTO subscriptions (
                group_id, subscription_status, trial_start_date,
                trial_end_date, subscription_start_date, subscription_end_date,
                next_billing_date, grace_period_end, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        now = datetime.now().isoformat()
        
        try:
            await self.execute_query(
                query,
                (
                    data['group_id'],
                    data['subscription_status'],
                    data['trial_start_date'],
                    data['trial_end_date'],
                    data.get('subscription_start_date'),
                    data.get('subscription_end_date'),
                    data.get('next_billing_date'),
                    data.get('grace_period_end'),
                    now,
                    now
                )
            )
            
            self.logger.info(f"Created subscription for group: {data['group_id']}")
            return await self.find_by_group_id(data['group_id'])
            
        except Exception as e:
            self.logger.error(f"Failed to create subscription: {e}")
            return None
    
    async def update(self, subscription_id: int, data: Dict[str, Any]) -> bool:
        """
        Update subscription data.
        
        Args:
            subscription_id: Subscription ID
            data: Dictionary of fields to update
            
        Returns:
            True if successful
        """
        fields = []
        values = []
        
        allowed_fields = [
            'subscription_status', 'trial_start_date', 'trial_end_date',
            'subscription_start_date', 'subscription_end_date',
            'next_billing_date', 'grace_period_end'
        ]
        
        for key, value in data.items():
            if key in allowed_fields:
                fields.append(f"{key} = ?")
                values.append(value)
        
        if not fields:
            return False
        
        # Always update updated_at
        fields.append("updated_at = ?")
        values.append(datetime.now().isoformat())
        
        query = f"UPDATE subscriptions SET {', '.join(fields)} WHERE subscription_id = ?"
        values.append(subscription_id)
        
        try:
            await self.execute_query(query, tuple(values))
            self.logger.info(f"Updated subscription: {subscription_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to update subscription {subscription_id}: {e}")
            return False
    
    async def delete(self, subscription_id: int) -> bool:
        """
        Delete subscription.
        
        Args:
            subscription_id: Subscription ID
            
        Returns:
            True if successful
        """
        query = "DELETE FROM subscriptions WHERE subscription_id = ?"
        
        try:
            await self.execute_query(query, (subscription_id,))
            self.logger.info(f"Deleted subscription: {subscription_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete subscription {subscription_id}: {e}")
            return False
    
    async def find_expiring_trials(self, days: int) -> List[Dict[str, Any]]:
        """
        Find trials expiring in N days.
        
        Args:
            days: Number of days
            
        Returns:
            List of subscription dictionaries
        """
        query = """
            SELECT subscription_id, group_id, subscription_status,
                   trial_start_date, trial_end_date, subscription_start_date,
                   subscription_end_date, next_billing_date, grace_period_end,
                   created_at, updated_at
            FROM subscriptions
            WHERE subscription_status = 'trial'
            AND trial_end_date BETWEEN datetime('now') AND datetime('now', '+' || ? || ' days')
        """
        
        return await self.execute_query(query, (days,), fetch_all=True)
    
    async def find_expired_subscriptions(self) -> List[Dict[str, Any]]:
        """
        Find expired subscriptions.
        
        Returns:
            List of subscription dictionaries
        """
        query = """
            SELECT subscription_id, group_id, subscription_status,
                   trial_start_date, trial_end_date, subscription_start_date,
                   subscription_end_date, next_billing_date, grace_period_end,
                   created_at, updated_at
            FROM subscriptions
            WHERE subscription_status = 'active'
            AND subscription_end_date < datetime('now')
        """
        
        return await self.execute_query(query, fetch_all=True)
    
    async def find_by_status(self, status: str) -> List[Dict[str, Any]]:
        """
        Find subscriptions by status.
        
        Args:
            status: Subscription status
            
        Returns:
            List of subscription dictionaries
        """
        query = """
            SELECT subscription_id, group_id, subscription_status,
                   trial_start_date, trial_end_date, subscription_start_date,
                   subscription_end_date, next_billing_date, grace_period_end,
                   created_at, updated_at
            FROM subscriptions
            WHERE subscription_status = ?
        """
        
        return await self.execute_query(query, (status,), fetch_all=True)
    
    async def track_trial(
        self,
        group_id: int,
        group_title: str,
        creator_user_id: int
    ) -> bool:
        """
        Track trial creation for abuse detection.
        
        Args:
            group_id: Telegram group ID
            group_title: Group title
            creator_user_id: User ID who created the trial
            
        Returns:
            True if successful
        """
        # Generate fingerprint
        fingerprint = hashlib.sha256(
            f"{group_id}:{group_title}".encode()
        ).hexdigest()
        
        query = """
            INSERT INTO trial_abuse_tracking (
                group_id, group_title_hash, creator_user_id,
                trial_started_at, is_flagged, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
        """
        
        now = datetime.now().isoformat()
        
        try:
            await self.execute_query(
                query,
                (group_id, fingerprint, creator_user_id, now, 0, now)
            )
            self.logger.info(f"Tracked trial for group: {group_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to track trial: {e}")
            return False
    
    async def find_by_fingerprint(self, fingerprint: str) -> List[Dict[str, Any]]:
        """
        Find trials by group fingerprint.
        
        Args:
            fingerprint: Group fingerprint hash
            
        Returns:
            List of trial tracking records
        """
        query = """
            SELECT tracking_id, group_id, group_title_hash, creator_user_id,
                   trial_started_at, is_flagged, flag_reason, created_at
            FROM trial_abuse_tracking
            WHERE group_title_hash = ?
            ORDER BY trial_started_at DESC
        """
        
        return await self.execute_query(query, (fingerprint,), fetch_all=True)
    
    async def find_by_creator(self, creator_user_id: int) -> List[Dict[str, Any]]:
        """
        Find trials by creator user ID.
        
        Args:
            creator_user_id: User ID
            
        Returns:
            List of trial tracking records
        """
        query = """
            SELECT tracking_id, group_id, group_title_hash, creator_user_id,
                   trial_started_at, is_flagged, flag_reason, created_at
            FROM trial_abuse_tracking
            WHERE creator_user_id = ?
            ORDER BY trial_started_at DESC
        """
        
        return await self.execute_query(query, (creator_user_id,), fetch_all=True)
    
    async def log_event(
        self,
        subscription_id: int,
        group_id: int,
        event_type: str,
        event_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Log subscription event.
        
        Args:
            subscription_id: Subscription ID
            group_id: Group ID
            event_type: Type of event
            event_data: Additional event data
            
        Returns:
            True if successful
        """
        import json
        
        query = """
            INSERT INTO subscription_events (
                subscription_id, group_id, event_type, event_data, created_at
            ) VALUES (?, ?, ?, ?, ?)
        """
        
        now = datetime.now().isoformat()
        data_json = json.dumps(event_data) if event_data else None
        
        try:
            await self.execute_query(
                query,
                (subscription_id, group_id, event_type, data_json, now)
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to log event: {e}")
            return False

