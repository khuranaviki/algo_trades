# Quick Start Guide - Agentic Trading System

Get started with paper trading in 5 minutes!

## Step 1: Set API Keys

```bash
# Export API keys (required)
export OPENAI_API_KEY="sk-your-openai-api-key-here"
export ANTHROPIC_API_KEY="sk-ant-your-anthropic-key-here"

# Optional: Make permanent by adding to ~/.bashrc or ~/.zshrc
echo 'export OPENAI_API_KEY="sk-your-key"' >> ~/.bashrc
echo 'export ANTHROPIC_API_KEY="sk-ant-your-key"' >> ~/.bashrc
source ~/.bashrc
```

## Step 2: Install Dependencies

```bash
# Install Python packages
pip install -r requirements.txt
```

## Step 3: Start Services

### Option A: Start Everything Together

```bash
# Start both API and Streamlit dashboard
./deploy/start_services.sh
```

This starts:
- FastAPI at http://localhost:8000
- Streamlit at http://localhost:8501

### Option B: Start Services Separately

```bash
# Terminal 1: API
uvicorn api.main:app --host 0.0.0.0 --port 8000

# Terminal 2: Streamlit
streamlit run streamlit_app.py --server.port 8501
```

## Step 4: Test the System

### Via Dashboard (Streamlit)

1. Open http://localhost:8501
2. Click "📊 Live Analysis" tab
3. Enter a stock ticker (e.g., RELIANCE.NS)
4. Click "🔍 Analyze"
5. View the decision, scores, and reasoning

### Via API (FastAPI)

```bash
# Analyze a stock
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{"ticker": "RELIANCE.NS", "use_llm": true}'

# Check portfolio
curl http://localhost:8000/portfolio
```

## Step 5: Start Automated Trading

```bash
# Start paper trading (runs continuously during market hours)
./deploy/start_paper_trading.sh
```

This will:
- Run Monday-Friday only
- Only trade during NSE hours (9:15 AM - 3:30 PM IST)
- Scan watchlist every 60 seconds
- Automatically execute trades based on agent analysis
- Log everything to `logs/paper_trading.log`

## Monitor Trading

```bash
# Watch live logs
tail -f logs/paper_trading.log

# Check portfolio via API
curl http://localhost:8000/portfolio | jq

# View on dashboard
open http://localhost:8501  # Click "💼 Portfolio" tab
```

## Stop Services

```bash
# Stop all services
./deploy/stop_services.sh
```

## Configuration

Edit `config/paper_trading_config.py` to customize:

```python
# Change watchlist
'watchlist': ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS'],

# Change scan frequency
'update_interval_seconds': 60,  # Scan every 60 seconds

# Adjust risk limits
'risk_management': {
    'max_position_size_pct': 5.0,    # 5% max per position
    'max_open_positions': 10,         # 10 max concurrent positions
    'max_drawdown_pct': 10.0,        # Stop if 10% drawdown
    'daily_loss_limit_pct': 3.0      # Stop if 3% daily loss
}

# Adjust decision thresholds
'buy_threshold': 70.0,        # Need 70+ score to BUY
'strong_buy_threshold': 85.0, # Need 85+ for STRONG_BUY
'sell_threshold': 40.0        # Below 40 triggers SELL
```

## Troubleshooting

### "Address already in use"
```bash
# Kill processes on ports
lsof -ti:8000 | xargs kill -9
lsof -ti:8501 | xargs kill -9
```

### "ModuleNotFoundError"
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### "API key not set"
```bash
# Check if keys are set
echo $OPENAI_API_KEY
echo $ANTHROPIC_API_KEY

# If empty, export them again
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"
```

### "All scores showing 0.0"
```bash
# Restart Streamlit to clear cache
./deploy/stop_services.sh
./deploy/start_services.sh
```

## Next Steps

1. **Test on Monday** with live market data
2. **Monitor first trades** closely in the dashboard
3. **Review logs** for any errors or warnings
4. **Adjust configuration** based on performance
5. **Read DEPLOYMENT.md** for advanced deployment options

## Important Notes

- This is **paper trading only** - no real money involved
- System uses AI models (OpenAI GPT-4, Anthropic Claude) which cost money per API call
- Keep API keys secret and never commit them to git
- Monitor API costs in OpenAI and Anthropic dashboards
- System is for **educational purposes only** - not financial advice

## Support

- Logs: Check `logs/` directory for detailed error messages
- Configuration: Review `config/paper_trading_config.py`
- Documentation: See `DEPLOYMENT.md` for full guide
- API Docs: http://localhost:8000/docs

---

**Ready to trade!** 🚀

For automated Monday morning startup, see "Scheduling" section in DEPLOYMENT.md
