"""
Database adapter for AI Market Insight Bot.
Supports both SQLite (local development) and PostgreSQL (production).
Automatically detects environment and uses appropriate database.
"""

import os
import logging
import threading
from queue import Queue, Empty
from contextlib import contextmanager
from typing import Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class DatabaseAdapter:
    """
    Universal database adapter supporting SQLite and PostgreSQL.
    Automatically detects which database to use based on environment.
    """
    
    def __init__(self, database_url: Optional[str] = None, pool_size: int = 5):
        """
        Initialize database adapter.
        
        Args:
            database_url: Database URL (PostgreSQL URL or SQLite path)
            pool_size: Number of connections to maintain in pool
        """
        self.database_url = database_url or os.getenv('DATABASE_URL', './bot_database.db')
        self.pool_size = pool_size
        self.pool = Queue(maxsize=pool_size)
        self.lock = threading.Lock()
        self.active_connections = 0
        
        # Detect database type
        self.is_postgres = self._is_postgres_url(self.database_url)
        
        if self.is_postgres:
            logger.info("Using PostgreSQL database")
            self._init_postgres()
        else:
            logger.info("Using SQLite database")
            self._init_sqlite()
        
        # Pre-populate pool with connections
        for _ in range(pool_size):
            try:
                conn = self._create_connection()
                self.pool.put(conn)
            except Exception as e:
                logger.error(f"Error creating connection for pool: {e}")
    
    def _is_postgres_url(self, url: str) -> bool:
        """Check if URL is a PostgreSQL connection string."""
        return url.startswith('postgresql://') or url.startswith('postgres://')
    
    def _init_postgres(self):
        """Initialize PostgreSQL-specific settings."""
        try:
            import psycopg2
            self.db_module = psycopg2
            logger.info("PostgreSQL driver loaded successfully")
        except ImportError:
            logger.error("psycopg2 not installed. Install with: pip install psycopg2-binary")
            raise
    
    def _init_sqlite(self):
        """Initialize SQLite-specific settings."""
        import sqlite3
        self.db_module = sqlite3
        self.db_path = self.database_url
    
    def _create_connection(self):
        """Create a new database connection."""
        if self.is_postgres:
            return self._create_postgres_connection()
        else:
            return self._create_sqlite_connection()
    
    def _create_postgres_connection(self):
        """Create PostgreSQL connection."""
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        conn = psycopg2.connect(self.database_url, cursor_factory=RealDictCursor)
        conn.autocommit = False
        return conn
    
    def _create_sqlite_connection(self):
        """Create SQLite connection."""
        import sqlite3
        
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    
    @contextmanager
    def get_connection(self):
        """
        Get a connection from the pool.
        
        Usage:
            with adapter.get_connection() as conn:
                cursor = conn.cursor()
                # ... do work ...
        """
        conn = None
        try:
            # Try to get connection from pool with timeout
            conn = self.pool.get(timeout=5)
            self.active_connections += 1
            yield conn
            conn.commit()
        except Empty:
            logger.warning("Connection pool exhausted, creating new connection")
            conn = self._create_connection()
            self.active_connections += 1
            yield conn
            conn.commit()
        except Exception as e:
            logger.error(f"Error during database operation: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                self.active_connections -= 1
                try:
                    self.pool.put(conn, timeout=1)
                except:
                    conn.close()
    
    def close_all(self):
        """Close all connections in the pool."""
        while not self.pool.empty():
            try:
                conn = self.pool.get_nowait()
                conn.close()
            except Empty:
                break
        logger.info("All database connections closed")
    
    def get_pool_stats(self):
        """Get pool statistics."""
        return {
            "database_type": "PostgreSQL" if self.is_postgres else "SQLite",
            "pool_size": self.pool_size,
            "available_connections": self.pool.qsize(),
            "active_connections": self.active_connections,
            "total_connections": self.pool.qsize() + self.active_connections
        }
    
    def get_placeholder(self) -> str:
        """
        Get the parameter placeholder for SQL queries.
        PostgreSQL uses %s, SQLite uses ?
        """
        return "%s" if self.is_postgres else "?"
    
    def adapt_query(self, query: str) -> str:
        """
        Adapt SQL query for the current database.
        Converts between SQLite and PostgreSQL syntax.
        """
        if self.is_postgres:
            # Convert SQLite syntax to PostgreSQL
            query = query.replace("AUTOINCREMENT", "")
            query = query.replace("INTEGER PRIMARY KEY", "SERIAL PRIMARY KEY")
            query = query.replace("?", "%s")
        return query


# Global adapter instance
_adapter: Optional[DatabaseAdapter] = None


def init_adapter(database_url: Optional[str] = None, pool_size: int = 5) -> DatabaseAdapter:
    """Initialize the global database adapter."""
    global _adapter
    _adapter = DatabaseAdapter(database_url, pool_size)
    logger.info(f"Database adapter initialized: {_adapter.get_pool_stats()}")
    return _adapter


def get_adapter() -> DatabaseAdapter:
    """Get the global database adapter."""
    global _adapter
    if _adapter is None:
        _adapter = init_adapter()
    return _adapter


def close_adapter():
    """Close the global database adapter."""
    global _adapter
    if _adapter:
        _adapter.close_all()
        _adapter = None

