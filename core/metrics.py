"""
Metrics collection and monitoring for AI Market Insight Bot.
Provides Prometheus-compatible metrics for observability.
"""

import logging
import time
from typing import Dict, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class Counter:
    """Simple counter metric."""
    name: str
    help_text: str
    value: int = 0
    labels: Dict[str, str] = field(default_factory=dict)
    
    def inc(self, amount: int = 1):
        """Increment counter."""
        self.value += amount
    
    def get(self) -> int:
        """Get current value."""
        return self.value
    
    def reset(self):
        """Reset counter to zero."""
        self.value = 0


@dataclass
class Gauge:
    """Gauge metric for values that can go up and down."""
    name: str
    help_text: str
    value: float = 0.0
    labels: Dict[str, str] = field(default_factory=dict)
    
    def set(self, value: float):
        """Set gauge value."""
        self.value = value
    
    def inc(self, amount: float = 1.0):
        """Increment gauge."""
        self.value += amount
    
    def dec(self, amount: float = 1.0):
        """Decrement gauge."""
        self.value -= amount
    
    def get(self) -> float:
        """Get current value."""
        return self.value


@dataclass
class Histogram:
    """Histogram metric for tracking distributions."""
    name: str
    help_text: str
    buckets: List[float] = field(default_factory=lambda: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0])
    observations: List[float] = field(default_factory=list)
    labels: Dict[str, str] = field(default_factory=dict)
    
    def observe(self, value: float):
        """Record an observation."""
        self.observations.append(value)
    
    def get_count(self) -> int:
        """Get number of observations."""
        return len(self.observations)
    
    def get_sum(self) -> float:
        """Get sum of all observations."""
        return sum(self.observations)
    
    def get_buckets(self) -> Dict[float, int]:
        """Get bucket counts."""
        bucket_counts = {b: 0 for b in self.buckets}
        bucket_counts[float('inf')] = 0
        
        for obs in self.observations:
            for bucket in self.buckets:
                if obs <= bucket:
                    bucket_counts[bucket] += 1
            bucket_counts[float('inf')] += 1
        
        return bucket_counts


class MetricsCollector:
    """
    Centralized metrics collection for monitoring and observability.
    
    Provides:
    - Counters for event counts
    - Gauges for current values
    - Histograms for distributions
    - Request latency tracking
    - Error rate tracking
    """
    
    def __init__(self):
        """Initialize metrics collector."""
        self._counters: Dict[str, Counter] = {}
        self._gauges: Dict[str, Gauge] = {}
        self._histograms: Dict[str, Histogram] = {}
        self._lock = asyncio.Lock()
        
        # Initialize standard metrics
        self._init_standard_metrics()
        
        logger.info("Metrics collector initialized")
    
    def _init_standard_metrics(self):
        """Initialize standard application metrics."""
        # Request metrics
        self.register_counter(
            "bot_requests_total",
            "Total number of bot requests",
            labels={"command": "", "status": ""}
        )
        
        self.register_counter(
            "bot_errors_total",
            "Total number of errors",
            labels={"type": "", "severity": ""}
        )
        
        self.register_histogram(
            "bot_request_duration_seconds",
            "Request duration in seconds",
            labels={"command": ""}
        )
        
        # API metrics
        self.register_counter(
            "api_calls_total",
            "Total API calls",
            labels={"service": "", "status": ""}
        )
        
        self.register_histogram(
            "api_call_duration_seconds",
            "API call duration in seconds",
            labels={"service": ""}
        )
        
        # Database metrics
        self.register_counter(
            "db_queries_total",
            "Total database queries",
            labels={"operation": "", "status": ""}
        )
        
        self.register_histogram(
            "db_query_duration_seconds",
            "Database query duration in seconds",
            labels={"operation": ""}
        )
        
        self.register_gauge(
            "db_connections_active",
            "Number of active database connections"
        )
        
        # Bot-specific metrics
        self.register_gauge(
            "bot_users_total",
            "Total number of registered users"
        )
        
        self.register_gauge(
            "bot_groups_total",
            "Total number of registered groups"
        )
        
        self.register_counter(
            "bot_messages_sent_total",
            "Total messages sent",
            labels={"type": ""}
        )
        
        # Cache metrics
        self.register_counter(
            "cache_hits_total",
            "Total cache hits"
        )
        
        self.register_counter(
            "cache_misses_total",
            "Total cache misses"
        )
        
        self.register_gauge(
            "cache_size",
            "Current cache size"
        )
    
    def register_counter(self, name: str, help_text: str, labels: Optional[Dict[str, str]] = None) -> Counter:
        """Register a new counter metric."""
        counter = Counter(name=name, help_text=help_text, labels=labels or {})
        self._counters[name] = counter
        return counter
    
    def register_gauge(self, name: str, help_text: str, labels: Optional[Dict[str, str]] = None) -> Gauge:
        """Register a new gauge metric."""
        gauge = Gauge(name=name, help_text=help_text, labels=labels or {})
        self._gauges[name] = gauge
        return gauge
    
    def register_histogram(self, name: str, help_text: str, labels: Optional[Dict[str, str]] = None) -> Histogram:
        """Register a new histogram metric."""
        histogram = Histogram(name=name, help_text=help_text, labels=labels or {})
        self._histograms[name] = histogram
        return histogram
    
    def inc_counter(self, name: str, amount: int = 1, labels: Optional[Dict[str, str]] = None):
        """Increment a counter."""
        if name in self._counters:
            self._counters[name].inc(amount)
    
    def set_gauge(self, name: str, value: float):
        """Set a gauge value."""
        if name in self._gauges:
            self._gauges[name].set(value)
    
    def observe_histogram(self, name: str, value: float):
        """Record a histogram observation."""
        if name in self._histograms:
            self._histograms[name].observe(value)
    
    def track_request(self, command: str):
        """Context manager for tracking request metrics."""
        return RequestTracker(self, command)
    
    def track_api_call(self, service: str):
        """Context manager for tracking API call metrics."""
        return APICallTracker(self, service)
    
    def track_db_query(self, operation: str):
        """Context manager for tracking database query metrics."""
        return DBQueryTracker(self, operation)
    
    async def get_metrics(self) -> Dict[str, any]:
        """Get all metrics in dictionary format."""
        async with self._lock:
            metrics = {
                "counters": {
                    name: {"value": counter.get(), "help": counter.help_text}
                    for name, counter in self._counters.items()
                },
                "gauges": {
                    name: {"value": gauge.get(), "help": gauge.help_text}
                    for name, gauge in self._gauges.items()
                },
                "histograms": {
                    name: {
                        "count": hist.get_count(),
                        "sum": hist.get_sum(),
                        "buckets": hist.get_buckets(),
                        "help": hist.help_text
                    }
                    for name, hist in self._histograms.items()
                }
            }
            return metrics
    
    async def get_prometheus_format(self) -> str:
        """Get metrics in Prometheus text format."""
        lines = []
        
        # Counters
        for name, counter in self._counters.items():
            lines.append(f"# HELP {name} {counter.help_text}")
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{name} {counter.get()}")
        
        # Gauges
        for name, gauge in self._gauges.items():
            lines.append(f"# HELP {name} {gauge.help_text}")
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name} {gauge.get()}")
        
        # Histograms
        for name, hist in self._histograms.items():
            lines.append(f"# HELP {name} {hist.help_text}")
            lines.append(f"# TYPE {name} histogram")
            
            buckets = hist.get_buckets()
            for bucket, count in buckets.items():
                bucket_str = "+Inf" if bucket == float('inf') else str(bucket)
                lines.append(f'{name}_bucket{{le="{bucket_str}"}} {count}')
            
            lines.append(f"{name}_sum {hist.get_sum()}")
            lines.append(f"{name}_count {hist.get_count()}")
        
        return "\n".join(lines)


class RequestTracker:
    """Context manager for tracking request metrics."""
    
    def __init__(self, collector: MetricsCollector, command: str):
        self.collector = collector
        self.command = command
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        status = "error" if exc_type else "success"
        self.collector.inc_counter("bot_requests_total")
        self.collector.observe_histogram("bot_request_duration_seconds", duration)
        
        if exc_type:
            self.collector.inc_counter("bot_errors_total")


class APICallTracker:
    """Context manager for tracking API call metrics."""
    
    def __init__(self, collector: MetricsCollector, service: str):
        self.collector = collector
        self.service = service
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        status = "error" if exc_type else "success"
        self.collector.inc_counter("api_calls_total")
        self.collector.observe_histogram("api_call_duration_seconds", duration)


class DBQueryTracker:
    """Context manager for tracking database query metrics."""
    
    def __init__(self, collector: MetricsCollector, operation: str):
        self.collector = collector
        self.operation = operation
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        status = "error" if exc_type else "success"
        self.collector.inc_counter("db_queries_total")
        self.collector.observe_histogram("db_query_duration_seconds", duration)


# Global metrics collector
_global_metrics: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector instance."""
    global _global_metrics
    if _global_metrics is None:
        _global_metrics = MetricsCollector()
    return _global_metrics

