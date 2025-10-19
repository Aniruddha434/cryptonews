# Quick Start: Deploy to Render.com in 10 Minutes

This is a condensed guide to get your bot running on Render.com as quickly as possible.

## Prerequisites

- GitHub account
- Render.com account (free)
- Telegram bot token
- API keys (Gemini, CryptoPanic, CryptoCompare)

---

## Step 1: Push to GitHub (2 minutes)

```bash
# Initialize and push to GitHub
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/Aniruddha434/cryptonews.git
git branch -M main
git push -u origin main
```

---

## Step 2: Deploy on Render (5 minutes)

1. **Go to Render Dashboard**: [dashboard.render.com](https://dashboard.render.com)

2. **Create New Blueprint**:
   - Click "New +" → "Blueprint"
   - Connect GitHub account
   - Select repository: `Aniruddha434/cryptonews`
   - Click "Apply"

3. **Wait for Services to Create** (2-3 minutes):
   - Database: `cryptonews-db`
   - Worker: `cryptonews-bot`

---

## Step 3: Configure Environment Variables (3 minutes)

1. **Go to Worker Service** (`cryptonews-bot`)

2. **Click "Environment" tab**

3. **Add these variables**:

```
TELEGRAM_BOT_TOKEN=your_bot_token_here
GEMINI_API_KEY=your_gemini_key_here
CRYPTOPANIC_API_KEY=your_cryptopanic_key_here
CRYPTOCOMPARE_API_KEY=your_cryptocompare_key_here
LOG_LEVEL=INFO
ENABLE_REALTIME_POSTING=true
NEWS_CHECK_INTERVAL_MINUTES=5
MIN_IMPORTANCE_SCORE=7
```

4. **Save Changes**

---

## Step 4: Deploy and Verify (2 minutes)

1. **Manual Deploy**:
   - Click "Manual Deploy" → "Deploy latest commit"
   - Wait 2-3 minutes for deployment

2. **Check Logs**:
   - Click "Logs" tab
   - Look for: `✅ Bot started successfully!`
   - Look for: `🔥 Real-time hot news monitoring started (24/7)`

3. **Test Bot**:
   - Open Telegram
   - Send `/start` to your bot
   - Should receive welcome message

---

## Done! 🎉

Your bot is now running 24/7 on Render.com!

### What Happens Next?

- Bot monitors crypto news every 5 minutes
- Posts important news (score ≥ 7) automatically
- Runs continuously on free tier

### Useful Commands

- `/start` - Start the bot
- `/help` - Show help menu
- `/admin` - Admin panel (for admins)
- `/status` - Bot status

### Monitoring

- **Logs**: [dashboard.render.com](https://dashboard.render.com) → Your Service → Logs
- **Database**: Check database dashboard for connection info
- **Updates**: Push to GitHub → Auto-deploys

---

## Troubleshooting

**Bot not starting?**
- Check all environment variables are set
- Verify bot token is correct
- Check logs for errors

**Database errors?**
- Ensure `DATABASE_URL` is auto-populated (don't set manually)
- Verify database service is running

**Need help?**
- See full guide: [DEPLOYMENT.md](DEPLOYMENT.md)

---

## Next Steps

1. **Add bot to Telegram groups** where you want news posted
2. **Configure posting preferences** via admin panel
3. **Monitor logs** for the first few hours
4. **Adjust settings** as needed (check interval, importance score, etc.)

---

**That's it!** Your crypto news bot is live and monitoring markets 24/7! 🚀

