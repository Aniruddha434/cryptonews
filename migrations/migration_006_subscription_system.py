"""
Migration 006: Subscription System
Adds tables for subscription management and payment processing.
Supports both SQLite and PostgreSQL via DatabaseAdapter.
"""

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

