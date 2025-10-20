# 🚀 Deploy to Render.com - Quick Guide

Your code is now on GitHub! Follow these steps to deploy to Render.com.

**Repository:** https://github.com/Aniruddha434/cryptonews

---

## ✅ **Step 1: Go to Render Dashboard**

1. Open: https://dashboard.render.com
2. Log in to your Render account (or sign up if you don't have one)

---

## ✅ **Step 2: Create New Blueprint**

1. Click **"New +"** button (top right)
2. Select **"Blueprint"**
3. Click **"Connect GitHub"** (if not already connected)
4. Authorize Render to access your GitHub account
5. Select repository: **`Aniruddha434/cryptonews`**
6. Click **"Apply"**

Render will now read your `render.yaml` file and create:
- ✅ PostgreSQL Database (`cryptonews-db`)
- ✅ Worker Service (`cryptonews-bot`)

**Wait 2-3 minutes** for services to be created.

---

## ✅ **Step 3: Configure Environment Variables**

### **3.1 Navigate to Worker Service**

1. In Render Dashboard, click on **`cryptonews-bot`** service
2. Click **"Environment"** tab (left sidebar)

### **3.2 Add Required Variables**

Click **"Add Environment Variable"** for each of these:

#### **🔐 REQUIRED - Telegram:**
```
Key: TELEGRAM_BOT_TOKEN
Value: [Your bot token from @BotFather]
```

#### **🔐 REQUIRED - Google Gemini:**
```
Key: GEMINI_API_KEY
Value: [Your Gemini API key]
```

#### **🔐 REQUIRED - CryptoPanic:**
```
Key: CRYPTOPANIC_API_KEY
Value: 33cba4c0c1d59be4c14fcdcdc86335f45223befd
```
*(Or use your own key from https://cryptopanic.com/developers/api/)*

#### **🔐 REQUIRED - CryptoCompare:**
```
Key: CRYPTOCOMPARE_API_KEY
Value: [Your CryptoCompare API key]
```

#### **💳 OPTIONAL - NOWPayments (for subscriptions):**

Only add these if you want to enable cryptocurrency payments:

```
Key: NOWPAYMENTS_API_KEY
Value: [Your NOWPayments API key]

Key: NOWPAYMENTS_IPN_SECRET
Value: [Your NOWPayments IPN secret]

Key: WEBHOOK_URL
Value: https://cryptonews-bot.onrender.com
```

### **3.3 Save Changes**

Click **"Save Changes"** button at the bottom.

---

## ✅ **Step 4: Deploy**

### **4.1 Trigger Deployment**

1. Scroll to **"Manual Deploy"** section
2. Click **"Deploy latest commit"**
3. Wait **2-3 minutes** for deployment

### **4.2 Monitor Logs**

1. Click **"Logs"** tab (left sidebar)
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

If you see these messages, **your bot is live!** 🎉

---

## ✅ **Step 5: Test Your Bot**

### **5.1 Test in Telegram**

1. Open Telegram
2. Search for your bot
3. Send `/start`
4. You should receive a welcome message with buttons!

### **5.2 Test Channel Setup**

1. Message your bot in **private chat**
2. Send `/start`
3. Click **"📺 Add My Channel"** button
4. Follow the guide to register your channel

---

## 🎯 **What Happens Next?**

Your bot is now running 24/7 on Render.com and will:

- ✅ Monitor crypto news every **5 minutes**
- ✅ Analyze each article with **Google Gemini AI**
- ✅ Post high-importance news (score ≥ 7) **automatically**
- ✅ Manage subscriptions and trials
- ✅ Accept cryptocurrency payments (if configured)

---

## 📊 **Monitoring Your Bot**

### **View Logs:**
1. Render Dashboard → `cryptonews-bot` → **Logs** tab
2. Monitor real-time activity

### **Check Service Status:**
1. Render Dashboard → `cryptonews-bot`
2. Status should show **"Live"** (green)

### **Database:**
1. Render Dashboard → `cryptonews-db`
2. Click **"Connect"** to get connection details

---

## 🔧 **Common Issues & Solutions**

### **❌ Bot Not Starting:**

**Check:**
- Logs for error messages
- All required environment variables are set
- `TELEGRAM_BOT_TOKEN` is correct

**Fix:**
- Add missing environment variables
- Restart service: Click **"Manual Deploy"** → **"Deploy latest commit"**

---

### **❌ Database Connection Failed:**

**Check:**
- `DATABASE_URL` is set (should be automatic)
- Database service is running

**Fix:**
- Restart database service
- Restart worker service

---

### **❌ Bot Not Posting News:**

**Check:**
- Logs show "Real-time hot news monitoring started"
- API keys are correct
- Subscription is active for your channel

**Fix:**
- Verify all API keys
- Check subscription status with `/channelstatus` command
- Wait for high-importance news (score ≥ 7)

---

## 🔄 **Updating Your Bot**

When you make changes to your code:

```bash
# Commit changes
git add .
git commit -m "Description of changes"

# Push to GitHub
git push origin main
```

Render will **automatically deploy** the new version!

---

## 💡 **Pro Tips**

### **1. Set Up Custom Domain (Optional):**
- Render Dashboard → `cryptonews-bot` → **Settings**
- Add custom domain for webhook URL

### **2. Enable Auto-Deploy:**
- Already enabled by default!
- Every push to `main` branch triggers deployment

### **3. Monitor Resource Usage:**
- Render Dashboard → `cryptonews-bot` → **Metrics**
- Check CPU, memory, and bandwidth usage

### **4. Set Up Alerts:**
- Render Dashboard → `cryptonews-bot` → **Settings** → **Notifications**
- Get email alerts for deployment failures

---

## 📞 **Need Help?**

### **Render Support:**
- Documentation: https://render.com/docs
- Support: https://render.com/docs/support

### **Bot Commands:**
- `/start` - Start the bot
- `/help` - Show all commands
- `/addchannel` - Channel setup guide
- `/mychannels` - View your channels
- `/admin` - Admin panel (in groups)

---

## ✅ **Deployment Checklist**

- [ ] GitHub repository created and pushed
- [ ] Render account created
- [ ] Blueprint applied successfully
- [ ] Database service created
- [ ] Worker service created
- [ ] All environment variables added
- [ ] Deployment successful
- [ ] Bot responds to `/start`
- [ ] Logs show success messages
- [ ] Channel/group registered
- [ ] News monitoring active

---

## 🎉 **Success!**

Your Telegram Crypto News Bot is now **live on Render.com**!

**Repository:** https://github.com/Aniruddha434/cryptonews  
**Service:** https://cryptonews-bot.onrender.com

The bot will:
- ✅ Run 24/7 automatically
- ✅ Monitor news every 5 minutes
- ✅ Post important updates to your channels
- ✅ Manage subscriptions
- ✅ Accept payments (if configured)

**Enjoy your automated crypto news bot! 🚀**

---

## 📚 **Additional Documentation**

For more detailed information, see:
- `RENDER_DEPLOYMENT_COMPLETE.md` - Complete deployment guide
- `DEPLOYMENT_CHECKLIST.md` - Detailed checklist
- `README.md` - Project overview
- `SUBSCRIPTION_README.md` - Subscription system guide

