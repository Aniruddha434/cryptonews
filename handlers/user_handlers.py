"""
Modern user handlers with inline buttons and enterprise features.
"""

import logging
from typing import Optional
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from core import CorrelationContext
from middleware import rate_limit, validate_input
from services.user_service import UserService
from services.news_service import NewsService
from services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)


class UserHandlers:
    """Modern user command handlers with inline buttons."""

    def __init__(
        self,
        user_service: UserService,
        news_service: NewsService,
        analytics_service: AnalyticsService,
        subscription_service=None,
        payment_service=None
    ):
        """Initialize handlers with services."""
        self.user_service = user_service
        self.news_service = news_service
        self.analytics_service = analytics_service
        self.subscription_service = subscription_service
        self.payment_service = payment_service

    @rate_limit(user_capacity=10, user_refill_rate=1.0)
    @validate_input
    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command - Professional onboarding flow."""

        async with CorrelationContext(
            user_id=update.effective_user.id,
            command="start"
        ):
            try:
                # Check if in private chat or group
                if update.effective_chat.type == 'private':
                    # Private chat - show professional welcome banner
                    welcome_message = """
🚀 **Welcome to AI Crypto News Bot!**

━━━━━━━━━━━━━━━━━━━━━━

Your **24/7 Crypto Intelligence Partner** for Telegram Groups

🔥 **Real-time hot news** delivered instantly
🤖 **AI-powered analysis** by Google Gemini
📊 **Multi-source aggregation** from top crypto platforms
🎯 **Trader-specific insights** tailored to your strategy

━━━━━━━━━━━━━━━━━━━━━━

**Trusted by crypto communities worldwide** to stay ahead of market-moving news.

Ready to supercharge your Telegram group with instant crypto intelligence?
                    """

                    keyboard = [
                        [
                            InlineKeyboardButton(
                                "🚀 Get Started",
                                callback_data="onboarding_step_1"
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                "📺 Add My Channel",
                                callback_data="show_channel_setup"
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                "⚡ Skip to Setup Guide",
                                callback_data="show_setup_guide"
                            )
                        ]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)

                    await update.message.reply_text(
                        welcome_message,
                        reply_markup=reply_markup,
                        parse_mode='Markdown'
                    )
                else:
                    # In group - suggest using /setup
                    await update.message.reply_text(
                        "👋 **Hello!**\n\n"
                        "I'm the AI Crypto News Bot. I deliver real-time crypto news with AI analysis to your group.\n\n"
                        "**To get started:**\n"
                        "• Use /setup to register this group\n"
                        "• Use /help to see all commands\n\n"
                        "Note: Only group admins can configure settings.",
                        parse_mode='Markdown'
                    )

                # Log analytics
                await self.analytics_service.log_command(
                    update.effective_user.id,
                    "start",
                    success=True
                )

            except Exception as e:
                logger.error(f"Error in start command: {e}", exc_info=True)
                await update.message.reply_text(
                    "❌ An error occurred. Please try again later."
                )

    @rate_limit(user_capacity=10, user_refill_rate=1.0)
    async def handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command - Show all available commands."""

        async with CorrelationContext(
            user_id=update.effective_user.id,
            command="help"
        ):
            try:
                help_message = """
📚 **AI Market Insight Bot - Help**

━━━━━━━━━━━━━━━━━━━━━━

**🔧 Group Setup Commands:**

/setup - Register your group for automated posting
   _Must be used in a group by an admin_

/admin - Open the admin control panel
   _Configure all settings with buttons_

/status - View current group configuration
   _See posting schedule, trader type, status_

━━━━━━━━━━━━━━━━━━━━━━

**📺 Channel Setup Commands (Private Chat Only):**

/addchannel - Step-by-step channel setup guide
   _Get instructions for adding your channel_

/registerchannel <id> <name> - Register a channel
   _Example: /registerchannel -1001234567890 My Channel_

/mychannels - View all your channels
   _See status of all registered channels_

/channelstatus <id> - Check channel status
   _View subscription and posting status_

/renewchannel <id> - Renew channel subscription
   _Generate payment invoice for channel renewal_

━━━━━━━━━━━━━━━━━━━━━━

**⚙️ Group Management Commands:**

/pause - Pause automated posting
   _Temporarily stop daily posts_

/resume - Resume automated posting
   _Restart daily posts_

/remove - Unregister group completely
   _Remove all data for this group_

━━━━━━━━━━━━━━━━━━━━━━

**💳 Subscription Commands:**

/subscription - View subscription status
   _Check trial or subscription details_

/renew - Renew subscription
   _Generate payment invoice for renewal_

━━━━━━━━━━━━━━━━━━━━━━

**ℹ️ Information Commands:**

/help - Show this help message
/start - Show welcome message

━━━━━━━━━━━━━━━━━━━━━━

**📋 How It Works:**

**For Groups:**
1. Add bot to your group as admin
2. Use /setup to register
3. Bot posts AI news automatically
4. Customize with /admin panel

**For Channels:**
1. Add bot to channel as admin (Post Messages permission)
2. Message me in private chat
3. Use /registerchannel to add your channel
4. Bot posts automatically 24/7

━━━━━━━━━━━━━━━━━━━━━━

💡 **Need Help?**
• Group commands require admin permissions
• Channel commands work in private chat only
                """

                await update.message.reply_text(
                    help_message,
                    parse_mode='Markdown'
                )

            except Exception as e:
                logger.error(f"Error in help command: {e}", exc_info=True)
                await update.message.reply_text(
                    "❌ Error showing help. Please try again."
                )
                await self.analytics_service.log_command(
                    update.effective_user.id,
                    "start",
                    success=False,
                    error_message=str(e)
                )

    @rate_limit(user_capacity=10, user_refill_rate=1.0)
    async def handle_trader_type_callback(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle trader type selection from inline buttons."""

        query = update.callback_query
        await query.answer()

        async with CorrelationContext(
            user_id=update.effective_user.id,
            command="set_trader_type"
        ):
            try:
                # Extract trader type from callback data
                trader_type = query.data.replace("trader_", "")

                # Update user
                await self.user_service.update_trader_type(
                    update.effective_user.id,
                    trader_type
                )

                # Trader type emojis and descriptions
                trader_info = {
                    "scalper": ("⚡", "Scalper", "High-frequency trading"),
                    "day_trader": ("🎯", "Day Trader", "Intraday momentum"),
                    "swing_trader": ("🌊", "Swing Trader", "Multi-day trends"),
                    "investor": ("🏛️", "Investor", "Long-term fundamentals")
                }

                emoji, name, desc = trader_info.get(trader_type, ("🎯", "Trader", "Trading"))

                # Create new keyboard
                keyboard = [
                    [
                        InlineKeyboardButton("📰 Get Latest News", callback_data="get_news")
                    ],
                    [
                        InlineKeyboardButton("🔄 Change Style", callback_data="change_trader_type"),
                        InlineKeyboardButton("📊 View Stats", callback_data="view_stats")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                success_message = f"""
✅ **Profile Updated Successfully!**

{emoji} **{name} Mode Activated**

━━━━━━━━━━━━━━━━━━━━━━

📋 **Your Settings:**
• Trading Style: {name}
• Focus: {desc}
• AI Analysis: Personalized
• Status: Active ✅

━━━━━━━━━━━━━━━━━━━━━━

🎯 **What's Next?**
• Get latest market insights
• View your statistics
• Change trading style anytime

👇 **Choose an action below:**
                """

                await query.edit_message_text(
                    success_message,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )

                # Log analytics
                await self.analytics_service.log_command(
                    update.effective_user.id,
                    "set_trader_type",
                    success=True
                )

            except Exception as e:
                logger.error(f"Error setting trader type: {e}", exc_info=True)
                await query.edit_message_text(
                    "❌ Error updating profile. Please try again."
                )

    @rate_limit(user_capacity=5, user_refill_rate=0.5)
    async def handle_news_callback(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle news request from inline button."""

        query = update.callback_query
        await query.answer("🔄 Fetching latest news...")

        async with CorrelationContext(
            user_id=update.effective_user.id,
            command="news"
        ):
            try:
                # Get user
                user = await self.user_service.get_user(update.effective_user.id)
                trader_type = user.get('trader_type', 'investor') if user else 'investor'

                # Show loading message
                loading_msg = await query.message.reply_text(
                    "🔄 **Analyzing latest market news...**\n\n"
                    "⏳ This may take a moment...",
                    parse_mode='Markdown'
                )

                # Get news with AI analysis (cached)
                articles = await self.news_service.get_trader_specific_news(
                    trader_type=trader_type,
                    limit=3
                )

                # Delete loading message
                await loading_msg.delete()

                if articles:
                    # Send each article
                    for i, article in enumerate(articles, 1):
                        keyboard = [
                            [
                                InlineKeyboardButton(
                                    "🔗 Read Full Article",
                                    url=article.get('url', '#')
                                )
                            ],
                            [
                                InlineKeyboardButton(
                                    "📰 More News",
                                    callback_data="get_news"
                                ),
                                InlineKeyboardButton(
                                    "🏠 Main Menu",
                                    callback_data="main_menu"
                                )
                            ]
                        ]
                        reply_markup = InlineKeyboardMarkup(keyboard)

                        message = f"""
📰 **Article {i}/{len(articles)}**

━━━━━━━━━━━━━━━━━━━━━━

{article.get('analysis', 'No analysis available')}

━━━━━━━━━━━━━━━━━━━━━━

🤖 _AI Analysis for {trader_type.replace('_', ' ').title()}s_
                        """

                        await query.message.reply_text(
                            message,
                            reply_markup=reply_markup,
                            parse_mode='Markdown'
                        )
                else:
                    keyboard = [
                        [
                            InlineKeyboardButton("🔄 Try Again", callback_data="get_news"),
                            InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
                        ]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)

                    await query.message.reply_text(
                        "⚠️ **No news available at the moment.**\n\n"
                        "Please try again in a few minutes.",
                        reply_markup=reply_markup,
                        parse_mode='Markdown'
                    )

                # Log analytics
                await self.analytics_service.log_command(
                    update.effective_user.id,
                    "news",
                    success=True
                )

            except Exception as e:
                logger.error(f"Error fetching news: {e}", exc_info=True)

                keyboard = [
                    [
                        InlineKeyboardButton("🔄 Try Again", callback_data="get_news"),
                        InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await query.message.reply_text(
                    "❌ **Error fetching news.**\n\n"
                    "Our AI service is temporarily unavailable. Please try again.",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )

                await self.analytics_service.log_command(
                    update.effective_user.id,
                    "news",
                    success=False,
                    error_message=str(e)
                )

    async def handle_main_menu_callback(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """Return to main menu."""

        query = update.callback_query
        await query.answer()

        # Recreate main menu
        keyboard = [
            [
                InlineKeyboardButton("⚡ Scalper", callback_data="trader_scalper"),
                InlineKeyboardButton("🎯 Day Trader", callback_data="trader_day_trader")
            ],
            [
                InlineKeyboardButton("🌊 Swing Trader", callback_data="trader_swing_trader"),
                InlineKeyboardButton("🏛️ Investor", callback_data="trader_investor")
            ],
            [
                InlineKeyboardButton("📰 Get Latest News", callback_data="get_news")
            ],
            [
                InlineKeyboardButton("📊 View Stats", callback_data="view_stats"),
                InlineKeyboardButton("❓ Help", callback_data="show_help")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "🏠 **Main Menu**\n\n"
            "Choose an option below:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def handle_help_callback(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """Show help information."""

        query = update.callback_query
        await query.answer()

        keyboard = [
            [
                InlineKeyboardButton("📰 Get News", callback_data="get_news"),
                InlineKeyboardButton("🔄 Change Style", callback_data="change_trader_type")
            ],
            [
                InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        help_message = """
📚 **Help & Commands**

━━━━━━━━━━━━━━━━━━━━━━

🎯 **Trading Styles:**

⚡ **Scalper**
• Timeframe: 1-5 minutes
• Focus: High volatility, quick profits
• Best for: Active traders

🎯 **Day Trader**
• Timeframe: Minutes to hours
• Focus: Intraday momentum
• Best for: Technical analysts

🌊 **Swing Trader**
• Timeframe: 2-10 days
• Focus: Trend following
• Best for: Pattern traders

🏛️ **Investor**
• Timeframe: Months to years
• Focus: Fundamentals
• Best for: Long-term holders

━━━━━━━━━━━━━━━━━━━━━━

💡 **Tips:**
• News is cached for faster access
• AI analysis is personalized
• Change style anytime
• Check stats to track usage

━━━━━━━━━━━━━━━━━━━━━━

🔧 **Commands:**
/start - Main menu
/news - Get latest news
/help - This message
/stats - View statistics

━━━━━━━━━━━━━━━━━━━━━━

🤖 _Powered by Google Gemini AI_
        """

        await query.edit_message_text(
            help_message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def handle_stats_callback(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """Show user statistics."""

        query = update.callback_query
        await query.answer()

        async with CorrelationContext(
            user_id=update.effective_user.id,
            command="stats"
        ):
            try:
                # Get user info
                user = await self.user_service.get_user(update.effective_user.id)

                if user:
                    trader_type = user.get('trader_type', 'investor')
                    created_at = user.get('created_at', 'Unknown')

                    # Get analytics
                    report = await self.analytics_service.get_analytics_report(days=30)

                    # Trader type emoji
                    trader_emojis = {
                        "scalper": "⚡",
                        "day_trader": "🎯",
                        "swing_trader": "🌊",
                        "investor": "🏛️"
                    }
                    emoji = trader_emojis.get(trader_type, "🎯")

                    keyboard = [
                        [
                            InlineKeyboardButton("📰 Get News", callback_data="get_news"),
                            InlineKeyboardButton("🔄 Change Style", callback_data="change_trader_type")
                        ],
                        [
                            InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
                        ]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)

                    stats_message = f"""
📊 **Your Statistics**

━━━━━━━━━━━━━━━━━━━━━━

👤 **Profile:**
• Trading Style: {emoji} {trader_type.replace('_', ' ').title()}
• Member Since: {created_at[:10]}
• Status: Active ✅

━━━━━━━━━━━━━━━━━━━━━━

📈 **Usage (Last 30 Days):**
• Total Commands: {report.get('total_commands', 0)}
• News Requests: {report.get('news_requests', 0)}
• Success Rate: {report.get('success_rate', 100):.1f}%

━━━━━━━━━━━━━━━━━━━━━━

⚡ **Performance:**
• Cache Hit Rate: {report.get('cache_hit_rate', 0):.0f}%
• Avg Response: {report.get('avg_response_time', 0):.2f}s
• Uptime: 99.9% ✅

━━━━━━━━━━━━━━━━━━━━━━

🎯 **Keep trading smart!**
                    """

                    await query.edit_message_text(
                        stats_message,
                        reply_markup=reply_markup,
                        parse_mode='Markdown'
                    )
                else:
                    await query.edit_message_text(
                        "❌ User not found. Please use /start first."
                    )

            except Exception as e:
                logger.error(f"Error showing stats: {e}", exc_info=True)
                await query.edit_message_text(
                    "❌ Error loading statistics. Please try again."
                )

    async def handle_change_trader_type_callback(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """Show trader type selection menu."""

        query = update.callback_query
        await query.answer()

        keyboard = [
            [
                InlineKeyboardButton("⚡ Scalper", callback_data="trader_scalper"),
                InlineKeyboardButton("🎯 Day Trader", callback_data="trader_day_trader")
            ],
            [
                InlineKeyboardButton("🌊 Swing Trader", callback_data="trader_swing_trader"),
                InlineKeyboardButton("🏛️ Investor", callback_data="trader_investor")
            ],
            [
                InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "🎯 **Select Your Trading Style:**\n\n"
            "Choose the style that best matches your trading approach:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )



    async def handle_setup_guide_callback(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """Show detailed setup guide for adding bot to groups."""

        query = update.callback_query
        await query.answer()

        try:
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup

            guide_message = """
📖 **Complete Setup Guide**

━━━━━━━━━━━━━━━━━━━━━━

**🚀 Quick Setup (5 minutes)**

**Step 1️⃣: Add Bot to Your Group**

1. Open your Telegram group
2. Tap the group name at the top
3. Tap "Add Members" or "Invite to Group"
4. Search for: `@YourBotUsername`
5. Select the bot and tap "Add"

━━━━━━━━━━━━━━━━━━━━━━

**Step 2️⃣: Grant Admin Permissions**

**Why?** The bot needs admin rights to post messages.

1. In your group, tap the group name
2. Tap "Administrators"
3. Tap "Add Administrator"
4. Select this bot from the list
5. **Required permissions:**
   ✅ Post Messages
   ✅ Delete Messages (optional, for cleanup)
6. Tap "Done" to save

━━━━━━━━━━━━━━━━━━━━━━

**Step 3️⃣: Register Your Group**

1. In your group chat, send this command:
   `/setup`

2. The bot will respond with:
   ✅ "Setup Complete!"
   ✅ Confirmation of registration
   ✅ Default settings applied

━━━━━━━━━━━━━━━━━━━━━━

**Step 4️⃣: Test the Bot (Optional)**

Send this command in your group:
`/testnews`

The bot will immediately fetch and post a sample news article with AI analysis. This confirms everything is working!

━━━━━━━━━━━━━━━━━━━━━━

**Step 5️⃣: Customize Settings (Optional)**

Send `/admin` in your group to access:

🎯 **Trader Type**: Choose your group's focus
• Scalper (high-frequency)
• Day Trader (intraday)
• Swing Trader (multi-day)
• Investor (long-term)

⏰ **Posting Schedule**: Set preferred time
• Default: 09:00 UTC
• Choose any hourly slot

🔔 **Status**: Enable/disable posting
• Pause anytime with `/pause`
• Resume with `/resume`

━━━━━━━━━━━━━━━━━━━━━━

**✅ You're All Set!**

The bot will now:
• Monitor crypto news 24/7
• Post hot/important news instantly
• Include AI analysis with every article
• Filter for quality (importance ≥ 5/10)
• Prevent duplicate posts

━━━━━━━━━━━━━━━━━━━━━━

**📋 Useful Commands:**

`/status` - View current configuration
`/pause` - Temporarily stop posting
`/resume` - Resume posting
`/testnews` - Post a test article
`/help` - Show all commands
`/admin` - Open admin panel

━━━━━━━━━━━━━━━━━━━━━━

**❓ Troubleshooting:**

**Bot not posting?**
• Check if bot is admin
• Verify "Post Messages" permission is enabled
• Try `/status` to check configuration

**Want to change settings?**
• Use `/admin` in your group
• All settings can be changed anytime

**Need to remove the bot?**
• Use `/remove` to unregister
• Then remove bot from group members

━━━━━━━━━━━━━━━━━━━━━━

**🎉 Welcome to automated crypto intelligence!**

Your group is now equipped with 24/7 AI-powered news monitoring. Sit back and let the bot keep your community informed!
            """

            keyboard = [
                [
                    InlineKeyboardButton(
                        "📰 See Sample News",
                        callback_data="preview_sample_news"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🎯 Learn About Trader Types",
                        callback_data="show_trader_types"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🔙 Back to Start",
                        callback_data="back_to_start"
                    )
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                guide_message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

        except Exception as e:
            logger.error(f"Error in setup guide callback: {e}", exc_info=True)
            await query.answer("❌ Error showing guide")

    async def handle_trader_types_callback(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """Show trader types explanation."""

        query = update.callback_query
        await query.answer()

        try:
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup

            types_message = """
🎯 **Trader Types Explained**

━━━━━━━━━━━━━━━━━━━━━━

Choose the trading style that matches your group's focus:

**⚡ Scalper**
• **Timeframe:** 1-5 minutes
• **Focus:** High-frequency opportunities
• **News:** Volatility triggers, quick moves
• **Best for:** Active day traders

**🎯 Day Trader**
• **Timeframe:** Minutes to hours
• **Focus:** Intraday momentum
• **News:** Technical breakouts, volume spikes
• **Best for:** Daily active traders

**🌊 Swing Trader**
• **Timeframe:** 2-10 days
• **Focus:** Multi-day trends
• **News:** Pattern formations, support/resistance
• **Best for:** Part-time traders

**🏛️ Investor**
• **Timeframe:** Months to years
• **Focus:** Long-term fundamentals
• **News:** Market trends, macro events
• **Best for:** Long-term holders

━━━━━━━━━━━━━━━━━━━━━━

💡 **Tip:** You can change this anytime using `/admin` in your group!
            """

            keyboard = [
                [
                    InlineKeyboardButton(
                        "🔙 Back to Start",
                        callback_data="back_to_start"
                    )
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                types_message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

        except Exception as e:
            logger.error(f"Error in trader types callback: {e}", exc_info=True)
            await query.answer("❌ Error showing trader types")

    async def handle_back_to_start_callback(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """Return to start message."""

        query = update.callback_query
        await query.answer()

        try:
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup

            welcome_message = """
🤖 **AI Market Insight Bot**
_Automated Daily News for Telegram Groups_

━━━━━━━━━━━━━━━━━━━━━━

**What I Do:**
📰 Post daily AI-analyzed market news to your Telegram groups
🤖 Powered by Google Gemini AI
🎯 Customizable for different trader types
⏰ Scheduled automated posting

━━━━━━━━━━━━━━━━━━━━━━

**How to Set Up:**

1️⃣ Add me to your Telegram group
2️⃣ Make me an admin (so I can post)
3️⃣ Use /setup in the group to register
4️⃣ Customize with /admin panel

━━━━━━━━━━━━━━━━━━━━━━

💡 **Quick Actions:**
            """

            keyboard = [
                [
                    InlineKeyboardButton(
                        "📰 Preview Sample News",
                        callback_data="preview_sample_news"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "📚 View All Commands",
                        callback_data="show_help"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "❓ How to Add Bot to Group",
                        callback_data="show_setup_guide"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🎯 Trader Types Explained",
                        callback_data="show_trader_types"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "📖 Documentation",
                        url="https://github.com/yourusername/ainews"
                    )
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                welcome_message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

        except Exception as e:
            logger.error(f"Error in back to start callback: {e}", exc_info=True)
            await query.answer("❌ Error returning to start")


    async def handle_preview_sample_news_callback(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """Show preview of how news will look in groups."""

        query = update.callback_query
        await query.answer()

        try:
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup

            # Show loading message
            await query.edit_message_text(
                "🔄 **Generating sample news preview...**\n\n"
                "⏳ This may take a moment...",
                parse_mode='Markdown'
            )

            # Generate sample news (use investor type as default)
            try:
                articles = await self.news_service.get_trader_specific_news(
                    trader_type='investor',
                    limit=3
                )

                if articles:
                    # Format as it would appear in a group
                    preview_message = """
📰 **Daily AI Market Insights**
_Powered by Google Gemini AI_

━━━━━━━━━━━━━━━━━━━━━━

"""

                    for i, article in enumerate(articles, 1):
                        title = article.get('title', 'No title')
                        summary = article.get('ai_summary', article.get('description', 'No summary'))
                        url = article.get('url', '')

                        preview_message += f"""
**{i}. {title}**

{summary}

🔗 [Read more]({url})

━━━━━━━━━━━━━━━━━━━━━━

"""

                    preview_message += """
💡 **This is how daily news will appear in your group!**

🎯 Trader Type: Investor (Long-term focus)
⏰ Posted automatically at your chosen time
🤖 AI-analyzed for relevance and insights
                    """

                else:
                    # No news available - show elaborate sample format
                    preview_message = """
📰 **Daily AI Market Insights - Sample Preview**
_Powered by Google Gemini AI_

━━━━━━━━━━━━━━━━━━━━━━

**1. Bitcoin Surges Past $75,000 - New All-Time High**

**Market Analysis:**
Bitcoin has reached a historic milestone, breaking through the $75,000 resistance level with strong momentum. This surge is attributed to several key factors:

• **Institutional Adoption**: Major financial institutions including BlackRock and Fidelity have increased their Bitcoin holdings by 23% this quarter
• **Regulatory Clarity**: The SEC's recent approval of spot Bitcoin ETFs has brought unprecedented legitimacy to the crypto market
• **Supply Dynamics**: With the upcoming halving event in 6 months, miners are reducing sell pressure, creating a supply squeeze

**AI Insight for Investors:**
This breakout represents a significant shift in market sentiment. Long-term holders (addresses holding for 1+ years) now control 68% of circulating supply, the highest level since 2020. Historical patterns suggest this accumulation phase typically precedes extended bull markets.

**Key Metrics:**
📊 Price: $75,234 (+12.4% 24h)
📈 Volume: $48.2B (+156%)
💰 Market Cap: $1.47T
🔥 Fear & Greed Index: 78 (Extreme Greed)

**Investment Perspective:**
For long-term investors, this could be an early stage of a multi-year bull cycle. Consider dollar-cost averaging rather than lump-sum entries at these elevated levels. Watch for pullbacks to $68K-$70K range for better entry points.

━━━━━━━━━━━━━━━━━━━━━━

**2. Ethereum Network Upgrade Slashes Gas Fees by 40%**

**Technical Development:**
The Ethereum network has successfully implemented the "Dencun" upgrade, bringing significant improvements to scalability and cost efficiency:

• **Layer 2 Optimization**: Proto-danksharding (EIP-4844) reduces L2 transaction costs by up to 90%
• **Network Efficiency**: Average gas fees dropped from 45 gwei to 27 gwei
• **Transaction Speed**: Block confirmation times improved by 15%

**AI Insight for Developers & DeFi Users:**
This upgrade fundamentally changes Ethereum's value proposition. Lower fees make DeFi protocols more accessible to retail users, potentially unlocking $50B+ in sidelined capital. Expect increased activity in lending protocols, DEXs, and NFT marketplaces.

**Impact Analysis:**
🔧 Gas Fees: 27 gwei (↓40%)
⚡ TPS: 29 transactions/sec (↑15%)
🌐 L2 Activity: +234% in 48 hours
💎 ETH Staked: 32.4M ETH ($78B)

**DeFi Opportunities:**
With lower fees, yield farming on Ethereum mainnet becomes profitable again for smaller portfolios ($5K-$50K). Protocols like Aave, Uniswap, and Curve are seeing 3x increase in new user onboarding.

**Developer Perspective:**
This upgrade positions Ethereum as the dominant smart contract platform. Projects building on L2s (Arbitrum, Optimism, Base) will see dramatic cost reductions, accelerating adoption.

━━━━━━━━━━━━━━━━━━━━━━

**3. Binance Expands Trading Pairs - 15 New Altcoins Listed**

**Exchange Development:**
Binance, the world's largest cryptocurrency exchange by volume, has announced a major expansion of its trading offerings:

**New Listings Include:**
• **AI Tokens**: Render (RNDR), Fetch.ai (FET), SingularityNET (AGIX)
• **DeFi Protocols**: Pendle (PENDLE), GMX (GMX), Radiant Capital (RDNT)
• **Layer 1s**: Sei (SEI), Celestia (TIA), Aptos (APT)
• **Gaming**: Immutable X (IMX), Gala (GALA), Axie Infinity (AXS)

**AI Insight for Traders:**
This listing wave signals Binance's strategic focus on emerging narratives: AI, gaming, and next-gen L1s. Historically, Binance listings trigger 20-40% price pumps in the first 48 hours, followed by 15-25% corrections.

**Trading Strategy:**
📊 **Short-term (1-7 days)**: Expect volatility. Many tokens pump 30-50% on listing day, then retrace 20-30%
📈 **Medium-term (1-3 months)**: Quality projects (RNDR, TIA, APT) tend to establish higher price floors post-listing
💰 **Long-term (6+ months)**: Focus on fundamentals. AI and gaming narratives are early-stage with 10x+ potential

**Risk Assessment:**
⚠️ High volatility expected in first week
✅ Increased liquidity benefits all traders
🎯 Best opportunities: Wait for post-listing dip (usually 3-5 days)

**Portfolio Allocation:**
For diversified portfolios, consider 5-10% allocation to these emerging sectors. AI tokens (RNDR, FET) show strongest fundamentals with real revenue and product-market fit.

━━━━━━━━━━━━━━━━━━━━━━

💡 **This is how daily news will appear in your group!**

🎯 **Trader Type**: Investor (Long-term focus)
⏰ **Posting Schedule**: Automated daily at your chosen time
🤖 **AI Analysis**: Powered by Google Gemini for deep insights
📊 **Content**: Comprehensive analysis - no need to click external links
🔍 **Customization**: Different insights for Day Traders, Swing Traders, Investors, and HODLers

**What You Get:**
✅ Latest trending crypto news (3-5 articles daily)
✅ AI-powered market analysis and insights
✅ Key metrics and data points
✅ Actionable trading/investment perspectives
✅ Risk assessments and opportunities
✅ No ads, no spam - pure value

_Note: This is sample data showing the format and depth of analysis. Real news will be fetched daily from live sources and analyzed by AI._
                    """

                keyboard = [
                    [
                        InlineKeyboardButton(
                            "✅ Add Bot to My Group",
                            callback_data="show_setup_guide"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "🔙 Back to Start",
                            callback_data="back_to_start"
                        )
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await query.edit_message_text(
                    preview_message,
                    reply_markup=reply_markup,
                    parse_mode='Markdown',
                    disable_web_page_preview=True
                )

            except Exception as news_error:
                logger.error(f"Error fetching news for preview: {news_error}", exc_info=True)

                # Show elaborate sample format on error
                sample_message = """
📰 **Daily AI Market Insights - Sample Preview**
_Powered by Google Gemini AI_

━━━━━━━━━━━━━━━━━━━━━━

**Bitcoin Breaks $75K - Historic Milestone Reached**

**Market Analysis:**
Bitcoin has shattered previous records, reaching $75,234 with unprecedented institutional support. This rally is driven by:

• **ETF Inflows**: $2.1B in net inflows this week
• **Halving Anticipation**: Supply reduction in 6 months
• **Institutional Adoption**: 68% held by long-term holders

**AI Insight:**
Historical patterns suggest early bull cycle phase. Long-term holders accumulating at record levels indicates strong conviction. Consider dollar-cost averaging for optimal entry strategy.

**Key Metrics:**
📊 Price: $75,234 (+12.4%)
📈 Volume: $48.2B
💰 Market Cap: $1.47T
🔥 Sentiment: Extreme Greed (78)

━━━━━━━━━━━━━━━━━━━━━━

**Ethereum Upgrade Cuts Fees 40%**

**Technical Development:**
Dencun upgrade successfully deployed with major improvements:

• **Gas Fees**: Reduced from 45 to 27 gwei
• **L2 Optimization**: 90% cost reduction for rollups
• **Network Speed**: 15% faster confirmations

**AI Insight:**
Lower fees unlock $50B+ in sidelined DeFi capital. Expect surge in DEX activity, yield farming, and NFT trading. Protocols like Aave and Uniswap seeing 3x user growth.

**Impact:**
🔧 Fees: ↓40%
⚡ Speed: ↑15%
🌐 L2 Activity: +234%
💎 Staked: $78B

━━━━━━━━━━━━━━━━━━━━━━

💡 **This is how news appears in your group!**

**Features:**
✅ Comprehensive analysis - no external links needed
✅ AI-powered insights for your trader type
✅ Key metrics and actionable data
✅ Risk assessments and opportunities
✅ Automated daily delivery
✅ Customized for Day Traders, Swing Traders, Investors, HODLers

**Get Started:**
1. Add bot to your group
2. Make it an admin
3. Use /setup to register
4. Configure with /admin panel

_Note: Live news requires API configuration._
                """

                keyboard = [
                    [
                        InlineKeyboardButton(
                            "✅ Add Bot to My Group",
                            callback_data="show_setup_guide"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "🔙 Back to Start",
                            callback_data="back_to_start"
                        )
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await query.edit_message_text(
                    sample_message,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )

        except Exception as e:
            logger.error(f"Error in preview sample news callback: {e}", exc_info=True)
            await query.answer("❌ Error showing preview")

    # ============================================================================
    # ONBOARDING FLOW HANDLERS
    # ============================================================================

    async def handle_onboarding_step_1_callback(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """Onboarding Step 1: What the bot does."""

        query = update.callback_query
        await query.answer()

        try:
            message = """
📱 **What is AI Crypto News Bot?**

━━━━━━━━━━━━━━━━━━━━━━

Your bot is a **24/7 crypto intelligence system** that monitors the crypto market around the clock and delivers instant, AI-analyzed news to your Telegram group.

**🔥 Real-Time Monitoring**
Unlike traditional news bots that post on a schedule, this bot **continuously scans** multiple crypto news sources and instantly posts when important market-moving news breaks.

**🤖 AI-Powered Analysis**
Every news article is analyzed by **Google Gemini AI** to provide:
• Market impact assessment
• Trading implications
• Risk analysis
• Actionable insights

**📊 Multi-Source Aggregation**
The bot pulls news from:
• CryptoPanic (community-voted important news)
• CryptoCompare (professional crypto news)
• Real-time filtering for hot/breaking news only

**🎯 Smart Filtering**
Only posts news with **importance score ≥ 5/10**, so your group gets quality over quantity - no spam, just valuable market intelligence.

━━━━━━━━━━━━━━━━━━━━━━

**Think of it as having a professional crypto analyst working 24/7 for your community.**
            """

            keyboard = [
                [
                    InlineKeyboardButton(
                        "Next: Key Features →",
                        callback_data="onboarding_step_2"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "⚡ Skip to Setup",
                        callback_data="show_setup_guide"
                    )
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

        except Exception as e:
            logger.error(f"Error in onboarding step 1: {e}", exc_info=True)
            await query.answer("❌ Error loading content")

    async def handle_onboarding_step_2_callback(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """Onboarding Step 2: Key features."""

        query = update.callback_query
        await query.answer()

        try:
            message = """
✨ **Key Features That Set Us Apart**

━━━━━━━━━━━━━━━━━━━━━━

**1. 🔥 Instant Hot News Delivery**
• No waiting for scheduled posts
• News arrives within minutes of breaking
• Importance-based filtering (only score ≥ 5/10)
• 24/7 monitoring, never misses a beat

**2. 🤖 Deep AI Analysis**
• Powered by Google Gemini 2.0 Flash
• Market impact assessment for each article
• Trading implications explained clearly
• Tailored insights for your trader type

**3. 🎯 Trader-Specific Insights**
Choose your group's focus:
• **⚡ Scalper**: High-frequency opportunities
• **🎯 Day Trader**: Intraday momentum plays
• **🌊 Swing Trader**: Multi-day trend analysis
• **🏛️ Investor**: Long-term fundamental insights

**4. 📊 Multi-Source Intelligence**
• CryptoPanic: Community-voted important news
• CryptoCompare: Professional crypto journalism
• Automatic deduplication of repeated stories
• Only the most relevant news makes it through

**5. 💎 Enterprise-Grade Reliability**
• Rate limiting prevents API overload
• Circuit breaker protection for stability
• Metrics tracking for performance monitoring
• Built for high-volume communities

━━━━━━━━━━━━━━━━━━━━━━

**Everything you need to keep your community informed and ahead of the market.**
            """

            keyboard = [
                [
                    InlineKeyboardButton(
                        "← Previous",
                        callback_data="onboarding_step_1"
                    ),
                    InlineKeyboardButton(
                        "Next: How It Works →",
                        callback_data="onboarding_step_3"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "⚡ Skip to Setup",
                        callback_data="show_setup_guide"
                    )
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

        except Exception as e:
            logger.error(f"Error in onboarding step 2: {e}", exc_info=True)
            await query.answer("❌ Error loading content")

    async def handle_onboarding_step_3_callback(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """Onboarding Step 3: How it works."""

        query = update.callback_query
        await query.answer()

        try:
            message = """
⚙️ **How It Works - Behind the Scenes**

━━━━━━━━━━━━━━━━━━━━━━

**The Complete Workflow:**

**Step 1: 🔍 Continuous Monitoring**
• Bot scans news sources every 5 minutes
• Fetches latest articles from CryptoPanic & CryptoCompare
• Filters for "important" and "hot" tagged news only

**Step 2: 📊 Importance Scoring**
Each article gets scored 0-10 based on:
• Community votes and engagement
• Source credibility
• Breaking news indicators
• Market impact potential

**Step 3: 🤖 AI Analysis**
Articles with score ≥ 5 are sent to Google Gemini AI for:
• Market impact assessment
• Trading implications analysis
• Risk/opportunity identification
• Trader-specific insights generation

**Step 4: 📱 Smart Delivery**
• Formatted message created with full article content
• AI analysis included (no need to click external links)
• Posted instantly to your registered groups
• Duplicate detection prevents spam

**Step 5: 📈 Tracking & Optimization**
• Metrics collected for performance monitoring
• Posted URLs tracked to prevent duplicates
• System health monitored 24/7

━━━━━━━━━━━━━━━━━━━━━━

**Result:** Your group gets comprehensive, AI-analyzed crypto news delivered instantly - no manual work required!
            """

            keyboard = [
                [
                    InlineKeyboardButton(
                        "← Previous",
                        callback_data="onboarding_step_2"
                    ),
                    InlineKeyboardButton(
                        "Next: Benefits →",
                        callback_data="onboarding_step_4"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "⚡ Skip to Setup",
                        callback_data="show_setup_guide"
                    )
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

        except Exception as e:
            logger.error(f"Error in onboarding step 3: {e}", exc_info=True)
            await query.answer("❌ Error loading content")

    async def handle_onboarding_step_4_callback(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """Onboarding Step 4: Benefits for group owners."""

        query = update.callback_query
        await query.answer()

        try:
            message = """
🎯 **Benefits for Your Telegram Group**

━━━━━━━━━━━━━━━━━━━━━━

**For Group Owners/Admins:**

**1. 📈 Increase Member Engagement**
• Keep members active with valuable, timely content
• Reduce churn by providing real value
• Position your group as a go-to crypto intelligence source
• Members stay for the quality insights

**2. ⏰ Save Massive Time**
• No manual news curation needed
• No copying/pasting from news sites
• No writing analysis yourself
• Set it up once, runs forever

**3. 🎯 Build Authority & Trust**
• Professional AI-analyzed content
• Consistent, reliable information flow
• Demonstrate you're serious about providing value
• Stand out from amateur groups

**4. 🚀 Grow Your Community**
• Quality content attracts new members
• Members invite friends for the insights
• Organic growth through word-of-mouth
• Retention improves dramatically

**5. 💎 Zero Maintenance Required**
• Fully automated 24/7 operation
• No daily tasks or monitoring needed
• Bot handles everything automatically
• You focus on community building

━━━━━━━━━━━━━━━━━━━━━━

**For Your Members:**

✅ **Stay Informed**: Never miss important crypto news
✅ **Save Time**: No need to browse multiple news sites
✅ **Get Insights**: AI analysis explains what news means
✅ **Make Better Decisions**: Understand market implications
✅ **Learn Continuously**: Educational value in every post

━━━━━━━━━━━━━━━━━━━━━━

**Bottom Line:** This bot transforms your group from "just another crypto chat" into a **professional intelligence hub** that members genuinely value.

**Ready to get started?**
            """

            keyboard = [
                [
                    InlineKeyboardButton(
                        "← Previous",
                        callback_data="onboarding_step_3"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🚀 Let's Set It Up!",
                        callback_data="show_setup_guide"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "📰 See Sample News",
                        callback_data="preview_sample_news"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🔙 Back to Start",
                        callback_data="back_to_start"
                    )
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

        except Exception as e:
            logger.error(f"Error in onboarding step 4: {e}", exc_info=True)
            await query.answer("❌ Error loading content")

    @rate_limit(user_capacity=10, user_refill_rate=1.0)
    @validate_input
    async def handle_subscription(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /subscription command - View subscription status."""

        async with CorrelationContext(
            user_id=update.effective_user.id,
            command="subscription"
        ):
            try:
                # Check if subscription service is available
                if not self.subscription_service:
                    await update.message.reply_text(
                        "❌ Subscription service is not available.",
                        parse_mode='Markdown'
                    )
                    return

                # Get chat type
                chat_type = update.effective_chat.type

                if chat_type == 'private':
                    # Private chat - explain how to use
                    message = """
💳 **Subscription Management**

This command works in **group chats only**.

**To check your group's subscription:**
1. Go to your Telegram group
2. Use `/subscription` command there

**Need help?** Use /help for more information.
                    """

                    await update.message.reply_text(
                        message,
                        parse_mode='Markdown'
                    )
                    return

                # Group chat - show subscription status
                group_id = update.effective_chat.id

                # Get subscription status
                status = await self.subscription_service.get_subscription_status(group_id)

                if not status['has_subscription']:
                    message = """
❌ **No Active Subscription**

This group doesn't have an active subscription yet.

**To get started:**
• Add this bot to your group
• The bot will automatically create a **15-day free trial**

Need help? Contact support.
                    """

                    await update.message.reply_text(
                        message,
                        parse_mode='Markdown'
                    )
                    return

                # Format subscription status
                subscription_status = status['status']
                posting_allowed = status['posting_allowed']

                if subscription_status == 'trial':
                    days_left = status.get('trial_days_left', 0)
                    trial_end = status.get('trial_end_date', '')

                    message = f"""
🎁 **Free Trial Active**

━━━━━━━━━━━━━━━━━━━━━━

**Status:** Trial Period
**Days Remaining:** {days_left} days
**Trial Ends:** {trial_end[:10] if trial_end else 'N/A'}
**Posting Status:** {'✅ Active' if posting_allowed else '❌ Inactive'}

━━━━━━━━━━━━━━━━━━━━━━

**After trial ends:**
• Subscribe for **$15/month**
• Continue receiving real-time crypto news
• AI-powered market analysis

Use /renew to subscribe now and get uninterrupted service!
                    """

                elif subscription_status == 'active':
                    days_left = status.get('subscription_days_left', 0)
                    sub_end = status.get('subscription_end_date', '')

                    message = f"""
✅ **Subscription Active**

━━━━━━━━━━━━━━━━━━━━━━

**Status:** Active Subscription
**Days Remaining:** {days_left} days
**Renewal Date:** {sub_end[:10] if sub_end else 'N/A'}
**Posting Status:** {'✅ Active' if posting_allowed else '❌ Inactive'}

━━━━━━━━━━━━━━━━━━━━━━

**Your benefits:**
• 24/7 real-time crypto news
• AI-powered market analysis
• Multi-source news aggregation
• Trader-specific insights

Use /renew to extend your subscription!
                    """

                elif subscription_status == 'expired':
                    message = """
⚠️ **Subscription Expired**

━━━━━━━━━━━━━━━━━━━━━━

**Status:** Expired
**Posting Status:** ❌ Inactive

Your subscription has expired. News posting is currently disabled.

**To reactivate:**
Use /renew to subscribe for **$15/month**

━━━━━━━━━━━━━━━━━━━━━━

Don't miss out on market-moving crypto news!
                    """

                else:
                    message = f"""
ℹ️ **Subscription Status**

**Status:** {subscription_status.title()}
**Posting Status:** {'✅ Active' if posting_allowed else '❌ Inactive'}

Use /renew to manage your subscription.
                    """

                keyboard = [
                    [
                        InlineKeyboardButton(
                            "💳 Renew Subscription",
                            callback_data="renew_subscription"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "📊 View Plans",
                            callback_data="view_plans"
                        )
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await update.message.reply_text(
                    message,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )

                # Log analytics
                await self.analytics_service.log_command(
                    update.effective_user.id,
                    "subscription",
                    {"group_id": group_id, "status": subscription_status}
                )

            except Exception as e:
                logger.error(f"Error in handle_subscription: {e}", exc_info=True)
                await update.message.reply_text(
                    "❌ Error retrieving subscription status. Please try again later.",
                    parse_mode='Markdown'
                )

    @rate_limit(user_capacity=5, user_refill_rate=0.5)
    @validate_input
    async def handle_renew(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /renew command - Renew subscription."""

        async with CorrelationContext(
            user_id=update.effective_user.id,
            command="renew"
        ):
            try:
                # Check if services are available
                if not self.subscription_service or not self.payment_service:
                    await update.message.reply_text(
                        "❌ Payment service is not available.",
                        parse_mode='Markdown'
                    )
                    return

                # Get chat type
                chat_type = update.effective_chat.type

                if chat_type == 'private':
                    # Private chat - explain how to use
                    message = """
💳 **Subscription Renewal**

This command works in **group chats only**.

**To renew your group's subscription:**
1. Go to your Telegram group
2. Use `/renew` command there
3. Choose your payment method
4. Complete the payment

**Need help?** Use /help for more information.
                    """

                    await update.message.reply_text(
                        message,
                        parse_mode='Markdown'
                    )
                    return

                # Group chat - show renewal options
                group_id = update.effective_chat.id
                group_name = update.effective_chat.title or "Unknown Group"

                # Get subscription
                subscription = await self.subscription_service.get_subscription(group_id)

                if not subscription:
                    message = """
❌ **No Subscription Found**

This group doesn't have a subscription yet.

**To get started:**
• Add this bot to your group
• The bot will automatically create a **15-day free trial**

After the trial, you can use /renew to subscribe.
                    """

                    await update.message.reply_text(
                        message,
                        parse_mode='Markdown'
                    )
                    return

                # Show renewal options with currency selection
                message = """
💳 **Renew Subscription**

━━━━━━━━━━━━━━━━━━━━━━

**Plan:** Monthly Subscription
**Price:** $15.00 USD/month

**What you get:**
• 24/7 real-time crypto news
• AI-powered market analysis
• Multi-source aggregation
• Trader-specific insights
• Priority support

━━━━━━━━━━━━━━━━━━━━━━

**Choose your payment method:**
                """

                # Get available currencies
                currencies = await self.payment_service.get_available_currencies()

                # Create currency buttons (2 per row)
                keyboard = []
                row = []

                currency_labels = {
                    'btc': '₿ Bitcoin',
                    'eth': 'Ξ Ethereum',
                    'usdt': '₮ USDT',
                    'usdc': '$ USDC',
                    'bnb': '🔶 BNB',
                    'trx': '⚡ TRON'
                }

                for currency in currencies[:6]:  # Limit to 6 currencies
                    label = currency_labels.get(currency.lower(), currency.upper())
                    row.append(
                        InlineKeyboardButton(
                            label,
                            callback_data=f"pay_{currency}_{subscription['subscription_id']}"
                        )
                    )

                    if len(row) == 2:
                        keyboard.append(row)
                        row = []

                if row:  # Add remaining button
                    keyboard.append(row)

                # Add cancel button
                keyboard.append([
                    InlineKeyboardButton(
                        "❌ Cancel",
                        callback_data="cancel_renewal"
                    )
                ])

                reply_markup = InlineKeyboardMarkup(keyboard)

                await update.message.reply_text(
                    message,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )

                # Log analytics
                await self.analytics_service.log_command(
                    update.effective_user.id,
                    "renew",
                    {"group_id": group_id, "subscription_id": subscription['subscription_id']}
                )

            except Exception as e:
                logger.error(f"Error in handle_renew: {e}", exc_info=True)
                await update.message.reply_text(
                    "❌ Error processing renewal request. Please try again later.",
                    parse_mode='Markdown'
                )

    async def handle_payment_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle payment currency selection callback."""

        query = update.callback_query
        await query.answer()

        try:
            # Parse callback data: pay_{currency}_{subscription_id}
            data_parts = query.data.split('_')

            if len(data_parts) < 3:
                await query.edit_message_text("❌ Invalid payment request.")
                return

            currency = data_parts[1]
            subscription_id = int(data_parts[2])

            # Get subscription
            subscription = await self.subscription_service.subscription_repo.find_by_id(subscription_id)

            if not subscription:
                await query.edit_message_text("❌ Subscription not found.")
                return

            # Create payment invoice
            invoice = await self.payment_service.create_invoice(
                subscription_id=subscription_id,
                group_id=subscription['group_id'],
                amount_usd=self.subscription_service.SUBSCRIPTION_PRICE_USD,
                currency=currency,
                description=f"Monthly subscription for group {subscription['group_id']}"
            )

            if not invoice:
                await query.edit_message_text(
                    "❌ Failed to create payment invoice. Please try again later."
                )
                return

            # Format payment instructions
            message = f"""
✅ **Payment Invoice Created**

━━━━━━━━━━━━━━━━━━━━━━

**Amount:** ${invoice.get('pay_amount', 'N/A')} {currency.upper()}
**Equivalent:** ${self.subscription_service.SUBSCRIPTION_PRICE_USD} USD

**Payment Address:**
`{invoice.get('pay_address', 'N/A')}`

**Invoice ID:** {invoice.get('invoice_id', 'N/A')}
**Expires:** {invoice.get('expires_at', 'N/A')[:16] if invoice.get('expires_at') else 'N/A'}

━━━━━━━━━━━━━━━━━━━━━━

**How to pay:**
1. Copy the payment address above
2. Send exactly **{invoice.get('pay_amount', 'N/A')} {currency.upper()}** to this address
3. Your subscription will be activated automatically after confirmation

**Payment URL:**
{invoice.get('payment_url', 'Payment URL not available')}

⚠️ **Important:**
• Send the exact amount shown
• Payment expires in 60 minutes
• You'll receive confirmation once payment is detected
            """

            keyboard = [
                [
                    InlineKeyboardButton(
                        "💳 Open Payment Page",
                        url=invoice.get('payment_url', 'https://nowpayments.io')
                    )
                ],
                [
                    InlineKeyboardButton(
                        "✅ I've Paid",
                        callback_data=f"check_payment_{invoice['payment_id']}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "❌ Cancel",
                        callback_data="cancel_payment"
                    )
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

            # Log analytics
            await self.analytics_service.log_event(
                query.from_user.id,
                "payment_invoice_created",
                {
                    "subscription_id": subscription_id,
                    "currency": currency,
                    "amount_usd": self.subscription_service.SUBSCRIPTION_PRICE_USD
                }
            )

        except Exception as e:
            logger.error(f"Error in handle_payment_callback: {e}", exc_info=True)
            await query.edit_message_text(
                "❌ Error processing payment. Please try again later."
            )

    async def handle_check_payment_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle check payment status callback."""

        query = update.callback_query
        await query.answer("Checking payment status...")

        try:
            # Parse callback data: check_payment_{payment_id}
            payment_id = int(query.data.split('_')[2])

            # Get payment
            payment = await self.payment_service.payment_repo.find_by_id(payment_id)

            if not payment:
                await query.answer("❌ Payment not found.", show_alert=True)
                return

            # Check payment status
            status = payment['payment_status']

            if status == 'finished':
                await query.edit_message_text(
                    "✅ **Payment Confirmed!**\n\n"
                    "Your subscription has been activated.\n"
                    "Thank you for your payment!",
                    parse_mode='Markdown'
                )
            elif status in ['pending', 'waiting']:
                await query.answer(
                    "⏳ Payment is still pending. Please wait for confirmation.",
                    show_alert=True
                )
            elif status == 'expired':
                await query.answer(
                    "❌ Payment expired. Please create a new invoice.",
                    show_alert=True
                )
            else:
                await query.answer(
                    f"ℹ️ Payment status: {status}",
                    show_alert=True
                )

        except Exception as e:
            logger.error(f"Error in handle_check_payment_callback: {e}", exc_info=True)
            await query.answer("❌ Error checking payment status.", show_alert=True)

    async def handle_add_channel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /addchannel command - Add a channel for automated posting."""

        try:
            # Must be in private chat
            if update.effective_chat.type != 'private':
                await update.message.reply_text(
                    "⚠️ This command only works in **private chat** with the bot.\n\n"
                    "Please message me directly.",
                    parse_mode='Markdown'
                )
                return

            # Show instructions
            message = """
📺 **Add Your Telegram Channel**

━━━━━━━━━━━━━━━━━━━━━━

**Step 1: Add Bot to Your Channel**

1. Open your Telegram channel
2. Tap the channel name at the top
3. Tap "Administrators"
4. Tap "Add Administrator"
5. Search for this bot and add it
6. **Enable these permissions:**
   ✅ Post Messages (required!)
   ✅ Edit Messages (optional)
   ✅ Delete Messages (optional)

━━━━━━━━━━━━━━━━━━━━━━

**Step 2: Get Your Channel ID**

**Option A: Forward a message**
• Forward any message from your channel to @userinfobot
• The bot will show your channel ID

**Option B: Use this bot**
• Forward any message from your channel to me
• I'll extract the channel ID for you

━━━━━━━━━━━━━━━━━━━━━━

**Step 3: Register Your Channel**

Once you have your channel ID, use this command:

`/registerchannel <channel_id> <channel_name>`

**Example:**
`/registerchannel -1001234567890 My Crypto Channel`

━━━━━━━━━━━━━━━━━━━━━━

💡 **Note:** Channel IDs are negative numbers starting with -100

**Need help?** Forward a message from your channel to me and I'll guide you!
            """

            await update.message.reply_text(message, parse_mode='Markdown')

        except Exception as e:
            logger.error(f"Error in handle_add_channel: {e}", exc_info=True)
            await update.message.reply_text(
                "❌ An error occurred. Please try again later."
            )

    async def handle_register_channel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /registerchannel command - Register a channel with ID and name."""

        try:
            # Must be in private chat
            if update.effective_chat.type != 'private':
                await update.message.reply_text(
                    "⚠️ This command only works in **private chat** with the bot.",
                    parse_mode='Markdown'
                )
                return

            # Check arguments
            if not context.args or len(context.args) < 2:
                await update.message.reply_text(
                    "❌ **Invalid format**\n\n"
                    "**Usage:**\n"
                    "`/registerchannel <channel_id> <channel_name>`\n\n"
                    "**Example:**\n"
                    "`/registerchannel -1001234567890 My Crypto Channel`\n\n"
                    "💡 Use /addchannel for detailed instructions",
                    parse_mode='Markdown'
                )
                return

            # Parse arguments
            try:
                channel_id = int(context.args[0])
                channel_name = ' '.join(context.args[1:])
            except ValueError:
                await update.message.reply_text(
                    "❌ **Invalid channel ID**\n\n"
                    "Channel ID must be a number (e.g., -1001234567890)\n\n"
                    "💡 Use /addchannel for help getting your channel ID",
                    parse_mode='Markdown'
                )
                return

            # Validate channel ID format
            if channel_id >= 0:
                await update.message.reply_text(
                    "❌ **Invalid channel ID format**\n\n"
                    "Channel IDs must be **negative numbers** starting with -100\n\n"
                    "**Example:** -1001234567890\n\n"
                    "💡 Forward a message from your channel to @userinfobot to get the correct ID",
                    parse_mode='Markdown'
                )
                return

            # Check if channel already exists
            group_repo = self.user_service.group_repo

            existing = await group_repo.find_by_id(channel_id)

            if existing:
                await update.message.reply_text(
                    f"⚠️ **Channel Already Registered**\n\n"
                    f"📱 **Channel:** {existing.get('group_name', 'Unknown')}\n"
                    f"📌 **Status:** {existing.get('subscription_status', 'unknown').upper()}\n\n"
                    f"Use /mychannels to view all your channels",
                    parse_mode='Markdown'
                )
                return

            # Create channel and subscription
            from datetime import datetime, timedelta
            now = datetime.now()
            trial_days = 15
            end_date = now + timedelta(days=trial_days)

            # Add channel using the correct method signature
            await group_repo.create(
                group_id=channel_id,
                group_name=channel_name,
                posting_time="09:00",  # Default posting time
                trader_type="investor"  # Default trader type
            )

            # Set creator_user_id for ownership tracking
            import sqlite3
            conn = sqlite3.connect('bot_database.db')
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE groups SET creator_user_id = ? WHERE group_id = ?
            """, (update.effective_user.id, channel_id))
            conn.commit()
            conn.close()

            # Create subscription
            if self.subscription_service:
                await self.subscription_service.create_trial_subscription(
                    group_id=channel_id,
                    group_name=channel_name,
                    creator_user_id=update.effective_user.id
                )

            # Success message
            message = f"""
✅ **Channel Registered Successfully!**

━━━━━━━━━━━━━━━━━━━━━━

📺 **Channel:** {channel_name}
🆔 **ID:** `{channel_id}`
📌 **Status:** TRIAL (15 days)
⏰ **Expires:** {end_date.strftime('%Y-%m-%d')}

━━━━━━━━━━━━━━━━━━━━━━

🚀 **What's Next?**

The bot will now automatically post important crypto news to your channel!

**How it works:**
• 🔍 Monitors crypto news 24/7
• 🤖 AI analyzes importance (0-10 scale)
• 📢 Posts news with score ≥ 7 automatically
• 🚫 Prevents duplicate posts

━━━━━━━━━━━━━━━━━━━━━━

**Manage Your Channel:**
• /mychannels - View all your channels
• /channelstatus {channel_id} - Check status

━━━━━━━━━━━━━━━━━━━━━━

💡 **Important:** Make sure the bot is added to your channel as an admin with "Post Messages" permission!
            """

            await update.message.reply_text(message, parse_mode='Markdown')

            # Log analytics
            if self.analytics_service:
                await self.analytics_service.log_command(
                    update.effective_user.id,
                    "register_channel",
                    {"channel_id": channel_id, "channel_name": channel_name}
                )

        except Exception as e:
            logger.error(f"Error in handle_register_channel: {e}", exc_info=True)
            await update.message.reply_text(
                "❌ An error occurred while registering your channel. Please try again later."
            )

    async def handle_my_channels(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /mychannels command - List all channels owned by user."""

        try:
            # Must be in private chat
            if update.effective_chat.type != 'private':
                await update.message.reply_text(
                    "⚠️ This command only works in **private chat** with the bot.",
                    parse_mode='Markdown'
                )
                return

            user_id = update.effective_user.id

            # Get all groups/channels created by this user
            group_repo = self.user_service.group_repo

            # Query groups by creator_user_id using the repository's db connection
            import sqlite3
            conn = sqlite3.connect('bot_database.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT g.group_id, g.group_name, g.subscription_status, g.is_active,
                       s.subscription_end_date, s.trial_end_date
                FROM groups g
                LEFT JOIN subscriptions s ON g.group_id = s.group_id
                WHERE g.creator_user_id = ?
                ORDER BY g.created_at DESC
            """, (user_id,))

            channels = cursor.fetchall()
            conn.close()

            if not channels:
                message = """
📺 **My Channels**

━━━━━━━━━━━━━━━━━━━━━━

You haven't registered any channels yet.

**To add a channel:**
1. Use /addchannel for instructions
2. Or use /registerchannel directly

━━━━━━━━━━━━━━━━━━━━━━

💡 **Tip:** You can manage unlimited channels with this bot!
                """
                await update.message.reply_text(message, parse_mode='Markdown')
                return

            # Build channels list
            from datetime import datetime
            now = datetime.now()

            message = "📺 **My Channels**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n"

            for idx, channel in enumerate(channels, 1):
                channel_id = channel['group_id']
                channel_name = channel['group_name']
                status = channel['subscription_status'] or 'unknown'
                is_active = channel['is_active']

                # Calculate days remaining
                end_date_str = channel['subscription_end_date'] or channel['trial_end_date']
                days_remaining = "N/A"

                if end_date_str:
                    try:
                        end_date = datetime.fromisoformat(end_date_str)
                        days_left = (end_date - now).days
                        days_remaining = f"{days_left} days" if days_left > 0 else "Expired"
                    except:
                        pass

                # Status emoji
                status_emoji = "✅" if is_active and status in ['trial', 'active'] else "❌"

                message += f"""
**{idx}. {channel_name}**
{status_emoji} Status: {status.upper()}
🆔 ID: `{channel_id}`
⏰ Expires: {days_remaining}

"""

            message += """━━━━━━━━━━━━━━━━━━━━━━

**Commands:**
• /channelstatus <id> - View details
• /addchannel - Add new channel

💡 **Tip:** Copy the channel ID to use in other commands
            """

            await update.message.reply_text(message, parse_mode='Markdown')

        except Exception as e:
            logger.error(f"Error in handle_my_channels: {e}", exc_info=True)
            await update.message.reply_text(
                "❌ An error occurred while fetching your channels. Please try again later."
            )

    async def handle_channel_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /channelstatus command - Show detailed status of a channel."""

        try:
            # Must be in private chat
            if update.effective_chat.type != 'private':
                await update.message.reply_text(
                    "⚠️ This command only works in **private chat** with the bot.",
                    parse_mode='Markdown'
                )
                return

            # Check arguments
            if not context.args:
                await update.message.reply_text(
                    "❌ **Missing channel ID**\n\n"
                    "**Usage:**\n"
                    "`/channelstatus <channel_id>`\n\n"
                    "**Example:**\n"
                    "`/channelstatus -1001234567890`\n\n"
                    "💡 Use /mychannels to see all your channel IDs",
                    parse_mode='Markdown'
                )
                return

            try:
                channel_id = int(context.args[0])
            except ValueError:
                await update.message.reply_text(
                    "❌ **Invalid channel ID**\n\n"
                    "Channel ID must be a number.",
                    parse_mode='Markdown'
                )
                return

            # Get channel and subscription info
            if self.subscription_service:
                status = await self.subscription_service.get_subscription_status(channel_id)

                if not status['has_subscription']:
                    await update.message.reply_text(
                        f"❌ **Channel Not Found**\n\n"
                        f"Channel ID `{channel_id}` is not registered.\n\n"
                        f"Use /mychannels to see your registered channels.",
                        parse_mode='Markdown'
                    )
                    return

                # Build status message
                from datetime import datetime

                subscription_status = status.get('status', 'unknown')
                is_trial = subscription_status == 'trial'

                # Calculate days remaining
                if is_trial:
                    days_remaining = status.get('trial_days_left', 0)
                else:
                    days_remaining = status.get('subscription_days_left', 0)

                posting_allowed = status['posting_allowed']

                status_emoji = "✅" if posting_allowed else "❌"

                message = f"""
📺 **Channel Status**

━━━━━━━━━━━━━━━━━━━━━━

🆔 **Channel ID:** `{channel_id}`
{status_emoji} **Status:** {subscription_status.upper()}
📅 **Type:** {'Trial' if is_trial else 'Paid Subscription'}
⏰ **Days Remaining:** {days_remaining}
🚀 **Posting:** {'Enabled' if posting_allowed else 'Disabled'}

━━━━━━━━━━━━━━━━━━━━━━
"""

                if not posting_allowed:
                    message += f"""
⚠️ **Action Required**

Your subscription has expired. To resume posting:

Use this command to renew:
`/renewchannel {channel_id}`

━━━━━━━━━━━━━━━━━━━━━━
"""
                else:
                    message += """
✅ **Everything is working!**

The bot is actively monitoring and posting news to your channel.

━━━━━━━━━━━━━━━━━━━━━━
"""

                await update.message.reply_text(message, parse_mode='Markdown')

        except Exception as e:
            logger.error(f"Error in handle_channel_status: {e}", exc_info=True)
            await update.message.reply_text(
                "❌ An error occurred while checking channel status. Please try again later."
            )

    async def handle_renew_channel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /renewchannel command - Renew channel subscription (private chat only)."""

        try:
            # Must be in private chat
            if update.effective_chat.type != 'private':
                await update.message.reply_text(
                    "⚠️ This command only works in **private chat** with the bot.\n\n"
                    "Please message me directly.",
                    parse_mode='Markdown'
                )
                return

            # Check if services are available
            if not self.subscription_service or not self.payment_service:
                await update.message.reply_text(
                    "❌ Payment service is not available.",
                    parse_mode='Markdown'
                )
                return

            # Check arguments
            if not context.args:
                await update.message.reply_text(
                    "❌ **Missing channel ID**\n\n"
                    "**Usage:**\n"
                    "`/renewchannel <channel_id>`\n\n"
                    "**Example:**\n"
                    "`/renewchannel -1001234567890`\n\n"
                    "💡 Use /mychannels to see all your channel IDs",
                    parse_mode='Markdown'
                )
                return

            try:
                channel_id = int(context.args[0])
            except ValueError:
                await update.message.reply_text(
                    "❌ **Invalid channel ID**\n\n"
                    "Channel ID must be a number.",
                    parse_mode='Markdown'
                )
                return

            # Get subscription
            subscription = await self.subscription_service.get_subscription(channel_id)

            if not subscription:
                await update.message.reply_text(
                    f"❌ **Channel Not Found**\n\n"
                    f"Channel ID `{channel_id}` is not registered.\n\n"
                    f"Use /mychannels to see your registered channels.",
                    parse_mode='Markdown'
                )
                return

            # Verify ownership (check if user is the creator)
            user_id = update.effective_user.id

            # Query to check ownership
            import sqlite3
            conn = sqlite3.connect('bot_database.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT creator_user_id FROM groups WHERE group_id = ?
            """, (channel_id,))

            result = cursor.fetchone()
            conn.close()

            if not result or result['creator_user_id'] != user_id:
                await update.message.reply_text(
                    "❌ **Access Denied**\n\n"
                    "You can only renew channels that you own.\n\n"
                    "Use /mychannels to see your channels.",
                    parse_mode='Markdown'
                )
                return

            # Show renewal options with currency selection
            message = f"""
💳 **Renew Channel Subscription**

━━━━━━━━━━━━━━━━━━━━━━

**Channel ID:** `{channel_id}`
**Plan:** Monthly Subscription
**Price:** $15.00 USD/month

**What you get:**
• 24/7 real-time crypto news
• AI-powered market analysis
• Multi-source aggregation
• Trader-specific insights
• Priority support

━━━━━━━━━━━━━━━━━━━━━━

**Choose your payment method:**
            """

            # Get available currencies
            currencies = await self.payment_service.get_available_currencies()

            # Create currency buttons (2 per row)
            keyboard = []
            row = []

            currency_labels = {
                'btc': '₿ Bitcoin',
                'eth': 'Ξ Ethereum',
                'usdt': '₮ USDT',
                'usdc': '$ USDC',
                'bnb': '🔶 BNB',
                'trx': '⚡ TRON'
            }

            for currency in currencies[:6]:  # Limit to 6 currencies
                label = currency_labels.get(currency.lower(), currency.upper())
                row.append(
                    InlineKeyboardButton(
                        label,
                        callback_data=f"pay_{currency}_{subscription['subscription_id']}"
                    )
                )

                if len(row) == 2:
                    keyboard.append(row)
                    row = []

            if row:  # Add remaining button
                keyboard.append(row)

            # Add cancel button
            keyboard.append([
                InlineKeyboardButton(
                    "❌ Cancel",
                    callback_data="cancel_renewal"
                )
            ])

            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

            # Log analytics
            if self.analytics_service:
                await self.analytics_service.log_command(
                    update.effective_user.id,
                    "renew_channel",
                    {"channel_id": channel_id, "subscription_id": subscription['subscription_id']}
                )

        except Exception as e:
            logger.error(f"Error in handle_renew_channel: {e}", exc_info=True)
            await update.message.reply_text(
                "❌ Error processing renewal request. Please try again later.",
                parse_mode='Markdown'
            )

    async def handle_channel_setup_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle 'Add My Channel' button callback."""

        query = update.callback_query
        await query.answer()

        try:
            message = """
📺 **Add Your Telegram Channel**

━━━━━━━━━━━━━━━━━━━━━━

**Step 1: Add Bot to Your Channel**

1. Open your Telegram channel
2. Tap the channel name → "Administrators"
3. Add this bot as administrator
4. Enable "Post Messages" permission ✅

━━━━━━━━━━━━━━━━━━━━━━

**Step 2: Get Your Channel ID**

Forward any message from your channel to:
• @userinfobot
• @getidsbot

You'll get an ID like: `-1001234567890`

━━━━━━━━━━━━━━━━━━━━━━

**Step 3: Register Your Channel**

Send this command (replace with your details):

`/registerchannel -1001234567890 My Channel Name`

━━━━━━━━━━━━━━━━━━━━━━

**Quick Commands:**

• /addchannel - Detailed guide
• /mychannels - View all channels
• /channelstatus <id> - Check status

━━━━━━━━━━━━━━━━━━━━━━

💡 **Note:** Channels are different from groups. You must use these commands in **private chat** with me!
            """

            keyboard = [
                [
                    InlineKeyboardButton(
                        "📖 Detailed Guide",
                        callback_data="show_detailed_channel_guide"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🔙 Back to Start",
                        callback_data="back_to_start"
                    )
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

        except Exception as e:
            logger.error(f"Error in handle_channel_setup_callback: {e}", exc_info=True)
            await query.edit_message_text(
                "❌ An error occurred. Please try /addchannel for help."
            )

    async def handle_detailed_channel_guide_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle 'Detailed Guide' button for channel setup."""

        query = update.callback_query
        await query.answer()

        try:
            message = """
📺 **Complete Channel Setup Guide**

━━━━━━━━━━━━━━━━━━━━━━

**🔍 What's the Difference?**

**Groups:**
• Two-way communication
• Commands work (/start, /setup)
• Use /setup in the group

**Channels:**
• One-way broadcast only
• Commands DON'T work
• Must register via private chat

━━━━━━━━━━━━━━━━━━━━━━

**📋 Channel Setup Steps:**

**1️⃣ Add Bot as Admin**
   • Open your channel
   • Settings → Administrators
   • Add this bot
   • Enable "Post Messages" ✅

**2️⃣ Get Channel ID**
   • Forward message to @userinfobot
   • Copy the ID (e.g., -1001234567890)

**3️⃣ Register Channel**
   • Come back to this chat
   • Send: `/registerchannel <id> <name>`
   • Example: `/registerchannel -1001234567890 My News`

**4️⃣ Verify Setup**
   • Use: `/mychannels`
   • Check status: `/channelstatus <id>`

━━━━━━━━━━━━━━━━━━━━━━

**🚀 After Setup:**

✅ Bot monitors crypto news 24/7
✅ AI analyzes importance (0-10)
✅ Auto-posts high-impact news (≥7)
✅ No duplicate posts
✅ Fully automated!

━━━━━━━━━━━━━━━━━━━━━━

**💡 Trial:** 15 days free for each channel

Ready to register? Send:
`/registerchannel <your_channel_id> <name>`
            """

            keyboard = [
                [
                    InlineKeyboardButton(
                        "🔙 Back",
                        callback_data="show_channel_setup"
                    )
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

        except Exception as e:
            logger.error(f"Error in handle_detailed_channel_guide_callback: {e}", exc_info=True)
            await query.edit_message_text(
                "❌ An error occurred. Please try /addchannel for help."
            )
