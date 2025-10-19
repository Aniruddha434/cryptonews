# 🚀 Complete Render.com Deployment Guide

Deploy your Telegram Crypto News Bot to Render.com in **15 minutes**!

---

## 📋 **Prerequisites**

Before you start, make sure you have:

- ✅ **GitHub Account** - [Sign up here](https://github.com/signup)
- ✅ **Render.com Account** - [Sign up here](https://dashboard.render.com/register)
- ✅ **Telegram Bot Token** - Get from [@BotFather](https://t.me/BotFather)
- ✅ **Google Gemini API Key** - Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
- ✅ **CryptoPanic API Key** - Get from [CryptoPanic](https://cryptopanic.com/developers/api/)
- ✅ **CryptoCompare API Key** - Get from [CryptoCompare](https://min-api.cryptocompare.com/)
- ✅ **NOWPayments API Key** (Optional) - Get from [NOWPayments](https://nowpayments.io/)

---

## 🎯 **Step 1: Prepare Your Repository (5 minutes)**

### **1.1 Initialize Git Repository**

```bash
# Navigate to your project directory
cd c:\Users\aniru\OneDrive\Desktop\ainews

# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - Telegram Crypto News Bot"
```

### **1.2 Create GitHub Repository**

1. Go to [GitHub](https://github.com/new)
2. Create a new repository (e.g., `crypto-news-bot`)
3. **DO NOT** initialize with README, .gitignore, or license
4. Click "Create repository"

### **1.3 Push to GitHub**

```bash
# Add remote origin (replace with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/crypto-news-bot.git

# Push to GitHub
git branch -M main
git push -u origin main
```

---

## 🌐 **Step 2: Deploy on Render.com (5 minutes)**

### **2.1 Create New Blueprint**

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"Blueprint"**
3. Click **"Connect GitHub"** (if not already connected)
4. Select your repository: `YOUR_USERNAME/crypto-news-bot`
5. Click **"Apply"**

### **2.2 Wait for Services to Create**

Render will automatically create:
- ✅ **PostgreSQL Database** (`cryptonews-db`)
- ✅ **Worker Service** (`cryptonews-bot`)

This takes **2-3 minutes**.

---

## ⚙️ **Step 3: Configure Environment Variables (5 minutes)**

### **3.1 Navigate to Worker Service**

1. In Render Dashboard, click on **`cryptonews-bot`** service
2. Click **"Environment"** tab on the left

### **3.2 Add Required Environment Variables**

Click **"Add Environment Variable"** and add each of these:

#### **🔐 Required Variables:**

| Variable | Value | Where to Get |
|----------|-------|--------------|
| `TELEGRAM_BOT_TOKEN` | Your bot token | [@BotFather](https://t.me/BotFather) |
| `GEMINI_API_KEY` | Your Gemini key | [Google AI Studio](https://makersuite.google.com/app/apikey) |
| `CRYPTOPANIC_API_KEY` | Your CryptoPanic key | [CryptoPanic API](https://cryptopanic.com/developers/api/) |
| `CRYPTOCOMPARE_API_KEY` | Your CryptoCompare key | [CryptoCompare](https://min-api.cryptocompare.com/) |

#### **💳 Payment Variables (Optional - for subscriptions):**

| Variable | Value | Where to Get |
|----------|-------|--------------|
| `NOWPAYMENTS_API_KEY` | Your NOWPayments key | [NOWPayments](https://nowpayments.io/) |
| `NOWPAYMENTS_IPN_SECRET` | Your IPN secret | NOWPayments Dashboard |
| `WEBHOOK_URL` | `https://cryptonews-bot.onrender.com` | Your Render service URL |

#### **📊 Already Configured (in render.yaml):**

These are already set with default values:
- ✅ `ENABLE_REALTIME_POSTING=true`
- ✅ `NEWS_CHECK_INTERVAL_MINUTES=5`
- ✅ `MIN_IMPORTANCE_SCORE=7`
- ✅ `TRIAL_DAYS=15`
- ✅ `SUBSCRIPTION_PRICE_USD=15.00`
- ✅ `LOG_LEVEL=INFO`

### **3.3 Save Changes**

Click **"Save Changes"** at the bottom.

---

## 🚀 **Step 4: Deploy and Verify (5 minutes)**

### **4.1 Trigger Manual Deploy**

1. Go to **"Manual Deploy"** section
2. Click **"Deploy latest commit"**
3. Wait **2-3 minutes** for deployment to complete

### **4.2 Monitor Deployment Logs**

1. Click **"Logs"** tab
2. Watch for these success messages:

```
✅ Services initialized
✅ Handlers configured
✅ Bot is running! Press Ctrl+C to stop.
🚀 Bot started successfully!
✅ Enterprise components active
💳 Payment webhook server started on port 8080
🔥 Real-time hot news monitoring started (24/7)
```

### **4.3 Test Your Bot**

1. Open Telegram
2. Search for your bot
3. Send `/start`
4. You should receive a welcome message!

---

## ✅ **Verification Checklist**

After deployment, verify everything is working:

- [ ] Bot responds to `/start` command
- [ ] Bot responds to `/help` command
- [ ] Logs show "Bot started successfully"
- [ ] Logs show "Real-time hot news monitoring started"
- [ ] No errors in Render logs
- [ ] Database connection successful
- [ ] Payment webhook server running (if configured)

---

## 🔧 **Post-Deployment Configuration**

### **Set Up Your First Channel/Group**

#### **For Groups:**
1. Add bot to your Telegram group
2. Make bot an admin
3. Send `/setup` in the group
4. Follow the interactive setup

#### **For Channels:**
1. Add bot to your channel as admin (with "Post Messages" permission)
2. Message bot in **private chat**
3. Send `/start`
4. Click **"📺 Add My Channel"**
5. Follow the guide to register your channel

---

## 📊 **Monitoring Your Bot**

### **View Logs:**
1. Go to Render Dashboard
2. Click on `cryptonews-bot` service
3. Click **"Logs"** tab
4. Monitor real-time activity

### **Check Database:**
1. Click on `cryptonews-db` service
2. Click **"Connect"** to get connection details
3. Use a PostgreSQL client to view data

---

## 🔄 **Updating Your Bot**

### **Deploy New Changes:**

```bash
# Make your changes locally
git add .
git commit -m "Description of changes"
git push origin main
```

Render will **automatically deploy** the new version!

---

## 💰 **Setting Up Payments (Optional)**

If you want to enable subscription payments:

### **1. Get NOWPayments API Keys:**
1. Sign up at [NOWPayments](https://nowpayments.io/)
2. Go to Settings → API Keys
3. Copy your API Key and IPN Secret

### **2. Add to Render:**
1. Go to `cryptonews-bot` → Environment
2. Add:
   - `NOWPAYMENTS_API_KEY=your_api_key`
   - `NOWPAYMENTS_IPN_SECRET=your_ipn_secret`
   - `WEBHOOK_URL=https://cryptonews-bot.onrender.com`

### **3. Configure NOWPayments Webhook:**
1. In NOWPayments Dashboard → Settings → IPN
2. Set IPN Callback URL: `https://cryptonews-bot.onrender.com/webhook/payment`
3. Save

---

## 🐛 **Troubleshooting**

### **Bot Not Starting:**
- Check logs for error messages
- Verify all required environment variables are set
- Check `TELEGRAM_BOT_TOKEN` is correct

### **Database Connection Failed:**
- Verify `DATABASE_URL` is set (should be automatic)
- Check database service is running
- Try restarting the worker service

### **Bot Not Posting News:**
- Check logs for "Real-time hot news monitoring started"
- Verify API keys are correct
- Check subscription is active for your group/channel

### **Payment Webhook Not Working:**
- Verify `WEBHOOK_URL` matches your Render service URL
- Check `WEBHOOK_PORT=8080` is set
- Verify NOWPayments IPN callback URL is correct

---

## 📞 **Support**

### **Useful Commands:**

```bash
# View logs
render logs cryptonews-bot

# Restart service
render restart cryptonews-bot

# Check service status
render status cryptonews-bot
```

### **Bot Commands:**

- `/start` - Start the bot
- `/help` - Show all commands
- `/admin` - Admin panel (in groups)
- `/addchannel` - Channel setup guide (private chat)
- `/mychannels` - View your channels (private chat)

---

## 🎉 **Success!**

Your bot is now running 24/7 on Render.com!

### **What Happens Next:**

- ✅ Bot monitors crypto news every 5 minutes
- ✅ AI analyzes each article for importance (0-10 scale)
- ✅ Posts high-impact news (score ≥ 7) automatically
- ✅ Manages subscriptions and trials
- ✅ Accepts cryptocurrency payments (if configured)
- ✅ Runs continuously on free tier

---

## 📚 **Additional Resources**

- [Render Documentation](https://render.com/docs)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Google Gemini API](https://ai.google.dev/docs)
- [CryptoPanic API](https://cryptopanic.com/developers/api/)
- [NOWPayments API](https://documenter.getpostman.com/view/7907941/S1a32n38)

---

**Deployed successfully? Give yourself a pat on the back! 🎊**

