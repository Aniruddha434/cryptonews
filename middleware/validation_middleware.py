"""
Validation middleware for AI Market Insight Bot.
Provides input validation and sanitization.
"""

import logging
from typing import Callable
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes

from validators import InputValidator, InputSanitizer

logger = logging.getLogger(__name__)


class ValidationMiddleware:
    """
    Validation middleware for bot commands.
    
    Provides:
    - Input validation
    - Input sanitization
    - Security checks
    """
    
    def __init__(self):
        """Initialize validation middleware."""
        self.validator = InputValidator()
        self.sanitizer = InputSanitizer()
        logger.info("ValidationMiddleware initialized")
    
    async def validate_update(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> bool:
        """
        Validate incoming update.
        
        Args:
            update: Telegram update
            context: Bot context
            
        Returns:
            True if valid, False otherwise
        """
        # Validate user
        if update.effective_user:
            user_id = update.effective_user.id
            if not self.validator.validate_chat_id(user_id):
                logger.warning(f"Invalid user ID: {user_id}")
                return False
        
        # Validate chat
        if update.effective_chat:
            chat_id = update.effective_chat.id
            if not self.validator.validate_chat_id(chat_id):
                logger.warning(f"Invalid chat ID: {chat_id}")
                return False
        
        # Validate message text
        if update.message and update.message.text:
            text = update.message.text
            
            # Check for SQL injection patterns
            if not self.validator.validate_text_input(text):
                logger.warning(f"Suspicious input detected from user {update.effective_user.id}")
                await update.message.reply_text(
                    "⚠️ Invalid input detected. Please try again."
                )
                return False
        
        return True
    
    def sanitize_text(self, text: str) -> str:
        """
        Sanitize text input.
        
        Args:
            text: Input text
            
        Returns:
            Sanitized text
        """
        return self.sanitizer.sanitize_text(text)
    
    def sanitize_group_name(self, name: str) -> str:
        """
        Sanitize group name.
        
        Args:
            name: Group name
            
        Returns:
            Sanitized name
        """
        return self.sanitizer.sanitize_group_name(name)


# Global validation middleware instance
_validation_middleware: ValidationMiddleware = None


def get_validation_middleware() -> ValidationMiddleware:
    """Get global validation middleware instance."""
    global _validation_middleware
    if _validation_middleware is None:
        _validation_middleware = ValidationMiddleware()
    return _validation_middleware


def validate_input(func: Callable) -> Callable:
    """
    Decorator for validating bot command inputs.
    
    Usage:
        @validate_input
        async def handle_command(update, context):
            # ... command logic ...
    """
    @wraps(func)
    async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        middleware = get_validation_middleware()
        
        # Validate input
        if not await middleware.validate_update(update, context):
            return  # Invalid input
        
        # Execute command
        return await func(self, update, context)
    
    return wrapper

