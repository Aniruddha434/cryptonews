"""
Rate limiter and retry logic for API calls.
Prevents hitting Telegram API limits and handles transient failures.
"""

import logging
import asyncio
import time
from functools import wraps
from typing import Callable, Any

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter for API calls."""
    
    def __init__(self, calls_per_second: float = 30):
        """
        Initialize rate limiter.
        
        Args:
            calls_per_second: Maximum calls per second (Telegram default is ~30)
        """
        self.calls_per_second = calls_per_second
        self.min_interval = 1.0 / calls_per_second
        self.last_call_time = 0
    
    async def acquire(self):
        """Wait if necessary to maintain rate limit."""
        current_time = time.time()
        time_since_last_call = current_time - self.last_call_time
        
        if time_since_last_call < self.min_interval:
            wait_time = self.min_interval - time_since_last_call
            logger.debug(f"Rate limiting: waiting {wait_time:.3f}s")
            await asyncio.sleep(wait_time)
        
        self.last_call_time = time.time()


class RetryConfig:
    """Configuration for retry logic."""
    
    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0
    ):
        """
        Initialize retry configuration.
        
        Args:
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Base for exponential backoff
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number."""
        delay = self.initial_delay * (self.exponential_base ** attempt)
        return min(delay, self.max_delay)


def async_retry(config: RetryConfig = None):
    """
    Decorator for async functions with retry logic.
    
    Args:
        config: RetryConfig instance
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(config.max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt < config.max_retries:
                        delay = config.get_delay(attempt)
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"All {config.max_retries + 1} attempts failed for {func.__name__}: {e}"
                        )
            
            raise last_exception
        
        return wrapper
    
    return decorator


def sync_retry(config: RetryConfig = None):
    """
    Decorator for sync functions with retry logic.
    
    Args:
        config: RetryConfig instance
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(config.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt < config.max_retries:
                        delay = config.get_delay(attempt)
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"All {config.max_retries + 1} attempts failed for {func.__name__}: {e}"
                        )
            
            raise last_exception
        
        return wrapper
    
    return decorator


class ConcurrentPostingManager:
    """Manages concurrent posting to multiple groups with rate limiting."""
    
    def __init__(self, max_concurrent: int = 5, calls_per_second: float = 30):
        """
        Initialize posting manager.
        
        Args:
            max_concurrent: Maximum concurrent posts
            calls_per_second: Rate limit for API calls
        """
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.rate_limiter = RateLimiter(calls_per_second)
        self.retry_config = RetryConfig()
    
    async def post_to_group(
        self,
        post_func: Callable,
        group_id: int,
        *args,
        **kwargs
    ) -> bool:
        """
        Post to a group with rate limiting and retry logic.
        
        Args:
            post_func: Async function to call for posting
            group_id: Target group ID
            *args: Arguments for post_func
            **kwargs: Keyword arguments for post_func
        
        Returns:
            True if successful, False otherwise
        """
        async with self.semaphore:
            await self.rate_limiter.acquire()
            
            last_exception = None
            for attempt in range(self.retry_config.max_retries + 1):
                try:
                    result = await post_func(group_id, *args, **kwargs)
                    logger.info(f"Successfully posted to group {group_id}")
                    return True
                except Exception as e:
                    last_exception = e
                    
                    if attempt < self.retry_config.max_retries:
                        delay = self.retry_config.get_delay(attempt)
                        logger.warning(
                            f"Post to group {group_id} failed (attempt {attempt + 1}): {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"Failed to post to group {group_id} after {self.retry_config.max_retries + 1} attempts: {e}"
                        )
            
            return False
    
    async def post_to_multiple_groups(
        self,
        post_func: Callable,
        group_ids: list,
        *args,
        **kwargs
    ) -> dict:
        """
        Post to multiple groups concurrently.
        
        Args:
            post_func: Async function to call for posting
            group_ids: List of target group IDs
            *args: Arguments for post_func
            **kwargs: Keyword arguments for post_func
        
        Returns:
            Dict with group_id -> success status
        """
        tasks = [
            self.post_to_group(post_func, group_id, *args, **kwargs)
            for group_id in group_ids
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=False)
        
        return {
            group_id: success
            for group_id, success in zip(group_ids, results)
        }

