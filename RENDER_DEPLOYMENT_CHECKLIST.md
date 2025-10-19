# Render.com Deployment Checklist

Use this checklist to ensure a smooth deployment of your Crypto News Bot to Render.com.

---

## Pre-Deployment Checklist

### 1. API Keys Ready
- [ ] Telegram Bot Token (from @BotFather)
- [ ] Google Gemini API Key
- [ ] CryptoPanic API Key
- [ ] CryptoCompare API Key
- [ ] NewsAPI Key (optional)

### 2. GitHub Repository
- [ ] GitHub account created
- [ ] Repository created: `https://github.com/Aniruddha434/cryptonews.git`
- [ ] Local git initialized
- [ ] All files committed
- [ ] Code pushed to GitHub

### 3. Render.com Account
- [ ] Account created at [render.com](https://render.com)
- [ ] GitHub account connected to Render
- [ ] Payment method added (even for free tier)

### 4. Verify Files Present
- [ ] `bot.py` - Main bot file
- [ ] `requirements.txt` - Dependencies
- [ ] `render.yaml` - Render configuration
- [ ] `Procfile` - Process definition
- [ ] `db_adapter.py` - Database adapter
- [ ] `migrations.py` - Database migrations
- [ ] `config.py` - Configuration
- [ ] `.gitignore` - Ignore file
- [ ] `DEPLOYMENT.md` - Deployment guide

### 5. Security Check
- [ ] `.env` file is NOT in repository
- [ ] No API keys in code
- [ ] `.gitignore` includes `.env`
- [ ] All secrets will be set as environment variables

---

## Deployment Checklist

### Step 1: Push to GitHub
- [ ] Run: `git add .`
- [ ] Run: `git commit -m "Ready for Render deployment"`
- [ ] Run: `git push origin main`
- [ ] Verify files on GitHub (check repository)

### Step 2: Create Render Services
- [ ] Log in to [dashboard.render.com](https://dashboard.render.com)
- [ ] Click "New +" → "Blueprint"
- [ ] Select repository: `Aniruddha434/cryptonews`
- [ ] Click "Apply"
- [ ] Wait for services to be created (2-3 minutes)

### Step 3: Verify Services Created
- [ ] Database service created: `cryptonews-db`
- [ ] Worker service created: `cryptonews-bot`
- [ ] Both services show in dashboard

### Step 4: Configure Environment Variables
Go to worker service (`cryptonews-bot`) → Environment tab:

#### Required Variables
- [ ] `TELEGRAM_BOT_TOKEN` = `your_bot_token`
- [ ] `GEMINI_API_KEY` = `your_gemini_key`
- [ ] `CRYPTOPANIC_API_KEY` = `your_cryptopanic_key`
- [ ] `CRYPTOCOMPARE_API_KEY` = `your_cryptocompare_key`

#### Optional Variables (Recommended)
- [ ] `LOG_LEVEL` = `INFO`
- [ ] `ENABLE_REALTIME_POSTING` = `true`
- [ ] `NEWS_CHECK_INTERVAL_MINUTES` = `5`
- [ ] `MIN_IMPORTANCE_SCORE` = `7`

#### Auto-Configured (Do NOT Set Manually)
- [ ] Verify `DATABASE_URL` is auto-populated from database

### Step 5: Deploy
- [ ] Click "Manual Deploy" → "Deploy latest commit"
- [ ] Wait for build to complete (2-5 minutes)
- [ ] Check build logs for errors

### Step 6: Verify Deployment
- [ ] Service status shows "Live" (green)
- [ ] No errors in logs
- [ ] Database status shows "Available"

---

## Post-Deployment Checklist

### Step 1: Check Logs
Look for these success messages:
- [ ] `✅ Bot started successfully!`
- [ ] `✅ Enterprise components active`
- [ ] `🔥 Real-time hot news monitoring started (24/7)`
- [ ] `Connection pool initialized`
- [ ] `All migrations completed`

### Step 2: Test Bot on Telegram
- [ ] Open Telegram
- [ ] Find your bot
- [ ] Send `/start` command
- [ ] Receive welcome message
- [ ] Send `/help` command
- [ ] Receive help menu

### Step 3: Test Admin Features (if applicable)
- [ ] Send `/admin` command
- [ ] See admin panel
- [ ] Send `/status` command
- [ ] See bot status

### Step 4: Test Group Posting
- [ ] Create test Telegram group
- [ ] Add bot to group
- [ ] Make bot admin
- [ ] Register group via admin panel
- [ ] Wait for news to be posted (may take 5-10 minutes)

### Step 5: Monitor for 1 Hour
- [ ] Check logs every 10 minutes
- [ ] Verify no errors
- [ ] Verify news checks happening
- [ ] Verify database connections working

### Step 6: Monitor for 24 Hours
- [ ] Check logs once every few hours
- [ ] Verify news being posted
- [ ] Check database size
- [ ] Monitor API usage

---

## Troubleshooting Checklist

### If Bot Won't Start

- [ ] Check all environment variables are set
- [ ] Verify `TELEGRAM_BOT_TOKEN` is correct
- [ ] Check logs for specific error messages
- [ ] Verify database is running
- [ ] Try manual redeploy

### If Database Errors

- [ ] Verify `DATABASE_URL` is set (auto-populated)
- [ ] Check database service is running
- [ ] Verify database and worker in same region
- [ ] Check database connection limit (97 max)
- [ ] Try restarting worker service

### If API Errors

- [ ] Verify all API keys are correct
- [ ] Check API key quotas/limits
- [ ] Test API keys manually
- [ ] Check for rate limiting
- [ ] Verify API endpoints are accessible

### If No News Posting

- [ ] Verify `ENABLE_REALTIME_POSTING=true`
- [ ] Check groups are registered
- [ ] Verify bot is admin in groups
- [ ] Check `MIN_IMPORTANCE_SCORE` (lower if needed)
- [ ] Verify news sources are working
- [ ] Check logs for news fetch attempts

---

## Optimization Checklist

### Performance
- [ ] Set `LOG_LEVEL=INFO` (not DEBUG) in production
- [ ] Monitor database query performance
- [ ] Check connection pool stats
- [ ] Optimize news check interval if needed

### Cost Management
- [ ] Monitor database size (1GB limit on free tier)
- [ ] Track API usage to avoid overages
- [ ] Review worker hours (750/month on free tier)
- [ ] Consider upgrading if limits reached

### Security
- [ ] Rotate API keys monthly
- [ ] Monitor logs for suspicious activity
- [ ] Keep dependencies updated
- [ ] Review admin user list

---

## Maintenance Checklist

### Weekly
- [ ] Check logs for errors
- [ ] Verify bot is responding
- [ ] Check news posting is working
- [ ] Monitor database size

### Monthly
- [ ] Review API usage and costs
- [ ] Check for dependency updates
- [ ] Review and clean old logs
- [ ] Verify backup strategy

### Quarterly
- [ ] Update dependencies: `pip list --outdated`
- [ ] Rotate API keys
- [ ] Review and optimize database
- [ ] Test disaster recovery

---

## Emergency Procedures

### If Bot Goes Down

1. [ ] Check Render service status
2. [ ] Review recent logs
3. [ ] Check database status
4. [ ] Verify environment variables
5. [ ] Try manual redeploy
6. [ ] Check GitHub for recent changes
7. [ ] Rollback if needed

### If Database Issues

1. [ ] Check database service status
2. [ ] Verify connection string
3. [ ] Check connection count
4. [ ] Review database logs
5. [ ] Check disk space
6. [ ] Contact Render support if needed

### If API Rate Limits Hit

1. [ ] Identify which API
2. [ ] Check current usage
3. [ ] Increase check interval temporarily
4. [ ] Review API plan/limits
5. [ ] Consider upgrading API tier
6. [ ] Implement additional caching

---

## Success Criteria

Your deployment is successful when:

- [x] Service status is "Live"
- [x] No errors in logs
- [x] Bot responds to `/start` command
- [x] News monitoring is active
- [x] Database is connected
- [x] News is being posted to groups
- [x] All API calls working
- [x] No rate limit errors
- [x] Logs show normal operation

---

## Next Steps After Successful Deployment

1. [ ] Add bot to production Telegram groups
2. [ ] Configure posting preferences per group
3. [ ] Set up monitoring alerts (optional)
4. [ ] Document any custom configurations
5. [ ] Share bot with users
6. [ ] Monitor performance for first week
7. [ ] Optimize settings based on usage
8. [ ] Plan for scaling if needed

---

## Support

If you encounter issues:

1. **Check Documentation**:
   - `DEPLOYMENT.md` - Full deployment guide
   - `RENDER_QUICK_START.md` - Quick start guide
   - `DEPLOYMENT_SUMMARY.md` - Overview

2. **Check Logs**:
   - Render dashboard → Service → Logs
   - Look for error messages
   - Check timestamps

3. **Verify Configuration**:
   - Environment variables
   - Database connection
   - API keys

4. **Render Support**:
   - [render.com/docs](https://render.com/docs)
   - Community forum
   - Support tickets (paid plans)

---

**Good luck with your deployment!** 🚀

Remember: Take it step by step, check each item, and verify before moving to the next step.

