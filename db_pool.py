"""
Database connection pooling module for AI Market Insight Bot.
Provides efficient connection management and pooling.
Now uses DatabaseAdapter for PostgreSQL/SQLite support.
"""

import logging
import os
from contextlib import contextmanager
from db_adapter import DatabaseAdapter, get_adapter, init_adapter, close_adapter

logger = logging.getLogger(__name__)


class ConnectionPool:
    """
    Connection pool wrapper for backward compatibility.
    Now delegates to DatabaseAdapter for PostgreSQL/SQLite support.
    """

    def __init__(self, db_path=None, pool_size=5):
        """
        Initialize connection pool.

        Args:
            db_path: Path to database (for backward compatibility)
            pool_size: Number of connections to maintain in pool
        """
        # Use DATABASE_URL from environment if available, otherwise use db_path
        database_url = os.getenv('DATABASE_URL')
        if not database_url and db_path:
            database_url = db_path

        self.adapter = DatabaseAdapter(database_url, pool_size)
        logger.info(f"ConnectionPool initialized with {self.adapter.get_pool_stats()}")

    @contextmanager
    def get_connection(self):
        """
        Get a connection from the pool.

        Usage:
            with pool.get_connection() as conn:
                cursor = conn.cursor()
                # ... do work ...
        """
        with self.adapter.get_connection() as conn:
            yield conn

    def close_all(self):
        """Close all connections in the pool."""
        self.adapter.close_all()

    def get_pool_stats(self):
        """Get pool statistics."""
        return self.adapter.get_pool_stats()


# Global connection pool instance
_pool = None


def init_pool(db_path=None, pool_size=5):
    """Initialize the global connection pool."""
    global _pool
    _pool = ConnectionPool(db_path, pool_size)
    stats = _pool.get_pool_stats()
    logger.info(f"Connection pool initialized: {stats}")
    return _pool


def get_pool():
    """Get the global connection pool."""
    global _pool
    if _pool is None:
        _pool = init_pool()
    return _pool


def close_pool():
    """Close the global connection pool."""
    global _pool
    if _pool:
        _pool.close_all()
        _pool = None

