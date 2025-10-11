# Agentic Trading System

An AI-powered multi-agent trading system that makes highly informed stock trading decisions through comprehensive analysis of fundamentals, technicals (with mandatory 5-year backtest validation), sentiment, and management quality.

## 🎯 Key Features

- **Multi-Agent Architecture**: 6 specialized agents working in concert
- **Dual Validation**: Every technical strategy must prove >70% win rate on 5-year backtest
- **LLM-Powered Analysis**: GPT-4 & Claude-3.5 for deep insights
- **Management Quality Assessment**: Con-calls & annual report analysis
- **Intelligent Caching**: 90-day cache for validated strategies
- **Production Ready**: Docker, CI/CD, monitoring

## 📊 Expected Performance

| Metric | Target |
|--------|--------|
| CAGR | 18-22% |
| Win Rate | 75-85% |
| Max Drawdown | <12% |
| Sharpe Ratio | >1.5 |

## 🏗️ Architecture

```
Orchestrator Agent
├── Fundamental Analyst (Financial health, growth, valuation)
├── Technical Analyst (Pattern detection + indicators)
│   └── Backtest Validator (5-year validation, >70% WR)
├── Sentiment Analyst (News, social media, analysts)
└── Management Quality Analyst (Con-calls, annual reports)
```

## 🚀 Quick Start

### ⚡ NEW: Ready for Deployment!

**For automated paper trading starting Monday morning:**

1. **Read [QUICKSTART.md](QUICKSTART.md)** - Get started in 5 minutes
2. **Or read [DEPLOYMENT.md](DEPLOYMENT.md)** - Full deployment guide

```bash
# 1. Set API keys
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"

# 2. Start services
./deploy/start_services.sh

# 3. Start automated trading
./deploy/start_paper_trading.sh
```

Access dashboard at http://localhost:8501

---

### Prerequisites

- Python 3.9+
- OpenAI API key (GPT-4)
- Anthropic API key (Claude)

### Installation

```bash
# Clone repository
cd agentic-trading-system

# Install dependencies
pip install -r requirements.txt

# Create virtual environment (optional)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
# Edit .env with your API keys

# Start databases
docker-compose up -d postgres redis

# Initialize database
python scripts/setup_database.py

# Run system
python scripts/run_daily_analysis.py
```

## 📁 Project Structure

```
agentic-trading-system/
├── agents/                  # All agent implementations
├── tools/                   # Data fetchers, analyzers, LLM clients
├── orchestration/           # LangGraph workflow
├── storage/                 # Data, documents, cache
├── config/                  # Configuration files
├── tests/                   # Unit, integration, E2E tests
└── docker/                  # Docker configuration
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=agents --cov=tools --cov-report=html

# Run specific test suite
pytest tests/unit/agents/test_backtest_validator.py -v
```

## 📚 Documentation

See [AGENTIC_TRADING_SYSTEM_IMPLEMENTATION_GUIDE.md](../algo-trading/AGENTIC_TRADING_SYSTEM_IMPLEMENTATION_GUIDE.md) for complete documentation.

## 💰 Cost Estimation

- **Month 1**: ~$2,420 (no cache)
- **Month 2+**: ~$484 (70% cache hit)
- **Annual**: ~$5,808

## 📈 Roadmap

- [x] Complete architecture design
- [x] Implementation guide
- [ ] Week 1-2: Foundation (Base agents, LLM clients, data fetchers)
- [ ] Week 3: Backtest Validator (CRITICAL)
- [ ] Week 4-6: All agents implementation
- [ ] Week 7: Orchestrator
- [ ] Week 8: System backtest
- [ ] Week 9: API & UI
- [ ] Week 10-11: Production deployment

## 🤝 Contributing

This is a private trading system. For questions or issues, contact the development team.

## ⚠️ Disclaimer

This is a backtesting and research tool. Past performance does not guarantee future results. Always paper trade strategies before using real money. This is NOT financial advice.

## 📄 License

Proprietary - All Rights Reserved

---

**Status**: 🚧 Under Development - Week 1 Foundation Phase
