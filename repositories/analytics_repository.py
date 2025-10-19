"""
Analytics repository for AI Market Insight Bot.
Handles analytics and usage tracking with connection pooling.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class AnalyticsRepository(BaseRepository):
    """
    Repository for analytics data operations.
    
    Provides methods for:
    - Usage tracking
    - Command statistics
    - Error logging
    - Performance metrics
    """
    
    async def log_command(
        self,
        chat_id: int,
        command: str,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> bool:
        """
        Log command execution.
        
        Args:
            chat_id: User/group chat ID
            command: Command name
            success: Whether command succeeded
            error_message: Error message if failed
            
        Returns:
            True if successful
        """
        query = """
            INSERT INTO command_logs (chat_id, command, success, error_message, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """
        
        now = datetime.now().isoformat()
        
        try:
            await self.execute_query(
                query,
                (chat_id, command, 1 if success else 0, error_message, now)
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to log command: {e}")
            return False
    
    async def get_command_stats(
        self,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Get command usage statistics.
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of command statistics
        """
        query = """
            SELECT command, 
                   COUNT(*) as total_count,
                   SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success_count,
                   SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as error_count
            FROM command_logs
            WHERE timestamp >= ?
            GROUP BY command
            ORDER BY total_count DESC
        """
        
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        return await self.execute_query(query, (cutoff,), fetch_all=True)
    
    async def get_user_activity(
        self,
        chat_id: int,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get user activity history.
        
        Args:
            chat_id: User chat ID
            days: Number of days to look back
            
        Returns:
            List of command logs
        """
        query = """
            SELECT command, success, error_message, timestamp
            FROM command_logs
            WHERE chat_id = ? AND timestamp >= ?
            ORDER BY timestamp DESC
        """
        
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        return await self.execute_query(query, (chat_id, cutoff), fetch_all=True)
    
    async def get_most_active_users(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get most active users.
        
        Args:
            limit: Number of users to return
            
        Returns:
            List of user activity statistics
        """
        query = """
            SELECT chat_id, COUNT(*) as command_count
            FROM command_logs
            GROUP BY chat_id
            ORDER BY command_count DESC
            LIMIT ?
        """
        
        return await self.execute_query(query, (limit,), fetch_all=True)
    
    async def get_error_rate(self, days: int = 7) -> float:
        """
        Calculate error rate.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Error rate (0.0 to 1.0)
        """
        query = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as errors
            FROM command_logs
            WHERE timestamp >= ?
        """
        
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        result = await self.execute_query(query, (cutoff,), fetch_one=True)
        
        if result and result['total'] > 0:
            return result['errors'] / result['total']
        return 0.0
    
    async def get_daily_usage(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get daily usage statistics.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            List of daily statistics
        """
        query = """
            SELECT 
                DATE(timestamp) as date,
                COUNT(*) as total_commands,
                COUNT(DISTINCT chat_id) as unique_users
            FROM command_logs
            WHERE timestamp >= ?
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
        """
        
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        return await self.execute_query(query, (cutoff,), fetch_all=True)
    
    async def cleanup_old_logs(self, days: int = 90) -> int:
        """
        Delete old command logs.
        
        Args:
            days: Keep logs newer than this many days
            
        Returns:
            Number of logs deleted
        """
        query = "DELETE FROM command_logs WHERE timestamp < ?"
        
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (cutoff,))
                count = cursor.rowcount
                self.logger.info(f"Deleted {count} old command logs")
                return count
        except Exception as e:
            self.logger.error(f"Failed to cleanup old logs: {e}")
            return 0
    
    async def get_peak_hours(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get peak usage hours.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            List of hourly statistics
        """
        query = """
            SELECT 
                CAST(strftime('%H', timestamp) AS INTEGER) as hour,
                COUNT(*) as command_count
            FROM command_logs
            WHERE timestamp >= ?
            GROUP BY hour
            ORDER BY command_count DESC
        """
        
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        return await self.execute_query(query, (cutoff,), fetch_all=True)

