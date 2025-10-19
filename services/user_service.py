"""
User service for AI Market Insight Bot.
Handles user management and preferences.
"""

import logging
from typing import Optional, Dict, Any, List, TYPE_CHECKING

from core.metrics import MetricsCollector
from repositories.user_repository import UserRepository
from repositories.group_repository import GroupRepository

if TYPE_CHECKING:
    from services.subscription_service import SubscriptionService

logger = logging.getLogger(__name__)


class UserService:
    """
    Service for user operations.

    Provides:
    - User registration and management
    - Trader type preferences
    - Group management
    - Activity tracking
    """

    def __init__(
        self,
        user_repo: UserRepository,
        group_repo: GroupRepository,
        metrics: MetricsCollector,
        subscription_service: Optional['SubscriptionService'] = None
    ):
        """
        Initialize user service.

        Args:
            user_repo: User repository
            group_repo: Group repository
            metrics: Metrics collector
            subscription_service: Subscription service (optional)
        """
        self.user_repo = user_repo
        self.group_repo = group_repo
        self.metrics = metrics
        self.subscription_service = subscription_service

        logger.info("UserService initialized")

    def set_subscription_service(self, subscription_service: 'SubscriptionService'):
        """
        Set subscription service for trial creation.

        Args:
            subscription_service: SubscriptionService instance
        """
        self.subscription_service = subscription_service
        logger.info("Subscription service set in UserService")

    async def register_user(
        self,
        chat_id: int,
        trader_type: str = "investor"
    ) -> bool:
        """
        Register new user or update existing.
        
        Args:
            chat_id: Telegram chat ID
            trader_type: Type of trader
            
        Returns:
            True if successful
        """
        try:
            # Check if user exists
            existing = await self.user_repo.find_by_id(chat_id)
            
            if existing:
                # Update last active
                await self.user_repo.update_last_active(chat_id)
                logger.info(f"User {chat_id} already registered")
                return True
            
            # Create new user
            success = await self.user_repo.create(chat_id, trader_type)
            
            if success:
                self.metrics.inc_counter("bot_users_total")
                logger.info(f"Registered new user: {chat_id} ({trader_type})")
            
            return success
            
        except Exception as e:
            logger.error(f"Error registering user {chat_id}: {e}", exc_info=True)
            return False
    
    async def get_user(self, chat_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user data.
        
        Args:
            chat_id: Telegram chat ID
            
        Returns:
            User data or None
        """
        try:
            user = await self.user_repo.find_by_id(chat_id)
            
            if user:
                # Update last active
                await self.user_repo.update_last_active(chat_id)
            
            return user
            
        except Exception as e:
            logger.error(f"Error getting user {chat_id}: {e}", exc_info=True)
            return None
    
    async def update_trader_type(
        self,
        chat_id: int,
        trader_type: str
    ) -> bool:
        """
        Update user's trader type.
        
        Args:
            chat_id: Telegram chat ID
            trader_type: New trader type
            
        Returns:
            True if successful
        """
        try:
            success = await self.user_repo.update_trader_type(chat_id, trader_type)
            
            if success:
                logger.info(f"Updated trader type for {chat_id}: {trader_type}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error updating trader type for {chat_id}: {e}", exc_info=True)
            return False
    
    async def get_or_create_user(
        self,
        chat_id: int,
        trader_type: str = "investor"
    ) -> Optional[Dict[str, Any]]:
        """
        Get existing user or create new one.
        
        Args:
            chat_id: Telegram chat ID
            trader_type: Default trader type
            
        Returns:
            User data
        """
        try:
            user = await self.user_repo.get_or_create(chat_id, trader_type)
            
            if user:
                # Update metrics
                total_users = await self.user_repo.count_total()
                self.metrics.set_gauge("bot_users_total", total_users)
            
            return user
            
        except Exception as e:
            logger.error(f"Error getting/creating user {chat_id}: {e}", exc_info=True)
            return None
    
    async def register_group(
        self,
        group_id: int,
        group_name: str,
        posting_time: str = "09:00",
        trader_type: str = "investor",
        creator_user_id: Optional[int] = None
    ) -> bool:
        """
        Register new group and create trial subscription.

        Args:
            group_id: Telegram group ID
            group_name: Group name
            posting_time: Daily posting time
            trader_type: Trader type for content
            creator_user_id: User ID who added the bot (for trial abuse detection)

        Returns:
            True if successful
        """
        try:
            # Check if group exists
            existing = await self.group_repo.find_by_id(group_id)

            if existing:
                logger.info(f"Group {group_id} already registered")
                return True

            # Create new group
            success = await self.group_repo.create(
                group_id,
                group_name,
                posting_time,
                trader_type
            )

            if not success:
                logger.error(f"Failed to create group {group_id}")
                return False

            # Create trial subscription if subscription service is available
            if self.subscription_service:
                subscription = await self.subscription_service.create_trial_subscription(
                    group_id,
                    group_name,
                    creator_user_id
                )

                if not subscription:
                    logger.warning(f"Failed to create trial subscription for group {group_id}")
                    # Don't fail the registration, but log the issue
                else:
                    logger.info(f"Created trial subscription for group {group_id}")

            self.metrics.inc_counter("bot_groups_total")
            logger.info(f"Registered new group: {group_id} ({group_name})")

            return True
            
        except Exception as e:
            logger.error(f"Error registering group {group_id}: {e}", exc_info=True)
            return False
    
    async def get_group(self, group_id: int) -> Optional[Dict[str, Any]]:
        """
        Get group data.
        
        Args:
            group_id: Telegram group ID
            
        Returns:
            Group data or None
        """
        try:
            return await self.group_repo.find_by_id(group_id)
        except Exception as e:
            logger.error(f"Error getting group {group_id}: {e}", exc_info=True)
            return None
    
    async def get_active_groups(self) -> List[Dict[str, Any]]:
        """
        Get all active groups.
        
        Returns:
            List of active groups
        """
        try:
            groups = await self.group_repo.find_active()
            
            # Update metrics
            self.metrics.set_gauge("bot_groups_total", len(groups))
            
            return groups
            
        except Exception as e:
            logger.error(f"Error getting active groups: {e}", exc_info=True)
            return []
    
    async def update_group_posting_time(
        self,
        group_id: int,
        posting_time: str
    ) -> bool:
        """
        Update group's posting time.
        
        Args:
            group_id: Telegram group ID
            posting_time: New posting time (HH:MM)
            
        Returns:
            True if successful
        """
        try:
            success = await self.group_repo.update_posting_time(group_id, posting_time)
            
            if success:
                logger.info(f"Updated posting time for group {group_id}: {posting_time}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error updating posting time for {group_id}: {e}", exc_info=True)
            return False
    
    async def deactivate_group(self, group_id: int) -> bool:
        """
        Deactivate group.

        Args:
            group_id: Telegram group ID

        Returns:
            True if successful
        """
        try:
            success = await self.group_repo.set_active(group_id, False)

            if success:
                logger.info(f"Deactivated group: {group_id}")

            return success

        except Exception as e:
            logger.error(f"Error deactivating group {group_id}: {e}", exc_info=True)
            return False

    async def pause_group(self, group_id: int) -> bool:
        """
        Pause automated posting for a group.

        Args:
            group_id: Telegram group ID

        Returns:
            True if successful
        """
        return await self.deactivate_group(group_id)

    async def resume_group(self, group_id: int) -> bool:
        """
        Resume automated posting for a group.

        Args:
            group_id: Telegram group ID

        Returns:
            True if successful
        """
        try:
            success = await self.group_repo.set_active(group_id, True)

            if success:
                logger.info(f"Resumed group: {group_id}")

            return success

        except Exception as e:
            logger.error(f"Error resuming group {group_id}: {e}", exc_info=True)
            return False

    async def remove_group(self, group_id: int) -> bool:
        """
        Remove a group from the database.

        Args:
            group_id: Telegram group ID

        Returns:
            True if successful
        """
        try:
            success = await self.group_repo.delete(group_id)

            if success:
                logger.info(f"Removed group: {group_id}")
                self.metrics.inc_counter("bot_groups_removed")

            return success

        except Exception as e:
            logger.error(f"Error removing group {group_id}: {e}", exc_info=True)
            return False

    async def update_group_post_time(self, group_id: int, post_time: str) -> bool:
        """
        Update group's posting time (alias for update_group_posting_time).

        Args:
            group_id: Telegram group ID
            post_time: New posting time (HH:MM)

        Returns:
            True if successful
        """
        return await self.update_group_posting_time(group_id, post_time)

    async def update_group_trader_type(
        self,
        group_id: int,
        trader_type: str
    ) -> bool:
        """
        Update group's trader type.

        Args:
            group_id: Telegram group ID
            trader_type: New trader type

        Returns:
            True if successful
        """
        try:
            success = await self.group_repo.update_trader_type(group_id, trader_type)

            if success:
                logger.info(f"Updated trader type for group {group_id}: {trader_type}")

            return success

        except Exception as e:
            logger.error(f"Error updating trader type for group {group_id}: {e}", exc_info=True)
            return False
    
    async def get_user_stats(self) -> Dict[str, Any]:
        """
        Get user statistics.
        
        Returns:
            Dictionary with user stats
        """
        try:
            total_users = await self.user_repo.count_total()
            by_trader_type = await self.user_repo.count_by_trader_type()
            total_groups = await self.group_repo.count_total()
            active_groups = await self.group_repo.count_active()
            
            return {
                'total_users': total_users,
                'by_trader_type': by_trader_type,
                'total_groups': total_groups,
                'active_groups': active_groups
            }
            
        except Exception as e:
            logger.error(f"Error getting user stats: {e}", exc_info=True)
            return {
                'total_users': 0,
                'by_trader_type': {},
                'total_groups': 0,
                'active_groups': 0
            }

