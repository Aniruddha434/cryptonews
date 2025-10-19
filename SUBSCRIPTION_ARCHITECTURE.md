# Subscription System - Technical Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Telegram Bot                                 │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │   /start     │  │ /subscription│  │    /renew    │             │
│  │   /admin     │  │   /status    │  │   /cancel    │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Service Layer                                   │
│                                                                      │
│  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────────┐  │
│  │ Subscription     │  │  Payment         │  │  Notification   │  │
│  │ Service          │  │  Service         │  │  Service        │  │
│  └──────────────────┘  └──────────────────┘  └─────────────────┘  │
│                                                                      │
│  ┌──────────────────┐  ┌──────────────────┐                        │
│  │ Subscription     │  │  Webhook         │                        │
│  │ Checker Service  │  │  Handler         │                        │
│  └──────────────────┘  └──────────────────┘                        │
└─────────────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┼─────────────┐
                ▼             ▼             ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │PostgreSQL│  │NOWPayments│ │ Telegram │
        │ Database │  │    API    │  │   API    │
        └──────────┘  └──────────┘  └──────────┘
```

---

## Data Flow Diagrams

### 1. Trial Subscription Creation Flow

```
User adds bot to group
         │
         ▼
Check for existing subscription
         │
         ├─ Exists ──> Resume subscription
         │
         └─ New ──> Check trial abuse
                      │
                      ├─ Flagged ──> Reject + notify admin
                      │
                      └─ OK ──> Create trial subscription
                                 │
                                 ├─> Create subscription record
                                 ├─> Set trial_end_date (+15 days)
                                 ├─> Log event
                                 └─> Send welcome message
```

### 2. Payment Flow

```
User clicks /renew
         │
         ▼
Generate payment invoice (NOWPayments)
         │
         ├─> Create payment record (status: pending)
         ├─> Generate payment URL
         └─> Send payment instructions to group
                      │
                      ▼
User sends cryptocurrency
         │
         ▼
NOWPayments detects payment
         │
         ▼
Webhook sent to bot
         │
         ├─> Verify signature
         ├─> Validate payment
         └─> Update payment status
                      │
                      ├─ Confirming ──> Wait for confirmations
                      │                  │
                      │                  ▼
                      │            Confirmations complete
                      │                  │
                      └─────────────────>│
                                         ▼
                                  Activate subscription
                                         │
                                         ├─> Update subscription status
                                         ├─> Set subscription_end_date (+30 days)
                                         ├─> Log event
                                         └─> Send confirmation message
```

### 3. Subscription Expiration Flow

```
Background task runs daily
         │
         ▼
Check for expiring trials/subscriptions
         │
         ├─> 3 days before expiration
         │    └─> Send warning notification
         │
         ├─> 1 day before expiration
         │    └─> Send urgent warning
         │
         └─> Expired
              │
              ├─> Set status to 'grace_period'
              ├─> Set grace_period_end (+3 days)
              └─> Send expiration notice
                       │
                       ▼
              Grace period expires
                       │
                       ├─> Set status to 'expired'
                       ├─> Set is_active = 0
                       ├─> Log event
                       └─> Send final notice
```

---

## Service Specifications

### SubscriptionService

**File:** `services/subscription_service.py`

```python
class SubscriptionService:
    """
    Manages subscription lifecycle and validation.
    """
    
    def __init__(
        self,
        subscription_repo: SubscriptionRepository,
        payment_repo: PaymentRepository,
        group_repo: GroupRepository,
        notification_service: NotificationService,
        metrics: MetricsCollector
    ):
        self.subscription_repo = subscription_repo
        self.payment_repo = payment_repo
        self.group_repo = group_repo
        self.notification_service = notification_service
        self.metrics = metrics
        
        # Configuration
        self.TRIAL_DAYS = 15
        self.GRACE_PERIOD_DAYS = 3
        self.SUBSCRIPTION_PRICE_USD = 15.00
    
    async def create_trial_subscription(
        self,
        group_id: int,
        group_name: str,
        creator_user_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new trial subscription for a group.
        
        Checks for trial abuse before creating.
        """
        # Check for abuse
        is_abuse = await self.check_trial_abuse(
            group_id,
            group_name,
            creator_user_id
        )
        
        if is_abuse:
            logger.warning(f"Trial abuse detected for group {group_id}")
            return None
        
        # Calculate dates
        trial_start = datetime.now()
        trial_end = trial_start + timedelta(days=self.TRIAL_DAYS)
        
        # Create subscription
        subscription = await self.subscription_repo.create({
            'group_id': group_id,
            'subscription_status': 'trial',
            'trial_start_date': trial_start,
            'trial_end_date': trial_end
        })
        
        # Update group
        await self.group_repo.update(group_id, {
            'subscription_id': subscription['subscription_id'],
            'subscription_status': 'trial',
            'trial_ends_at': trial_end
        })
        
        # Log event
        await self.log_subscription_event(
            subscription['subscription_id'],
            'trial_started',
            {'group_name': group_name}
        )
        
        # Send welcome message
        await self.notification_service.send_trial_welcome(
            group_id,
            trial_end
        )
        
        self.metrics.inc_counter('trials_created')
        
        return subscription
    
    async def is_posting_allowed(self, group_id: int) -> bool:
        """
        Check if posting is allowed for a group.
        
        Returns True if:
        - Trial is active
        - Subscription is active
        - In grace period
        """
        subscription = await self.subscription_repo.find_by_group_id(group_id)
        
        if not subscription:
            return False
        
        status = subscription['subscription_status']
        now = datetime.now()
        
        # Active subscription
        if status == 'active':
            if subscription['subscription_end_date'] > now:
                return True
        
        # Active trial
        elif status == 'trial':
            if subscription['trial_end_date'] > now:
                return True
        
        # Grace period
        elif status == 'grace_period':
            if subscription['grace_period_end'] > now:
                return True
        
        return False
    
    async def activate_subscription(
        self,
        subscription_id: int,
        payment_id: int,
        months: int = 1
    ) -> bool:
        """
        Activate a subscription after payment confirmation.
        """
        subscription = await self.subscription_repo.find_by_id(subscription_id)
        
        if not subscription:
            return False
        
        # Calculate dates
        now = datetime.now()
        
        # If trial, start from trial end date
        if subscription['subscription_status'] == 'trial':
            start_date = subscription['trial_end_date']
        else:
            # Renewal - start from current end date or now
            if subscription['subscription_end_date'] and subscription['subscription_end_date'] > now:
                start_date = subscription['subscription_end_date']
            else:
                start_date = now
        
        end_date = start_date + timedelta(days=30 * months)
        next_billing = end_date - timedelta(days=7)  # Remind 7 days before
        
        # Update subscription
        await self.subscription_repo.update(subscription_id, {
            'subscription_status': 'active',
            'subscription_start_date': start_date,
            'subscription_end_date': end_date,
            'next_billing_date': next_billing
        })
        
        # Update group
        await self.group_repo.update(subscription['group_id'], {
            'subscription_status': 'active',
            'is_active': 1
        })
        
        # Log event
        await self.log_subscription_event(
            subscription_id,
            'subscription_activated',
            {'payment_id': payment_id, 'months': months}
        )
        
        # Send confirmation
        await self.notification_service.send_subscription_activated(
            subscription['group_id'],
            end_date
        )
        
        self.metrics.inc_counter('subscriptions_activated')
        
        return True
    
    async def check_trial_abuse(
        self,
        group_id: int,
        group_title: str,
        creator_user_id: int
    ) -> bool:
        """
        Check for trial abuse patterns.
        
        Returns True if abuse detected.
        """
        # Generate fingerprint
        fingerprint = hashlib.sha256(
            f"{group_id}:{group_title}".encode()
        ).hexdigest()
        
        # Check for existing trials with same fingerprint
        existing = await self.subscription_repo.find_by_fingerprint(fingerprint)
        
        if existing:
            # Check cooldown period (30 days)
            last_trial = existing[0]['trial_start_date']
            cooldown_end = last_trial + timedelta(days=30)
            
            if datetime.now() < cooldown_end:
                logger.warning(f"Trial abuse: Same fingerprint within cooldown")
                return True
        
        # Check trials by creator
        creator_trials = await self.subscription_repo.find_by_creator(creator_user_id)
        
        if len(creator_trials) >= 3:
            logger.warning(f"Trial abuse: Creator has {len(creator_trials)} trials")
            return True
        
        # Track this trial
        await self.subscription_repo.track_trial(
            group_id,
            fingerprint,
            creator_user_id
        )
        
        return False
```

### PaymentService

**File:** `services/payment_service.py`

```python
class PaymentService:
    """
    Handles payment processing with NOWPayments.
    """
    
    def __init__(
        self,
        payment_repo: PaymentRepository,
        subscription_service: SubscriptionService,
        metrics: MetricsCollector
    ):
        self.payment_repo = payment_repo
        self.subscription_service = subscription_service
        self.metrics = metrics
        
        # NOWPayments configuration
        self.api_key = os.getenv('NOWPAYMENTS_API_KEY')
        self.ipn_secret = os.getenv('NOWPAYMENTS_IPN_SECRET')
        self.api_url = 'https://api.nowpayments.io/v1'
        
        # Supported currencies
        self.supported_currencies = ['BTC', 'ETH', 'USDT', 'USDC', 'LTC']
    
    async def create_payment_invoice(
        self,
        subscription_id: int,
        amount_usd: float,
        currency: str = 'USDT'
    ) -> Optional[Dict[str, Any]]:
        """
        Create a payment invoice with NOWPayments.
        """
        if currency not in self.supported_currencies:
            logger.error(f"Unsupported currency: {currency}")
            return None
        
        subscription = await self.subscription_service.subscription_repo.find_by_id(
            subscription_id
        )
        
        if not subscription:
            return None
        
        # Create invoice via NOWPayments API
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    'x-api-key': self.api_key,
                    'Content-Type': 'application/json'
                }
                
                payload = {
                    'price_amount': amount_usd,
                    'price_currency': 'usd',
                    'pay_currency': currency.lower(),
                    'ipn_callback_url': f"{os.getenv('WEBHOOK_URL')}/webhook/nowpayments",
                    'order_id': f"sub_{subscription_id}_{int(time.time())}",
                    'order_description': f"Crypto News Bot - Monthly Subscription"
                }
                
                async with session.post(
                    f"{self.api_url}/invoice",
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Create payment record
                        payment = await self.payment_repo.create({
                            'subscription_id': subscription_id,
                            'group_id': subscription['group_id'],
                            'amount_usd': amount_usd,
                            'currency': currency,
                            'payment_status': 'pending',
                            'payment_url': data['invoice_url'],
                            'invoice_id': data['id'],
                            'expires_at': datetime.now() + timedelta(hours=1)
                        })
                        
                        self.metrics.inc_counter('payment_invoices_created')
                        
                        return payment
                    else:
                        logger.error(f"NOWPayments API error: {response.status}")
                        return None
        
        except Exception as e:
            logger.error(f"Error creating payment invoice: {e}", exc_info=True)
            return None
    
    async def verify_webhook_signature(
        self,
        payload: str,
        signature: str
    ) -> bool:
        """
        Verify NOWPayments webhook signature.
        """
        expected = hmac.new(
            self.ipn_secret.encode(),
            payload.encode(),
            hashlib.sha512
        ).hexdigest()
        
        return hmac.compare_digest(expected, signature)
    
    async def process_payment_webhook(
        self,
        webhook_data: Dict[str, Any]
    ) -> bool:
        """
        Process payment webhook from NOWPayments.
        """
        try:
            invoice_id = webhook_data.get('invoice_id')
            payment_status = webhook_data.get('payment_status')
            
            # Find payment
            payment = await self.payment_repo.find_by_invoice_id(invoice_id)
            
            if not payment:
                logger.error(f"Payment not found for invoice: {invoice_id}")
                return False
            
            # Update payment
            await self.payment_repo.update(payment['payment_id'], {
                'payment_status': payment_status,
                'webhook_data': json.dumps(webhook_data),
                'transaction_hash': webhook_data.get('pay_address'),
                'amount_crypto': webhook_data.get('actually_paid')
            })
            
            # Handle status
            if payment_status == 'finished':
                # Payment confirmed
                await self.payment_repo.update(payment['payment_id'], {
                    'confirmed_at': datetime.now()
                })
                
                # Activate subscription
                await self.subscription_service.activate_subscription(
                    payment['subscription_id'],
                    payment['payment_id']
                )
                
                self.metrics.inc_counter('payments_confirmed')
                
            elif payment_status == 'failed':
                self.metrics.inc_counter('payments_failed')
            
            elif payment_status == 'partially_paid':
                # Handle partial payment
                await self.handle_partial_payment(payment['payment_id'], webhook_data)
            
            return True
        
        except Exception as e:
            logger.error(f"Error processing webhook: {e}", exc_info=True)
            return False
```

---

## Database Indexes Strategy

### Performance Optimization

```sql
-- Subscriptions table
CREATE INDEX idx_subscriptions_status ON subscriptions(subscription_status);
CREATE INDEX idx_subscriptions_trial_end ON subscriptions(trial_end_date);
CREATE INDEX idx_subscriptions_sub_end ON subscriptions(subscription_end_date);
CREATE INDEX idx_subscriptions_next_billing ON subscriptions(next_billing_date);
CREATE INDEX idx_subscriptions_group ON subscriptions(group_id);

-- Payments table
CREATE INDEX idx_payments_subscription ON payments(subscription_id);
CREATE INDEX idx_payments_status ON payments(payment_status);
CREATE INDEX idx_payments_invoice ON payments(invoice_id);
CREATE INDEX idx_payments_created ON payments(created_at);

-- Events table
CREATE INDEX idx_events_subscription ON subscription_events(subscription_id);
CREATE INDEX idx_events_type ON subscription_events(event_type);
CREATE INDEX idx_events_created ON subscription_events(created_at);

-- Abuse tracking
CREATE INDEX idx_abuse_group ON trial_abuse_tracking(group_id);
CREATE INDEX idx_abuse_creator ON trial_abuse_tracking(creator_user_id);
CREATE INDEX idx_abuse_hash ON trial_abuse_tracking(group_title_hash);
```

---

## API Integration Details

### NOWPayments API Endpoints

**Base URL:** `https://api.nowpayments.io/v1`

**Authentication:** API Key in header `x-api-key`

**Key Endpoints:**

1. **Create Invoice**
   ```
   POST /invoice
   {
     "price_amount": 15.00,
     "price_currency": "usd",
     "pay_currency": "usdt",
     "ipn_callback_url": "https://your-bot.onrender.com/webhook/nowpayments",
     "order_id": "sub_123_1234567890",
     "order_description": "Monthly Subscription"
   }
   ```

2. **Get Payment Status**
   ```
   GET /payment/{payment_id}
   ```

3. **Webhook Callback**
   ```
   POST /webhook/nowpayments
   Headers:
     x-nowpayments-sig: <signature>
   Body:
     {
       "payment_id": "123",
       "invoice_id": "456",
       "payment_status": "finished",
       "pay_address": "0x...",
       "actually_paid": "15.00",
       ...
     }
   ```

---

## Environment Variables

```bash
# NOWPayments Configuration
NOWPAYMENTS_API_KEY=your_api_key_here
NOWPAYMENTS_IPN_SECRET=your_ipn_secret_here
NOWPAYMENTS_SANDBOX=false  # true for testing

# Subscription Configuration
SUBSCRIPTION_PRICE_USD=15.00
TRIAL_DAYS=15
GRACE_PERIOD_DAYS=3

# Webhook Configuration
WEBHOOK_URL=https://your-bot.onrender.com
WEBHOOK_SECRET=your_webhook_secret_here
```

---

## Monitoring & Alerts

### Key Metrics to Track

```python
# Business Metrics
- subscriptions_total (gauge)
- subscriptions_active (gauge)
- subscriptions_trial (gauge)
- subscriptions_expired (gauge)
- revenue_total (counter)
- revenue_monthly (gauge)

# Payment Metrics
- payments_created (counter)
- payments_confirmed (counter)
- payments_failed (counter)
- payment_confirmation_time (histogram)

# Conversion Metrics
- trial_to_paid_conversion_rate (gauge)
- churn_rate (gauge)
- renewal_rate (gauge)

# Technical Metrics
- webhook_processing_time (histogram)
- webhook_errors (counter)
- api_errors (counter)
```

### Alert Conditions

```python
# Critical Alerts
- Payment webhook failures > 5 in 1 hour
- Database connection failures
- NOWPayments API errors > 10 in 1 hour

# Warning Alerts
- Trial conversion rate < 20%
- Churn rate > 10%
- Payment confirmation time > 5 minutes
```

---

## Testing Strategy

### Unit Tests
- SubscriptionService methods
- PaymentService methods
- Webhook signature verification
- Trial abuse detection
- Date calculations

### Integration Tests
- End-to-end payment flow
- Webhook processing
- Subscription activation
- Expiration handling

### Load Tests
- 100 concurrent payment webhooks
- 1000 subscription status checks
- Database query performance

---

This architecture provides a solid foundation for an enterprise-level subscription system!

