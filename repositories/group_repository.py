"""
Group repository for AI Market Insight Bot.
Handles all group-related database operations with connection pooling.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class GroupRepository(BaseRepository):
    """
    Repository for group data operations.
    
    Provides methods for:
    - Group registration and retrieval
    - Posting schedule management
    - Group preferences
    - Activity tracking
    """
    
    async def find_by_id(self, group_id: int) -> Optional[Dict[str, Any]]:
        """
        Find group by ID.
        
        Args:
            group_id: Telegram group ID
            
        Returns:
            Group data dictionary or None
        """
        query = """
            SELECT group_id, group_name, posting_time, trader_type, 
                   is_active, created_at, last_post
            FROM groups
            WHERE group_id = ?
        """
        
        result = await self.execute_query(query, (group_id,), fetch_one=True)
        
        if result:
            self.logger.debug(f"Found group: {group_id}")
        
        return result
    
    async def find_all(self) -> List[Dict[str, Any]]:
        """
        Get all registered groups.
        
        Returns:
            List of group dictionaries
        """
        query = """
            SELECT group_id, group_name, posting_time, trader_type,
                   is_active, created_at, last_post
            FROM groups
            ORDER BY created_at DESC
        """
        
        return await self.execute_query(query, fetch_all=True)
    
    async def find_active(self) -> List[Dict[str, Any]]:
        """
        Get all active groups.
        
        Returns:
            List of active group dictionaries
        """
        query = """
            SELECT group_id, group_name, posting_time, trader_type,
                   is_active, created_at, last_post
            FROM groups
            WHERE is_active = 1
            ORDER BY posting_time
        """
        
        return await self.execute_query(query, fetch_all=True)
    
    async def create(
        self,
        group_id: int,
        group_name: str,
        posting_time: str = "09:00",
        trader_type: str = "investor"
    ) -> bool:
        """
        Create new group.
        
        Args:
            group_id: Telegram group ID
            group_name: Group name
            posting_time: Daily posting time (HH:MM format)
            trader_type: Type of trader content
            
        Returns:
            True if successful
        """
        query = """
            INSERT INTO groups (group_id, group_name, posting_time, trader_type,
                              is_active, created_at, last_post)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        now = datetime.now().isoformat()
        
        try:
            await self.execute_query(
                query,
                (group_id, group_name, posting_time, trader_type, 1, now, None)
            )
            self.logger.info(f"Created group: {group_id} ({group_name})")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create group {group_id}: {e}")
            return False
    
    async def update(self, group_id: int, data: Dict[str, Any]) -> bool:
        """
        Update group data.
        
        Args:
            group_id: Telegram group ID
            data: Dictionary of fields to update
            
        Returns:
            True if successful
        """
        # Build dynamic UPDATE query
        fields = []
        values = []
        
        allowed_fields = ['group_name', 'posting_time', 'trader_type', 'is_active', 'last_post']
        
        for key, value in data.items():
            if key in allowed_fields:
                fields.append(f"{key} = ?")
                values.append(value)
        
        if not fields:
            return False
        
        query = f"UPDATE groups SET {', '.join(fields)} WHERE group_id = ?"
        values.append(group_id)
        
        try:
            await self.execute_query(query, tuple(values))
            self.logger.info(f"Updated group: {group_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to update group {group_id}: {e}")
            return False
    
    async def delete(self, group_id: int) -> bool:
        """
        Delete group.
        
        Args:
            group_id: Telegram group ID
            
        Returns:
            True if successful
        """
        query = "DELETE FROM groups WHERE group_id = ?"
        
        try:
            await self.execute_query(query, (group_id,))
            self.logger.info(f"Deleted group: {group_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete group {group_id}: {e}")
            return False
    
    async def set_active(self, group_id: int, is_active: bool) -> bool:
        """
        Set group active status.
        
        Args:
            group_id: Telegram group ID
            is_active: Active status
            
        Returns:
            True if successful
        """
        return await self.update(group_id, {"is_active": 1 if is_active else 0})
    
    async def update_posting_time(self, group_id: int, posting_time: str) -> bool:
        """
        Update group's posting time.
        
        Args:
            group_id: Telegram group ID
            posting_time: New posting time (HH:MM format)
            
        Returns:
            True if successful
        """
        return await self.update(group_id, {"posting_time": posting_time})
    
    async def update_trader_type(self, group_id: int, trader_type: str) -> bool:
        """
        Update group's trader type.
        
        Args:
            group_id: Telegram group ID
            trader_type: New trader type
            
        Returns:
            True if successful
        """
        return await self.update(group_id, {"trader_type": trader_type})
    
    async def update_last_post(self, group_id: int) -> bool:
        """
        Update group's last post timestamp.
        
        Args:
            group_id: Telegram group ID
            
        Returns:
            True if successful
        """
        now = datetime.now().isoformat()
        return await self.update(group_id, {"last_post": now})
    
    async def get_by_posting_time(self, posting_time: str) -> List[Dict[str, Any]]:
        """
        Get all active groups with specific posting time.
        
        Args:
            posting_time: Posting time (HH:MM format)
            
        Returns:
            List of group dictionaries
        """
        query = """
            SELECT group_id, group_name, posting_time, trader_type,
                   is_active, created_at, last_post
            FROM groups
            WHERE posting_time = ? AND is_active = 1
        """
        
        return await self.execute_query(query, (posting_time,), fetch_all=True)
    
    async def count_total(self) -> int:
        """
        Get total number of groups.
        
        Returns:
            Group count
        """
        query = "SELECT COUNT(*) as count FROM groups"
        result = await self.execute_query(query, fetch_one=True)
        return result['count'] if result else 0
    
    async def count_active(self) -> int:
        """
        Get number of active groups.
        
        Returns:
            Active group count
        """
        query = "SELECT COUNT(*) as count FROM groups WHERE is_active = 1"
        result = await self.execute_query(query, fetch_one=True)
        return result['count'] if result else 0
    
    async def exists(self, group_id: int) -> bool:
        """
        Check if group exists.
        
        Args:
            group_id: Telegram group ID
            
        Returns:
            True if group exists
        """
        group = await self.find_by_id(group_id)
        return group is not None
    
    async def get_or_create(
        self,
        group_id: int,
        group_name: str,
        posting_time: str = "09:00",
        trader_type: str = "investor"
    ) -> Dict[str, Any]:
        """
        Get existing group or create new one.

        Args:
            group_id: Telegram group ID
            group_name: Group name
            posting_time: Default posting time
            trader_type: Default trader type

        Returns:
            Group data dictionary
        """
        group = await self.find_by_id(group_id)

        if group:
            return group

        # Create new group
        await self.create(group_id, group_name, posting_time, trader_type)
        return await self.find_by_id(group_id)

    async def update_active_status(self, group_id: int, is_active: bool) -> bool:
        """
        Update group's active status (alias for set_active).

        Args:
            group_id: Telegram group ID
            is_active: Active status

        Returns:
            True if successful
        """
        return await self.set_active(group_id, is_active)

