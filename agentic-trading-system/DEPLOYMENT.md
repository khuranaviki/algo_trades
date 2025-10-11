# Deployment Guide - Agentic Trading System

## Overview
This guide will help you deploy the Agentic Trading System for automated paper trading starting Monday morning.

## System Components

1. **FastAPI Backend** (Port 8000) - REST API for stock analysis
2. **Streamlit Dashboard** (Port 8501) - Interactive UI
3. **Paper Trading Engine** - Automated trading orchestrator
4. **Scheduler** - Runs analysis on watchlist every 60 seconds during market hours

## Prerequisites

### System Requirements
- Python 3.9+
- 4GB RAM minimum
- Stable internet connection
- Operating System: Linux, macOS, or Windows

### Required API Keys
Set these environment variables before deployment:

```bash
# OpenAI API (for Fundamental analysis with GPT-4)
export OPENAI_API_KEY="your-openai-api-key-here"

# Anthropic API (for Management analysis with Claude)
export ANTHROPIC_API_KEY="your-anthropic-api-key-here"

# Optional: Perplexity API (currently disabled due to event loop issues)
# export PERPLEXITY_API_KEY="your-perplexity-api-key-here"
```

### Install Dependencies

```bash
cd agentic-trading-system
pip install -r requirements.txt
```

## Quick Start

### Method 1: Run Both Services Together (Recommended)

```bash
# Start both API and Streamlit together
./deploy/start_services.sh
```

This will:
- Start FastAPI on http://localhost:8000
- Start Streamlit on http://localhost:8501
- Log output to `logs/api.log` and `logs/streamlit.log`

### Method 2: Run Services Separately

```bash
# Terminal 1: Start FastAPI
uvicorn api.main:app --host 0.0.0.0 --port 8000

# Terminal 2: Start Streamlit
streamlit run streamlit_app.py --server.port 8501
```

## Automated Paper Trading

### Option 1: Continuous Trading (Market Hours)

Run the paper trading engine continuously during market hours:

```bash
# Start automated paper trading
./deploy/start_paper_trading.sh
```

This script:
- Runs Monday-Friday only
- Active during NSE market hours: 9:15 AM - 3:30 PM IST
- Scans watchlist every 60 seconds
- Automatically executes trades based on agent analysis
- Logs all trades to `logs/paper_trading.log`

### Option 2: Manual Paper Trading

Run the engine manually for testing:

```bash
python paper_trading/run_paper_trading.py
```

### Option 3: Schedule with Cron (Linux/macOS)

Set up automated start every Monday morning:

```bash
# Edit crontab
crontab -e

# Add this line to start trading at 9:00 AM every Monday-Friday
0 9 * * 1-5 cd /path/to/agentic-trading-system && ./deploy/start_paper_trading.sh >> logs/cron.log 2>&1
```

### Option 4: Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Weekly, Monday-Friday at 9:00 AM
4. Action: Start a program
5. Program: `C:\path\to\python.exe`
6. Arguments: `paper_trading/run_paper_trading.py`
7. Start in: `C:\path\to\agentic-trading-system`

## Configuration

### Trading Configuration

Edit `config/paper_trading_config.py`:

```python
PAPER_TRADING_CONFIG = {
    # Capital
    'initial_capital': 1000000,  # ₹10 lakhs

    # Watchlist (10 stocks)
    'watchlist': [
        'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS',
        'INFY.NS', 'ICICIBANK.NS', 'BHARTIARTL.NS',
        'BAJFINANCE.NS', 'TITAN.NS', 'MARUTI.NS', 'TATAMOTORS.NS'
    ],

    # Scan interval
    'update_interval_seconds': 60,  # Every 60 seconds

    # Risk management
    'risk_management': {
        'max_position_size_pct': 5.0,
        'max_open_positions': 10,
        'max_drawdown_pct': 10.0,
        'daily_loss_limit_pct': 3.0
    }
}
```

### Agent Weights

Adjust agent importance in `config/paper_trading_config.py`:

```python
'weights': {
    'fundamental': 0.25,      # 25% - Company financials
    'technical': 0.20,        # 20% - Price patterns
    'sentiment': 0.20,        # 20% - News/sentiment
    'management': 0.15,       # 15% - Management quality
    'market_regime': 0.10,    # 10% - Market conditions
    'risk_adjustment': 0.10   # 10% - Risk factors
}
```

### Decision Thresholds

```python
'buy_threshold': 70.0,        # Minimum 70/100 score to BUY
'strong_buy_threshold': 85.0, # Minimum 85/100 for STRONG_BUY
'sell_threshold': 40.0        # Below 40/100 triggers SELL
```

## Monitoring

### View Live Logs

```bash
# API logs
tail -f logs/api.log

# Streamlit logs
tail -f logs/streamlit.log

# Paper trading logs
tail -f logs/paper_trading.log

# Application logs
tail -f streamlit_app.log
```

### Dashboard Access

- **Streamlit Dashboard**: http://localhost:8501
  - Live Analysis tab: Analyze stocks manually
  - Portfolio tab: View positions and P&L
  - Performance tab: View equity curve
  - Settings tab: Adjust configuration

- **FastAPI Swagger Docs**: http://localhost:8000/docs
  - Interactive API documentation
  - Test endpoints directly

### Health Checks

```bash
# Check if services are running
curl http://localhost:8000/health
curl http://localhost:8501/_stcore/health

# Check portfolio status via API
curl http://localhost:8000/portfolio
```

## Trading System Behavior

### How It Works

1. **Watchlist Scanning**: Every 60 seconds, the system analyzes all stocks in the watchlist
2. **Multi-Agent Analysis**: 6 agents analyze each stock:
   - Fundamental Agent (financials, ratios, growth)
   - Technical Agent (patterns, indicators, 5-year validation)
   - Sentiment Agent (news, social media, market sentiment)
   - Management Agent (quarterly reports, guidance quality)
   - Market Regime Agent (bull/bear/sideways detection)
   - Pattern Validator (historical pattern success validation)

3. **Decision Making**:
   - Composite score calculated from weighted agent scores
   - Score ≥ 70: BUY signal
   - Score ≥ 85: STRONG_BUY signal
   - Score < 40: SELL existing positions
   - Score 40-70: WAIT

4. **Trade Execution**:
   - Position sizing based on score and risk level
   - Stop-loss and target prices from technical analysis
   - Transaction costs included (NSE realistic costs)
   - Maximum 5% per position, 10 max positions

5. **Risk Management**:
   - Stop trading if 10% drawdown reached
   - Stop trading if 3% daily loss reached
   - Reduce position size after 3 consecutive losses
   - Maximum 30% exposure per sector

### Trade Examples

**BUY Signal (Score: 75/100)**
```
Analyzing RELIANCE.NS...
├─ Fundamental: 80/100 (Strong financials)
├─ Technical: 75/100 (Bullish breakout pattern)
├─ Sentiment: 70/100 (Positive news)
├─ Management: 65/100 (Good guidance)
├─ Market Regime: 80/100 (Strong bull market)
└─ Composite: 75/100

Decision: BUY
Position Size: 50 shares (₹2,50,000 / 2.5% of portfolio)
Entry: ₹2,500
Stop Loss: ₹2,375 (5% below)
Target: ₹2,750 (10% above)
```

**SELL Signal (Score: 35/100)**
```
Analyzing TATAMOTORS.NS...
├─ Fundamental: 40/100 (Declining margins)
├─ Technical: 30/100 (Bearish breakdown)
├─ Sentiment: 25/100 (Negative news)
├─ Management: 40/100 (Weak guidance)
├─ Market Regime: 45/100 (Market weakness)
└─ Composite: 35/100

Decision: SELL
Closing position: 100 shares @ ₹850
Entry was: ₹800
P&L: +₹5,000 (+6.25%)
```

## Stopping Services

### Stop All Services

```bash
./deploy/stop_services.sh
```

### Stop Individual Services

```bash
# Find process IDs
ps aux | grep uvicorn
ps aux | grep streamlit
ps aux | grep paper_trading

# Kill by PID
kill <PID>

# Or kill by name
pkill -f "uvicorn api.main"
pkill -f "streamlit run"
pkill -f "run_paper_trading"
```

## Backup and Recovery

### Backup Portfolio State

```bash
# Create backup directory
mkdir -p backups

# Backup portfolio and trade history
cp data/portfolio_state.json backups/portfolio_$(date +%Y%m%d_%H%M%S).json
cp data/trade_history.csv backups/trades_$(date +%Y%m%d_%H%M%S).csv
```

### Restore Portfolio State

```bash
# Restore from backup
cp backups/portfolio_20250110_090000.json data/portfolio_state.json
cp backups/trades_20250110_090000.csv data/trade_history.csv
```

## Troubleshooting

### Services Won't Start

**Issue**: "Address already in use"
```bash
# Find and kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Find and kill process on port 8501
lsof -ti:8501 | xargs kill -9
```

**Issue**: "ModuleNotFoundError"
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### API Key Issues

**Issue**: "Anthropic API Error"
```bash
# Check if key is set
echo $ANTHROPIC_API_KEY

# Set permanently in ~/.bashrc or ~/.zshrc
echo 'export ANTHROPIC_API_KEY="your-key"' >> ~/.bashrc
source ~/.bashrc
```

**Issue**: "OpenAI Rate Limit"
- Reduce `update_interval_seconds` to 120 or 300 (slower scanning)
- Disable LLM analysis in config: `'use_llm': False`

### Trading Issues

**Issue**: "No positions being opened"
- Check logs for veto reasons
- Lower `buy_threshold` from 70 to 65 in config
- Check if sufficient cash available
- Verify stock prices are being fetched

**Issue**: "All scores showing 0.0"
- Restart Streamlit to clear cache: `Ctrl+C` then restart
- Check logs for agent errors
- Verify API keys are set correctly

**Issue**: "Event loop is already running"
- This is why Perplexity is disabled
- Keep `use_perplexity: False` in config
- LLM analysis uses sync calls to avoid this

## Performance Optimization

### Reduce API Costs

```python
# Disable LLM analysis (fallback to rule-based)
'fundamental_config': {'use_llm': False},
'management_config': {'use_llm': False},

# Reduce scan frequency
'update_interval_seconds': 300,  # 5 minutes instead of 60 seconds
```

### Speed Up Analysis

```python
# Reduce historical data lookback
'technical_config': {
    'lookback_days': 365,  # 1 year instead of 5
    'validate_patterns': False  # Disable pattern validation
}
```

## Security Best Practices

1. **Never commit API keys** to git
2. **Use environment variables** for sensitive data
3. **Restrict file permissions**: `chmod 600 config/secrets.env`
4. **Enable firewall** on production servers
5. **Use HTTPS** if exposing services externally
6. **Regularly rotate API keys**

## Next Steps

1. **Test on Monday morning** with real market data
2. **Monitor first few trades** closely
3. **Adjust agent weights** based on performance
4. **Review weekly performance** metrics
5. **Backup portfolio state** daily

## Support

- **Logs**: Check `logs/` directory for detailed error messages
- **Configuration**: Review `config/paper_trading_config.py`
- **API Docs**: http://localhost:8000/docs
- **Dashboard**: http://localhost:8501

## License

This is a paper trading system for educational purposes. Not financial advice.
