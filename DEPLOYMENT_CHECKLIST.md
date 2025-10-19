# 📋 Render.com Deployment Checklist

Use this checklist to ensure a smooth deployment to Render.com.

---

## ✅ **Pre-Deployment Checklist**

### **1. API Keys Ready**
- [ ] Telegram Bot Token (from @BotFather)
- [ ] Google Gemini API Key
- [ ] CryptoPanic API Key
- [ ] CryptoCompare API Key
- [ ] NOWPayments API Key (optional)
- [ ] NOWPayments IPN Secret (optional)

### **2. Accounts Created**
- [ ] GitHub account
- [ ] Render.com account
- [ ] NOWPayments account (optional)

### **3. Code Ready**
- [ ] All files committed to Git
- [ ] `render.yaml` file present
- [ ] `requirements.txt` file present
- [ ] `Procfile` file present
- [ ] No sensitive data in code (use env vars)

---

## 🚀 **Deployment Steps**

### **Step 1: GitHub Setup**
- [ ] Repository created on GitHub
- [ ] Code pushed to GitHub
- [ ] Repository is public or Render has access

### **Step 2: Render Blueprint**
- [ ] Logged into Render Dashboard
- [ ] New Blueprint created
- [ ] GitHub repository connected
- [ ] Blueprint applied successfully

### **Step 3: Services Created**
- [ ] PostgreSQL database created (`cryptonews-db`)
- [ ] Worker service created (`cryptonews-bot`)
- [ ] Both services show "Live" status

### **Step 4: Environment Variables**
- [ ] `TELEGRAM_BOT_TOKEN` added
- [ ] `GEMINI_API_KEY` added
- [ ] `CRYPTOPANIC_API_KEY` added
- [ ] `CRYPTOCOMPARE_API_KEY` added
- [ ] `NOWPAYMENTS_API_KEY` added (if using payments)
- [ ] `NOWPAYMENTS_IPN_SECRET` added (if using payments)
- [ ] `WEBHOOK_URL` added (if using payments)
- [ ] All variables saved

### **Step 5: Deployment**
- [ ] Manual deploy triggered
- [ ] Build completed successfully
- [ ] Service started successfully
- [ ] No errors in logs

---

## ✅ **Post-Deployment Verification**

### **1. Check Logs**
- [ ] "✅ Services initialized" appears
- [ ] "✅ Handlers configured" appears
- [ ] "✅ Bot is running!" appears
- [ ] "🚀 Bot started successfully!" appears
- [ ] "🔥 Real-time hot news monitoring started" appears
- [ ] No error messages

### **2. Test Bot**
- [ ] Bot responds to `/start`
- [ ] Bot responds to `/help`
- [ ] Welcome message displays correctly
- [ ] Buttons work (if applicable)

### **3. Test Channel/Group Setup**
- [ ] Bot can be added to group
- [ ] `/setup` command works in group
- [ ] Channel registration works in private chat
- [ ] Subscription created successfully

### **4. Test News Posting**
- [ ] Bot fetches news (check logs)
- [ ] AI analysis working (check logs)
- [ ] News posts to channel/group (wait for high-importance news)

### **5. Test Payments (if configured)**
- [ ] Webhook server running on port 8080
- [ ] `/renew` command generates payment invoice
- [ ] Payment callback URL accessible
- [ ] NOWPayments IPN configured

---

## 🔧 **Configuration Verification**

### **Default Settings (from render.yaml)**
- [ ] `ENABLE_REALTIME_POSTING=true`
- [ ] `NEWS_CHECK_INTERVAL_MINUTES=5`
- [ ] `MIN_IMPORTANCE_SCORE=7`
- [ ] `TRIAL_DAYS=15`
- [ ] `SUBSCRIPTION_PRICE_USD=15.00`
- [ ] `GRACE_PERIOD_DAYS=3`
- [ ] `WEBHOOK_PORT=8080`
- [ ] `LOG_LEVEL=INFO`

---

## 🐛 **Troubleshooting Checklist**

### **If Bot Not Starting:**
- [ ] Check Render logs for errors
- [ ] Verify `TELEGRAM_BOT_TOKEN` is correct
- [ ] Verify all required env vars are set
- [ ] Check database connection
- [ ] Try restarting service

### **If Bot Not Responding:**
- [ ] Check bot is running (Render logs)
- [ ] Verify bot token is valid
- [ ] Check Telegram API status
- [ ] Try `/start` command again

### **If News Not Posting:**
- [ ] Check logs for "Real-time monitoring started"
- [ ] Verify API keys are correct
- [ ] Check subscription is active
- [ ] Verify importance threshold (MIN_IMPORTANCE_SCORE)
- [ ] Wait for high-importance news (score ≥ 7)

### **If Database Errors:**
- [ ] Check `DATABASE_URL` is set
- [ ] Verify database service is running
- [ ] Check database migrations ran
- [ ] Try restarting database service

### **If Payment Webhook Not Working:**
- [ ] Verify `WEBHOOK_URL` is correct
- [ ] Check webhook server is running (logs)
- [ ] Verify NOWPayments IPN callback URL
- [ ] Check `NOWPAYMENTS_IPN_SECRET` is correct
- [ ] Test webhook endpoint manually

---

## 📊 **Monitoring Checklist**

### **Daily Checks:**
- [ ] Service status is "Live"
- [ ] No errors in logs
- [ ] News being fetched regularly
- [ ] Bot responding to commands

### **Weekly Checks:**
- [ ] Review posted news quality
- [ ] Check subscription expirations
- [ ] Monitor payment transactions
- [ ] Review error logs

### **Monthly Checks:**
- [ ] Update dependencies if needed
- [ ] Review API usage/limits
- [ ] Check database size
- [ ] Optimize performance if needed

---

## 🔄 **Update Checklist**

### **Before Updating:**
- [ ] Test changes locally
- [ ] Commit changes to Git
- [ ] Update version/changelog
- [ ] Backup database (if major changes)

### **During Update:**
- [ ] Push to GitHub
- [ ] Wait for auto-deploy
- [ ] Monitor deployment logs
- [ ] Check for errors

### **After Update:**
- [ ] Verify bot still running
- [ ] Test core functionality
- [ ] Check logs for issues
- [ ] Test new features

---

## 📞 **Emergency Contacts**

### **Service Status Pages:**
- Render: https://status.render.com/
- Telegram: https://telegram.org/
- Google Cloud: https://status.cloud.google.com/

### **Support:**
- Render Support: https://render.com/docs/support
- Telegram Bot API: https://core.telegram.org/bots/api

---

## ✅ **Deployment Complete!**

Once all items are checked:
- ✅ Bot is deployed
- ✅ All services running
- ✅ Tests passing
- ✅ Monitoring in place

**Your bot is live! 🎉**

---

## 📝 **Notes**

Use this space to track deployment-specific information:

**Deployment Date:** _______________

**Render Service URL:** _______________

**Database Name:** _______________

**Issues Encountered:** 
- 
- 
- 

**Resolutions:**
- 
- 
- 

**Custom Configuration:**
- 
- 
- 

