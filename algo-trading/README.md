# Algorithmic Trading System

A comprehensive algorithmic trading system built with Python and Backtrader, implementing strategies based on technical patterns (RHS, CWH) and fundamental analysis.

---

## 🎯 Features

- **Pattern-Based Strategies**
  - Reverse Head & Shoulder (RHS) Pattern Detection
  - Cup with Handle (CWH) Pattern Detection

- **Fundamental Screening**
  - Growth-based stock screening (Revenue, Profit, ROCE, ROE)
  - Multibagger potential identification
  - Debt and valuation analysis

- **Backtesting Framework**
  - Built on Backtrader - industry-standard backtesting library
  - Multi-ticker support
  - Comprehensive performance metrics

- **Risk Management**
  - Position sizing (2-5% per trade)
  - Stop loss and target management
  - Maximum concurrent positions control

---

## 📁 Project Structure

```
algo-trading/
├── strategies/
│   ├── __init__.py
│   ├── rhs_strategy.py              # Reverse Head & Shoulder strategy
│   ├── cwh_strategy.py              # Cup with Handle strategy
│   └── fundamental_screen_strategy.py  # Fundamental screening strategies
├── utils/
│   ├── __init__.py
│   ├── data_fetcher.py              # Data fetching utilities
│   └── performance_analyzer.py       # Performance analysis tools
├── data/                             # Data storage (auto-created)
├── backtest_results/                 # Results storage (auto-created)
├── logs/                             # Log files (auto-created)
├── backtest_engine.py               # Main backtesting engine
├── config.py                        # Configuration settings
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```

---

## 🛠️ Installation

### 1. Prerequisites

- Python 3.8 or higher
- pip package manager

### 2. Install Dependencies

```bash
cd algo-trading
pip install -r requirements.txt
```

### 3. Optional: Install TA-Lib (for advanced technical indicators)

**macOS:**
```bash
brew install ta-lib
pip install ta-lib
```

**Linux:**
```bash
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install
pip install ta-lib
```

**Windows:**
Download pre-built wheel from https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib

---

## 🚀 Usage

### Quick Start

Run the example backtest:

```bash
python backtest_engine.py
```

This will run a demo RHS strategy backtest on RELIANCE.NS for the past 2 years.

### Command Line Usage

```bash
python backtest_engine.py --strategy <strategy> --tickers <tickers> --start <start_date> --end <end_date> [options]
```

**Parameters:**
- `--strategy`: Strategy to use (`rhs`, `cwh`, `fundamental`, `multibagger`)
- `--tickers`: Space-separated list of ticker symbols (e.g., `RELIANCE.NS TCS.NS`)
- `--start`: Start date in YYYY-MM-DD format
- `--end`: End date in YYYY-MM-DD format
- `--cash`: Initial cash (default: 100000)
- `--commission`: Commission rate (default: 0.001 = 0.1%)
- `--save`: Save results to JSON file

### Examples

**1. RHS Strategy on Single Stock:**
```bash
python backtest_engine.py \
  --strategy rhs \
  --tickers RELIANCE.NS \
  --start 2023-01-01 \
  --end 2024-12-31 \
  --save
```

**2. CWH Strategy on Multiple Stocks:**
```bash
python backtest_engine.py \
  --strategy cwh \
  --tickers RELIANCE.NS TCS.NS INFY.NS \
  --start 2022-01-01 \
  --end 2024-12-31 \
  --cash 200000 \
  --save
```

**3. Fundamental Screening Strategy:**
```bash
python backtest_engine.py \
  --strategy fundamental \
  --tickers DELHIVERY.NS ZOMATO.NS \
  --start 2023-06-01 \
  --end 2024-12-31 \
  --save
```

**4. Multibagger Strategy:**
```bash
python backtest_engine.py \
  --strategy multibagger \
  --tickers DELHIVERY.NS POLICYBZR.NS DIXON.NS \
  --start 2023-01-01 \
  --end 2024-12-31 \
  --cash 150000 \
  --save
```

---

## 📊 Strategies Explained

### 1. RHS (Reverse Head & Shoulder) Strategy

**Pattern Detection:**
- Identifies 3 troughs: Left Shoulder, Head (deepest), Right Shoulder
- Right shoulder should be higher than left (bullish signal)
- Validates neckline breakout with volume

**Entry:**
- Price breaks above neckline
- Volume > 1.5x average
- Risk:Reward ratio ≥ 2:1

**Exit:**
- Target: Neckline + Pattern Depth
- Stop Loss: Below right shoulder low
- Trailing Stop: Below SMA 20

**Position Sizing:** 4% of portfolio

---

### 2. CWH (Cup with Handle) Strategy

**Pattern Detection:**
- U-shaped cup formation (12-33% depth)
- Shallow handle pullback (<15% of cup depth)
- Handle duration: 5 days to 30% of cup duration

**Entry:**
- Price breaks above handle high
- Volume > 1.5x average
- Risk:Reward ratio ≥ 2:1

**Exit:**
- Target: Breakout price + Cup depth
- Stop Loss: 3% below handle low
- Trailing Stop: Below SMA 20

**Position Sizing:** 4% of portfolio

---

### 3. Fundamental Screening Strategy

**Screening Criteria:**
- Revenue Growth > 20% YoY
- ROCE > 20%
- ROE > 15%
- Debt-to-Equity < 1.0
- Market Cap < ₹50,000 Cr

**Technical Entry:**
- Golden Cross (SMA 20 crosses above SMA 50)
- RSI < 70 (not overbought)
- Price above SMA 20

**Exit:**
- Target: 20% gain
- Stop Loss: 10% loss
- Death Cross (SMA 20 crosses below SMA 50)
- RSI > 70 (overbought)

**Position Sizing:** 3% of portfolio
**Max Positions:** 5 concurrent

---

### 4. Multibagger Strategy

**Aggressive Screening Criteria:**
- Revenue Growth > 25% YoY
- ROCE > 25%
- ROE > 20%
- Debt-to-Equity < 0.5 (low debt)
- Market Cap < ₹10,000 Cr (small cap)

**Technical Entry:**
- Same as Fundamental strategy

**Exit:**
- Target: 30% gain (higher)
- Stop Loss: 12% loss (wider)

**Position Sizing:** 5% of portfolio
**Max Positions:** 3 concurrent (concentrated)

---

## 📈 Performance Metrics

The backtest engine provides the following metrics:

- **Total Return (%)**: Overall portfolio return
- **Sharpe Ratio**: Risk-adjusted return metric
- **Maximum Drawdown (%)**: Largest peak-to-trough decline
- **Win Rate (%)**: Percentage of winning trades
- **Total Trades**: Number of trades executed
- **Profit Factor**: Gross profit / Gross loss
- **Expectancy**: Average expected return per trade

---

## 🔧 Configuration

Edit `config.py` to customize:

### Portfolio Settings
```python
INITIAL_CASH = 100000  # Starting capital
COMMISSION_RATE = 0.001  # 0.1% commission
```

### Strategy Parameters
```python
RHS_PARAMS = {
    'min_pattern_days': 100,
    'volume_threshold': 1.5,
    'position_size_pct': 0.04,
    # ... more parameters
}
```

### Stock Universes
```python
NIFTY_50 = ['RELIANCE.NS', 'TCS.NS', ...]
MID_CAP_STOCKS = ['DELHIVERY.NS', 'ZOMATO.NS', ...]
SECTORS = {
    'PHARMA': [...],
    'IT': [...],
    # ... more sectors
}
```

---

## 📊 Analyzing Results

### View Results Summary

Results are printed to console after each backtest:

```
================================================================================
📊 BACKTEST RESULTS: RHSPatternStrategy
================================================================================
Tickers:          RELIANCE.NS
Period:           2023-01-01 to 2024-12-31

💰 PERFORMANCE:
Initial Cash:     ₹100,000.00
Final Value:      ₹125,450.00
Total Return:     25.45% (₹25,450.00)
Sharpe Ratio:     1.45
Max Drawdown:     -8.32%

📈 TRADING STATISTICS:
Total Trades:     8
Won Trades:       6
Lost Trades:      2
Win Rate:         75.00%
================================================================================
```

### Saved Results

Results are saved as JSON in `backtest_results/` directory:

```json
{
  "strategy": "RHSPatternStrategy",
  "tickers": ["RELIANCE.NS"],
  "start_date": "2023-01-01",
  "end_date": "2024-12-31",
  "initial_cash": 100000.0,
  "final_value": 125450.0,
  "total_return": 25.45,
  "sharpe_ratio": 1.45,
  "max_drawdown": -8.32,
  "total_trades": 8,
  "won_trades": 6,
  "lost_trades": 2,
  "win_rate": 75.0
}
```

### Compare Multiple Strategies

Use the performance analyzer:

```python
from utils.performance_analyzer import PerformanceAnalyzer

analyzer = PerformanceAnalyzer()
results = analyzer.load_all_results('backtest_results')
comparison = analyzer.compare_strategies(results)
analyzer.print_comparison(comparison)
```

---

## 🎓 Advanced Usage

### Custom Strategy Development

1. Create a new strategy file in `strategies/` directory
2. Inherit from `bt.Strategy`
3. Implement `__init__()`, `next()`, and optional `notify_order()`, `notify_trade()` methods

Example:

```python
import backtrader as bt

class MyCustomStrategy(bt.Strategy):
    params = (
        ('my_param', 10),
    )

    def __init__(self):
        self.sma = bt.indicators.SMA(self.data.close, period=self.params.my_param)

    def next(self):
        if not self.position:
            if self.data.close[0] > self.sma[0]:
                self.buy()
        else:
            if self.data.close[0] < self.sma[0]:
                self.sell()
```

### Integration with Existing Analysis System

The algo-trading system integrates with the parent `streamlit-market-analysis` project:

```python
from utils.data_fetcher import DataFetcher

fetcher = DataFetcher()

# Fetch fundamental data using existing scraper
fund_data = fetcher.fetch_fundamental_data('RELIANCE.NS')

# Use in strategy
cerebro.addstrategy(FundamentalScreenStrategy, fundamental_data=fund_data)
```

---

## 🔍 Data Sources

- **OHLCV Data**: Yahoo Finance via `yfinance`
- **Fundamental Data**: Screener.in via parent project's `fundamental_scraper.py`
- **Supported Markets**:
  - Indian stocks (NSE): Add `.NS` suffix (e.g., `RELIANCE.NS`)
  - US stocks: Use ticker directly (e.g., `AAPL`)

---

## 🛡️ Risk Disclaimer

**IMPORTANT**: This is a backtesting and research tool.

- Past performance does NOT guarantee future results
- Backtests may suffer from overfitting, look-ahead bias, and survivorship bias
- Real trading involves slippage, market impact, and other costs not fully captured
- This is NOT financial advice
- Always paper trade strategies before using real money
- Consult with a financial advisor before making investment decisions

---

## 📝 Logging

Logs are stored in `logs/` directory. Configure logging in `config.py`:

```python
LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR
```

Enable detailed logging in strategies:

```python
cerebro.addstrategy(RHSPatternStrategy, print_log=True)
```

---

## 🤝 Contributing

To add new features:

1. Create new strategy in `strategies/`
2. Add strategy to `backtest_engine.py` strategy map
3. Update `config.py` with strategy parameters
4. Test thoroughly with multiple stocks and time periods
5. Document the strategy in this README

---

## 📚 Resources

### Backtrader Documentation
- Official Docs: https://www.backtrader.com/docu/
- Community: https://community.backtrader.com/

### Strategy References
- RHS Pattern: Based on classic technical analysis
- CWH Pattern: William O'Neil's CAN SLIM methodology
- Fundamental Screening: Growth investing principles

### Python Libraries
- Backtrader: https://github.com/mementum/backtrader
- yfinance: https://github.com/ranaroussi/yfinance
- Pandas: https://pandas.pydata.org/

---

## 🐛 Troubleshooting

### Common Issues

**1. "No data found for ticker"**
- Verify ticker symbol is correct (use `.NS` for Indian stocks)
- Check date range is valid
- Ensure internet connection is active

**2. "No module named 'strategies'"**
- Run from the `algo-trading` directory
- Ensure `__init__.py` files exist in subdirectories

**3. "Pattern not detected"**
- Patterns are rare - try longer time periods (2+ years)
- Adjust pattern parameters in `config.py`
- Enable debug logging to see detection details

**4. "TA-Lib installation failed"**
- TA-Lib is optional, strategies work without it
- Follow platform-specific installation instructions above

---

## 📞 Support

For issues and questions:
1. Check existing documentation
2. Review backtest logs in `logs/` directory
3. Refer to parent project documentation in `../ANALYSIS_STRATEGY_DOCUMENTATION.md`

---

## 📄 License

This project inherits the license from the parent `streamlit-market-analysis` project.

---

## 🎯 Next Steps

1. **Run Example Backtests**: Test each strategy on different stocks
2. **Analyze Results**: Compare strategy performance
3. **Customize Parameters**: Tune strategies for your risk tolerance
4. **Paper Trade**: Test strategies in real-time without real money
5. **Iterate**: Refine strategies based on results

**Happy Backtesting! 📈**
