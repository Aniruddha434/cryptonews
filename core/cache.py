"""
Caching layer for AI Market Insight Bot.
Provides in-memory caching with TTL support for improved performance.
"""

import logging
import time
import asyncio
from typing import Any, Optional, Callable, Dict
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import wraps
import hashlib
import json

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with value and metadata."""
    value: Any
    created_at: float
    ttl: float
    hits: int = 0
    
    def is_expired(self) -> bool:
        """Check if entry has expired."""
        return time.time() - self.created_at > self.ttl
    
    def get_age(self) -> float:
        """Get age of entry in seconds."""
        return time.time() - self.created_at


class Cache:
    """
    Thread-safe in-memory cache with TTL support.
    
    Features:
    - TTL-based expiration
    - LRU eviction when max size reached
    - Hit/miss statistics
    - Async-safe operations
    
    Args:
        default_ttl: Default time-to-live in seconds
        max_size: Maximum number of entries
        cleanup_interval: Seconds between cleanup runs
    """
    
    def __init__(
        self,
        default_ttl: float = 300.0,  # 5 minutes
        max_size: int = 1000,
        cleanup_interval: float = 60.0  # 1 minute
    ):
        """Initialize cache."""
        self.default_ttl = default_ttl
        self.max_size = max_size
        self.cleanup_interval = cleanup_interval
        
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "expirations": 0
        }
        
        # Start cleanup task
        self._cleanup_task = None
        
        logger.info(
            f"Cache initialized: default_ttl={default_ttl}s, "
            f"max_size={max_size}, cleanup_interval={cleanup_interval}s"
        )
    
    async def start_cleanup(self):
        """Start background cleanup task."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("Cache cleanup task started")
    
    async def stop_cleanup(self):
        """Stop background cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            logger.info("Cache cleanup task stopped")
    
    async def _cleanup_loop(self):
        """Background task to clean up expired entries."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cache cleanup: {e}")
    
    async def _cleanup_expired(self):
        """Remove expired entries."""
        async with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                del self._cache[key]
                self._stats["expirations"] += 1
            
            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    async def _evict_lru(self):
        """Evict least recently used entry."""
        if not self._cache:
            return
        
        # Find entry with oldest access time (lowest hits)
        lru_key = min(
            self._cache.keys(),
            key=lambda k: (self._cache[k].hits, self._cache[k].created_at)
        )
        
        del self._cache[lru_key]
        self._stats["evictions"] += 1
        logger.debug(f"Evicted LRU cache entry: {lru_key}")
    
    def _generate_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments."""
        # Create deterministic key from arguments
        key_data = {
            "args": args,
            "kwargs": sorted(kwargs.items())
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        async with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self._stats["misses"] += 1
                return None
            
            if entry.is_expired():
                del self._cache[key]
                self._stats["misses"] += 1
                self._stats["expirations"] += 1
                return None
            
            entry.hits += 1
            self._stats["hits"] += 1
            return entry.value
    
    async def set(self, key: str, value: Any, ttl: Optional[float] = None):
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        async with self._lock:
            # Evict if at max size
            if len(self._cache) >= self.max_size and key not in self._cache:
                await self._evict_lru()
            
            entry = CacheEntry(
                value=value,
                created_at=time.time(),
                ttl=ttl or self.default_ttl
            )
            
            self._cache[key] = entry
    
    async def delete(self, key: str) -> bool:
        """
        Delete entry from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted, False if not found
        """
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    async def clear(self):
        """Clear all cache entries."""
        async with self._lock:
            self._cache.clear()
            logger.info("Cache cleared")
    
    async def get_stats(self) -> dict:
        """Get cache statistics."""
        async with self._lock:
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_rate = (
                self._stats["hits"] / total_requests
                if total_requests > 0
                else 0.0
            )
            
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "hit_rate": hit_rate,
                "evictions": self._stats["evictions"],
                "expirations": self._stats["expirations"]
            }
    
    def cached(self, ttl: Optional[float] = None, key_prefix: str = ""):
        """
        Decorator for caching function results.
        
        Args:
            ttl: Time-to-live for cached result
            key_prefix: Prefix for cache key
            
        Usage:
            @cache.cached(ttl=300)
            async def expensive_operation(arg1, arg2):
                # ... expensive work ...
                return result
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = f"{key_prefix}{func.__name__}:{self._generate_key(*args, **kwargs)}"
                
                # Try to get from cache
                cached_value = await self.get(cache_key)
                if cached_value is not None:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return cached_value
                
                # Execute function
                logger.debug(f"Cache miss for {func.__name__}")
                result = await func(*args, **kwargs)
                
                # Store in cache
                await self.set(cache_key, result, ttl)
                
                return result
            
            return wrapper
        
        return decorator


# Global cache instance
_global_cache: Optional[Cache] = None


def get_cache() -> Cache:
    """Get global cache instance."""
    global _global_cache
    if _global_cache is None:
        _global_cache = Cache()
    return _global_cache


async def init_cache(default_ttl: float = 300.0, max_size: int = 1000) -> Cache:
    """Initialize global cache instance."""
    global _global_cache
    _global_cache = Cache(default_ttl=default_ttl, max_size=max_size)
    await _global_cache.start_cleanup()
    return _global_cache


async def shutdown_cache():
    """Shutdown global cache instance."""
    global _global_cache
    if _global_cache:
        await _global_cache.stop_cleanup()
        await _global_cache.clear()
        _global_cache = None

