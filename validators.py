"""
Input validation and sanitization module for AI Market Insight Bot.
Provides security and data integrity checks.
"""

import re
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class InputValidator:
    """Validates and sanitizes user input."""
    
    # Regex patterns
    CHAT_ID_PATTERN = re.compile(r'^-?\d+$')
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_]{1,32}$')
    URL_PATTERN = re.compile(r'^https?://[^\s/$.?#].[^\s]*$', re.IGNORECASE)
    
    @staticmethod
    def validate_chat_id(chat_id: Any) -> bool:
        """Validate Telegram chat ID."""
        try:
            chat_id_str = str(chat_id)
            return bool(InputValidator.CHAT_ID_PATTERN.match(chat_id_str))
        except Exception as e:
            logger.warning(f"Chat ID validation failed: {e}")
            return False
    
    @staticmethod
    def validate_group_name(name: str, max_length: int = 255) -> bool:
        """Validate group name."""
        if not isinstance(name, str):
            return False
        
        if len(name) == 0 or len(name) > max_length:
            return False
        
        # Check for suspicious patterns
        if any(char in name for char in ['<', '>', '"', "'"]):
            return False
        
        return True
    
    @staticmethod
    def validate_trader_type(trader_type: str) -> bool:
        """Validate trader type."""
        valid_types = ["scalper", "day_trader", "swing_trader", "investor"]
        return trader_type.lower() in valid_types
    
    @staticmethod
    def validate_posting_hour(hour: int) -> bool:
        """Validate posting hour (0-23)."""
        try:
            hour_int = int(hour)
            return 0 <= hour_int <= 23
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_posting_minute(minute: int) -> bool:
        """Validate posting minute (0-59)."""
        try:
            minute_int = int(minute)
            return 0 <= minute_int <= 59
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format."""
        if not isinstance(url, str):
            return False
        
        return bool(InputValidator.URL_PATTERN.match(url))
    
    @staticmethod
    def validate_article_title(title: str, max_length: int = 500) -> bool:
        """Validate article title."""
        if not isinstance(title, str):
            return False
        
        if len(title) == 0 or len(title) > max_length:
            return False
        
        return True
    
    @staticmethod
    def validate_sentiment(sentiment: str) -> bool:
        """Validate sentiment value."""
        valid_sentiments = ["Bullish", "Bearish", "Neutral"]
        return sentiment in valid_sentiments

    @staticmethod
    def validate_text_input(text: str, max_length: int = 4000) -> bool:
        """
        Validate text input for security.
        Checks for SQL injection patterns and excessive length.
        """
        if not isinstance(text, str):
            return False

        if len(text) > max_length:
            return False

        # Check for SQL injection patterns
        sql_patterns = [
            r"(\bUNION\b.*\bSELECT\b)",
            r"(\bDROP\b.*\bTABLE\b)",
            r"(\bINSERT\b.*\bINTO\b)",
            r"(\bDELETE\b.*\bFROM\b)",
            r"(--)",
            r"(;.*\bDROP\b)",
        ]

        text_upper = text.upper()
        for pattern in sql_patterns:
            if re.search(pattern, text_upper, re.IGNORECASE):
                logger.warning(f"SQL injection pattern detected: {pattern}")
                return False

        return True


class InputSanitizer:
    """Sanitizes user input to prevent injection attacks."""
    
    @staticmethod
    def sanitize_text(text: str, max_length: int = 1000) -> str:
        """
        Sanitize text input.
        
        Args:
            text: Input text
            max_length: Maximum allowed length
        
        Returns:
            Sanitized text
        """
        if not isinstance(text, str):
            return ""
        
        # Truncate to max length
        text = text[:max_length]
        
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Remove control characters except newlines and tabs
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
        
        return text.strip()
    
    @staticmethod
    def sanitize_group_name(name: str) -> str:
        """Sanitize group name."""
        name = InputSanitizer.sanitize_text(name, max_length=255)
        
        # Remove HTML-like tags
        name = re.sub(r'<[^>]+>', '', name)
        
        return name
    
    @staticmethod
    def sanitize_url(url: str) -> str:
        """Sanitize URL."""
        url = InputSanitizer.sanitize_text(url, max_length=2048)
        
        # Remove potentially dangerous characters
        url = url.replace('\n', '').replace('\r', '')
        
        return url
    
    @staticmethod
    def sanitize_article_title(title: str) -> str:
        """Sanitize article title."""
        title = InputSanitizer.sanitize_text(title, max_length=500)
        
        # Remove HTML-like tags
        title = re.sub(r'<[^>]+>', '', title)
        
        return title
    
    @staticmethod
    def sanitize_html_message(message: str) -> str:
        """
        Sanitize message for HTML parsing.
        
        Args:
            message: Message to sanitize
        
        Returns:
            Sanitized message safe for HTML parsing
        """
        message = InputSanitizer.sanitize_text(message)
        
        # Escape HTML special characters
        message = message.replace('&', '&amp;')
        message = message.replace('<', '&lt;')
        message = message.replace('>', '&gt;')
        message = message.replace('"', '&quot;')
        message = message.replace("'", '&#39;')
        
        return message


class DataValidator:
    """Validates data integrity and consistency."""
    
    @staticmethod
    def validate_group_settings(settings: dict) -> bool:
        """Validate group settings dictionary."""
        required_fields = [
            'include_scalper', 'include_day_trader',
            'include_swing_trader', 'include_investor',
            'posting_hour', 'posting_minute'
        ]
        
        # Check all required fields exist
        if not all(field in settings for field in required_fields):
            return False
        
        # Validate boolean fields
        for field in ['include_scalper', 'include_day_trader', 'include_swing_trader', 'include_investor']:
            if not isinstance(settings[field], (bool, int)):
                return False
        
        # Validate time fields
        if not InputValidator.validate_posting_hour(settings['posting_hour']):
            return False
        
        if not InputValidator.validate_posting_minute(settings['posting_minute']):
            return False
        
        return True
    
    @staticmethod
    def validate_article_data(article: dict) -> bool:
        """Validate article data structure."""
        required_fields = ['title', 'description', 'url', 'source', 'publishedAt']
        
        if not all(field in article for field in required_fields):
            return False
        
        # Validate individual fields
        if not InputValidator.validate_article_title(article['title']):
            return False
        
        if not InputValidator.validate_url(article['url']):
            return False
        
        return True

