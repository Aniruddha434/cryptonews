"""
Database migration system for AI Market Insight Bot.
Manages schema versioning and upgrades.
Supports both SQLite and PostgreSQL.
"""

import logging
import os
from datetime import datetime
from db_pool import get_pool

logger = logging.getLogger(__name__)


class MigrationManager:
    """Manages database migrations and schema versioning."""

    def __init__(self):
        """Initialize migration manager."""
        self.pool = get_pool()
        self.is_postgres = self.pool.adapter.is_postgres
        self.init_migrations_table()

    def get_placeholder(self):
        """Get SQL parameter placeholder."""
        return "%s" if self.is_postgres else "?"
    
    def init_migrations_table(self):
        """Initialize migrations tracking table."""
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()

                if self.is_postgres:
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS migrations (
                            id SERIAL PRIMARY KEY,
                            name TEXT UNIQUE,
                            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                else:
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS migrations (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT UNIQUE,
                            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)

            logger.info("Migrations table initialized")
        except Exception as e:
            logger.error(f"Error initializing migrations table: {e}")
    
    def get_applied_migrations(self):
        """Get list of applied migrations."""
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("SELECT name FROM migrations ORDER BY applied_at")
                results = cursor.fetchall()

                if self.is_postgres:
                    return [r['name'] for r in results]
                else:
                    return [r[0] for r in results]
        except Exception as e:
            logger.error(f"Error getting applied migrations: {e}")
            return []
    
    def record_migration(self, name):
        """Record a migration as applied."""
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()

                placeholder = self.get_placeholder()
                cursor.execute(f"INSERT INTO migrations (name) VALUES ({placeholder})", (name,))

            logger.info(f"Migration recorded: {name}")
        except Exception as e:
            logger.error(f"Error recording migration: {e}")
    
    def apply_migration(self, name, sql_statements):
        """Apply a migration."""
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()

                # Execute all SQL statements
                for statement in sql_statements:
                    if statement.strip():
                        # Adapt statement for PostgreSQL if needed
                        adapted_statement = self._adapt_sql(statement)
                        cursor.execute(adapted_statement)

            self.record_migration(name)
            logger.info(f"Migration applied: {name}")
            return True
        except Exception as e:
            logger.error(f"Error applying migration {name}: {e}")
            return False

    def _adapt_sql(self, sql: str) -> str:
        """Adapt SQL statement for current database type."""
        if self.is_postgres:
            # Convert SQLite syntax to PostgreSQL
            sql = sql.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
            sql = sql.replace("AUTOINCREMENT", "")
            sql = sql.replace("BOOLEAN DEFAULT 1", "BOOLEAN DEFAULT TRUE")
            sql = sql.replace("BOOLEAN DEFAULT 0", "BOOLEAN DEFAULT FALSE")
        return sql
    
    def run_pending_migrations(self):
        """Run all pending migrations."""
        applied = self.get_applied_migrations()

        # Define all available migrations
        migrations = {
            "001_initial_schema": MIGRATION_001,
            "002_add_analytics_tables": MIGRATION_002,
            "003_add_backup_tables": MIGRATION_003,
            "004_add_groups_columns": MIGRATION_004,
            "005_add_news_cache_columns": MIGRATION_005,
            "006_subscription_system": MIGRATION_006,
        }

        for name, sql_statements in migrations.items():
            if name not in applied:
                logger.info(f"Running migration: {name}")
                self.apply_migration(name, sql_statements)
            else:
                logger.debug(f"Migration already applied: {name}")


# Migration 001: Initial schema - Base tables
MIGRATION_001 = [
    # Users table
    """
    CREATE TABLE IF NOT EXISTS users (
        chat_id INTEGER PRIMARY KEY,
        trader_type TEXT DEFAULT 'investor',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,

    # Groups table (base version - migrations 004 and 006 will add more columns)
    """
    CREATE TABLE IF NOT EXISTS groups (
        group_id INTEGER PRIMARY KEY,
        group_name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,

    # News cache table (base version - migration 005 will add more columns)
    """
    CREATE TABLE IF NOT EXISTS news_cache (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        article_url TEXT,
        title TEXT,
        summary TEXT,
        cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,

    # Command logs table
    """
    CREATE TABLE IF NOT EXISTS command_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        chat_id INTEGER,
        command TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        success BOOLEAN DEFAULT 1,
        error_message TEXT
    )
    """,

    # Indexes for base tables
    "CREATE INDEX IF NOT EXISTS idx_users_trader_type ON users(trader_type)",
    "CREATE INDEX IF NOT EXISTS idx_groups_name ON groups(group_name)",
    "CREATE INDEX IF NOT EXISTS idx_news_cache_url ON news_cache(article_url)",
    "CREATE INDEX IF NOT EXISTS idx_news_cache_cached ON news_cache(cached_at)",
    "CREATE INDEX IF NOT EXISTS idx_command_logs_user ON command_logs(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_command_logs_timestamp ON command_logs(timestamp)",
]

# Migration 002: Add analytics tables
MIGRATION_002 = [
    """
    CREATE TABLE IF NOT EXISTS user_activity (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        details TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS group_activity (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id INTEGER,
        action TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        details TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS daily_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE UNIQUE,
        messages_processed INTEGER DEFAULT 0,
        groups_posted INTEGER DEFAULT 0,
        api_calls INTEGER DEFAULT 0,
        errors INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_user_activity_user ON user_activity(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_group_activity_group ON group_activity(group_id)",
    "CREATE INDEX IF NOT EXISTS idx_daily_stats_date ON daily_stats(date)",
]

# Migration 003: Add backup and recovery tables
MIGRATION_003 = [
    """
    CREATE TABLE IF NOT EXISTS backups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        backup_name TEXT UNIQUE,
        backup_path TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        size_bytes INTEGER,
        status TEXT DEFAULT 'completed'
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS backup_metadata (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        backup_id INTEGER,
        key TEXT,
        value TEXT,
        FOREIGN KEY (backup_id) REFERENCES backups(id)
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_backups_created ON backups(created_at)",
]

# Migration 004: Add missing columns to groups table
MIGRATION_004 = [
    # Add posting_time column
    """
    ALTER TABLE groups ADD COLUMN posting_time TEXT DEFAULT '09:00'
    """,
    # Add trader_type column
    """
    ALTER TABLE groups ADD COLUMN trader_type TEXT DEFAULT 'investor'
    """,
    # Add is_active column
    """
    ALTER TABLE groups ADD COLUMN is_active BOOLEAN DEFAULT 1
    """,
    # Add last_post column
    """
    ALTER TABLE groups ADD COLUMN last_post TIMESTAMP
    """,
    # Note: Removed UPDATE statement for posting_enabled column
    # (column doesn't exist in fresh deployments, is_active already has DEFAULT 1)
]

# Migration 005: Add missing columns to news_cache table
MIGRATION_005 = [
    # Add url column
    """
    ALTER TABLE news_cache ADD COLUMN url TEXT
    """,
    # Add analysis column
    """
    ALTER TABLE news_cache ADD COLUMN analysis TEXT
    """,
    # Add trader_type column
    """
    ALTER TABLE news_cache ADD COLUMN trader_type TEXT DEFAULT 'investor'
    """,
    # Add created_at column
    """
    ALTER TABLE news_cache ADD COLUMN created_at TIMESTAMP
    """,
    # Add expires_at column
    """
    ALTER TABLE news_cache ADD COLUMN expires_at TIMESTAMP
    """,
    # Migrate data from article_url to url
    """
    UPDATE news_cache SET url = article_url WHERE article_url IS NOT NULL
    """,
    # Migrate data from cached_at to created_at
    """
    UPDATE news_cache SET created_at = cached_at WHERE cached_at IS NOT NULL
    """,
    # Set expires_at to created_at + 24 hours (using datetime function)
    """
    UPDATE news_cache SET expires_at = datetime(created_at, '+24 hours') WHERE created_at IS NOT NULL
    """,
]

# Migration 006: Subscription System
MIGRATION_006 = [
    # Subscriptions table
    """
    CREATE TABLE IF NOT EXISTS subscriptions (
        subscription_id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id INTEGER NOT NULL UNIQUE,
        subscription_status TEXT NOT NULL,
        trial_start_date TIMESTAMP NOT NULL,
        trial_end_date TIMESTAMP NOT NULL,
        subscription_start_date TIMESTAMP,
        subscription_end_date TIMESTAMP,
        next_billing_date TIMESTAMP,
        grace_period_end TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (group_id) REFERENCES groups(group_id) ON DELETE CASCADE
    )
    """,

    # Payments table
    """
    CREATE TABLE IF NOT EXISTS payments (
        payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        subscription_id INTEGER NOT NULL,
        group_id INTEGER NOT NULL,
        amount_usd DECIMAL(10, 2) NOT NULL,
        amount_crypto DECIMAL(20, 8),
        currency TEXT NOT NULL,
        payment_address TEXT,
        payment_status TEXT NOT NULL,
        payment_url TEXT,
        invoice_id TEXT UNIQUE,
        payment_id_external TEXT,
        transaction_hash TEXT,
        confirmations INTEGER DEFAULT 0,
        required_confirmations INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        confirmed_at TIMESTAMP,
        expires_at TIMESTAMP,
        webhook_data TEXT,
        FOREIGN KEY (subscription_id) REFERENCES subscriptions(subscription_id) ON DELETE CASCADE,
        FOREIGN KEY (group_id) REFERENCES groups(group_id) ON DELETE CASCADE
    )
    """,

    # Subscription events table (audit log)
    """
    CREATE TABLE IF NOT EXISTS subscription_events (
        event_id INTEGER PRIMARY KEY AUTOINCREMENT,
        subscription_id INTEGER NOT NULL,
        group_id INTEGER NOT NULL,
        event_type TEXT NOT NULL,
        event_data TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (subscription_id) REFERENCES subscriptions(subscription_id) ON DELETE CASCADE
    )
    """,

    # Trial abuse tracking
    """
    CREATE TABLE IF NOT EXISTS trial_abuse_tracking (
        tracking_id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id INTEGER NOT NULL,
        group_title_hash TEXT NOT NULL,
        creator_user_id INTEGER,
        trial_started_at TIMESTAMP NOT NULL,
        is_flagged BOOLEAN DEFAULT 0,
        flag_reason TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,

    # Indexes for subscriptions table
    "CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(subscription_status)",
    "CREATE INDEX IF NOT EXISTS idx_subscriptions_group ON subscriptions(group_id)",
    "CREATE INDEX IF NOT EXISTS idx_subscriptions_trial_end ON subscriptions(trial_end_date)",
    "CREATE INDEX IF NOT EXISTS idx_subscriptions_sub_end ON subscriptions(subscription_end_date)",
    "CREATE INDEX IF NOT EXISTS idx_subscriptions_next_billing ON subscriptions(next_billing_date)",

    # Indexes for payments table
    "CREATE INDEX IF NOT EXISTS idx_payments_subscription ON payments(subscription_id)",
    "CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(payment_status)",
    "CREATE INDEX IF NOT EXISTS idx_payments_invoice ON payments(invoice_id)",
    "CREATE INDEX IF NOT EXISTS idx_payments_created ON payments(created_at)",
    "CREATE INDEX IF NOT EXISTS idx_payments_group ON payments(group_id)",

    # Indexes for events table
    "CREATE INDEX IF NOT EXISTS idx_events_subscription ON subscription_events(subscription_id)",
    "CREATE INDEX IF NOT EXISTS idx_events_type ON subscription_events(event_type)",
    "CREATE INDEX IF NOT EXISTS idx_events_created ON subscription_events(created_at)",
    "CREATE INDEX IF NOT EXISTS idx_events_group ON subscription_events(group_id)",

    # Indexes for abuse tracking
    "CREATE INDEX IF NOT EXISTS idx_abuse_group ON trial_abuse_tracking(group_id)",
    "CREATE INDEX IF NOT EXISTS idx_abuse_creator ON trial_abuse_tracking(creator_user_id)",
    "CREATE INDEX IF NOT EXISTS idx_abuse_hash ON trial_abuse_tracking(group_title_hash)",
    "CREATE INDEX IF NOT EXISTS idx_abuse_flagged ON trial_abuse_tracking(is_flagged)",

    # Add subscription columns to groups table
    """
    ALTER TABLE groups ADD COLUMN subscription_id INTEGER
    """,
    """
    ALTER TABLE groups ADD COLUMN subscription_status TEXT DEFAULT 'trial'
    """,
    """
    ALTER TABLE groups ADD COLUMN trial_ends_at TIMESTAMP
    """,
]


def run_all_migrations():
    """Run all pending migrations."""
    manager = MigrationManager()
    manager.run_pending_migrations()
    logger.info("All migrations completed")

