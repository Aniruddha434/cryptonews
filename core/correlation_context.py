"""
Correlation context for distributed tracing and structured logging.
Provides request tracking across async operations.
"""

import logging
import uuid
from typing import Optional, Dict, Any
from contextvars import ContextVar
from dataclasses import dataclass, field, asdict
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class CorrelationData:
    """Correlation data for request tracking."""
    
    correlation_id: str
    user_id: Optional[int] = None
    group_id: Optional[int] = None
    command: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    def to_log_extra(self) -> Dict[str, Any]:
        """Convert to logging extra fields."""
        return {
            'correlation_id': self.correlation_id,
            'user_id': self.user_id,
            'group_id': self.group_id,
            'command': self.command,
            'timestamp': self.timestamp,
            **self.metadata
        }


# Context variable for correlation data
_correlation_context: ContextVar[Optional[CorrelationData]] = ContextVar(
    'correlation_context',
    default=None
)


class CorrelationContext:
    """
    Context manager for correlation tracking.
    
    Usage:
        with CorrelationContext(user_id=123, command="news"):
            logger.info("Processing request")  # Includes correlation ID
            await process_request()
    """
    
    def __init__(
        self,
        user_id: Optional[int] = None,
        group_id: Optional[int] = None,
        command: Optional[str] = None,
        correlation_id: Optional[str] = None,
        **metadata
    ):
        """
        Initialize correlation context.
        
        Args:
            user_id: User chat ID
            group_id: Group chat ID
            command: Command name
            correlation_id: Existing correlation ID (generates new if None)
            **metadata: Additional metadata
        """
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.user_id = user_id
        self.group_id = group_id
        self.command = command
        self.metadata = metadata
        self._token = None
        self._previous_data = None
    
    def __enter__(self):
        """Enter context and set correlation data."""
        # Save previous context
        self._previous_data = _correlation_context.get()
        
        # Create new correlation data
        data = CorrelationData(
            correlation_id=self.correlation_id,
            user_id=self.user_id,
            group_id=self.group_id,
            command=self.command,
            metadata=self.metadata
        )
        
        # Set context
        self._token = _correlation_context.set(data)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and restore previous correlation data."""
        if self._token:
            _correlation_context.reset(self._token)
    
    async def __aenter__(self):
        """Async context manager enter."""
        return self.__enter__()
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        return self.__exit__(exc_type, exc_val, exc_tb)
    
    @staticmethod
    def get_current() -> Optional[CorrelationData]:
        """Get current correlation data."""
        return _correlation_context.get()
    
    @staticmethod
    def get_correlation_id() -> Optional[str]:
        """Get current correlation ID."""
        data = _correlation_context.get()
        return data.correlation_id if data else None
    
    @staticmethod
    def get_log_extra() -> Dict[str, Any]:
        """Get logging extra fields from current context."""
        data = _correlation_context.get()
        return data.to_log_extra() if data else {}


class CorrelationFilter(logging.Filter):
    """
    Logging filter that adds correlation data to log records.
    
    Usage:
        handler = logging.StreamHandler()
        handler.addFilter(CorrelationFilter())
        logger.addHandler(handler)
    """
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation data to log record."""
        data = CorrelationContext.get_current()
        
        if data:
            record.correlation_id = data.correlation_id
            record.user_id = data.user_id
            record.group_id = data.group_id
            record.command = data.command
        else:
            record.correlation_id = None
            record.user_id = None
            record.group_id = None
            record.command = None
        
        return True


class CorrelationFormatter(logging.Formatter):
    """
    Logging formatter that includes correlation data.
    
    Usage:
        formatter = CorrelationFormatter(
            '%(asctime)s [%(correlation_id)s] %(levelname)s: %(message)s'
        )
        handler.setFormatter(formatter)
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with correlation data."""
        # Ensure correlation fields exist
        if not hasattr(record, 'correlation_id'):
            record.correlation_id = None
        if not hasattr(record, 'user_id'):
            record.user_id = None
        if not hasattr(record, 'group_id'):
            record.group_id = None
        if not hasattr(record, 'command'):
            record.command = None
        
        return super().format(record)


def setup_correlation_logging():
    """
    Setup correlation logging for all loggers.
    
    Adds CorrelationFilter to root logger.
    """
    root_logger = logging.getLogger()
    
    # Add correlation filter to all handlers
    for handler in root_logger.handlers:
        handler.addFilter(CorrelationFilter())
    
    logger.info("Correlation logging configured")


def get_structured_logger(name: str) -> logging.Logger:
    """
    Get logger with correlation support.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    log = logging.getLogger(name)
    
    # Wrap logger methods to include correlation context
    original_info = log.info
    original_warning = log.warning
    original_error = log.error
    original_debug = log.debug
    
    def info_with_context(msg, *args, **kwargs):
        extra = kwargs.get('extra', {})
        extra.update(CorrelationContext.get_log_extra())
        kwargs['extra'] = extra
        return original_info(msg, *args, **kwargs)
    
    def warning_with_context(msg, *args, **kwargs):
        extra = kwargs.get('extra', {})
        extra.update(CorrelationContext.get_log_extra())
        kwargs['extra'] = extra
        return original_warning(msg, *args, **kwargs)
    
    def error_with_context(msg, *args, **kwargs):
        extra = kwargs.get('extra', {})
        extra.update(CorrelationContext.get_log_extra())
        kwargs['extra'] = extra
        return original_error(msg, *args, **kwargs)
    
    def debug_with_context(msg, *args, **kwargs):
        extra = kwargs.get('extra', {})
        extra.update(CorrelationContext.get_log_extra())
        kwargs['extra'] = extra
        return original_debug(msg, *args, **kwargs)
    
    log.info = info_with_context
    log.warning = warning_with_context
    log.error = error_with_context
    log.debug = debug_with_context
    
    return log

