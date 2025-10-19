"""
Core infrastructure components for AI Market Insight Bot.
Provides foundational services for enterprise-grade operation.
"""

from core.circuit_breaker import CircuitBreaker, circuit_breaker, CircuitBreakerError
from core.cache import Cache, get_cache, init_cache, shutdown_cache
from core.metrics import MetricsCollector, get_metrics_collector
from core.dependency_injection import (
    DependencyContainer,
    ServiceContainer,
    get_container,
    init_container,
    shutdown_container
)
from core.correlation_context import (
    CorrelationContext,
    CorrelationData,
    CorrelationFilter,
    CorrelationFormatter,
    setup_correlation_logging,
    get_structured_logger
)

__all__ = [
    # Circuit Breaker
    'CircuitBreaker',
    'circuit_breaker',
    'CircuitBreakerError',

    # Cache
    'Cache',
    'get_cache',
    'init_cache',
    'shutdown_cache',

    # Metrics
    'MetricsCollector',
    'get_metrics_collector',

    # Dependency Injection
    'DependencyContainer',
    'ServiceContainer',
    'get_container',
    'init_container',
    'shutdown_container',

    # Correlation Context
    'CorrelationContext',
    'CorrelationData',
    'CorrelationFilter',
    'CorrelationFormatter',
    'setup_correlation_logging',
    'get_structured_logger'
]

