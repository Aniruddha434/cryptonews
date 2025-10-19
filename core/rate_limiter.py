"""
Rate limiter for AI Market Insight Bot.
Prevents abuse by limiting request rates per user/group.
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter.
    
    Provides:
    - Per-user rate limiting
    - Per-group rate limiting
    - Configurable limits and windows
    - Automatic cleanup of old requests
    """
    
    def __init__(
        self,
        max_requests: int = 10,
        window_seconds: int = 60,
        name: str = "default"
    ):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
            name: Name for logging purposes
        """
        self.max_requests = max_requests
        self.window = timedelta(seconds=window_seconds)
        self.name = name
        
        # Store request timestamps per identifier
        self.requests: Dict[int, List[datetime]] = defaultdict(list)
        
        # Track violations for monitoring
        self.violations = 0
        
        logger.info(f"RateLimiter '{name}' initialized: {max_requests} requests per {window_seconds}s")
    
    def is_allowed(self, identifier: int) -> bool:
        """
        Check if request is allowed for identifier.
        
        Args:
            identifier: User ID or Group ID
            
        Returns:
            True if request is allowed
        """
        now = datetime.now()
        
        # Clean old requests outside the window
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if now - req_time < self.window
        ]
        
        # Check if limit exceeded
        if len(self.requests[identifier]) >= self.max_requests:
            self.violations += 1
            logger.warning(
                f"Rate limit exceeded for {identifier} in '{self.name}': "
                f"{len(self.requests[identifier])}/{self.max_requests} requests"
            )
            return False
        
        # Add current request
        self.requests[identifier].append(now)
        return True
    
    def get_remaining(self, identifier: int) -> int:
        """
        Get remaining requests for identifier.
        
        Args:
            identifier: User ID or Group ID
            
        Returns:
            Number of remaining requests
        """
        now = datetime.now()
        
        # Clean old requests
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if now - req_time < self.window
        ]
        
        return max(0, self.max_requests - len(self.requests[identifier]))
    
    def get_reset_time(self, identifier: int) -> Optional[datetime]:
        """
        Get time when rate limit resets for identifier.
        
        Args:
            identifier: User ID or Group ID
            
        Returns:
            Reset time or None if no requests
        """
        if not self.requests[identifier]:
            return None
        
        # Oldest request + window = reset time
        oldest = min(self.requests[identifier])
        return oldest + self.window
    
    def reset(self, identifier: int):
        """
        Reset rate limit for identifier.
        
        Args:
            identifier: User ID or Group ID
        """
        if identifier in self.requests:
            del self.requests[identifier]
            logger.info(f"Rate limit reset for {identifier} in '{self.name}'")
    
    def cleanup(self):
        """
        Clean up old request data.
        Should be called periodically to prevent memory growth.
        """
        now = datetime.now()
        cleaned = 0
        
        # Remove identifiers with no recent requests
        identifiers_to_remove = []
        for identifier, timestamps in self.requests.items():
            # Filter out old timestamps
            recent = [t for t in timestamps if now - t < self.window]
            
            if not recent:
                identifiers_to_remove.append(identifier)
            else:
                self.requests[identifier] = recent
        
        # Remove empty identifiers
        for identifier in identifiers_to_remove:
            del self.requests[identifier]
            cleaned += 1
        
        if cleaned > 0:
            logger.debug(f"Cleaned {cleaned} identifiers from '{self.name}' rate limiter")
    
    def get_stats(self) -> Dict:
        """
        Get rate limiter statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            'name': self.name,
            'max_requests': self.max_requests,
            'window_seconds': self.window.total_seconds(),
            'active_identifiers': len(self.requests),
            'total_violations': self.violations
        }


class RateLimiterCollection:
    """
    Collection of rate limiters for different purposes.
    
    Provides:
    - Multiple rate limiters with different limits
    - Centralized management
    - Automatic cleanup
    """
    
    def __init__(self):
        """Initialize rate limiter collection."""
        self.limiters: Dict[str, RateLimiter] = {}
        logger.info("RateLimiterCollection initialized")
    
    def add_limiter(
        self,
        name: str,
        max_requests: int,
        window_seconds: int
    ) -> RateLimiter:
        """
        Add a rate limiter.
        
        Args:
            name: Limiter name
            max_requests: Maximum requests in window
            window_seconds: Time window in seconds
            
        Returns:
            Created rate limiter
        """
        limiter = RateLimiter(max_requests, window_seconds, name)
        self.limiters[name] = limiter
        return limiter
    
    def get_limiter(self, name: str) -> Optional[RateLimiter]:
        """
        Get rate limiter by name.
        
        Args:
            name: Limiter name
            
        Returns:
            Rate limiter or None
        """
        return self.limiters.get(name)
    
    def is_allowed(self, limiter_name: str, identifier: int) -> bool:
        """
        Check if request is allowed.
        
        Args:
            limiter_name: Name of rate limiter
            identifier: User ID or Group ID
            
        Returns:
            True if allowed
        """
        limiter = self.limiters.get(limiter_name)
        if not limiter:
            logger.warning(f"Rate limiter '{limiter_name}' not found")
            return True  # Allow if limiter doesn't exist
        
        return limiter.is_allowed(identifier)
    
    def cleanup_all(self):
        """Clean up all rate limiters."""
        for limiter in self.limiters.values():
            limiter.cleanup()
    
    def get_all_stats(self) -> Dict:
        """
        Get statistics for all rate limiters.
        
        Returns:
            Statistics dictionary
        """
        return {
            name: limiter.get_stats()
            for name, limiter in self.limiters.items()
        }


# Global rate limiter collection
_rate_limiters = None


def get_rate_limiters() -> RateLimiterCollection:
    """
    Get global rate limiter collection.
    
    Returns:
        Rate limiter collection
    """
    global _rate_limiters
    if _rate_limiters is None:
        _rate_limiters = RateLimiterCollection()
        
        # Add default rate limiters
        _rate_limiters.add_limiter('user_commands', max_requests=10, window_seconds=60)
        _rate_limiters.add_limiter('group_commands', max_requests=20, window_seconds=60)
        _rate_limiters.add_limiter('admin_commands', max_requests=30, window_seconds=60)
        _rate_limiters.add_limiter('webhook', max_requests=100, window_seconds=60)
        
        logger.info("Global rate limiters initialized")
    
    return _rate_limiters

