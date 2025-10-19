# Operations Runbook

**AI Market Insight Bot - Subscription Payment System**  
**Version:** 1.0  
**Last Updated:** October 19, 2025

---

## 📋 Table of Contents

1. [Daily Operations](#daily-operations)
2. [Monitoring](#monitoring)
3. [Common Issues](#common-issues)
4. [Emergency Procedures](#emergency-procedures)
5. [Maintenance Tasks](#maintenance-tasks)
6. [Support Procedures](#support-procedures)

---

## 1. Daily Operations

### **Morning Checklist (9:00 AM UTC)**

The subscription checker runs automatically at 9:00 AM UTC daily. Monitor the following:

```bash
# Check subscription checker logs
tail -f logs/bot.log | grep "SubscriptionChecker"

# Expected output:
[INFO] Starting daily subscription check...
[INFO] Checking trial warnings...
[INFO] Checking trial expirations...
[INFO] Checking grace period warnings...
[INFO] Checking subscription expirations...
[INFO] Daily subscription check completed
```

**What to Monitor:**
- ✅ Number of trials expiring today
- ✅ Number of grace periods ending
- ✅ Number of subscriptions expiring
- ✅ Any errors in the checker

**Action Items:**
- Review any groups entering grace period
- Follow up on payment failures
- Monitor customer support requests

---

### **Continuous Monitoring**

**Key Metrics to Watch:**

1. **Bot Health**
   - Bot uptime
   - Response time
   - Error rate

2. **Subscription Metrics**
   - Active trials
   - Active subscriptions
   - Conversion rate (trial → paid)
   - Churn rate

3. **Payment Metrics**
   - Payment success rate
   - Average payment time
   - Failed payments
   - Webhook delivery rate

4. **News Posting**
   - News posted per hour
   - AI analysis success rate
   - Group posting success rate

---

## 2. Monitoring

### **Application Logs**

**Log Locations:**
```bash
# Main application log
logs/bot.log

# Error log
logs/error.log

# Payment log
logs/payment.log
```

**Log Levels:**
- `DEBUG` - Detailed information for debugging
- `INFO` - General information about operations
- `WARNING` - Warning messages (non-critical)
- `ERROR` - Error messages (requires attention)
- `CRITICAL` - Critical errors (immediate action required)

**Important Log Patterns:**

```bash
# Monitor errors
tail -f logs/bot.log | grep ERROR

# Monitor payments
tail -f logs/bot.log | grep "payment"

# Monitor subscriptions
tail -f logs/bot.log | grep "subscription"

# Monitor webhooks
tail -f logs/bot.log | grep "webhook"
```

---

### **Database Monitoring**

**Check Database Size:**
```sql
-- PostgreSQL
SELECT pg_size_pretty(pg_database_size('ainews_bot'));

-- Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

**Check Active Subscriptions:**
```sql
SELECT 
    subscription_status,
    COUNT(*) as count
FROM subscriptions
GROUP BY subscription_status;
```

**Check Payment Status:**
```sql
SELECT 
    payment_status,
    COUNT(*) as count,
    SUM(amount_usd) as total_usd
FROM payments
GROUP BY payment_status;
```

**Check Trial Abuse:**
```sql
SELECT 
    group_fingerprint,
    COUNT(*) as attempts
FROM trial_abuse_tracking
GROUP BY group_fingerprint
HAVING COUNT(*) > 1
ORDER BY attempts DESC;
```

---

### **Performance Monitoring**

**Key Performance Indicators (KPIs):**

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Bot Response Time | < 1s | > 3s |
| Database Query Time | < 100ms | > 500ms |
| Webhook Processing Time | < 2s | > 5s |
| News Posting Success Rate | > 95% | < 90% |
| Payment Success Rate | > 98% | < 95% |
| Uptime | > 99.5% | < 99% |

---

## 3. Common Issues

### **Issue 1: Bot Not Responding**

**Symptoms:**
- Bot doesn't respond to commands
- No messages in groups

**Diagnosis:**
```bash
# Check if bot is running
ps aux | grep bot.py

# Check bot status
curl https://api.telegram.org/bot<TOKEN>/getMe

# Check logs
tail -f logs/bot.log
```

**Solutions:**
1. Restart bot: `sudo systemctl restart ainews-bot`
2. Check `TELEGRAM_BOT_TOKEN` is correct
3. Verify network connectivity
4. Check for rate limiting from Telegram

---

### **Issue 2: Webhook Not Receiving Payments**

**Symptoms:**
- Payments made but not confirmed
- No webhook logs

**Diagnosis:**
```bash
# Check webhook endpoint
curl https://yourdomain.com/webhook/payment

# Check webhook logs
tail -f logs/bot.log | grep webhook

# Check NOWPayments IPN settings
# Log in to NOWPayments dashboard → Settings → IPN
```

**Solutions:**
1. Verify `WEBHOOK_URL` is correct
2. Check `NOWPAYMENTS_IPN_SECRET` is set
3. Verify SSL certificate is valid
4. Check firewall rules
5. Test webhook manually:
```bash
curl -X POST https://yourdomain.com/webhook/payment \
  -H "Content-Type: application/json" \
  -H "x-nowpayments-sig: test" \
  -d '{"payment_id": "test"}'
```

---

### **Issue 3: Database Connection Errors**

**Symptoms:**
- `DatabaseError` in logs
- Bot crashes on startup

**Diagnosis:**
```bash
# Test database connection
python -c "from db_pool import get_pool; pool = get_pool(); print('✅ Connected')"

# Check DATABASE_URL
echo $DATABASE_URL

# Check PostgreSQL status (if self-hosted)
sudo systemctl status postgresql
```

**Solutions:**
1. Verify `DATABASE_URL` is correct
2. Check database server is running
3. Verify credentials
4. Check connection limits
5. Restart database connection pool

---

### **Issue 4: News Not Posting**

**Symptoms:**
- No news posted to groups
- Empty news feed

**Diagnosis:**
```bash
# Check news service logs
tail -f logs/bot.log | grep "RealtimeNewsService"

# Test CryptoPanic API
curl "https://cryptopanic.com/api/developer/v2/posts/?auth_token=YOUR_TOKEN"

# Test Gemini API
python -c "import google.generativeai as genai; genai.configure(api_key='YOUR_KEY'); print('✅ OK')"
```

**Solutions:**
1. Verify `CRYPTOPANIC_API_KEY` is valid
2. Verify `GEMINI_API_KEY` is valid
3. Check API rate limits
4. Check group posting permissions
5. Verify subscription status

---

### **Issue 5: Subscription Checker Not Running**

**Symptoms:**
- No trial expiration warnings
- No grace period notifications

**Diagnosis:**
```bash
# Check scheduler logs
tail -f logs/bot.log | grep "scheduler"

# Check if scheduler is running
python -c "from services.subscription_checker_service import SubscriptionCheckerService; print('✅ OK')"
```

**Solutions:**
1. Restart bot
2. Check system time is correct
3. Verify scheduler is enabled
4. Check for errors in checker service

---

## 4. Emergency Procedures

### **Emergency 1: Payment System Down**

**Immediate Actions:**
1. ✅ Post status update to admin channel
2. ✅ Disable `/renew` command temporarily
3. ✅ Contact NOWPayments support
4. ✅ Monitor existing subscriptions

**Recovery Steps:**
1. Identify root cause
2. Fix issue or switch to backup payment provider
3. Re-enable `/renew` command
4. Process any pending payments manually
5. Post recovery update

---

### **Emergency 2: Database Corruption**

**Immediate Actions:**
1. ✅ Stop bot immediately: `sudo systemctl stop ainews-bot`
2. ✅ Create database backup
3. ✅ Assess damage

**Recovery Steps:**
```bash
# Restore from latest backup
pg_restore -d ainews_bot backup.sql

# Verify data integrity
python -c "from db_pool import get_pool; pool = get_pool(); print('✅ OK')"

# Restart bot
sudo systemctl start ainews-bot
```

---

### **Emergency 3: Security Breach**

**Immediate Actions:**
1. ✅ Stop bot: `sudo systemctl stop ainews-bot`
2. ✅ Rotate all API keys immediately
3. ✅ Change database password
4. ✅ Review access logs
5. ✅ Notify affected users

**Recovery Steps:**
1. Identify breach vector
2. Patch vulnerability
3. Update all credentials
4. Deploy security fix
5. Monitor for suspicious activity
6. Document incident

---

## 5. Maintenance Tasks

### **Daily Tasks**

- ✅ Review error logs
- ✅ Monitor subscription metrics
- ✅ Check payment success rate
- ✅ Verify backup completion

### **Weekly Tasks**

- ✅ Review database performance
- ✅ Clean up old logs (> 30 days)
- ✅ Update dependencies (security patches)
- ✅ Review trial abuse tracking
- ✅ Generate weekly report

**Weekly Report Template:**
```
Week of: [Date]

Metrics:
- New trials: X
- Trial → Paid conversions: X (X%)
- Active subscriptions: X
- Revenue: $X
- Churn rate: X%

Issues:
- [List any issues]

Actions:
- [List actions taken]
```

### **Monthly Tasks**

- ✅ Full database backup
- ✅ Security audit
- ✅ Performance optimization
- ✅ Update documentation
- ✅ Review and rotate API keys
- ✅ Generate monthly report

---

## 6. Support Procedures

### **Customer Support Workflow**

**Step 1: Identify Issue**
- Trial not created
- Payment not confirmed
- Subscription not activated
- Bot not posting

**Step 2: Gather Information**
```sql
-- Get group subscription status
SELECT * FROM subscriptions WHERE group_id = ?;

-- Get payment history
SELECT * FROM payments WHERE group_id = ? ORDER BY created_at DESC;

-- Get subscription events
SELECT * FROM subscription_events WHERE subscription_id = ? ORDER BY created_at DESC;
```

**Step 3: Resolve Issue**

**Common Resolutions:**

1. **Extend Trial:**
```sql
UPDATE subscriptions
SET trial_end_date = DATE_ADD(trial_end_date, INTERVAL 7 DAY)
WHERE subscription_id = ?;
```

2. **Manually Activate Subscription:**
```sql
UPDATE subscriptions
SET subscription_status = 'active',
    subscription_start_date = NOW(),
    subscription_end_date = DATE_ADD(NOW(), INTERVAL 30 DAY)
WHERE subscription_id = ?;
```

3. **Refund Payment:**
- Contact NOWPayments support
- Process refund through dashboard
- Update payment status:
```sql
UPDATE payments
SET payment_status = 'refunded'
WHERE payment_id = ?;
```

**Step 4: Document Resolution**
- Log ticket in support system
- Update customer
- Add notes to database

---

## 📞 Emergency Contacts

| Service | Contact | Priority |
|---------|---------|----------|
| Hosting (Render.com) | support@render.com | High |
| NOWPayments | support@nowpayments.io | High |
| Database (Supabase) | support@supabase.com | Critical |
| Telegram Support | @BotSupport | Medium |

---

## 📊 Monitoring Dashboard

**Recommended Tools:**
- **Uptime Monitoring:** UptimeRobot, Pingdom
- **Error Tracking:** Sentry
- **Log Management:** Papertrail, Loggly
- **Performance:** New Relic, DataDog
- **Database:** pgAdmin, TablePlus

---

## 🔄 Backup Schedule

| Backup Type | Frequency | Retention |
|-------------|-----------|-----------|
| Database Full | Daily | 30 days |
| Database Incremental | Hourly | 7 days |
| Configuration | Weekly | 90 days |
| Logs | Daily | 30 days |

**Backup Command:**
```bash
# PostgreSQL backup
pg_dump ainews_bot > backup_$(date +%Y%m%d).sql

# Compress
gzip backup_$(date +%Y%m%d).sql

# Upload to cloud storage
aws s3 cp backup_$(date +%Y%m%d).sql.gz s3://backups/
```

---

**Operations Status:** Production Ready ✅  
**Last Review:** October 19, 2025  
**Next Review:** November 19, 2025

