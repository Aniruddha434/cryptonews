"""
Configuration module for AI Market Insight Bot.
Loads environment variables and provides configuration constants.
"""

import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================================================================
# TELEGRAM CONFIGURATION
# ============================================================================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "")

# Admin user IDs (comma-separated in .env)
ADMIN_USER_IDS_STR = os.getenv("ADMIN_USER_IDS", "")
ADMIN_USER_IDS = [int(uid.strip()) for uid in ADMIN_USER_IDS_STR.split(",") if uid.strip()]

# ============================================================================
# NEWS API CONFIGURATION
# ============================================================================
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")
CRYPTOPANIC_API_KEY = os.getenv("CRYPTOPANIC_API_KEY", "")
CRYPTOCOMPARE_API_KEY = os.getenv("CRYPTOCOMPARE_API_KEY", "")  # Free tier: 50k calls/month

# ============================================================================
# GOOGLE GEMINI CONFIGURATION
# ============================================================================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# ============================================================================
# SCHEDULER CONFIGURATION
# ============================================================================
POSTING_HOUR = int(os.getenv("POSTING_HOUR", "9"))
POSTING_MINUTE = int(os.getenv("POSTING_MINUTE", "0"))
TIMEZONE = os.getenv("TIMEZONE", "UTC")

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================
# Support both DATABASE_URL (PostgreSQL on Render) and DATABASE_PATH (SQLite local)
DATABASE_URL = os.getenv("DATABASE_URL")
DATABASE_PATH = os.getenv("DATABASE_PATH", "./bot_database.db")

# Detect production environment
IS_PRODUCTION = DATABASE_URL is not None and DATABASE_URL.startswith(('postgresql://', 'postgres://'))

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Note: Logging is configured in bot.py to ensure proper UTF-8 encoding support
logger = logging.getLogger(__name__)

# ============================================================================
# VALIDATION
# ============================================================================
def validate_config():
    """Validate that all required configuration is present."""
    missing_keys = []
    
    if not TELEGRAM_BOT_TOKEN:
        missing_keys.append("TELEGRAM_BOT_TOKEN")
    if not TELEGRAM_CHANNEL_ID:
        missing_keys.append("TELEGRAM_CHANNEL_ID")
    
    if missing_keys:
        logger.warning(f"Missing required configuration: {', '.join(missing_keys)}")
        logger.warning("Please add these to your .env file")
        return False
    
    return True

# ============================================================================
# TRADER TYPES
# ============================================================================
TRADER_TYPES = {
    "scalper": "Scalper",
    "day_trader": "Day Trader",
    "swing_trader": "Swing Trader",
    "investor": "Investor"
}

# ============================================================================
# API ENDPOINTS
# ============================================================================
NEWSAPI_ENDPOINT = "https://newsapi.org/v2/everything"
CRYPTOPANIC_ENDPOINT = "https://cryptopanic.com/api/developer/v2/posts/"
CRYPTOCOMPARE_NEWS_ENDPOINT = "https://min-api.cryptocompare.com/data/v2/news/"
COINGECKO_NEWS_ENDPOINT = "https://api.coingecko.com/api/v3/news"

# ============================================================================
# REAL-TIME NEWS MONITORING CONFIGURATION
# ============================================================================
# Check for hot news every N minutes
NEWS_CHECK_INTERVAL_MINUTES = int(os.getenv("NEWS_CHECK_INTERVAL_MINUTES", "5"))

# Minimum importance score to post news immediately (0-10 scale)
MIN_IMPORTANCE_SCORE = int(os.getenv("MIN_IMPORTANCE_SCORE", "7"))

# Enable real-time hot news posting (24/7 monitoring)
ENABLE_REALTIME_POSTING = os.getenv("ENABLE_REALTIME_POSTING", "true").lower() == "true"

# Filters for hot news
HOT_NEWS_FILTERS = {
    "important": True,  # Only important news
    "min_votes": 5,     # Minimum votes/engagement
}

# ============================================================================
# SUBSCRIPTION & PAYMENT CONFIGURATION
# ============================================================================
# Trial period
TRIAL_DAYS = int(os.getenv("TRIAL_DAYS", "15"))

# Subscription pricing
SUBSCRIPTION_PRICE_USD = float(os.getenv("SUBSCRIPTION_PRICE_USD", "15.00"))

# Trial abuse prevention
TRIAL_COOLDOWN_DAYS = int(os.getenv("TRIAL_COOLDOWN_DAYS", "30"))
MAX_TRIALS_PER_CREATOR = int(os.getenv("MAX_TRIALS_PER_CREATOR", "3"))

# Grace period after subscription expires
GRACE_PERIOD_DAYS = int(os.getenv("GRACE_PERIOD_DAYS", "3"))

# NOWPayments API Configuration
NOWPAYMENTS_API_KEY = os.getenv("NOWPAYMENTS_API_KEY", "")
NOWPAYMENTS_IPN_SECRET = os.getenv("NOWPAYMENTS_IPN_SECRET", "")
NOWPAYMENTS_API_URL = os.getenv("NOWPAYMENTS_API_URL", "https://api.nowpayments.io/v1")

# Supported cryptocurrencies (comma-separated)
SUPPORTED_CURRENCIES_STR = os.getenv("SUPPORTED_CURRENCIES", "btc,eth,usdt,usdc,bnb,trx")
SUPPORTED_CURRENCIES = [c.strip().lower() for c in SUPPORTED_CURRENCIES_STR.split(",") if c.strip()]

# Payment invoice expiration (in minutes)
PAYMENT_INVOICE_EXPIRATION_MINUTES = int(os.getenv("PAYMENT_INVOICE_EXPIRATION_MINUTES", "60"))

# Webhook URL for payment notifications
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")

# Webhook server port
# Use Render's PORT env var if available (for web services), otherwise use WEBHOOK_PORT
WEBHOOK_PORT = int(os.getenv("PORT", os.getenv("WEBHOOK_PORT", "8080")))
