"""
Dependency Injection container for AI Market Insight Bot.
Provides centralized dependency management and lifecycle control.
"""

import logging
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass

# Import core components
from core.cache import Cache, init_cache
from core.metrics import MetricsCollector, get_metrics_collector
from core.circuit_breaker import CircuitBreaker

# Import repositories
from repositories.user_repository import UserRepository
from repositories.group_repository import GroupRepository
from repositories.news_repository import NewsRepository
from repositories.analytics_repository import AnalyticsRepository
from repositories.subscription_repository import SubscriptionRepository
from repositories.payment_repository import PaymentRepository

# Import existing components
from db_pool import get_pool, ConnectionPool
from news_fetcher import NewsFetcher
from ai_analyzer import AIAnalyzer
from rate_limiter import RateLimiter, ConcurrentPostingManager

logger = logging.getLogger(__name__)


@dataclass
class ServiceContainer:
    """Container for all application services and dependencies."""

    # Core infrastructure
    cache: Cache
    metrics: MetricsCollector
    db_pool: ConnectionPool

    # Repositories
    user_repo: UserRepository
    group_repo: GroupRepository
    news_repo: NewsRepository
    analytics_repo: AnalyticsRepository
    subscription_repo: SubscriptionRepository
    payment_repo: PaymentRepository

    # External services
    news_fetcher: NewsFetcher
    ai_analyzer: AIAnalyzer

    # Rate limiting
    rate_limiter: RateLimiter
    posting_manager: ConcurrentPostingManager

    # Circuit breakers
    gemini_circuit_breaker: CircuitBreaker
    news_api_circuit_breaker: CircuitBreaker


class DependencyContainer:
    """
    Dependency injection container.
    
    Manages lifecycle and provides access to all application dependencies.
    Implements singleton pattern for shared resources.
    """
    
    _instance: Optional['DependencyContainer'] = None
    _initialized: bool = False
    
    def __new__(cls):
        """Ensure singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize container (only once)."""
        if not self._initialized:
            self._services: Optional[ServiceContainer] = None
            self._factories: Dict[str, Callable] = {}
            DependencyContainer._initialized = True
            logger.info("Dependency container created")
    
    async def initialize(self) -> ServiceContainer:
        """
        Initialize all services and dependencies.
        
        Returns:
            ServiceContainer with all initialized services
        """
        if self._services is not None:
            logger.warning("Container already initialized")
            return self._services
        
        logger.info("Initializing dependency container...")
        
        # Initialize core infrastructure
        cache = await init_cache(default_ttl=300, max_size=1000)
        metrics = get_metrics_collector()
        db_pool = get_pool()
        
        # Initialize repositories
        user_repo = UserRepository(db_pool)
        group_repo = GroupRepository(db_pool)
        news_repo = NewsRepository(db_pool)
        analytics_repo = AnalyticsRepository(db_pool)
        subscription_repo = SubscriptionRepository(db_pool)
        payment_repo = PaymentRepository(db_pool)
        
        # Initialize external services
        news_fetcher = NewsFetcher()
        ai_analyzer = AIAnalyzer()
        
        # Initialize rate limiting
        rate_limiter = RateLimiter(calls_per_second=30)
        posting_manager = ConcurrentPostingManager(max_concurrent=5, calls_per_second=30)
        
        # Initialize circuit breakers
        gemini_circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60.0,
            name="gemini_api"
        )
        
        news_api_circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=30.0,
            name="news_api"
        )
        
        # Create service container
        self._services = ServiceContainer(
            cache=cache,
            metrics=metrics,
            db_pool=db_pool,
            user_repo=user_repo,
            group_repo=group_repo,
            news_repo=news_repo,
            analytics_repo=analytics_repo,
            subscription_repo=subscription_repo,
            payment_repo=payment_repo,
            news_fetcher=news_fetcher,
            ai_analyzer=ai_analyzer,
            rate_limiter=rate_limiter,
            posting_manager=posting_manager,
            gemini_circuit_breaker=gemini_circuit_breaker,
            news_api_circuit_breaker=news_api_circuit_breaker
        )
        
        logger.info("Dependency container initialized successfully")
        return self._services
    
    def get_services(self) -> ServiceContainer:
        """
        Get initialized service container.
        
        Returns:
            ServiceContainer
            
        Raises:
            RuntimeError: If container not initialized
        """
        if self._services is None:
            raise RuntimeError(
                "Container not initialized. Call initialize() first."
            )
        return self._services
    
    async def shutdown(self):
        """Shutdown all services and cleanup resources."""
        if self._services is None:
            return
        
        logger.info("Shutting down dependency container...")
        
        try:
            # Stop cache cleanup task
            await self._services.cache.stop_cleanup()
            await self._services.cache.clear()
            
            # Close database connections
            self._services.db_pool.close_all()
            
            logger.info("Dependency container shutdown complete")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}", exc_info=True)
        finally:
            self._services = None
    
    def register_factory(self, name: str, factory: Callable):
        """
        Register a factory function for lazy initialization.
        
        Args:
            name: Service name
            factory: Factory function that creates the service
        """
        self._factories[name] = factory
        logger.debug(f"Registered factory: {name}")
    
    def create(self, name: str) -> Any:
        """
        Create service using registered factory.
        
        Args:
            name: Service name
            
        Returns:
            Created service instance
            
        Raises:
            KeyError: If factory not registered
        """
        if name not in self._factories:
            raise KeyError(f"No factory registered for: {name}")
        
        return self._factories[name]()


# Global container instance
_container: Optional[DependencyContainer] = None


def get_container() -> DependencyContainer:
    """Get global dependency container instance."""
    global _container
    if _container is None:
        _container = DependencyContainer()
    return _container


async def init_container() -> ServiceContainer:
    """Initialize global dependency container."""
    container = get_container()
    return await container.initialize()


async def shutdown_container():
    """Shutdown global dependency container."""
    global _container
    if _container:
        await _container.shutdown()
        _container = None

