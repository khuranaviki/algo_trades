# Deployment Package Summary

## ✅ System Ready for Monday Morning Trading!

Your Agentic Trading System is now fully packaged and ready for deployment.

## 📦 What's Been Created

### 1. Documentation
- **QUICKSTART.md** - Get started in 5 minutes
- **DEPLOYMENT.md** - Comprehensive deployment guide (15+ pages)
- **DEPLOYMENT_SUMMARY.md** - This file
- **paper_trading/README.md** - Paper trading engine documentation

### 2. Deployment Scripts
All scripts in `deploy/` directory:

- **start_services.sh** - Start both FastAPI and Streamlit
- **stop_services.sh** - Stop all running services
- **start_paper_trading.sh** - Start automated trading (market hours only)
- **crontab.example** - Template for scheduling with cron

All scripts are executable (`chmod +x` applied).

### 3. Paper Trading Runner
- **paper_trading/run_paper_trading.py** - Main automated trading script
  - Runs continuously during NSE market hours (9:15 AM - 3:30 PM)
  - Scans watchlist every 60 seconds
  - Executes trades based on multi-agent analysis
  - Logs everything to `logs/paper_trading.log`

### 4. Bug Fixes Applied
- ✅ Fixed Portfolio UI errors (streamlit_app.py:256-279)
  - Changed `portfolio.total_value` → `portfolio.get_total_value()`
  - Changed `pos.avg_price` → `pos.avg_entry_price`
  - Changed `pos.target` → `pos.target_price`
- ✅ All Portfolio methods now correctly called

## 🚀 Quick Start (3 Commands)

```bash
# 1. Set API keys
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"

# 2. Start dashboard
./deploy/start_services.sh

# 3. Start automated trading
./deploy/start_paper_trading.sh
```

That's it! The system is now running.

## 📊 Access Points

- **Streamlit Dashboard**: http://localhost:8501
- **FastAPI Swagger Docs**: http://localhost:8000/docs
- **API Health Check**: http://localhost:8000/health

## 📁 Directory Structure

```
agentic-trading-system/
├── QUICKSTART.md              ← START HERE (5-minute guide)
├── DEPLOYMENT.md              ← Full deployment guide
├── DEPLOYMENT_SUMMARY.md      ← This file
│
├── deploy/                    ← Deployment scripts
│   ├── start_services.sh      ← Start API + Streamlit
│   ├── stop_services.sh       ← Stop all services
│   ├── start_paper_trading.sh ← Start automated trading
│   └── crontab.example        ← Cron scheduling template
│
├── paper_trading/
│   ├── run_paper_trading.py   ← Main trading script
│   ├── engine.py              ← Trading engine
│   ├── portfolio.py           ← Portfolio management
│   └── README.md              ← Paper trading docs
│
├── config/
│   └── paper_trading_config.py ← All configuration
│
├── logs/                       ← All logs go here
│   ├── api.log
│   ├── streamlit.log
│   ├── paper_trading.log
│   └── cron.log
│
├── api/
│   └── main.py                ← FastAPI application
│
├── streamlit_app.py           ← Streamlit dashboard
│
└── agents/
    ├── orchestrator.py        ← Main orchestrator
    ├── fundamental_agent.py   ← Fundamental analysis
    ├── technical_agent.py     ← Technical analysis
    ├── sentiment_agent.py     ← Sentiment analysis
    └── management_agent.py    ← Management quality
```

## ⚙️ Configuration

Edit `config/paper_trading_config.py`:

```python
PAPER_TRADING_CONFIG = {
    'initial_capital': 1000000,  # ₹10 lakhs

    'watchlist': [
        'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS',
        'INFY.NS', 'ICICIBANK.NS', 'BHARTIARTL.NS',
        'BAJFINANCE.NS', 'TITAN.NS', 'MARUTI.NS', 'TATAMOTORS.NS'
    ],

    'update_interval_seconds': 60,  # Scan every 60 seconds

    'risk_management': {
        'max_position_size_pct': 5.0,
        'max_open_positions': 10,
        'max_drawdown_pct': 10.0,
        'daily_loss_limit_pct': 3.0
    },

    'orchestrator': {
        'weights': {
            'fundamental': 0.25,
            'technical': 0.20,
            'sentiment': 0.20,
            'management': 0.15,
            'market_regime': 0.10
        },
        'buy_threshold': 70.0,
        'strong_buy_threshold': 85.0,
        'sell_threshold': 40.0
    }
}
```

## 🔄 Monday Morning Automation

### Option 1: Cron (Linux/macOS)

```bash
# Edit crontab
crontab -e

# Add this line to start at 9:00 AM every weekday
0 9 * * 1-5 cd /path/to/agentic-trading-system && ./deploy/start_paper_trading.sh >> logs/cron.log 2>&1
```

See `deploy/crontab.example` for complete examples.

### Option 2: Manual Start

```bash
# Run this command Monday morning at 9:00 AM
./deploy/start_paper_trading.sh
```

The script automatically:
- ✅ Checks if it's a weekday
- ✅ Waits until 9:15 AM if too early
- ✅ Stops at 3:30 PM automatically
- ✅ Refuses to run on weekends

## 📈 How It Works

### Automated Trading Flow

```
1. System scans watchlist every 60 seconds
   ↓
2. For each stock, 6 agents analyze:
   • Fundamental Agent (financials, ratios)
   • Technical Agent (patterns, 5-year validation)
   • Sentiment Agent (news, market mood)
   • Management Agent (quarterly reports)
   • Market Regime Agent (bull/bear detection)
   • Pattern Validator (historical success rates)
   ↓
3. Orchestrator combines scores (weighted)
   ↓
4. Decision logic:
   • Score ≥ 70: BUY signal
   • Score ≥ 85: STRONG_BUY signal
   • Score < 40: SELL existing positions
   • Score 40-70: WAIT
   ↓
5. Risk Manager validates trade:
   • Check position size limits (5% max)
   • Check max positions (10 max)
   • Check drawdown limits (10% max)
   • Check daily loss limits (3% max)
   ↓
6. If approved, execute trade:
   • Calculate position size
   • Set stop-loss (from technical analysis)
   • Set target price (from technical analysis)
   • Execute with realistic slippage and costs
   ↓
7. Log trade and update portfolio
   ↓
8. Continue monitoring and repeat
```

### Example Trade

```
🔍 Scanning RELIANCE.NS...

📊 Agent Analysis:
├─ Fundamental: 80/100 (Strong financials, growing revenue)
├─ Technical: 75/100 (Bullish breakout, validated pattern)
├─ Sentiment: 70/100 (Positive news sentiment)
├─ Management: 65/100 (Good quarterly guidance)
├─ Market Regime: 80/100 (Strong bull market)
└─ Composite: 75/100

✅ Decision: BUY

💰 Position Sizing:
├─ Portfolio Value: ₹10,00,000
├─ Position Size: 5% = ₹50,000
├─ Current Price: ₹2,500
└─ Shares: 20

📍 Trade Details:
├─ Entry: ₹2,500
├─ Stop Loss: ₹2,375 (-5%)
├─ Target: ₹2,750 (+10%)
└─ Risk/Reward: 1:2

✅ Order Executed:
BUY 20 shares RELIANCE.NS @ ₹2,500
Total Cost: ₹50,000 + ₹25 (costs) = ₹50,025

📊 Updated Portfolio:
├─ Cash: ₹9,49,975
├─ Positions: 1
└─ Total Value: ₹10,00,000
```

## 📊 Monitoring

### View Live Logs

```bash
# Paper trading activity
tail -f logs/paper_trading.log

# API logs
tail -f logs/api.log

# Streamlit logs
tail -f logs/streamlit.log

# Cron logs (if using cron)
tail -f logs/cron.log
```

### Dashboard Monitoring

1. Open http://localhost:8501
2. Navigate to "💼 Portfolio" tab
3. View:
   - Total portfolio value
   - Current positions
   - Realized/unrealized P&L
   - Return percentage

### API Monitoring

```bash
# Get portfolio status
curl http://localhost:8000/portfolio | jq

# Analyze a specific stock
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"ticker": "RELIANCE.NS", "use_llm": true}' | jq
```

## 🛑 Stopping Services

```bash
# Stop everything
./deploy/stop_services.sh
```

This stops:
- FastAPI server
- Streamlit dashboard
- Paper trading engine

## 💾 Backup & Recovery

### Daily Backups (Recommended)

```bash
# Create backup
mkdir -p backups
cp data/portfolio_state.json backups/portfolio_$(date +%Y%m%d).json

# Automate with cron
0 0 * * * cd /path/to/project && mkdir -p backups && cp data/portfolio_state.json backups/portfolio_$(date +\%Y\%m\%d).json
```

### Restore from Backup

```bash
# List backups
ls -lh backups/

# Restore specific backup
cp backups/portfolio_20250110.json data/portfolio_state.json
```

## ⚠️ Important Notes

### API Costs
- OpenAI GPT-4: ~$0.01-0.03 per analysis
- Anthropic Claude: ~$0.01-0.02 per analysis
- With 10 stocks scanned every 60s during market hours (6.25 hours):
  - ~375 scans per day
  - ~$3.75-$11.25 per day in API costs
  - Monitor usage in OpenAI/Anthropic dashboards

### Risk Management
- This is **paper trading** only (simulated)
- Start with default thresholds (buy: 70, sell: 40)
- Monitor first week closely
- Adjust agent weights based on performance
- Review weekly P&L and trade history

### API Keys
- **Never commit API keys** to git
- Use environment variables
- Keys are in `.gitignore`
- Rotate keys periodically

### Performance Tracking
- Review `logs/paper_trading.log` daily
- Check win rate vs. target (aim for >50%)
- Monitor drawdown (should stay < 10%)
- Analyze which agents are most accurate

## 📚 Documentation Reference

1. **QUICKSTART.md** - 5-minute setup guide
2. **DEPLOYMENT.md** - Full deployment documentation
3. **paper_trading/README.md** - Paper trading engine details
4. **deploy/crontab.example** - Scheduling examples

## ✅ Pre-Flight Checklist

Before Monday morning:

- [ ] API keys set in environment
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Test scripts manually once
- [ ] Review configuration in `config/paper_trading_config.py`
- [ ] Set up cron job (if using automation)
- [ ] Verify watchlist stocks are correct
- [ ] Check logs directory exists and is writable
- [ ] Backup any existing portfolio state
- [ ] Review risk limits one more time

## 🎯 Next Steps

1. **Test Today**: Run `./deploy/start_services.sh` and test the dashboard
2. **Dry Run**: Try `./deploy/start_paper_trading.sh` and watch logs for 10 minutes
3. **Schedule**: Set up cron job for Monday 9:00 AM (see `deploy/crontab.example`)
4. **Monitor**: Plan to watch first trades closely on Monday
5. **Optimize**: After 1 week, review performance and adjust configuration

## 🆘 Support

- Check logs in `logs/` directory
- Review configuration in `config/paper_trading_config.py`
- Read DEPLOYMENT.md for troubleshooting
- API docs at http://localhost:8000/docs

---

**System is ready for deployment! 🚀**

Good luck with your Monday morning trading! Remember:
- This is educational/paper trading only
- Not financial advice
- Monitor closely and adjust as needed
- Review performance weekly
