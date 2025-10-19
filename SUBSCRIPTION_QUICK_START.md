# Subscription System - Quick Start Guide

## Overview

This guide will help you implement the subscription system in phases. Follow these steps to add cryptocurrency payment support to your Telegram bot.

---

## Prerequisites

### 1. NOWPayments Account Setup

**Step 1:** Sign up at [NOWPayments](https://nowpayments.io)

**Step 2:** Complete account verification
- Email verification
- Basic KYC (if required)

**Step 3:** Get API credentials
- Go to Settings → API Keys
- Copy your API Key
- Copy your IPN Secret
- Save both securely

**Step 4:** Configure webhook URL
- Go to Settings → IPN Settings
- Set IPN callback URL: `https://your-bot.onrender.com/webhook/nowpayments`
- Save settings

### 2. Environment Variables

Add to your `.env` file:

```bash
# NOWPayments Configuration
NOWPAYMENTS_API_KEY=your_api_key_here
NOWPAYMENTS_IPN_SECRET=your_ipn_secret_here
NOWPAYMENTS_SANDBOX=true  # Set to false for production

# Subscription Configuration
SUBSCRIPTION_PRICE_USD=15.00
TRIAL_DAYS=15
GRACE_PERIOD_DAYS=3

# Webhook Configuration
WEBHOOK_URL=https://your-bot.onrender.com
```

---

## Phase 1: Database Setup (Day 1-2)

### Step 1: Create Migration File

Create `migrations/migration_006_subscription_system.py`:

```python
"""
Migration 006: Subscription System
Adds tables for subscription management and payment processing.
"""

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
    
    # Subscription events table
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
    
    # Indexes
    "CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(subscription_status)",
    "CREATE INDEX IF NOT EXISTS idx_subscriptions_group ON subscriptions(group_id)",
    "CREATE INDEX IF NOT EXISTS idx_subscriptions_trial_end ON subscriptions(trial_end_date)",
    "CREATE INDEX IF NOT EXISTS idx_subscriptions_next_billing ON subscriptions(next_billing_date)",
    
    "CREATE INDEX IF NOT EXISTS idx_payments_subscription ON payments(subscription_id)",
    "CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(payment_status)",
    "CREATE INDEX IF NOT EXISTS idx_payments_invoice ON payments(invoice_id)",
    "CREATE INDEX IF NOT EXISTS idx_payments_created ON payments(created_at)",
    
    "CREATE INDEX IF NOT EXISTS idx_events_subscription ON subscription_events(subscription_id)",
    "CREATE INDEX IF NOT EXISTS idx_events_type ON subscription_events(event_type)",
    "CREATE INDEX IF NOT EXISTS idx_events_created ON subscription_events(created_at)",
    
    "CREATE INDEX IF NOT EXISTS idx_abuse_group ON trial_abuse_tracking(group_id)",
    "CREATE INDEX IF NOT EXISTS idx_abuse_creator ON trial_abuse_tracking(creator_user_id)",
    "CREATE INDEX IF NOT EXISTS idx_abuse_hash ON trial_abuse_tracking(group_title_hash)",
    
    # Modify groups table
    "ALTER TABLE groups ADD COLUMN subscription_id INTEGER",
    "ALTER TABLE groups ADD COLUMN subscription_status TEXT DEFAULT 'trial'",
    "ALTER TABLE groups ADD COLUMN trial_ends_at TIMESTAMP",
]
```

### Step 2: Add Migration to migrations.py

```python
from migrations.migration_006_subscription_system import MIGRATION_006

# Add to MIGRATIONS dict
MIGRATIONS = {
    "001_initial_schema": MIGRATION_001,
    "002_analytics_tables": MIGRATION_002,
    "003_backup_tables": MIGRATION_003,
    "004_groups_columns": MIGRATION_004,
    "005_command_logs": MIGRATION_005,
    "006_subscription_system": MIGRATION_006,  # NEW
}
```

### Step 3: Run Migration

```bash
python bot.py  # Migrations run automatically on startup
```

---

## Phase 2: Repositories (Day 2-3)

### Create SubscriptionRepository

Create `repositories/subscription_repository.py`:

```python
from repositories.base_repository import BaseRepository
from typing import Optional, List, Dict, Any
from datetime import datetime
import hashlib

class SubscriptionRepository(BaseRepository):
    """Repository for subscription operations."""
    
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new subscription."""
        query = """
            INSERT INTO subscriptions (
                group_id, subscription_status, trial_start_date,
                trial_end_date, subscription_start_date, subscription_end_date,
                next_billing_date, grace_period_end
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        await self.execute_query(query, (
            data['group_id'],
            data['subscription_status'],
            data['trial_start_date'],
            data['trial_end_date'],
            data.get('subscription_start_date'),
            data.get('subscription_end_date'),
            data.get('next_billing_date'),
            data.get('grace_period_end')
        ))
        
        return await self.find_by_group_id(data['group_id'])
    
    async def find_by_id(self, subscription_id: int) -> Optional[Dict[str, Any]]:
        """Find subscription by ID."""
        query = "SELECT * FROM subscriptions WHERE subscription_id = ?"
        return await self.execute_query(query, (subscription_id,), fetch_one=True)
    
    async def find_by_group_id(self, group_id: int) -> Optional[Dict[str, Any]]:
        """Find subscription by group ID."""
        query = "SELECT * FROM subscriptions WHERE group_id = ?"
        return await self.execute_query(query, (group_id,), fetch_one=True)
    
    async def update(self, subscription_id: int, data: Dict[str, Any]) -> bool:
        """Update subscription."""
        fields = []
        values = []
        
        for key, value in data.items():
            fields.append(f"{key} = ?")
            values.append(value)
        
        fields.append("updated_at = ?")
        values.append(datetime.now().isoformat())
        
        query = f"UPDATE subscriptions SET {', '.join(fields)} WHERE subscription_id = ?"
        values.append(subscription_id)
        
        await self.execute_query(query, tuple(values))
        return True
    
    async def find_expiring_trials(self, days: int) -> List[Dict[str, Any]]:
        """Find trials expiring in N days."""
        query = """
            SELECT * FROM subscriptions
            WHERE subscription_status = 'trial'
            AND trial_end_date BETWEEN datetime('now') AND datetime('now', '+' || ? || ' days')
        """
        return await self.execute_query(query, (days,), fetch_all=True)
    
    async def find_expired_subscriptions(self) -> List[Dict[str, Any]]:
        """Find expired subscriptions."""
        query = """
            SELECT * FROM subscriptions
            WHERE subscription_status = 'active'
            AND subscription_end_date < datetime('now')
        """
        return await self.execute_query(query, fetch_all=True)
```

### Create PaymentRepository

Create `repositories/payment_repository.py`:

```python
from repositories.base_repository import BaseRepository
from typing import Optional, List, Dict, Any

class PaymentRepository(BaseRepository):
    """Repository for payment operations."""
    
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new payment."""
        query = """
            INSERT INTO payments (
                subscription_id, group_id, amount_usd, amount_crypto,
                currency, payment_address, payment_status, payment_url,
                invoice_id, payment_id_external, expires_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        await self.execute_query(query, (
            data['subscription_id'],
            data['group_id'],
            data['amount_usd'],
            data.get('amount_crypto'),
            data['currency'],
            data.get('payment_address'),
            data['payment_status'],
            data.get('payment_url'),
            data.get('invoice_id'),
            data.get('payment_id_external'),
            data.get('expires_at')
        ))
        
        return await self.find_by_invoice_id(data['invoice_id'])
    
    async def find_by_id(self, payment_id: int) -> Optional[Dict[str, Any]]:
        """Find payment by ID."""
        query = "SELECT * FROM payments WHERE payment_id = ?"
        return await self.execute_query(query, (payment_id,), fetch_one=True)
    
    async def find_by_invoice_id(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        """Find payment by invoice ID."""
        query = "SELECT * FROM payments WHERE invoice_id = ?"
        return await self.execute_query(query, (invoice_id,), fetch_one=True)
    
    async def update(self, payment_id: int, data: Dict[str, Any]) -> bool:
        """Update payment."""
        fields = []
        values = []
        
        for key, value in data.items():
            fields.append(f"{key} = ?")
            values.append(value)
        
        query = f"UPDATE payments SET {', '.join(fields)} WHERE payment_id = ?"
        values.append(payment_id)
        
        await self.execute_query(query, tuple(values))
        return True
```

---

## Phase 3: Core Services (Day 3-5)

See `SUBSCRIPTION_ARCHITECTURE.md` for complete service implementations.

**Files to create:**
1. `services/subscription_service.py`
2. `services/payment_service.py`
3. `services/notification_service.py`
4. `services/subscription_checker_service.py`

---

## Phase 4: Bot Commands (Day 5-7)

### Add Subscription Commands

Update `handlers/user_handlers.py`:

```python
async def subscription_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show subscription status."""
    group_id = update.effective_chat.id
    
    subscription = await self.subscription_service.get_subscription(group_id)
    
    if not subscription:
        await update.message.reply_text("No subscription found.")
        return
    
    status = subscription['subscription_status']
    
    if status == 'trial':
        days_left = (subscription['trial_end_date'] - datetime.now()).days
        message = (
            f"🎁 **Trial Subscription**\n\n"
            f"⏰ Days remaining: {days_left}\n"
            f"📅 Trial ends: {subscription['trial_end_date'].strftime('%Y-%m-%d')}\n\n"
            f"💡 Use /renew to subscribe after trial"
        )
    elif status == 'active':
        days_left = (subscription['subscription_end_date'] - datetime.now()).days
        message = (
            f"✅ **Active Subscription**\n\n"
            f"⏰ Days remaining: {days_left}\n"
            f"📅 Renews: {subscription['subscription_end_date'].strftime('%Y-%m-%d')}\n\n"
            f"💡 Use /renew to extend subscription"
        )
    else:
        message = (
            f"❌ **Subscription Expired**\n\n"
            f"💡 Use /renew to reactivate"
        )
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def renew_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate payment link for renewal."""
    group_id = update.effective_chat.id
    
    # Get subscription
    subscription = await self.subscription_service.get_subscription(group_id)
    
    if not subscription:
        await update.message.reply_text("No subscription found.")
        return
    
    # Create payment invoice
    payment = await self.payment_service.create_payment_invoice(
        subscription['subscription_id'],
        15.00,  # $15 USD
        'USDT'  # Default currency
    )
    
    if not payment:
        await update.message.reply_text("Failed to create payment. Please try again.")
        return
    
    message = (
        f"💳 **Payment Information**\n\n"
        f"Amount: $15.00 USD\n"
        f"Currency: USDT (Tether)\n\n"
        f"🔗 [Click here to pay]({payment['payment_url']})\n\n"
        f"⏰ Payment expires in 1 hour\n\n"
        f"💡 Other currencies available:\n"
        f"• Bitcoin (BTC)\n"
        f"• Ethereum (ETH)\n"
        f"• Litecoin (LTC)\n\n"
        f"Reply with currency code to change (e.g., 'BTC')"
    )
    
    await update.message.reply_text(message, parse_mode='Markdown')
```

---

## Phase 5: Webhook Handler (Day 7-8)

### Create Webhook Endpoint

Create `handlers/webhook_handler.py`:

```python
from aiohttp import web
import hmac
import hashlib
import json
import logging

logger = logging.getLogger(__name__)

class WebhookHandler:
    """Handle NOWPayments webhooks."""
    
    def __init__(self, payment_service):
        self.payment_service = payment_service
    
    async def handle_nowpayments_webhook(self, request):
        """Process NOWPayments IPN callback."""
        try:
            # Get signature
            signature = request.headers.get('x-nowpayments-sig')
            
            # Get payload
            payload = await request.text()
            
            # Verify signature
            if not await self.payment_service.verify_webhook_signature(payload, signature):
                logger.error("Invalid webhook signature")
                return web.Response(status=401, text="Invalid signature")
            
            # Parse data
            data = json.loads(payload)
            
            # Process webhook
            success = await self.payment_service.process_payment_webhook(data)
            
            if success:
                return web.Response(status=200, text="OK")
            else:
                return web.Response(status=500, text="Processing failed")
        
        except Exception as e:
            logger.error(f"Webhook error: {e}", exc_info=True)
            return web.Response(status=500, text="Internal error")

# Add to bot.py
async def setup_webhook_server(payment_service):
    """Set up webhook server."""
    app = web.Application()
    handler = WebhookHandler(payment_service)
    
    app.router.add_post('/webhook/nowpayments', handler.handle_nowpayments_webhook)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    
    logger.info("Webhook server started on port 8080")
```

---

## Testing Checklist

### Manual Testing

- [ ] Create trial subscription when bot added to group
- [ ] Check subscription status with `/subscription`
- [ ] Generate payment link with `/renew`
- [ ] Complete test payment in sandbox
- [ ] Verify webhook received and processed
- [ ] Confirm subscription activated
- [ ] Test trial expiration warnings
- [ ] Test grace period logic
- [ ] Test subscription expiration

### Automated Testing

- [ ] Unit tests for SubscriptionService
- [ ] Unit tests for PaymentService
- [ ] Integration test for payment flow
- [ ] Webhook signature verification test
- [ ] Trial abuse detection test

---

## Deployment

### Update render.yaml

```yaml
services:
  - type: worker
    name: cryptonews-bot
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python bot.py
    envVars:
      - key: NOWPAYMENTS_API_KEY
        sync: false
      - key: NOWPAYMENTS_IPN_SECRET
        sync: false
      - key: WEBHOOK_URL
        value: https://cryptonews-bot.onrender.com
```

### Deploy

```bash
git add .
git commit -m "Add subscription system"
git push origin main
```

---

## Go Live Checklist

- [ ] NOWPayments production API keys configured
- [ ] Webhook URL configured in NOWPayments dashboard
- [ ] Database migrations run successfully
- [ ] All services initialized
- [ ] Webhook endpoint accessible
- [ ] Test payment completed successfully
- [ ] Monitoring and alerts set up
- [ ] Terms of Service published
- [ ] Privacy Policy published
- [ ] Support contact available

---

**Congratulations!** Your subscription system is ready! 🎉

