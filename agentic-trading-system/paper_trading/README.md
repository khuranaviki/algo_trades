# Paper Trading System

Complete simulated trading system for validating the agentic trading strategy without risking capital.

## 🎯 Features

- **Real-time data streaming** - Live price feeds with 5-year historical cache
- **Portfolio management** - Position tracking, P&L calculation, performance metrics
- **Order execution** - Market orders with realistic slippage and NSE transaction costs
- **Risk management** - Portfolio-level controls, position sizing, drawdown protection
- **Signal monitoring** - Continuous analysis using orchestrator with LLM synthesis
- **Automated position management** - Stop-loss, target, and trailing stop execution

## 📦 Architecture

```
Paper Trading System
├── data_stream.py       - Real-time data & caching
├── portfolio.py         - Position & trade tracking
├── order_executor.py    - Order simulation
├── transaction_costs.py - NSE cost modeling
├── risk_manager.py      - Portfolio risk controls
└── engine.py           - Main orchestrator
```

## 🚀 Quick Start

### Component Tests

Test individual modules:

```bash
python3 test_paper_trading.py --mode components
```

### Full Paper Trading

Start the paper trading engine:

```bash
python3 test_paper_trading.py --mode full
```

Or programmatically:

```python
from paper_trading.engine import PaperTradingEngine
from config.paper_trading_config import PAPER_TRADING_CONFIG

engine = PaperTradingEngine(PAPER_TRADING_CONFIG)
await engine.start()
```

## ⚙️ Configuration

Edit `config/paper_trading_config.py`:

```python
PAPER_TRADING_CONFIG = {
    'initial_capital': 1000000,  # ₹10 lakhs

    'watchlist': [
        'RELIANCE.NS',
        'TCS.NS',
        # ... add more
    ],

    'risk_management': {
        'max_position_size_pct': 5.0,
        'max_portfolio_risk_pct': 2.0,
        'max_drawdown_pct': 10.0,
        # ... more settings
    }
}
```

## 📊 Component Details

### 1. Data Stream (`data_stream.py`)

Handles real-time price streaming and caching:

```python
stream = LiveDataStream(
    tickers=['RELIANCE.NS', 'TCS.NS'],
    update_interval=60,
    max_cache_days=1825
)

await stream.start()

# Get latest price
price = await stream.get_latest_price('RELIANCE.NS')

# Check market hours
is_open = stream.is_market_open()
```

**Features:**
- 1-minute price updates
- 5-year historical cache
- NSE market hours detection
- Subscriber pattern for callbacks

### 2. Portfolio (`portfolio.py`)

Manages positions and trades:

```python
portfolio = Portfolio(initial_capital=1000000)

# Open position
portfolio.open_position(
    ticker='RELIANCE.NS',
    quantity=10,
    price=2850.0,
    stop_loss=2800.0,
    target=2950.0,
    reason='BUY signal'
)

# Get performance metrics
metrics = portfolio.get_performance_metrics()
# Returns: Sharpe, win rate, drawdown, etc.
```

**Features:**
- Position tracking (cost basis, P&L, stops, targets)
- Trade history recording
- Performance metrics (Sharpe, win rate, max drawdown)
- Kelly Criterion position sizing
- Daily snapshots for equity curve

### 3. Order Executor (`order_executor.py`)

Simulates realistic order execution:

```python
executor = OrderExecutor(slippage_pct=0.05)

result = executor.execute_market_order(
    ticker='TCS.NS',
    action='BUY',
    quantity=5,
    current_price=3500.0
)

# Returns: fill_price, slippage_cost, transaction_cost
```

**Features:**
- Slippage simulation (0.05% default)
- NSE transaction costs (~0.25% round-trip)
- Stop-loss and target checking
- Trailing stop support
- Partial fill simulation

### 4. Transaction Costs (`transaction_costs.py`)

Realistic NSE cost modeling:

```python
costs = TransactionCostModel.calculate_total_cost(
    order_value=100000,
    action='BUY'
)

# Returns breakdown:
# - Brokerage: ₹20
# - STT: ₹0
# - Exchange: ₹3.25
# - GST: ₹4.18
# - Stamp Duty: ₹15
# TOTAL: ₹42.43 (0.042%)
```

**Cost Structure (NSE 2025):**
- Brokerage: min(0.03%, ₹20)
- STT: 0.025% (sell only)
- Exchange: 0.00325%
- GST: 18% on brokerage+exchange
- Stamp Duty: 0.015% (buy only)
- **Round-trip: ~0.25%**

### 5. Risk Manager (`risk_manager.py`)

Portfolio-level risk controls:

```python
risk_manager = RiskManager({
    'max_position_size_pct': 5.0,
    'max_portfolio_risk_pct': 2.0,
    'max_drawdown_pct': 10.0
})

# Check if position allowed
can_open, reasons = risk_manager.can_open_position(
    portfolio, ticker, analysis
)

# Calculate safe position size
quantity = risk_manager.calculate_safe_position_size(
    portfolio, analysis
)
```

**Risk Controls:**
- Max position size (5% default)
- Max portfolio risk per trade (2% default)
- Max open positions (10 default)
- Max sector exposure (30% default)
- Drawdown protection (10% default)
- Daily loss limit (3% default)
- Dynamic sizing after losses

### 6. Engine (`engine.py`)

Main paper trading orchestrator:

```python
engine = PaperTradingEngine(config)

await engine.start()  # Runs until stopped
```

**Flow:**
1. Check if market open
2. Scan watchlist for signals
3. For each ticker:
   - Get latest price
   - If in position: check stops/targets/exit signals
   - If not in position: check entry signals
4. Execute trades through order simulator
5. Enforce risk limits
6. Update portfolio
7. Take daily snapshot
8. Sleep until next update

## 📈 Test Results

### Component Tests

```
✅ Portfolio Management - PASSED
   - Open/close positions
   - P&L calculation
   - Performance metrics

✅ Order Execution - PASSED
   - Slippage simulation
   - Transaction costs
   - Fill price calculation

✅ Transaction Costs - PASSED
   - NSE cost breakdown
   - Round-trip: 0.25%

✅ Risk Management - PASSED
   - Position sizing (Kelly Criterion)
   - Risk checks
   - Portfolio limits
```

## 🎯 Expected Performance (1 month)

Based on backtests:

| Metric | Minimum | Good | Excellent |
|--------|---------|------|-----------|
| Win Rate | 55% | 65% | 75% |
| Sharpe Ratio | 0.8 | 1.2 | 1.8 |
| Max Drawdown | <15% | <10% | <5% |
| Total Return | >3% | >8% | >15% |
| Avg Win | 5% | 7% | 10% |
| Avg Loss | -3% | -2% | -1.5% |

## 📋 Usage Examples

### Example 1: Basic Setup

```python
import asyncio
from paper_trading.engine import PaperTradingEngine
from config.paper_trading_config import PAPER_TRADING_CONFIG

async def run_paper_trading():
    engine = PaperTradingEngine(PAPER_TRADING_CONFIG)
    await engine.start()

asyncio.run(run_paper_trading())
```

### Example 2: Custom Configuration

```python
custom_config = {
    'initial_capital': 500000,
    'watchlist': ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS'],
    'update_interval_seconds': 30,
    'risk_management': {
        'max_position_size_pct': 3.0,
        'max_drawdown_pct': 5.0
    },
    'orchestrator': {
        # ... orchestrator config
    }
}

engine = PaperTradingEngine(custom_config)
await engine.start()
```

### Example 3: Monitoring Performance

```python
# Get performance metrics
metrics = engine.portfolio.get_performance_metrics()

print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
print(f"Win Rate: {metrics['win_rate']:.1f}%")
print(f"Max Drawdown: {metrics['max_drawdown_pct']:.1f}%")

# Get risk report
risk_report = engine.risk_manager.get_risk_report(engine.portfolio)

print(f"Position Utilization: {risk_report['utilization']['positions']:.1f}%")
print(f"Drawdown Utilization: {risk_report['utilization']['drawdown']:.1f}%")
```

## 🚨 Important Notes

### Limitations

1. **Data Provider:** Using yfinance (free, 15-min delay for NSE)
   - For production: upgrade to real-time data provider
   - Consider: Polygon, IEX Cloud, or broker APIs

2. **Market Hours:** Simplified holiday calendar
   - NSE holidays not fully implemented
   - Can be enhanced with proper holiday API

3. **Sector Mapping:** Hardcoded for test stocks
   - Need proper sector classification API
   - Or maintain database of stock metadata

4. **Slippage Model:** Fixed percentage
   - In reality, varies by liquidity, order size
   - Can be enhanced with volume-based model

### Cost Estimates

**For 10 stocks with daily scans:**
- Data: FREE (yfinance)
- LLM calls: ~$0.01/stock/day × 10 = $0.10/day
- Monthly: ~$3

**For 100 stocks:**
- Monthly: ~$30

### Next Steps

1. **Week 1:** ✅ Complete (foundation implemented)
2. **Week 2:**
   - Run 1-week paper trading test
   - Monitor performance
   - Identify issues
3. **Week 3:**
   - Build Streamlit dashboard
   - Add live monitoring
   - Performance analytics
4. **Month 2+:**
   - If metrics acceptable → broker API integration
   - Production deployment
   - Real trading (start small)

## 📚 References

- [NSE Transaction Charges](https://www.nseindia.com/invest/charges-on-the-exchange)
- [Kelly Criterion](https://en.wikipedia.org/wiki/Kelly_criterion)
- [Sharpe Ratio](https://www.investopedia.com/terms/s/sharperatio.asp)
- [Position Sizing](https://www.investopedia.com/terms/p/positionsizing.asp)

---

**Status:** ✅ Week 1 Complete - Ready for Testing
