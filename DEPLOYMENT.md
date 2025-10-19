# Deployment Guide: Crypto News Bot on Render.com

This guide provides step-by-step instructions for deploying the Telegram Crypto News Bot to Render.com for production use.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Environment Variables](#environment-variables)
3. [GitHub Setup](#github-setup)
4. [Render.com Deployment](#rendercom-deployment)
5. [Database Setup](#database-setup)
6. [Monitoring and Troubleshooting](#monitoring-and-troubleshooting)
7. [Post-Deployment Verification](#post-deployment-verification)

---

## Prerequisites

Before deploying, ensure you have:

1. **GitHub Account** - To host your code repository
2. **Render.com Account** - Sign up at [render.com](https://render.com)
3. **Telegram Bot Token** - From [@BotFather](https://t.me/botfather)
4. **API Keys**:
   - Google Gemini API Key
   - CryptoPanic API Key
   - CryptoCompare API Key
   - NewsAPI Key (optional)

---

## Environment Variables

The following environment variables need to be configured in Render:

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token from BotFather | `8423002540:AAHkZEhaH697Gg_iTn7aBISdOeoYrEDqMI4` |
| `GEMINI_API_KEY` | Google Gemini API key for AI analysis | `AIzaSyChPIrowf8nSTmvR0AbluVelRh_SbtB1GQ` |
| `CRYPTOPANIC_API_KEY` | CryptoPanic API key | `33cba4c0c1d59be4c14fcdcdc86335f45223befd` |
| `CRYPTOCOMPARE_API_KEY` | CryptoCompare API key | `790f523b655ea334c1058c6b1c78f2948e0449c786f24b8b1371f2bacb950f20` |
| `DATABASE_URL` | PostgreSQL connection string (auto-populated by Render) | `postgresql://user:pass@host/db` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEWSAPI_KEY` | NewsAPI.org API key | - |
| `TELEGRAM_CHANNEL_ID` | Default channel ID for posting | - |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | `INFO` |
| `ENABLE_REALTIME_POSTING` | Enable 24/7 hot news monitoring | `true` |
| `NEWS_CHECK_INTERVAL_MINUTES` | How often to check for hot news | `5` |
| `MIN_IMPORTANCE_SCORE` | Minimum score to post news (0-10) | `7` |
| `POSTING_HOUR` | Legacy scheduled posting hour (UTC) | `9` |
| `POSTING_MINUTE` | Legacy scheduled posting minute | `0` |
| `TIMEZONE` | Timezone for scheduled posting | `UTC` |

---

## GitHub Setup

### Step 1: Push Code to GitHub

1. **Initialize Git repository** (if not already done):
   ```bash
   git init
   git add .
   git commit -m "Initial commit - Crypto News Bot"
   ```

2. **Create a new repository on GitHub**:
   - Go to [github.com/new](https://github.com/new)
   - Repository name: `cryptonews`
   - Make it **Private** (recommended for security)
   - Do NOT initialize with README (you already have one)

3. **Push to GitHub**:
   ```bash
   git remote add origin https://github.com/Aniruddha434/cryptonews.git
   git branch -M main
   git push -u origin main
   ```

### Step 2: Verify Repository

Ensure these files are in your repository:
- ✅ `bot.py` - Main bot file
- ✅ `requirements.txt` - Python dependencies
- ✅ `render.yaml` - Render configuration
- ✅ `Procfile` - Process definition
- ✅ `db_adapter.py` - Database adapter
- ✅ `migrations.py` - Database migrations
- ✅ `.gitignore` - Ignore sensitive files

**Important**: Verify that `.env` file is NOT in the repository (it should be in `.gitignore`).

---

## Render.com Deployment

### Method 1: Using Render Blueprint (Recommended)

1. **Log in to Render.com**
   - Go to [dashboard.render.com](https://dashboard.render.com)

2. **Create New Blueprint**
   - Click "New +" → "Blueprint"
   - Connect your GitHub account if not already connected
   - Select repository: `Aniruddha434/cryptonews`
   - Render will automatically detect `render.yaml`

3. **Review Blueprint Configuration**
   - Service Name: `cryptonews-bot`
   - Database Name: `cryptonews-db`
   - Click "Apply"

4. **Configure Environment Variables**
   - Go to your service dashboard
   - Click "Environment" tab
   - Add all required environment variables (see table above)
   - **Important**: Do NOT add `DATABASE_URL` manually - Render auto-populates it

5. **Deploy**
   - Click "Manual Deploy" → "Deploy latest commit"
   - Wait for deployment to complete (5-10 minutes)

### Method 2: Manual Setup

If Blueprint doesn't work, follow these steps:

#### Step 1: Create PostgreSQL Database

1. Click "New +" → "PostgreSQL"
2. Name: `cryptonews-db`
3. Database: `cryptonews`
4. User: `cryptonews_user`
5. Region: Choose closest to you
6. Plan: **Free**
7. Click "Create Database"

#### Step 2: Create Worker Service

1. Click "New +" → "Background Worker"
2. Connect GitHub repository: `Aniruddha434/cryptonews`
3. Configure:
   - **Name**: `cryptonews-bot`
   - **Region**: Same as database
   - **Branch**: `main`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot.py`
   - **Plan**: Free

4. Add Environment Variables (see table above)

5. Link Database:
   - In "Environment" tab
   - Add environment variable:
     - Key: `DATABASE_URL`
     - Value: Select "From Database" → `cryptonews-db`

6. Click "Create Web Service"

---

## Database Setup

The database will be automatically initialized on first run:

1. **Migrations Run Automatically**
   - The bot runs migrations on startup
   - Check logs to verify: "All migrations completed"

2. **Database Tables Created**:
   - `users` - User registrations
   - `groups` - Telegram groups
   - `news_cache` - Cached news articles
   - `user_activity` - User activity logs
   - `group_activity` - Group activity logs
   - `daily_stats` - Daily statistics
   - `backups` - Backup metadata
   - `command_logs` - Command execution logs
   - `migrations` - Migration tracking

3. **Verify Database**:
   - Go to database dashboard on Render
   - Click "Connect" → "External Connection"
   - Use provided credentials to connect with a PostgreSQL client

---

## Monitoring and Troubleshooting

### Viewing Logs

1. **Real-time Logs**:
   - Go to service dashboard
   - Click "Logs" tab
   - View live logs

2. **Log Levels**:
   - `DEBUG` - Detailed debugging information
   - `INFO` - General information (recommended for production)
   - `WARNING` - Warning messages
   - `ERROR` - Error messages only

### Common Issues

#### Issue 1: Bot Not Starting

**Symptoms**: Service keeps restarting
**Solution**:
1. Check logs for error messages
2. Verify all required environment variables are set
3. Ensure `TELEGRAM_BOT_TOKEN` is correct
4. Check database connection

#### Issue 2: Database Connection Errors

**Symptoms**: "Connection refused" or "Database not found"
**Solution**:
1. Verify `DATABASE_URL` is set correctly
2. Ensure database service is running
3. Check database and worker are in same region
4. Restart the worker service

#### Issue 3: API Rate Limits

**Symptoms**: "Rate limit exceeded" errors
**Solution**:
1. Check API key quotas
2. Reduce `NEWS_CHECK_INTERVAL_MINUTES` if needed
3. Verify API keys are valid

#### Issue 4: Bot Not Responding

**Symptoms**: Bot doesn't respond to commands
**Solution**:
1. Check if bot is running: Look for "Bot is running!" in logs
2. Verify bot token is correct
3. Check if bot has proper permissions in Telegram groups
4. Restart the service

### Health Checks

Monitor these indicators:

1. **Service Status**: Should show "Live" (green)
2. **Last Deploy**: Should be recent
3. **Logs**: Should show "Bot is running!" and "Real-time hot news monitoring started"
4. **Database**: Should show "Available"

---

## Post-Deployment Verification

### Step 1: Verify Bot is Running

Check logs for these messages:
```
✅ Bot started successfully!
✅ Enterprise components active
🔥 Real-time hot news monitoring started (24/7)
```

### Step 2: Test Bot Commands

1. **Start a chat with your bot** on Telegram
2. **Test basic commands**:
   ```
   /start - Should show welcome message
   /help - Should show help menu
   /status - Should show bot status
   ```

3. **Test admin commands** (if you're an admin):
   ```
   /admin - Should show admin panel
   /stats - Should show statistics
   ```

### Step 3: Test News Posting

1. **Add bot to a test group**
2. **Register the group**:
   - Use admin panel to add group
   - Or bot will auto-register when added

3. **Wait for news**:
   - Bot checks for hot news every 5 minutes
   - Important news (score ≥ 7) will be posted automatically

### Step 4: Monitor Performance

1. **Check logs regularly** for errors
2. **Monitor database size** (Free tier: 1GB limit)
3. **Track API usage** to avoid rate limits
4. **Review daily stats** using `/stats` command

---

## Updating the Bot

### Automatic Deployments

Render automatically deploys when you push to GitHub:

```bash
git add .
git commit -m "Update: description of changes"
git push origin main
```

Render will:
1. Detect the push
2. Build the new version
3. Deploy automatically
4. Zero-downtime deployment

### Manual Deployment

1. Go to service dashboard
2. Click "Manual Deploy"
3. Select "Deploy latest commit"

---

## Scaling and Optimization

### Free Tier Limitations

- **Worker**: 750 hours/month (enough for 24/7)
- **Database**: 1GB storage, 97 connection limit
- **Bandwidth**: Unlimited

### Upgrading

If you need more resources:
1. Go to service settings
2. Click "Change Plan"
3. Select paid tier (starts at $7/month)

### Performance Tips

1. **Optimize Database Queries**: Use indexes
2. **Cache Frequently Accessed Data**: Use in-memory cache
3. **Reduce API Calls**: Increase check intervals
4. **Monitor Logs**: Set `LOG_LEVEL=INFO` in production

---

## Security Best Practices

1. **Never commit `.env` file** to GitHub
2. **Use environment variables** for all secrets
3. **Rotate API keys** regularly
4. **Monitor logs** for suspicious activity
5. **Keep dependencies updated**: Run `pip list --outdated`
6. **Use HTTPS** for all API calls
7. **Validate user input** in bot commands

---

## Support and Resources

- **Render Documentation**: [render.com/docs](https://render.com/docs)
- **Telegram Bot API**: [core.telegram.org/bots/api](https://core.telegram.org/bots/api)
- **Python Telegram Bot**: [python-telegram-bot.org](https://python-telegram-bot.org)
- **CryptoPanic API**: [cryptopanic.com/developers/api](https://cryptopanic.com/developers/api)

---

## Troubleshooting Checklist

Before asking for help, verify:

- [ ] All environment variables are set correctly
- [ ] Database is running and connected
- [ ] Bot token is valid
- [ ] API keys are valid and have quota remaining
- [ ] Logs show no errors
- [ ] Service status is "Live"
- [ ] Latest code is pushed to GitHub
- [ ] Dependencies are up to date

---

**Congratulations!** 🎉 Your Crypto News Bot is now deployed and running 24/7 on Render.com!

