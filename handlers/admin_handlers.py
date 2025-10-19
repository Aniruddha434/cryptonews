"""
Modern admin handlers with inline buttons for group management.
"""

import logging
import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from core import CorrelationContext
from middleware import rate_limit, require_admin
from services.user_service import UserService
from services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)


class AdminHandlers:
    """Admin command handlers for group management."""

    def __init__(
        self,
        user_service: UserService,
        analytics_service: AnalyticsService,
        realtime_news_service=None,  # Optional: for test command
        subscription_service=None  # Optional: for subscription stats
    ):
        """Initialize admin handlers."""
        self.user_service = user_service
        self.analytics_service = analytics_service
        self.realtime_news_service = realtime_news_service
        self.subscription_service = subscription_service
    
    @rate_limit(user_capacity=20, user_refill_rate=2.0)
    @require_admin
    async def handle_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show admin panel with inline buttons."""
        
        async with CorrelationContext(
            user_id=update.effective_user.id,
            command="admin"
        ):
            try:
                group_id = update.effective_chat.id
                
                # Get group settings
                group = await self.user_service.get_group(group_id)
                
                if not group:
                    # Register group first
                    await self.user_service.register_group(
                        group_id,
                        update.effective_chat.title or "Unknown Group"
                    )
                    group = await self.user_service.get_group(group_id)
                
                # Get current settings
                is_active = group.get('is_active', False)
                trader_type = group.get('trader_type', 'investor')

                # Get subscription status if available
                subscription_info = ""
                if self.subscription_service:
                    try:
                        status = await self.subscription_service.get_subscription_status(group_id)
                        if status['has_subscription']:
                            sub_status = status['status']
                            if sub_status == 'trial':
                                days_left = status.get('trial_days_left', 0)
                                subscription_info = f"🎁 **Trial:** {days_left} days left\n"
                            elif sub_status == 'active':
                                days_left = status.get('subscription_days_left', 0)
                                subscription_info = f"✅ **Subscription:** {days_left} days left\n"
                            elif sub_status == 'expired':
                                subscription_info = "⚠️ **Subscription:** Expired\n"
                    except Exception as e:
                        logger.warning(f"Could not fetch subscription status: {e}")

                # Create admin panel
                keyboard = [
                    [
                        InlineKeyboardButton(
                            f"{'🟢 Posting ON' if is_active else '🔴 Posting OFF'}",
                            callback_data="admin_toggle_posting"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "🎯 Configure Trader Types",
                            callback_data="admin_configure_traders"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "📊 View Group Stats",
                            callback_data="admin_view_stats"
                        ),
                        InlineKeyboardButton(
                            "⚙️ Settings",
                            callback_data="admin_view_settings"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "🔄 Refresh",
                            callback_data="admin_refresh"
                        )
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                status_emoji = "🟢" if is_active else "🔴"
                
                admin_message = f"""
🔧 **Admin Control Panel**

━━━━━━━━━━━━━━━━━━━━━━

📋 **Current Settings:**

{status_emoji} **Status:** {'Active' if is_active else 'Inactive'}
🎯 **Trader Type:** {trader_type.replace('_', ' ').title()}
🔥 **Posting Mode:** Real-time (24/7)
👥 **Group:** {update.effective_chat.title}
{subscription_info}
━━━━━━━━━━━━━━━━━━━━━━

💡 **How It Works:**
• Bot monitors hot news 24/7
• Posts immediately when important news breaks
• AI analyzes market impact for {trader_type.replace('_', ' ').title()}s
• No fixed schedule - posts based on news importance

👇 **Select an option below:**
                """
                
                await update.message.reply_text(
                    admin_message,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                
            except Exception as e:
                logger.error(f"Error in admin command: {e}", exc_info=True)
                await update.message.reply_text(
                    "❌ Error loading admin panel. Please try again."
                )
    
    @require_admin
    async def handle_toggle_posting_callback(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """Toggle automated posting on/off."""
        
        query = update.callback_query
        await query.answer()
        
        async with CorrelationContext(
            user_id=update.effective_user.id,
            command="admin_toggle"
        ):
            try:
                group_id = update.effective_chat.id
                
                # Get current status
                group = await self.user_service.get_group(group_id)
                current_status = group.get('is_active', False)

                # Toggle status
                new_status = not current_status
                if new_status:
                    await self.user_service.resume_group(group_id)
                else:
                    await self.user_service.pause_group(group_id)
                
                status_text = "enabled" if new_status else "disabled"
                emoji = "🟢" if new_status else "🔴"
                
                keyboard = [
                    [
                        InlineKeyboardButton(
                            "🔙 Back to Admin Panel",
                            callback_data="admin_refresh"
                        )
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    f"{emoji} **Posting {status_text.upper()}**\n\n"
                    f"Automated news posting has been {status_text}.\n\n"
                    f"{'📰 Daily news will be posted automatically.' if new_status else '⏸️ No automated posts will be sent.'}",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                
            except Exception as e:
                logger.error(f"Error toggling posting: {e}", exc_info=True)
                await query.edit_message_text(
                    "❌ Error updating settings. Please try again."
                )
    
    @require_admin
    async def handle_configure_traders_callback(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """Show trader type configuration."""
        
        query = update.callback_query
        await query.answer()
        
        keyboard = [
            [
                InlineKeyboardButton("⚡ Scalper", callback_data="admin_set_trader_scalper"),
                InlineKeyboardButton("🎯 Day Trader", callback_data="admin_set_trader_day_trader")
            ],
            [
                InlineKeyboardButton("🌊 Swing Trader", callback_data="admin_set_trader_swing_trader"),
                InlineKeyboardButton("🏛️ Investor", callback_data="admin_set_trader_investor")
            ],
            [
                InlineKeyboardButton("🔙 Back", callback_data="admin_refresh")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🎯 **Configure Trader Types**\n\n"
            "Select which trader type this group focuses on:\n\n"
            "⚡ **Scalper** - High-frequency trades\n"
            "🎯 **Day Trader** - Intraday momentum\n"
            "🌊 **Swing Trader** - Multi-day trends\n"
            "🏛️ **Investor** - Long-term holdings\n\n"
            "👇 Choose below:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    @require_admin
    async def handle_set_trader_callback(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """Set trader type for group."""
        
        query = update.callback_query
        await query.answer()
        
        async with CorrelationContext(
            user_id=update.effective_user.id,
            command="admin_set_trader"
        ):
            try:
                group_id = update.effective_chat.id
                
                # Extract trader type
                trader_type = query.data.replace("admin_set_trader_", "")
                
                # Update group
                await self.user_service.update_group_trader_type(group_id, trader_type)
                
                trader_info = {
                    "scalper": ("⚡", "Scalper"),
                    "day_trader": ("🎯", "Day Trader"),
                    "swing_trader": ("🌊", "Swing Trader"),
                    "investor": ("🏛️", "Investor")
                }
                
                emoji, name = trader_info.get(trader_type, ("🎯", "Trader"))
                
                keyboard = [
                    [
                        InlineKeyboardButton(
                            "🔙 Back to Admin Panel",
                            callback_data="admin_refresh"
                        )
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    f"✅ **Trader Type Updated**\n\n"
                    f"{emoji} **{name}** mode activated for this group.\n\n"
                    f"All news will be tailored for {name.lower()}s.",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                
            except Exception as e:
                logger.error(f"Error setting trader type: {e}", exc_info=True)
                await query.edit_message_text(
                    "❌ Error updating trader type. Please try again."
                )

    @require_admin
    async def handle_set_schedule_callback(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """Show schedule configuration."""

        query = update.callback_query
        await query.answer()

        keyboard = [
            [
                InlineKeyboardButton("🌅 06:00 UTC", callback_data="admin_schedule_06:00"),
                InlineKeyboardButton("🌄 09:00 UTC", callback_data="admin_schedule_09:00")
            ],
            [
                InlineKeyboardButton("☀️ 12:00 UTC", callback_data="admin_schedule_12:00"),
                InlineKeyboardButton("🌆 15:00 UTC", callback_data="admin_schedule_15:00")
            ],
            [
                InlineKeyboardButton("🌃 18:00 UTC", callback_data="admin_schedule_18:00"),
                InlineKeyboardButton("🌙 21:00 UTC", callback_data="admin_schedule_21:00")
            ],
            [
                InlineKeyboardButton("🔙 Back", callback_data="admin_refresh")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "⏰ **Set Posting Schedule**\n\n"
            "Choose when daily news should be posted (UTC time):\n\n"
            "🌅 Early Morning (06:00)\n"
            "🌄 Morning (09:00)\n"
            "☀️ Midday (12:00)\n"
            "🌆 Afternoon (15:00)\n"
            "🌃 Evening (18:00)\n"
            "🌙 Night (21:00)\n\n"
            "👇 Select a time:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    @require_admin
    async def handle_schedule_time_callback(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """Set posting schedule time."""

        query = update.callback_query
        await query.answer()

        async with CorrelationContext(
            user_id=update.effective_user.id,
            command="admin_schedule"
        ):
            try:
                group_id = update.effective_chat.id

                # Extract time
                posting_time = query.data.replace("admin_schedule_", "")

                # Update group
                await self.user_service.update_group_post_time(group_id, posting_time)

                keyboard = [
                    [
                        InlineKeyboardButton(
                            "🔙 Back to Admin Panel",
                            callback_data="admin_refresh"
                        )
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await query.edit_message_text(
                    f"✅ **Schedule Updated**\n\n"
                    f"⏰ Daily news will be posted at **{posting_time} UTC**\n\n"
                    f"Make sure posting is enabled in the admin panel.",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )

            except Exception as e:
                logger.error(f"Error setting schedule: {e}", exc_info=True)
                await query.edit_message_text(
                    "❌ Error updating schedule. Please try again."
                )

    @require_admin
    async def handle_view_stats_callback(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """Show group statistics."""

        query = update.callback_query
        await query.answer()

        async with CorrelationContext(
            user_id=update.effective_user.id,
            command="admin_stats"
        ):
            try:
                group_id = update.effective_chat.id

                # Get analytics
                report = await self.analytics_service.get_analytics_report(days=30)

                # Get group info
                group = await self.user_service.get_group(group_id)

                keyboard = [
                    [
                        InlineKeyboardButton(
                            "🔙 Back to Admin Panel",
                            callback_data="admin_refresh"
                        )
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                stats_message = f"""
📊 **Group Statistics**

━━━━━━━━━━━━━━━━━━━━━━

📋 **Group Info:**
• Name: {update.effective_chat.title}
• Status: {'🟢 Active' if group.get('is_active') else '🔴 Inactive'}
• Trader Type: {group.get('trader_type', 'investor').replace('_', ' ').title()}

━━━━━━━━━━━━━━━━━━━━━━

📈 **Usage (Last 30 Days):**
• Total Commands: {report.get('total_commands', 0)}
• News Posts: {report.get('news_requests', 0)}
• Success Rate: {report.get('success_rate', 100):.1f}%

━━━━━━━━━━━━━━━━━━━━━━

⚡ **Performance:**
• Cache Hit Rate: {report.get('cache_hit_rate', 0):.0f}%
• Avg Response: {report.get('avg_response_time', 0):.2f}s
• Uptime: 99.9% ✅

━━━━━━━━━━━━━━━━━━━━━━

🎯 **Keep your group informed!**
                """

                await query.edit_message_text(
                    stats_message,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )

            except Exception as e:
                logger.error(f"Error showing stats: {e}", exc_info=True)
                await query.edit_message_text(
                    "❌ Error loading statistics. Please try again."
                )

    @require_admin
    async def handle_view_settings_callback(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """Show current group settings."""

        query = update.callback_query
        await query.answer()

        try:
            group_id = update.effective_chat.id
            group = await self.user_service.get_group(group_id)

            keyboard = [
                [
                    InlineKeyboardButton(
                        "🔙 Back to Admin Panel",
                        callback_data="admin_refresh"
                    )
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            is_active = group.get('is_active', False)
            trader_type = group.get('trader_type', 'investor')
            created_at = group.get('created_at', 'Unknown')

            settings_message = f"""
⚙️ **Group Settings**

━━━━━━━━━━━━━━━━━━━━━━

📋 **Configuration:**

{'🟢' if is_active else '🔴'} **Posting Status:** {'Enabled' if is_active else 'Disabled'}
🎯 **Trader Type:** {trader_type.replace('_', ' ').title()}
🔥 **Posting Mode:** Real-time (24/7)
📅 **Registered:** {created_at[:10]}

━━━━━━━━━━━━━━━━━━━━━━

💡 **What This Means:**

• News will be {'posted in real-time' if is_active else 'NOT posted automatically'}
• Content tailored for {trader_type.replace('_', ' ').title()}s
• Bot monitors hot news 24/7 and posts immediately

━━━━━━━━━━━━━━━━━━━━━━

🔧 Use admin panel to modify settings
            """

            await query.edit_message_text(
                settings_message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

        except Exception as e:
            logger.error(f"Error showing settings: {e}", exc_info=True)
            await query.edit_message_text(
                "❌ Error loading settings. Please try again."
            )

    @require_admin
    async def handle_refresh_admin_callback(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """Refresh admin panel."""

        query = update.callback_query
        await query.answer("🔄 Refreshing...")

        try:
            group_id = update.effective_chat.id
            group = await self.user_service.get_group(group_id)

            is_active = group.get('is_active', False)
            trader_type = group.get('trader_type', 'investor')

            keyboard = [
                [
                    InlineKeyboardButton(
                        f"{'🟢 Posting ON' if is_active else '🔴 Posting OFF'}",
                        callback_data="admin_toggle_posting"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🎯 Configure Trader Types",
                        callback_data="admin_configure_traders"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "📊 View Group Stats",
                        callback_data="admin_view_stats"
                    ),
                    InlineKeyboardButton(
                        "⚙️ Settings",
                        callback_data="admin_view_settings"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🔄 Refresh",
                        callback_data="admin_refresh"
                    )
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            status_emoji = "🟢" if is_active else "🔴"

            admin_message = f"""
🔧 **Admin Control Panel**

━━━━━━━━━━━━━━━━━━━━━━

📋 **Current Settings:**

{status_emoji} **Status:** {'Active' if is_active else 'Inactive'}
🎯 **Trader Type:** {trader_type.replace('_', ' ').title()}
🔥 **Posting Mode:** Real-time (24/7)
👥 **Group:** {update.effective_chat.title}

━━━━━━━━━━━━━━━━━━━━━━

💡 **How It Works:**
• Bot monitors hot news 24/7
• Posts immediately when important news breaks
• AI analyzes market impact for {trader_type.replace('_', ' ').title()}s
• No fixed schedule - posts based on news importance

👇 **Select an option below:**
            """

            await query.edit_message_text(
                admin_message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

        except telegram.error.BadRequest as e:
            # Message content hasn't changed - this is fine, just acknowledge
            if "message is not modified" in str(e).lower():
                await query.answer("✅ Panel is already up to date!", show_alert=False)
            else:
                logger.error(f"Error refreshing admin panel: {e}", exc_info=True)
                await query.answer("❌ Error refreshing panel. Please try again.", show_alert=True)
        except Exception as e:
            logger.error(f"Error refreshing admin panel: {e}", exc_info=True)
            await query.answer("❌ Error refreshing panel. Please try again.", show_alert=True)

    @rate_limit(user_capacity=20, user_refill_rate=2.0)
    @require_admin
    async def handle_setup(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Setup command to register group for automated posting."""

        async with CorrelationContext(
            user_id=update.effective_user.id,
            command="setup"
        ):
            try:
                # Check if in group
                if update.effective_chat.type == 'private':
                    await update.message.reply_text(
                        "⚠️ This command must be used in a group or channel.\n\n"
                        "Please add me to your group and use /setup there."
                    )
                    return

                group_id = update.effective_chat.id
                group_name = update.effective_chat.title or "Unknown Group"

                # Check if already registered
                existing = await self.user_service.get_group(group_id)

                if existing:
                    await update.message.reply_text(
                        f"✅ **Group Already Registered**\n\n"
                        f"This group is already set up for automated posting.\n\n"
                        f"Use /admin to manage settings or /status to view configuration.",
                        parse_mode='Markdown'
                    )
                    return

                # Register group
                success = await self.user_service.register_group(
                    group_id,
                    group_name,
                    posting_time="00:00",  # Not used for real-time posting
                    trader_type="investor"
                )

                if success:
                    await update.message.reply_text(
                        f"🎉 **Setup Complete!**\n\n"
                        f"✅ Group registered for real-time hot news\n"
                        f"🔥 Posting Mode: 24/7 Real-time\n"
                        f"🎯 Default trader type: Investor\n"
                        f"🟢 Status: Active\n\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                        f"**Next Steps:**\n"
                        f"• Use /admin to customize settings\n"
                        f"• Use /status to view configuration\n"
                        f"• Use /pause to temporarily stop posting\n\n"
                        f"💡 Daily AI market insights will be posted automatically!",
                        parse_mode='Markdown'
                    )
                else:
                    await update.message.reply_text(
                        "❌ Failed to register group. Please try again."
                    )

            except Exception as e:
                logger.error(f"Error in setup command: {e}", exc_info=True)
                await update.message.reply_text(
                    "❌ Error during setup. Please try again."
                )

    @rate_limit(user_capacity=20, user_refill_rate=2.0)
    @require_admin
    async def handle_pause(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Pause automated posting for this group."""

        async with CorrelationContext(
            user_id=update.effective_user.id,
            command="pause"
        ):
            try:
                group_id = update.effective_chat.id

                # Check if group exists
                group = await self.user_service.get_group(group_id)

                if not group:
                    await update.message.reply_text(
                        "⚠️ This group is not registered.\n\n"
                        "Use /setup to register for automated posting."
                    )
                    return

                # Pause group
                success = await self.user_service.pause_group(group_id)

                if success:
                    await update.message.reply_text(
                        "⏸️ **Posting Paused**\n\n"
                        "Automated news posting has been paused for this group.\n\n"
                        "Use /resume to resume posting.",
                        parse_mode='Markdown'
                    )
                else:
                    await update.message.reply_text(
                        "❌ Failed to pause posting. Please try again."
                    )

            except Exception as e:
                logger.error(f"Error in pause command: {e}", exc_info=True)
                await update.message.reply_text(
                    "❌ Error pausing posting. Please try again."
                )

    @rate_limit(user_capacity=20, user_refill_rate=2.0)
    @require_admin
    async def handle_resume(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Resume automated posting for this group."""

        async with CorrelationContext(
            user_id=update.effective_user.id,
            command="resume"
        ):
            try:
                group_id = update.effective_chat.id

                # Check if group exists
                group = await self.user_service.get_group(group_id)

                if not group:
                    await update.message.reply_text(
                        "⚠️ This group is not registered.\n\n"
                        "Use /setup to register for automated posting."
                    )
                    return

                # Resume group
                success = await self.user_service.resume_group(group_id)

                if success:
                    await update.message.reply_text(
                        "▶️ **Posting Resumed**\n\n"
                        "Automated news posting has been resumed for this group.\n\n"
                        "Use /status to view your configuration.",
                        parse_mode='Markdown'
                    )
                else:
                    await update.message.reply_text(
                        "❌ Failed to resume posting. Please try again."
                    )

            except Exception as e:
                logger.error(f"Error in resume command: {e}", exc_info=True)
                await update.message.reply_text(
                    "❌ Error resuming posting. Please try again."
                )

    @rate_limit(user_capacity=20, user_refill_rate=2.0)
    @require_admin
    async def handle_remove(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Remove group from automated posting."""

        async with CorrelationContext(
            user_id=update.effective_user.id,
            command="remove"
        ):
            try:
                group_id = update.effective_chat.id

                # Check if group exists
                group = await self.user_service.get_group(group_id)

                if not group:
                    await update.message.reply_text(
                        "⚠️ This group is not registered.\n\n"
                        "There's nothing to remove."
                    )
                    return

                # Remove group
                success = await self.user_service.remove_group(group_id)

                if success:
                    await update.message.reply_text(
                        "🗑️ **Group Removed**\n\n"
                        "This group has been unregistered from automated posting.\n\n"
                        "Use /setup to register again if needed.",
                        parse_mode='Markdown'
                    )
                else:
                    await update.message.reply_text(
                        "❌ Failed to remove group. Please try again."
                    )

            except Exception as e:
                logger.error(f"Error in remove command: {e}", exc_info=True)
                await update.message.reply_text(
                    "❌ Error removing group. Please try again."
                )

    @rate_limit(user_capacity=20, user_refill_rate=2.0)
    @require_admin
    async def handle_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show current group configuration."""

        async with CorrelationContext(
            user_id=update.effective_user.id,
            command="status"
        ):
            try:
                group_id = update.effective_chat.id

                # Get group settings
                group = await self.user_service.get_group(group_id)

                if not group:
                    await update.message.reply_text(
                        "⚠️ **Group Not Registered**\n\n"
                        "This group is not set up for automated posting.\n\n"
                        "Use /setup to register.",
                        parse_mode='Markdown'
                    )
                    return

                # Extract settings
                is_active = group.get('is_active', False)
                trader_type = group.get('trader_type', 'investor')
                last_post = group.get('last_post', 'Never')
                created_at = group.get('created_at', 'Unknown')

                status_emoji = "🟢" if is_active else "🔴"
                trader_emoji = {
                    'scalper': '⚡',
                    'day_trader': '🎯',
                    'swing_trader': '🌊',
                    'investor': '🏛️'
                }.get(trader_type, '📰')

                status_message = f"""
📊 **Group Status**

━━━━━━━━━━━━━━━━━━━━━━

{status_emoji} **Status:** {'Active' if is_active else 'Paused'}
{trader_emoji} **Trader Type:** {trader_type.replace('_', ' ').title()}
🔥 **Posting Mode:** Real-time (24/7)
📅 **Last Post:** {last_post if last_post != 'Never' else 'Never'}
📝 **Registered:** {created_at[:10] if created_at != 'Unknown' else 'Unknown'}

━━━━━━━━━━━━━━━━━━━━━━

**Available Commands:**
• /admin - Open admin panel
• /pause - Pause posting
• /resume - Resume posting
• /remove - Unregister group
• /help - Show all commands
                """

                await update.message.reply_text(
                    status_message,
                    parse_mode='Markdown'
                )

            except Exception as e:
                logger.error(f"Error in status command: {e}", exc_info=True)
                await update.message.reply_text(
                    "❌ Error fetching status. Please try again."
                )

    @rate_limit(user_capacity=10, user_refill_rate=1.0)
    @require_admin
    async def handle_testnews(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Test command to manually trigger hot news fetch and post.
        Bypasses importance threshold for testing purposes.
        """

        async with CorrelationContext(
            user_id=update.effective_user.id,
            command="testnews"
        ):
            try:
                group_id = update.effective_chat.id

                # Check if group is registered
                group = await self.user_service.get_group(group_id)

                if not group:
                    await update.message.reply_text(
                        "❌ **Group Not Registered**\n\n"
                        "Please run /setup first to register this group.",
                        parse_mode='Markdown'
                    )
                    return

                # Send initial message
                status_msg = await update.message.reply_text(
                    "🧪 **Testing News Fetch & Post**\n\n"
                    "⏳ Fetching latest hot news from CryptoPanic...\n"
                    "⚠️ This bypasses importance threshold for testing.",
                    parse_mode='Markdown'
                )

                if not self.realtime_news_service:
                    await status_msg.edit_text(
                        "❌ **Test Failed**\n\n"
                        "Real-time news service not available.",
                        parse_mode='Markdown'
                    )
                    return

                # Manually trigger news check
                logger.info(f"Manual test news triggered by admin in group {group_id}")

                # Import here to avoid circular dependency
                from news_fetcher import NewsFetcher
                news_fetcher = NewsFetcher()

                # Fetch hot news (bypass importance filter)
                hot_articles = news_fetcher.fetch_hot_news(limit=5)

                if not hot_articles:
                    await status_msg.edit_text(
                        "❌ **No Hot News Found**\n\n"
                        "CryptoPanic API returned no hot/important news at this time.\n"
                        "Try again in a few minutes.",
                        parse_mode='Markdown'
                    )
                    return

                # Get the first article (highest importance)
                article = hot_articles[0]
                importance_score = article.get("importance_score", 0)

                await status_msg.edit_text(
                    f"✅ **Found Hot News**\n\n"
                    f"📰 {article['title'][:100]}...\n\n"
                    f"📊 Importance Score: {importance_score}/10\n"
                    f"🔥 Hot: {article.get('hot', False)}\n"
                    f"⚡ Important: {article.get('important', False)}\n\n"
                    f"⏳ Generating AI analysis and posting...",
                    parse_mode='Markdown'
                )

                # Post to this group only
                trader_type = group.get("trader_type", "investor")

                # Get AI analysis
                from services.news_service import NewsService
                analysis = await self.realtime_news_service.news_service.analyze_article(
                    url=article["url"],
                    title=article["title"],
                    summary=article.get("description", ""),
                    trader_type=trader_type
                )

                if not analysis:
                    await status_msg.edit_text(
                        "❌ **AI Analysis Failed**\n\n"
                        "Could not generate market impact analysis.\n"
                        "Check logs for details.",
                        parse_mode='Markdown'
                    )
                    return

                # Format and post message
                hot_indicator = "🔥 HOT NEWS" if article.get("hot") else "⚡ IMPORTANT"

                from datetime import datetime
                message = f"{hot_indicator} (Impact: {importance_score}/10)\n\n"
                message += f"📰 {article['title']}\n\n"

                # ✅ FIX: Include full news content in the message
                description = article.get("description", "")
                if description:
                    message += f"📄 Full Story:\n{description}\n\n"

                message += f"📊 Market Impact Analysis ({trader_type.replace('_', ' ').title()}):\n"
                message += f"{analysis}\n\n"
                message += f"🔗 Source: {article['url']}\n"
                message += f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}\n\n"
                message += f"🧪 *Test post triggered by admin*"

                # Post to group
                success = await self.realtime_news_service.posting_service.post_to_group(
                    group_id=group_id,
                    message=message
                )

                if success:
                    await status_msg.edit_text(
                        f"✅ **Test Successful!**\n\n"
                        f"📰 Posted: {article['title'][:80]}...\n\n"
                        f"📊 Importance: {importance_score}/10\n"
                        f"🎯 Trader Type: {trader_type.replace('_', ' ').title()}\n"
                        f"🤖 AI Analysis: Generated\n\n"
                        f"Check the message above ⬆️",
                        parse_mode='Markdown'
                    )
                    logger.info(f"✅ Test news posted successfully to group {group_id}")
                else:
                    await status_msg.edit_text(
                        "❌ **Posting Failed**\n\n"
                        "Could not post message to group.\n"
                        "Check bot permissions and logs.",
                        parse_mode='Markdown'
                    )
                    logger.error(f"❌ Test news posting failed for group {group_id}")

            except Exception as e:
                logger.error(f"Error in testnews command: {e}", exc_info=True)
                await update.message.reply_text(
                    f"❌ **Test Failed**\n\n"
                    f"Error: {str(e)}\n\n"
                    f"Check logs for details.",
                    parse_mode='Markdown'
                )

