# 🧪 Subscription System Testing Guide

Complete guide for testing the subscription payment system (Phases 1-5).

---

## 📋 **Quick Start Testing**

### **Option 1: Automated Test Script (Recommended)**

```bash
python test_subscription_system.py
```

This runs all automated tests and provides a comprehensive report.

### **Option 2: Manual Bot Testing**

```bash
# 1. Set up environment
cp .env.example .env
# Edit .env with your credentials

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the bot
python bot.py

# 4. Test commands in Telegram
```

---

## 🔧 **Environment Setup**

### **Minimum Configuration (.env)**

```env
# Required for basic testing
TELEGRAM_BOT_TOKEN=your_bot_token_here
DATABASE_URL=sqlite:///ainews.db
TRIAL_DAYS=15
SUBSCRIPTION_PRICE_USD=15.00
```

### **Full Configuration (for payment testing)**

```env
# Add these for payment tests
NOWPAYMENTS_API_KEY=your_api_key_here
NOWPAYMENTS_IPN_SECRET=your_ipn_secret_here
WEBHOOK_URL=https://your-domain.com/webhook/payment
WEBHOOK_PORT=8080
```

---

## 🧪 **Automated Test Suite**

### **What Gets Tested**

The `test_subscription_system.py` script tests:

1. ✅ **Database Migrations** - Verifies all tables are created
2. ✅ **Trial Creation** - Tests 15-day trial subscription creation
3. ✅ **Subscription Status** - Tests status retrieval
4. ✅ **Posting Validation** - Tests subscription-based posting checks
5. ✅ **Trial Abuse Detection** - Tests duplicate trial prevention
6. ✅ **Payment Invoice** - Tests NOWPayments invoice creation
7. ✅ **Webhook Signature** - Tests HMAC-SHA512 verification

### **Expected Output**

```
==================================================
🧪 SUBSCRIPTION SYSTEM TEST SUITE
==================================================

🔧 Setting up test environment...
📦 Running migrations...
✅ Setup complete!

📝 Test 1: Trial Subscription Creation
==================================================
✅ PASS - Trial Creation
   Trial created with ID: 1, Ends: 2024-01-15
✅ PASS - Trial Duration
   Trial duration: 15 days (expected: 15)

📝 Test 2: Subscription Status Retrieval
==================================================
✅ PASS - Status Retrieval
   Status: trial, Posting allowed: True, Trial days left: 15

📝 Test 3: Posting Validation
==================================================
✅ PASS - Posting Validation
   Posting allowed: True

📝 Test 4: Trial Abuse Detection
==================================================
✅ PASS - Duplicate Trial Prevention
   Duplicate trial correctly blocked

📝 Test 5: Payment Invoice Creation
==================================================
✅ PASS - Payment Invoice
   ⚠️ SKIPPED - NOWPayments API key not configured

📝 Test 6: Webhook Signature Verification
==================================================
✅ PASS - Webhook Signature
   Signature verification: Valid
✅ PASS - Invalid Signature Detection
   Invalid signature correctly rejected: True

==================================================
📊 TEST SUMMARY
==================================================

Total Tests: 8
✅ Passed: 8
❌ Failed: 0
Success Rate: 100.0%

✅ All tests passed!
```

---

## 🤖 **Manual Bot Testing**

### **Test 1: Bot Startup**

```bash
python bot.py
```

**Expected logs:**
```
✅ Services initialized
✅ Handlers configured
✅ Webhook server started on 0.0.0.0:8080
🚀 Bot started successfully!
```

### **Test 2: `/setup` Command**

**Steps:**
1. Add bot to a Telegram group
2. Make bot an admin
3. Send `/setup` command

**Expected response:**
```
✅ Group Registered Successfully!

Your group is now registered for automated crypto news!

🔥 Posting Mode: 24/7 Real-time
🎯 Default trader type: Investor
🟢 Status: Active
🎁 Free Trial: 15 days

━━━━━━━━━━━━━━━━━━━━━━

Next Steps:
• Use /admin to customize settings
• Use /subscription to view trial status
• Use /help for all commands
```

### **Test 3: `/subscription` Command**

**Steps:**
1. In the group, send `/subscription`

**Expected response:**
```
🎁 Free Trial Active

━━━━━━━━━━━━━━━━━━━━━━

Status: Trial Period
Days Remaining: 15 days
Trial Ends: 2024-01-15
Posting Status: ✅ Active

━━━━━━━━━━━━━━━━━━━━━━

After trial ends:
• Subscribe for $15/month
• Continue receiving real-time crypto news
• AI-powered market analysis

Use /renew to subscribe now!

[💳 Renew Subscription] [📊 View Plans]
```

### **Test 4: `/renew` Command**

**Steps:**
1. In the group, send `/renew`
2. Click a currency button (e.g., "₿ Bitcoin")

**Expected response (Step 1):**
```
💳 Renew Subscription

━━━━━━━━━━━━━━━━━━━━━━

Plan: Monthly Subscription
Price: $15.00 USD/month

What you get:
• 24/7 real-time crypto news
• AI-powered market analysis
• Multi-source aggregation
• Trader-specific insights
• Priority support

━━━━━━━━━━━━━━━━━━━━━━

Choose your payment method:

[₿ Bitcoin] [Ξ Ethereum]
[₮ USDT]    [$ USDC]
[🔶 BNB]    [⚡ TRON]
[❌ Cancel]
```

**Expected response (Step 2 - after clicking Bitcoin):**
```
✅ Payment Invoice Created

━━━━━━━━━━━━━━━━━━━━━━

Amount: 0.00045 BTC
Equivalent: $15.00 USD

Payment Address:
bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh

Invoice ID: INV123456
Expires: 2024-01-01 10:00

━━━━━━━━━━━━━━━━━━━━━━

How to pay:
1. Copy the payment address above
2. Send exactly 0.00045 BTC to this address
3. Your subscription will be activated automatically

[💳 Open Payment Page]
[✅ I've Paid]
[❌ Cancel]
```

### **Test 5: `/admin` Command**

**Steps:**
1. In the group, send `/admin` (must be group admin)

**Expected response:**
```
🔧 Admin Control Panel

━━━━━━━━━━━━━━━━━━━━━━

📋 Current Settings:

🟢 Status: Active
🎯 Trader Type: Investor
🔥 Posting Mode: Real-time (24/7)
👥 Group: My Test Group
🎁 Trial: 15 days left

━━━━━━━━━━━━━━━━━━━━━━

💡 How It Works:
• Bot monitors hot news 24/7
• Posts immediately when important news breaks
• AI analyzes market impact for Investors
• No fixed schedule - posts based on news importance

👇 Select an option below:

[🟢 Posting ON]
[🎯 Configure Trader Types]
[⏰ Set Schedule]
[📊 View Stats]
[⚙️ View Settings]
[🔄 Refresh]
```

---

## 🌐 **Webhook Testing**

### **Test 1: Health Check**

```bash
curl http://localhost:8080/health
```

**Expected:**
```json
{"status": "ok"}
```

### **Test 2: Webhook Endpoint**

```bash
curl -X POST http://localhost:8080/webhook/payment \
  -H "Content-Type: application/json" \
  -H "x-nowpayments-sig: invalid_signature" \
  -d '{"invoice_id":"test","payment_status":"finished"}'
```

**Expected:** 401 Unauthorized (invalid signature)

### **Test 3: NOWPayments Integration (Optional)**

**Prerequisites:**
- NOWPayments account with API key
- Webhook URL configured

**Steps:**
1. Use ngrok to expose local server: `ngrok http 8080`
2. Update `.env` with ngrok URL: `WEBHOOK_URL=https://xxx.ngrok.io/webhook/payment`
3. Configure webhook in NOWPayments dashboard
4. Create test payment
5. Verify webhook is received and processed

---

## 📊 **Database Verification**

### **Check Migrations**

```bash
python -c "
import asyncio
from db_pool import DatabasePool
from db_adapter import DatabaseAdapter
from migrations import run_all_migrations

async def test():
    pool = DatabasePool()
    await pool.initialize()
    adapter = DatabaseAdapter(pool)
    await run_all_migrations(adapter)
    await pool.close()
    print('✅ Migrations successful!')

asyncio.run(test())
"
```

### **Check Subscription Data**

```bash
# For SQLite
sqlite3 ainews.db "SELECT * FROM subscriptions LIMIT 5;"

# For PostgreSQL
psql -d ainews -c "SELECT * FROM subscriptions LIMIT 5;"
```

---

## ✅ **Test Completion Checklist**

### **Automated Tests**
- [ ] All 8 automated tests pass
- [ ] No errors in test output
- [ ] Database migrations complete successfully

### **Bot Commands**
- [ ] `/setup` registers group with trial
- [ ] `/subscription` shows trial status
- [ ] `/renew` displays payment options
- [ ] Payment invoice is created (if API configured)
- [ ] `/admin` shows subscription info
- [ ] `/help` includes subscription commands

### **Webhook Server**
- [ ] Webhook server starts on port 8080
- [ ] Health endpoint responds
- [ ] Webhook endpoint rejects invalid signatures

### **Database**
- [ ] All 4 subscription tables created
- [ ] Trial subscription is created on group registration
- [ ] Subscription status is tracked correctly

---

## 🔍 **Troubleshooting**

### **Import Errors**

```bash
pip install -r requirements.txt
```

### **Database Errors**

Try SQLite for testing:
```env
DATABASE_URL=sqlite:///ainews.db
```

### **Webhook Not Accessible**

Use ngrok:
```bash
ngrok http 8080
```

Then update `.env`:
```env
WEBHOOK_URL=https://your-ngrok-url.ngrok.io/webhook/payment
```

---

## 📝 **What's Been Implemented**

✅ **Phase 1:** Database Foundation (4 tables, 16 indexes)  
✅ **Phase 2:** Core Subscription Logic (trial creation, validation)  
✅ **Phase 3:** Payment Integration (NOWPayments API)  
✅ **Phase 4:** Webhook System (payment notifications)  
✅ **Phase 5:** Bot Commands (/subscription, /renew)  

---

## 🚀 **Next Phases**

⏳ **Phase 6:** Notification System (trial expiration warnings)  
⏳ **Phase 7:** Background Tasks (subscription expiration checking)  
⏳ **Phase 8:** Security & Testing (comprehensive testing)  
⏳ **Phase 9:** Production Readiness (deployment preparation)  

---

**Happy Testing! 🎉**

