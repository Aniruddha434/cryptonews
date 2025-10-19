"""
Rate limiting middleware for AI Market Insight Bot.
Provides per-user and per-group rate limiting.
"""

import logging
import time
from typing import Dict, Callable
from functools import wraps
from collections import defaultdict
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


class TokenBucket:
    """Token bucket for rate limiting."""
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket.
        
        Args:
            capacity: Maximum tokens
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
    
    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens.
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if tokens available
        """
        self._refill()
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        
        return False
    
    def _refill(self):
        """Refill tokens based on time elapsed."""
        now = time.time()
        elapsed = now - self.last_refill
        
        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now
    
    def get_wait_time(self, tokens: int = 1) -> float:
        """
        Get time to wait until tokens available.
        
        Args:
            tokens: Number of tokens needed
            
        Returns:
            Wait time in seconds
        """
        self._refill()
        
        if self.tokens >= tokens:
            return 0.0
        
        tokens_needed = tokens - self.tokens
        return tokens_needed / self.refill_rate


class RateLimitMiddleware:
    """
    Rate limiting middleware for bot commands.
    
    Provides:
    - Per-user rate limiting
    - Per-group rate limiting
    - Configurable limits
    - Token bucket algorithm
    """
    
    def __init__(
        self,
        user_capacity: int = 10,
        user_refill_rate: float = 1.0,  # 1 token per second
        group_capacity: int = 20,
        group_refill_rate: float = 2.0  # 2 tokens per second
    ):
        """
        Initialize rate limiter.
        
        Args:
            user_capacity: Max requests per user
            user_refill_rate: User tokens per second
            group_capacity: Max requests per group
            group_refill_rate: Group tokens per second
        """
        self.user_capacity = user_capacity
        self.user_refill_rate = user_refill_rate
        self.group_capacity = group_capacity
        self.group_refill_rate = group_refill_rate
        
        self.user_buckets: Dict[int, TokenBucket] = {}
        self.group_buckets: Dict[int, TokenBucket] = {}
        
        logger.info(
            f"RateLimitMiddleware initialized: "
            f"user={user_capacity}/{user_refill_rate}s, "
            f"group={group_capacity}/{group_refill_rate}s"
        )
    
    def _get_user_bucket(self, user_id: int) -> TokenBucket:
        """Get or create token bucket for user."""
        if user_id not in self.user_buckets:
            self.user_buckets[user_id] = TokenBucket(
                self.user_capacity,
                self.user_refill_rate
            )
        return self.user_buckets[user_id]
    
    def _get_group_bucket(self, group_id: int) -> TokenBucket:
        """Get or create token bucket for group."""
        if group_id not in self.group_buckets:
            self.group_buckets[group_id] = TokenBucket(
                self.group_capacity,
                self.group_refill_rate
            )
        return self.group_buckets[group_id]
    
    async def check_rate_limit(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> bool:
        """
        Check if request is within rate limit.
        
        Args:
            update: Telegram update
            context: Bot context
            
        Returns:
            True if allowed, False if rate limited
        """
        # Get user/group ID
        user_id = update.effective_user.id if update.effective_user else None
        chat_id = update.effective_chat.id if update.effective_chat else None
        
        # Check user rate limit
        if user_id:
            bucket = self._get_user_bucket(user_id)
            if not bucket.consume():
                wait_time = bucket.get_wait_time()
                logger.warning(
                    f"User {user_id} rate limited. Wait {wait_time:.1f}s"
                )
                
                await update.message.reply_text(
                    f"⚠️ Rate limit exceeded. Please wait {int(wait_time)} seconds."
                )
                return False
        
        # Check group rate limit (if in group)
        if chat_id and chat_id < 0:  # Negative ID = group
            bucket = self._get_group_bucket(chat_id)
            if not bucket.consume():
                wait_time = bucket.get_wait_time()
                logger.warning(
                    f"Group {chat_id} rate limited. Wait {wait_time:.1f}s"
                )
                
                await update.message.reply_text(
                    f"⚠️ Group rate limit exceeded. Please wait {int(wait_time)} seconds."
                )
                return False
        
        return True
    
    def cleanup_old_buckets(self, max_age: float = 3600.0):
        """
        Clean up old token buckets.
        
        Args:
            max_age: Maximum age in seconds
        """
        now = time.time()
        
        # Clean user buckets
        old_users = [
            user_id for user_id, bucket in self.user_buckets.items()
            if now - bucket.last_refill > max_age
        ]
        for user_id in old_users:
            del self.user_buckets[user_id]
        
        # Clean group buckets
        old_groups = [
            group_id for group_id, bucket in self.group_buckets.items()
            if now - bucket.last_refill > max_age
        ]
        for group_id in old_groups:
            del self.group_buckets[group_id]
        
        if old_users or old_groups:
            logger.debug(
                f"Cleaned up {len(old_users)} user buckets, "
                f"{len(old_groups)} group buckets"
            )


# Global rate limiter instance
_rate_limiter: RateLimitMiddleware = None


def get_rate_limiter() -> RateLimitMiddleware:
    """Get global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimitMiddleware()
    return _rate_limiter


def rate_limit(
    user_capacity: int = 10,
    user_refill_rate: float = 1.0
):
    """
    Decorator for rate limiting bot commands.
    
    Args:
        user_capacity: Max requests per user
        user_refill_rate: User tokens per second
        
    Usage:
        @rate_limit(user_capacity=5, user_refill_rate=0.5)
        async def handle_command(update, context):
            # ... command logic ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
            limiter = get_rate_limiter()
            
            # Check rate limit
            if not await limiter.check_rate_limit(update, context):
                return  # Rate limited
            
            # Execute command
            return await func(self, update, context)
        
        return wrapper
    
    return decorator

