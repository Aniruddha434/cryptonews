"""
Base repository with common database operations.
Provides connection pooling and transaction management.
"""

import logging
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
from abc import ABC, abstractmethod
from db_pool import get_pool, ConnectionPool

logger = logging.getLogger(__name__)


class IRepository(ABC):
    """Interface for repository pattern."""
    
    @abstractmethod
    async def find_by_id(self, id: Any) -> Optional[Dict[str, Any]]:
        """Find entity by ID."""
        pass
    
    @abstractmethod
    async def find_all(self) -> List[Dict[str, Any]]:
        """Find all entities."""
        pass
    
    @abstractmethod
    async def create(self, data: Dict[str, Any]) -> bool:
        """Create new entity."""
        pass
    
    @abstractmethod
    async def update(self, id: Any, data: Dict[str, Any]) -> bool:
        """Update existing entity."""
        pass
    
    @abstractmethod
    async def delete(self, id: Any) -> bool:
        """Delete entity."""
        pass


class BaseRepository:
    """
    Base repository with connection pooling and common operations.
    
    All repositories should inherit from this class to get:
    - Connection pooling
    - Transaction management
    - Error handling
    - Logging
    """
    
    def __init__(self, pool: Optional[ConnectionPool] = None):
        """
        Initialize repository.
        
        Args:
            pool: Connection pool instance (uses global if None)
        """
        self.pool = pool or get_pool()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @asynccontextmanager
    async def get_connection(self):
        """
        Get database connection from pool.
        
        Usage:
            async with self.get_connection() as conn:
                cursor = conn.cursor()
                # ... database operations ...
        """
        # Note: db_pool.ConnectionPool.get_connection() is synchronous
        # We'll wrap it for async compatibility
        with self.pool.get_connection() as conn:
            try:
                yield conn
            except Exception as e:
                self.logger.error(f"Database error: {e}", exc_info=True)
                raise
    
    async def execute_query(
        self,
        query: str,
        params: tuple = (),
        fetch_one: bool = False,
        fetch_all: bool = False
    ) -> Optional[Any]:
        """
        Execute a database query with connection pooling.
        
        Args:
            query: SQL query string
            params: Query parameters
            fetch_one: Return single row
            fetch_all: Return all rows
            
        Returns:
            Query result or None
        """
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                
                if fetch_one:
                    result = cursor.fetchone()
                    return dict(result) if result else None
                elif fetch_all:
                    results = cursor.fetchall()
                    return [dict(row) for row in results]
                else:
                    return cursor.lastrowid
                    
        except Exception as e:
            self.logger.error(f"Query execution error: {e}", exc_info=True)
            raise
    
    async def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """
        Execute query with multiple parameter sets (batch operation).
        
        Args:
            query: SQL query string
            params_list: List of parameter tuples
            
        Returns:
            Number of affected rows
        """
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.executemany(query, params_list)
                return cursor.rowcount
                
        except Exception as e:
            self.logger.error(f"Batch execution error: {e}", exc_info=True)
            raise
    
    async def transaction(self, operations: List[tuple]) -> bool:
        """
        Execute multiple operations in a transaction.
        
        Args:
            operations: List of (query, params) tuples
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                
                for query, params in operations:
                    cursor.execute(query, params)
                
                # Connection context manager handles commit
                return True
                
        except Exception as e:
            self.logger.error(f"Transaction error: {e}", exc_info=True)
            # Connection context manager handles rollback
            return False
    
    def _row_to_dict(self, row, columns: List[str]) -> Dict[str, Any]:
        """Convert database row to dictionary."""
        if row is None:
            return None
        return {col: row[i] for i, col in enumerate(columns)}
    
    def _rows_to_dicts(self, rows, columns: List[str]) -> List[Dict[str, Any]]:
        """Convert database rows to list of dictionaries."""
        return [self._row_to_dict(row, columns) for row in rows]

