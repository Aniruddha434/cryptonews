"""
Authentication middleware for AI Market Insight Bot.
Provides admin authorization and permission checks.
"""

import logging
from typing import Callable, List
from functools import wraps
from telegram import Update, ChatMember
from telegram.ext import ContextTypes

from config import ADMIN_USER_IDS

logger = logging.getLogger(__name__)


class AuthMiddleware:
    """
    Authentication middleware for bot commands.
    
    Provides:
    - Admin authorization
    - Group admin checks
    - Permission validation
    """
    
    def __init__(self, admin_ids: List[int] = None):
        """
        Initialize auth middleware.
        
        Args:
            admin_ids: List of admin user IDs
        """
        self.admin_ids = admin_ids or ADMIN_USER_IDS
        logger.info(f"AuthMiddleware initialized with {len(self.admin_ids)} admins")
    
    def is_admin(self, user_id: int) -> bool:
        """
        Check if user is bot admin.
        
        Args:
            user_id: User ID
            
        Returns:
            True if admin
        """
        return user_id in self.admin_ids
    
    async def is_group_admin(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> bool:
        """
        Check if user is group admin.
        
        Args:
            update: Telegram update
            context: Bot context
            
        Returns:
            True if group admin
        """
        if not update.effective_chat or update.effective_chat.type == 'private':
            return False
        
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        try:
            member = await context.bot.get_chat_member(chat_id, user_id)
            return member.status in [
                ChatMember.ADMINISTRATOR,
                ChatMember.OWNER
            ]
        except Exception as e:
            logger.error(f"Error checking group admin status: {e}")
            return False
    
    async def check_admin_permission(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> bool:
        """
        Check if user has admin permission.
        
        Args:
            update: Telegram update
            context: Bot context
            
        Returns:
            True if authorized
        """
        user_id = update.effective_user.id
        
        # Check bot admin
        if self.is_admin(user_id):
            return True
        
        # Check group admin (if in group)
        if update.effective_chat and update.effective_chat.type != 'private':
            if await self.is_group_admin(update, context):
                return True
        
        return False
    
    async def require_admin(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> bool:
        """
        Require admin permission.
        
        Args:
            update: Telegram update
            context: Bot context
            
        Returns:
            True if authorized, False otherwise
        """
        if not await self.check_admin_permission(update, context):
            logger.warning(
                f"Unauthorized admin access attempt by user {update.effective_user.id}"
            )
            
            await update.message.reply_text(
                "⛔ This command requires admin privileges."
            )
            return False
        
        return True


# Global auth middleware instance
_auth_middleware: AuthMiddleware = None


def get_auth_middleware() -> AuthMiddleware:
    """Get global auth middleware instance."""
    global _auth_middleware
    if _auth_middleware is None:
        _auth_middleware = AuthMiddleware()
    return _auth_middleware


def require_admin(func: Callable) -> Callable:
    """
    Decorator for requiring admin permission.
    
    Usage:
        @require_admin
        async def handle_admin_command(update, context):
            # ... admin command logic ...
    """
    @wraps(func)
    async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        middleware = get_auth_middleware()
        
        # Check admin permission
        if not await middleware.require_admin(update, context):
            return  # Not authorized
        
        # Execute command
        return await func(self, update, context)
    
    return wrapper

