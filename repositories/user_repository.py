"""
User repository for AI Market Insight Bot.
Handles all user-related database operations with connection pooling.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository):
    """
    Repository for user data operations.
    
    Provides methods for:
    - User registration and retrieval
    - Trader type management
    - User preferences
    - Activity tracking
    """
    
    async def find_by_id(self, chat_id: int) -> Optional[Dict[str, Any]]:
        """
        Find user by chat ID.
        
        Args:
            chat_id: Telegram chat ID
            
        Returns:
            User data dictionary or None
        """
        query = """
            SELECT chat_id, trader_type, created_at, last_active
            FROM users
            WHERE chat_id = ?
        """
        
        result = await self.execute_query(query, (chat_id,), fetch_one=True)
        
        if result:
            self.logger.debug(f"Found user: {chat_id}")
        
        return result
    
    async def find_all(self) -> List[Dict[str, Any]]:
        """
        Get all registered users.
        
        Returns:
            List of user dictionaries
        """
        query = """
            SELECT chat_id, trader_type, created_at, last_active
            FROM users
            ORDER BY created_at DESC
        """
        
        return await self.execute_query(query, fetch_all=True)
    
    async def create(self, chat_id: int, trader_type: str = "investor") -> bool:
        """
        Create new user.
        
        Args:
            chat_id: Telegram chat ID
            trader_type: Type of trader (scalper, day_trader, swing_trader, investor)
            
        Returns:
            True if successful
        """
        query = """
            INSERT INTO users (chat_id, trader_type, created_at, last_active)
            VALUES (?, ?, ?, ?)
        """
        
        now = datetime.now().isoformat()
        
        try:
            await self.execute_query(query, (chat_id, trader_type, now, now))
            self.logger.info(f"Created user: {chat_id} ({trader_type})")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create user {chat_id}: {e}")
            return False
    
    async def update(self, chat_id: int, data: Dict[str, Any]) -> bool:
        """
        Update user data.
        
        Args:
            chat_id: Telegram chat ID
            data: Dictionary of fields to update
            
        Returns:
            True if successful
        """
        # Build dynamic UPDATE query
        fields = []
        values = []
        
        for key, value in data.items():
            if key in ['trader_type', 'last_active']:
                fields.append(f"{key} = ?")
                values.append(value)
        
        if not fields:
            return False
        
        query = f"UPDATE users SET {', '.join(fields)} WHERE chat_id = ?"
        values.append(chat_id)
        
        try:
            await self.execute_query(query, tuple(values))
            self.logger.info(f"Updated user: {chat_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to update user {chat_id}: {e}")
            return False
    
    async def delete(self, chat_id: int) -> bool:
        """
        Delete user.
        
        Args:
            chat_id: Telegram chat ID
            
        Returns:
            True if successful
        """
        query = "DELETE FROM users WHERE chat_id = ?"
        
        try:
            await self.execute_query(query, (chat_id,))
            self.logger.info(f"Deleted user: {chat_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete user {chat_id}: {e}")
            return False
    
    async def update_trader_type(self, chat_id: int, trader_type: str) -> bool:
        """
        Update user's trader type.
        
        Args:
            chat_id: Telegram chat ID
            trader_type: New trader type
            
        Returns:
            True if successful
        """
        return await self.update(chat_id, {"trader_type": trader_type})
    
    async def update_last_active(self, chat_id: int) -> bool:
        """
        Update user's last active timestamp.
        
        Args:
            chat_id: Telegram chat ID
            
        Returns:
            True if successful
        """
        now = datetime.now().isoformat()
        return await self.update(chat_id, {"last_active": now})
    
    async def get_by_trader_type(self, trader_type: str) -> List[Dict[str, Any]]:
        """
        Get all users of a specific trader type.
        
        Args:
            trader_type: Trader type to filter by
            
        Returns:
            List of user dictionaries
        """
        query = """
            SELECT chat_id, trader_type, created_at, last_active
            FROM users
            WHERE trader_type = ?
            ORDER BY created_at DESC
        """
        
        return await self.execute_query(query, (trader_type,), fetch_all=True)
    
    async def count_total(self) -> int:
        """
        Get total number of users.
        
        Returns:
            User count
        """
        query = "SELECT COUNT(*) as count FROM users"
        result = await self.execute_query(query, fetch_one=True)
        return result['count'] if result else 0
    
    async def count_by_trader_type(self) -> Dict[str, int]:
        """
        Get user count by trader type.
        
        Returns:
            Dictionary of trader_type -> count
        """
        query = """
            SELECT trader_type, COUNT(*) as count
            FROM users
            GROUP BY trader_type
        """
        
        results = await self.execute_query(query, fetch_all=True)
        return {row['trader_type']: row['count'] for row in results}
    
    async def exists(self, chat_id: int) -> bool:
        """
        Check if user exists.
        
        Args:
            chat_id: Telegram chat ID
            
        Returns:
            True if user exists
        """
        user = await self.find_by_id(chat_id)
        return user is not None
    
    async def get_or_create(self, chat_id: int, trader_type: str = "investor") -> Dict[str, Any]:
        """
        Get existing user or create new one.
        
        Args:
            chat_id: Telegram chat ID
            trader_type: Default trader type for new users
            
        Returns:
            User data dictionary
        """
        user = await self.find_by_id(chat_id)
        
        if user:
            # Update last active
            await self.update_last_active(chat_id)
            return user
        
        # Create new user
        await self.create(chat_id, trader_type)
        return await self.find_by_id(chat_id)
    
    async def create_many(self, users: List[Dict[str, Any]]) -> int:
        """
        Create multiple users in batch.
        
        Args:
            users: List of user dictionaries with chat_id and trader_type
            
        Returns:
            Number of users created
        """
        query = """
            INSERT INTO users (chat_id, trader_type, created_at, last_active)
            VALUES (?, ?, ?, ?)
        """
        
        now = datetime.now().isoformat()
        params_list = [
            (user['chat_id'], user.get('trader_type', 'investor'), now, now)
            for user in users
        ]
        
        try:
            count = await self.execute_many(query, params_list)
            self.logger.info(f"Created {count} users in batch")
            return count
        except Exception as e:
            self.logger.error(f"Failed to create users in batch: {e}")
            return 0

