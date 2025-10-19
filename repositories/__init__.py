"""
Repository layer for AI Market Insight Bot.
Provides data access abstraction and centralized database operations.
"""

from repositories.base_repository import IRepository, BaseRepository
from repositories.user_repository import UserRepository
from repositories.group_repository import GroupRepository
from repositories.news_repository import NewsRepository
from repositories.analytics_repository import AnalyticsRepository
from repositories.subscription_repository import SubscriptionRepository
from repositories.payment_repository import PaymentRepository

__all__ = [
    'IRepository',
    'BaseRepository',
    'UserRepository',
    'GroupRepository',
    'NewsRepository',
    'AnalyticsRepository',
    'SubscriptionRepository',
    'PaymentRepository'
]

