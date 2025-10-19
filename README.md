# 🚀 Crypto News Bot - AI-Powered Telegram Bot

An enterprise-grade Telegram bot that monitors cryptocurrency news 24/7 and automatically posts important market updates to your Telegram groups.

## ✨ Features

- **🔥 Real-Time News Monitoring** - Checks for hot crypto news every 5 minutes
- **🤖 AI-Powered Analysis** - Uses Google Gemini to analyze news importance
- **📊 Multi-Source Aggregation** - Fetches from CryptoPanic, CryptoCompare, and more
- **⚡ Instant Posting** - Automatically posts important news (score ≥ 7/10)
- **👥 Multi-Group Support** - Post to unlimited Telegram groups
- **🎯 Trader Type Customization** - Tailored content for scalpers, day traders, swing traders, and investors
- **📈 Analytics & Metrics** - Track bot performance and user engagement
- **🔒 Enterprise Security** - Rate limiting, circuit breakers, and connection pooling
- **☁️ Production Ready** - Deployed on Render.com with PostgreSQL

## 🎯 Quick Start

### Option 1: Deploy to Render.com (Recommended)

**Deploy in 10 minutes!** See [RENDER_QUICK_START.md](RENDER_QUICK_START.md)

1. Push to GitHub
2. Create Render Blueprint
3. Configure environment variables
4. Deploy!

### Option 2: Run Locally

1. **Clone the repository**
   ```bash
   git clone https://github.com/Aniruddha434/cryptonews.git
   cd cryptonews
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. **Run the bot**
   ```bash
   python bot.py
   ```

## 📋 Requirements

### API Keys Needed

- **Telegram Bot Token** - Get from [@BotFather](https://t.me/botfather)
- **Google Gemini API Key** - Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
- **CryptoPanic API Key** - Get from [CryptoPanic](https://cryptopanic.com/developers/api/)
- **CryptoCompare API Key** - Get from [CryptoCompare](https://www.cryptocompare.com/cryptopian/api-keys)

### Environment Variables

See [.env.example](.env.example) for all configuration options.

**Required:**
- `TELEGRAM_BOT_TOKEN`
- `GEMINI_API_KEY`
- `CRYPTOPANIC_API_KEY`
- `CRYPTOCOMPARE_API_KEY`

**Optional:**
- `LOG_LEVEL` (default: INFO)
- `ENABLE_REALTIME_POSTING` (default: true)
- `NEWS_CHECK_INTERVAL_MINUTES` (default: 5)
- `MIN_IMPORTANCE_SCORE` (default: 7)

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Telegram Bot API                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        Bot Core (bot.py)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Handlers   │  │   Services   │  │ Middleware   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┼─────────────┐
                ▼             ▼             ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │   News   │  │    AI    │  │ Database │
        │ Fetcher  │  │ Analyzer │  │  Adapter │
        └──────────┘  └──────────┘  └──────────┘
                │             │             │
                ▼             ▼             ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │CryptoPanic│  │  Gemini  │  │PostgreSQL│
        │CryptoComp│  │   API    │  │ /SQLite  │
        └──────────┘  └──────────┘  └──────────┘
```

## 📚 Documentation

- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Comprehensive deployment guide
- **[RENDER_QUICK_START.md](RENDER_QUICK_START.md)** - 10-minute deployment guide
- **[DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md)** - Technical overview
- **[RENDER_DEPLOYMENT_CHECKLIST.md](RENDER_DEPLOYMENT_CHECKLIST.md)** - Step-by-step checklist

## 🎮 Bot Commands

### User Commands
- `/start` - Start the bot and see welcome message
- `/help` - Show help menu with all commands
- `/status` - Check bot status and uptime
- `/news` - Get latest crypto news
- `/settings` - Configure your preferences

### Admin Commands
- `/admin` - Open admin panel
- `/stats` - View bot statistics
- `/groups` - Manage registered groups
- `/broadcast` - Send message to all groups

## 🔧 Technology Stack

- **Python 3.11+** - Core language
- **python-telegram-bot** - Telegram Bot API wrapper
- **Google Gemini** - AI analysis
- **PostgreSQL** - Production database
- **SQLite** - Local development database
- **APScheduler** - Task scheduling
- **Render.com** - Cloud hosting

## 🚀 Deployment

### Render.com (Recommended)

**Free Tier Includes:**
- 750 hours/month worker time (24/7 coverage)
- 1GB PostgreSQL database
- Unlimited bandwidth
- Auto-deployments from GitHub

**See [RENDER_QUICK_START.md](RENDER_QUICK_START.md) for deployment instructions.**

### Other Platforms

The bot can also be deployed to:
- Heroku
- Railway
- DigitalOcean
- AWS
- Google Cloud
- Any platform supporting Python workers

## 📊 Features in Detail

### Real-Time News Monitoring

- Checks multiple news sources every 5 minutes
- AI analyzes each article for importance (0-10 scale)
- Automatically posts news with score ≥ 7
- Filters out duplicates and low-quality content

### AI Analysis

Uses Google Gemini to analyze:
- Market impact
- Urgency
- Relevance to crypto traders
- Sentiment (bullish/bearish/neutral)
- Key takeaways

### Multi-Group Support

- Post to unlimited Telegram groups
- Customize posting schedule per group
- Different content for different trader types
- Group-specific preferences

### Analytics

Track:
- Total users and groups
- News posted per day
- API usage
- Bot uptime
- User engagement

## 🔒 Security

- API keys stored as environment variables
- Rate limiting on all endpoints
- Circuit breakers for external APIs
- Input validation on all commands
- Connection pooling for database
- Secure PostgreSQL connections

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/Aniruddha434/cryptonews/issues)
- **Documentation**: See docs folder
- **Telegram**: Contact bot admin

## 🎯 Roadmap

- [ ] Add more news sources
- [ ] Implement sentiment analysis
- [ ] Add price alerts
- [ ] Create web dashboard
- [ ] Add multi-language support
- [ ] Implement machine learning for better filtering

## 📈 Status

- **Version**: 1.0.0
- **Status**: Production Ready ✅
- **Last Updated**: 2025-01-18

## 🙏 Acknowledgments

- [python-telegram-bot](https://python-telegram-bot.org/) - Telegram Bot framework
- [Google Gemini](https://ai.google.dev/) - AI analysis
- [CryptoPanic](https://cryptopanic.com/) - News aggregation
- [CryptoCompare](https://www.cryptocompare.com/) - Market data
- [Render.com](https://render.com/) - Cloud hosting

---

**Made with ❤️ for the crypto community**

⭐ Star this repo if you find it useful!

