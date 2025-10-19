"""
Input validation and sanitization for AI Market Insight Bot.
Prevents injection attacks and ensures data integrity.
"""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


class InputValidator:
    """
    Input validation and sanitization utilities.
    
    Provides:
    - String sanitization
    - Length validation
    - Format validation
    - SQL injection prevention
    - XSS prevention
    """
    
    # Maximum lengths for various fields
    MAX_GROUP_NAME_LENGTH = 255
    MAX_DESCRIPTION_LENGTH = 1000
    MAX_CURRENCY_LENGTH = 10
    MAX_INVOICE_ID_LENGTH = 100
    
    # Allowed characters patterns
    ALPHANUMERIC_PATTERN = re.compile(r'^[a-zA-Z0-9_\-\s]+$')
    CURRENCY_PATTERN = re.compile(r'^[a-z]{3,10}$')
    
    @staticmethod
    def sanitize_string(text: str, max_length: Optional[int] = None) -> str:
        """
        Sanitize a string by removing control characters.
        
        Args:
            text: Input string
            max_length: Maximum allowed length
            
        Returns:
            Sanitized string
        """
        if not text:
            return ""
        
        # Remove control characters (keep printable chars only)
        sanitized = ''.join(char for char in text if char.isprintable())
        
        # Remove leading/trailing whitespace
        sanitized = sanitized.strip()
        
        # Apply length limit
        if max_length and len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
            logger.debug(f"String truncated to {max_length} characters")
        
        return sanitized
    
    @staticmethod
    def sanitize_group_name(name: str) -> str:
        """
        Sanitize Telegram group name.
        
        Args:
            name: Group name
            
        Returns:
            Sanitized group name
        """
        return InputValidator.sanitize_string(
            name,
            max_length=InputValidator.MAX_GROUP_NAME_LENGTH
        )
    
    @staticmethod
    def sanitize_description(description: str) -> str:
        """
        Sanitize description text.
        
        Args:
            description: Description text
            
        Returns:
            Sanitized description
        """
        return InputValidator.sanitize_string(
            description,
            max_length=InputValidator.MAX_DESCRIPTION_LENGTH
        )
    
    @staticmethod
    def validate_currency(currency: str, allowed_currencies: list) -> bool:
        """
        Validate cryptocurrency code.
        
        Args:
            currency: Currency code (e.g., 'btc', 'eth')
            allowed_currencies: List of allowed currencies
            
        Returns:
            True if valid
        """
        if not currency:
            return False
        
        # Convert to lowercase
        currency = currency.lower()
        
        # Check format
        if not InputValidator.CURRENCY_PATTERN.match(currency):
            logger.warning(f"Invalid currency format: {currency}")
            return False
        
        # Check against whitelist
        if currency not in allowed_currencies:
            logger.warning(f"Currency not in whitelist: {currency}")
            return False
        
        return True
    
    @staticmethod
    def validate_group_id(group_id: int) -> bool:
        """
        Validate Telegram group ID.
        
        Args:
            group_id: Group ID
            
        Returns:
            True if valid
        """
        # Telegram group IDs are negative integers
        if not isinstance(group_id, int):
            logger.warning(f"Invalid group ID type: {type(group_id)}")
            return False
        
        if group_id >= 0:
            logger.warning(f"Invalid group ID (must be negative): {group_id}")
            return False
        
        # Telegram IDs are typically in range -1000000000000 to -1
        if group_id < -10000000000000:
            logger.warning(f"Group ID out of range: {group_id}")
            return False
        
        return True
    
    @staticmethod
    def validate_user_id(user_id: int) -> bool:
        """
        Validate Telegram user ID.
        
        Args:
            user_id: User ID
            
        Returns:
            True if valid
        """
        # Telegram user IDs are positive integers
        if not isinstance(user_id, int):
            logger.warning(f"Invalid user ID type: {type(user_id)}")
            return False
        
        if user_id <= 0:
            logger.warning(f"Invalid user ID (must be positive): {user_id}")
            return False
        
        # Telegram user IDs are typically in range 1 to 10000000000
        if user_id > 10000000000:
            logger.warning(f"User ID out of range: {user_id}")
            return False
        
        return True
    
    @staticmethod
    def validate_amount(amount: float, min_amount: float = 0.01, max_amount: float = 10000.0) -> bool:
        """
        Validate payment amount.
        
        Args:
            amount: Amount in USD
            min_amount: Minimum allowed amount
            max_amount: Maximum allowed amount
            
        Returns:
            True if valid
        """
        if not isinstance(amount, (int, float)):
            logger.warning(f"Invalid amount type: {type(amount)}")
            return False
        
        if amount < min_amount:
            logger.warning(f"Amount below minimum: {amount} < {min_amount}")
            return False
        
        if amount > max_amount:
            logger.warning(f"Amount above maximum: {amount} > {max_amount}")
            return False
        
        return True
    
    @staticmethod
    def sanitize_invoice_id(invoice_id: str) -> str:
        """
        Sanitize invoice ID.
        
        Args:
            invoice_id: Invoice ID
            
        Returns:
            Sanitized invoice ID
        """
        # Remove any non-alphanumeric characters except dash and underscore
        sanitized = re.sub(r'[^a-zA-Z0-9_\-]', '', str(invoice_id))
        
        # Apply length limit
        if len(sanitized) > InputValidator.MAX_INVOICE_ID_LENGTH:
            sanitized = sanitized[:InputValidator.MAX_INVOICE_ID_LENGTH]
        
        return sanitized
    
    @staticmethod
    def validate_webhook_payload(payload: dict, required_fields: list) -> bool:
        """
        Validate webhook payload structure.
        
        Args:
            payload: Webhook payload dictionary
            required_fields: List of required field names
            
        Returns:
            True if valid
        """
        if not isinstance(payload, dict):
            logger.warning("Webhook payload is not a dictionary")
            return False
        
        # Check required fields
        for field in required_fields:
            if field not in payload:
                logger.warning(f"Missing required field in webhook: {field}")
                return False
        
        return True
    
    @staticmethod
    def sanitize_html(text: str) -> str:
        """
        Sanitize HTML to prevent XSS attacks.
        
        Args:
            text: Input text
            
        Returns:
            Sanitized text with HTML entities escaped
        """
        if not text:
            return ""
        
        # Escape HTML special characters
        html_escape_table = {
            "&": "&amp;",
            '"': "&quot;",
            "'": "&#x27;",
            ">": "&gt;",
            "<": "&lt;",
        }
        
        return "".join(html_escape_table.get(c, c) for c in text)
    
    @staticmethod
    def validate_date_string(date_str: str) -> bool:
        """
        Validate ISO format date string.
        
        Args:
            date_str: Date string (ISO format)
            
        Returns:
            True if valid
        """
        if not date_str:
            return False
        
        # Check basic ISO format pattern
        iso_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}')
        
        if not iso_pattern.match(date_str):
            logger.warning(f"Invalid date format: {date_str}")
            return False
        
        return True


# Convenience functions for common validations

def sanitize_group_name(name: str) -> str:
    """Sanitize group name."""
    return InputValidator.sanitize_group_name(name)


def sanitize_description(description: str) -> str:
    """Sanitize description."""
    return InputValidator.sanitize_description(description)


def validate_currency(currency: str, allowed: list) -> bool:
    """Validate currency code."""
    return InputValidator.validate_currency(currency, allowed)


def validate_group_id(group_id: int) -> bool:
    """Validate group ID."""
    return InputValidator.validate_group_id(group_id)


def validate_user_id(user_id: int) -> bool:
    """Validate user ID."""
    return InputValidator.validate_user_id(user_id)


def validate_amount(amount: float) -> bool:
    """Validate payment amount."""
    return InputValidator.validate_amount(amount)

