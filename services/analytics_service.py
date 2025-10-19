"""
Analytics service for AI Market Insight Bot.
Handles usage tracking and reporting.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from core.metrics import MetricsCollector
from repositories.analytics_repository import AnalyticsRepository

logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    Service for analytics operations.
    
    Provides:
    - Command usage tracking
    - Error logging
    - Performance metrics
    - Usage reports
    """
    
    def __init__(
        self,
        analytics_repo: AnalyticsRepository,
        metrics: MetricsCollector
    ):
        """
        Initialize analytics service.
        
        Args:
            analytics_repo: Analytics repository
            metrics: Metrics collector
        """
        self.analytics_repo = analytics_repo
        self.metrics = metrics
        
        logger.info("AnalyticsService initialized")
    
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
            True if logged successfully
        """
        try:
            # Log to database
            await self.analytics_repo.log_command(
                chat_id,
                command,
                success,
                error_message
            )
            
            # Update metrics
            self.metrics.inc_counter("bot_requests_total")
            
            if not success:
                self.metrics.inc_counter("bot_errors_total")
            
            return True
            
        except Exception as e:
            logger.error(f"Error logging command: {e}", exc_info=True)
            return False
    
    async def get_command_stats(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get command usage statistics.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            List of command statistics
        """
        try:
            return await self.analytics_repo.get_command_stats(days)
        except Exception as e:
            logger.error(f"Error getting command stats: {e}", exc_info=True)
            return []
    
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
            List of user activities
        """
        try:
            return await self.analytics_repo.get_user_activity(chat_id, days)
        except Exception as e:
            logger.error(f"Error getting user activity: {e}", exc_info=True)
            return []
    
    async def get_most_active_users(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get most active users.
        
        Args:
            limit: Number of users to return
            
        Returns:
            List of user activity stats
        """
        try:
            return await self.analytics_repo.get_most_active_users(limit)
        except Exception as e:
            logger.error(f"Error getting most active users: {e}", exc_info=True)
            return []
    
    async def get_error_rate(self, days: int = 7) -> float:
        """
        Calculate error rate.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Error rate (0.0 to 1.0)
        """
        try:
            return await self.analytics_repo.get_error_rate(days)
        except Exception as e:
            logger.error(f"Error calculating error rate: {e}", exc_info=True)
            return 0.0
    
    async def get_daily_usage(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get daily usage statistics.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            List of daily statistics
        """
        try:
            return await self.analytics_repo.get_daily_usage(days)
        except Exception as e:
            logger.error(f"Error getting daily usage: {e}", exc_info=True)
            return []
    
    async def get_peak_hours(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get peak usage hours.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            List of hourly statistics
        """
        try:
            return await self.analytics_repo.get_peak_hours(days)
        except Exception as e:
            logger.error(f"Error getting peak hours: {e}", exc_info=True)
            return []
    
    async def get_analytics_report(self, days: int = 7) -> Dict[str, Any]:
        """
        Generate comprehensive analytics report.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Analytics report dictionary
        """
        try:
            command_stats = await self.get_command_stats(days)
            error_rate = await self.get_error_rate(days)
            daily_usage = await self.get_daily_usage(days)
            peak_hours = await self.get_peak_hours(days)
            most_active = await self.get_most_active_users(10)
            
            # Get metrics
            metrics = await self.metrics.get_metrics()
            cache_stats = metrics.get('gauges', {}).get('cache_size', {})
            
            return {
                'period_days': days,
                'generated_at': datetime.now().isoformat(),
                'command_stats': command_stats,
                'error_rate': error_rate,
                'daily_usage': daily_usage,
                'peak_hours': peak_hours,
                'most_active_users': most_active,
                'cache_stats': cache_stats,
                'metrics_summary': {
                    'total_requests': metrics.get('counters', {}).get('bot_requests_total', {}).get('value', 0),
                    'total_errors': metrics.get('counters', {}).get('bot_errors_total', {}).get('value', 0),
                    'cache_hits': metrics.get('counters', {}).get('cache_hits_total', {}).get('value', 0),
                    'cache_misses': metrics.get('counters', {}).get('cache_misses_total', {}).get('value', 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating analytics report: {e}", exc_info=True)
            return {
                'period_days': days,
                'generated_at': datetime.now().isoformat(),
                'error': str(e)
            }
    
    async def cleanup_old_logs(self, days: int = 90) -> int:
        """
        Clean up old analytics logs.
        
        Args:
            days: Keep logs newer than this many days
            
        Returns:
            Number of logs deleted
        """
        try:
            count = await self.analytics_repo.cleanup_old_logs(days)
            logger.info(f"Cleaned up {count} old analytics logs")
            return count
        except Exception as e:
            logger.error(f"Error cleaning up logs: {e}", exc_info=True)
            return 0

