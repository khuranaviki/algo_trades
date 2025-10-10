# Historical Backtest Simulator

## 🎯 Overview

The **Historical Backtest Simulator** replays the paper trading system over past periods (e.g., last 6 months) to see what would have happened if the system had been running live.

### Key Features

- ✅ **Day-by-day replay** - Simulates each trading day in sequence
- ✅ **No look-ahead bias** - Uses only data available at each decision point
- ✅ **Real orchestrator analysis** - Full 5-agent + LLM synthesis at each signal
- ✅ **Realistic costs** - NSE transaction costs and slippage
- ✅ **Complete trade log** - Every signal, entry, exit recorded
- ✅ **Performance metrics** - Sharpe, win rate, drawdown, monthly returns
- ✅ **Graded results** - Automatic A+ to F grading

## 🚀 Quick Start

### Run 6-Month Backtest (Default)

```bash
python3 run_historical_backtest.py
```

This will:
1. Download 6 months of historical data
2. Simulate day-by-day trading
3. Generate complete performance report
4. Save results to JSON file

### Run Quick Test (1 month, 3 stocks)

```bash
python3 run_historical_backtest.py --quick
```

Perfect for testing before running full backtest.

### Custom Period

```bash
# 3-month backtest
python3 run_historical_backtest.py --months 3

# Specific dates
python3 run_historical_backtest.py --start 2025-04-01 --end 2025-10-01
```

### Custom Stocks

```bash
# Test specific stocks
python3 run_historical_backtest.py --stocks RELIANCE TCS HDFCBANK INFY

# Combine with custom period
python3 run_historical_backtest.py --stocks RELIANCE TCS --months 3
```

## 📊 Output Example

```
================================================================================
  BACKTEST SUMMARY
================================================================================

💰 RETURNS:
   Total Return:     +12.5%
   Final Value:      ₹1,125,000
   Profit/Loss:      ₹+125,000

📊 RISK METRICS:
   Sharpe Ratio:     1.45
   Max Drawdown:     -8.2%
   Volatility:       15.3%

📈 TRADING ACTIVITY:
   BUY Signals:      15
   Trades Executed:  12
   Execution Rate:   80.0%
   Win Rate:         66.7%

💹 TRADE STATISTICS:
   Avg Win:          +6.5%
   Avg Loss:         -2.8%
   Profit Factor:    2.32
   Avg Trade:        ₹10,417

🏆 TOP 3 TRADES:
   1. TCS.NS        2025-07-15 | ₹+28,500 (+9.2%) | target_reached
   2. RELIANCE.NS   2025-08-22 | ₹+22,100 (+7.8%) | target_reached
   3. HDFCBANK.NS   2025-06-10 | ₹+18,750 (+6.5%) | target_reached

❌ WORST 3 TRADES:
   1. MARUTI.NS     2025-09-05 | ₹-12,300 (-4.2%) | stop_loss_hit
   2. TITAN.NS      2025-07-28 | ₹-8,900  (-3.5%) | stop_loss_hit
   3. TATAMOTORS.NS 2025-08-15 | ₹-6,500  (-2.8%) | stop_loss_hit

📅 MONTHLY BREAKDOWN:
   Month      Return     Ending Value
   ----------------------------------------
   2025-05    +3.5%      ₹1,035,000
   2025-06    +4.2%      ₹1,078,470
   2025-07    +2.8%      ₹1,108,650
   2025-08    -1.5%      ₹1,092,020
   2025-09    +2.1%      ₹1,114,930
   2025-10    +1.4%      ₹1,125,000

🎯 PERFORMANCE GRADE: A (Very Good)
================================================================================
```

## 🧪 How It Works

### 1. Data Fetching

```python
# Downloads historical data for all watchlist stocks
# Includes 5-year buffer for technical analysis
await backtest._fetch_historical_data()
```

### 2. Trading Days Generation

```python
# Generates list of actual trading days in period
# Excludes weekends and holidays
backtest._generate_trading_days()
```

### 3. Day-by-Day Simulation

For each trading day:

```python
# 1. Update position prices with current day's close
current_prices = backtest._get_prices_for_date(current_date)
portfolio.update_prices(current_prices)

# 2. Check existing positions for exits
for ticker in positions:
    if check_stop_loss(ticker, current_price):
        close_position(ticker, 'stop_loss_hit')
    elif check_target(ticker, current_price):
        close_position(ticker, 'target_reached')

# 3. Check for new entry signals
for ticker in watchlist:
    if ticker not in positions:
        result = await orchestrator.analyze(ticker)
        if result['decision'] == 'BUY':
            if risk_checks_pass():
                execute_buy(ticker)
```

### 4. Report Generation

```python
# Calculate performance metrics
metrics = portfolio.get_performance_metrics()

# Generate trade analysis
trades_df = pd.DataFrame(all_trades)

# Save complete report
backtest.save_report('backtest_report.json')
```

## 📈 Performance Metrics

### Returns
- Total return %
- Final portfolio value
- Profit/loss in rupees

### Risk Metrics
- Sharpe ratio (risk-adjusted returns)
- Max drawdown (worst peak-to-trough)
- Volatility (annualized std dev)

### Trading Stats
- Win rate (% of winning trades)
- Average win/loss %
- Profit factor (gross profit / gross loss)
- Average trade P&L

### Activity
- Number of BUY signals detected
- Number of trades executed
- Execution rate (trades / signals)
- LLM synthesis usage

## 🎯 Grading System

Performance is graded A+ to F based on:

| Metric | Weight | Excellent | Good | Average |
|--------|--------|-----------|------|---------|
| Total Return | 30% | ≥15% | ≥8% | ≥3% |
| Sharpe Ratio | 25% | ≥1.8 | ≥1.2 | ≥0.8 |
| Win Rate | 20% | ≥75% | ≥65% | ≥55% |
| Max Drawdown | 15% | ≤5% | ≤10% | ≤15% |
| Trade Count | 10% | ≥10 | ≥5 | ≥1 |

**Grades:**
- **A+ (90-100):** Excellent - Deploy with confidence
- **A (80-89):** Very Good - Minor tweaks recommended
- **B+ (70-79):** Good - Some optimization needed
- **B (60-69):** Above Average - Significant improvements needed
- **C (50-59):** Average - Major rework recommended
- **D (<50):** Poor - Strategy not viable

## ⚠️ Important Notes

### No Look-Ahead Bias

The backtest **strictly prevents look-ahead bias**:

```python
# ✅ CORRECT: Uses data up to (but not including) current date
historical_df = get_historical_data_until(ticker, current_date)
result = await orchestrator.analyze(ticker)

# ❌ WRONG: Would use future data
historical_df = get_all_data(ticker)  # Includes future!
```

Every analysis uses only data that would have been available at that time.

### Realistic Constraints

- ✅ NSE transaction costs (~0.25% round-trip)
- ✅ Slippage (0.05% default)
- ✅ Stop-loss/target execution
- ✅ Risk management limits
- ✅ Position sizing rules

### Computation Time

**Approximate times:**

| Period | Stocks | Time |
|--------|--------|------|
| 1 month | 3 | ~2 min |
| 3 months | 5 | ~8 min |
| 6 months | 10 | ~25 min |

Each signal requires full orchestrator analysis (5 agents + potential LLM calls).

### Cost

**LLM costs during backtest:**

- Entry signal analysis: $0.01 per stock per signal
- No cost for exits (stop/target checking)

**Example:**
- 6 months, 10 stocks
- Assume 1 signal per stock per month = 60 signals
- Cost: 60 × $0.01 = **$0.60 total**

Very affordable to validate strategy over long periods!

## 📋 Output Files

### JSON Report

Complete backtest data saved to:
```
backtest_report_YYYYMMDD_HHMMSS.json
```

Contains:
- Configuration used
- All trades (entries + exits)
- All signals detected
- Daily portfolio values
- Performance metrics
- Trade-by-trade P&L

### Log File

Detailed execution log saved to:
```
historical_backtest_YYYYMMDD_HHMMSS.log
```

Contains:
- Data download progress
- Each BUY/SELL execution
- Risk check results
- Error messages (if any)

## 🔧 Configuration

Uses same config as paper trading:

```python
from config.paper_trading_config import PAPER_TRADING_CONFIG

config = {
    **PAPER_TRADING_CONFIG,
    'start_date': datetime(2025, 4, 1),
    'end_date': datetime(2025, 10, 1)
}

backtest = HistoricalBacktest(config)
await backtest.run()
```

## 💡 Use Cases

### 1. Strategy Validation

Before deploying paper trading live:

```bash
# Test last 6 months
python3 run_historical_backtest.py

# Check: Sharpe ≥ 1.0, Win Rate ≥ 60%, Drawdown < 10%
# If passing → proceed to live paper trading
# If failing → iterate on strategy
```

### 2. Parameter Optimization

Test different configurations:

```bash
# Test with more conservative risk
python3 run_historical_backtest.py --config conservative

# Test with aggressive risk
python3 run_historical_backtest.py --config aggressive

# Compare results to find optimal
```

### 3. Market Regime Analysis

Test across different market conditions:

```bash
# Bull market period
python3 run_historical_backtest.py --start 2024-01-01 --end 2024-06-30

# Bear market period
python3 run_historical_backtest.py --start 2024-07-01 --end 2024-12-31

# Compare performance
```

### 4. Stock Selection

Identify best performers:

```bash
# Test each stock individually
for stock in RELIANCE TCS HDFCBANK INFY; do
    python3 run_historical_backtest.py --stocks $stock --months 6
done

# Focus on stocks with best Sharpe ratios
```

## 🚀 Next Steps

### After Running Backtest

1. **Review Performance**
   - Check grade (aim for B+ or better)
   - Analyze best/worst trades
   - Identify patterns in winners/losers

2. **If Results Good (Grade B+ or better)**
   - Proceed to live paper trading
   - Monitor for 1 week
   - Compare live vs backtest performance

3. **If Results Poor (Grade C or worse)**
   - Analyze trade-by-trade log
   - Identify systematic issues
   - Adjust configuration
   - Re-run backtest
   - Iterate until Grade B+ achieved

## 📚 Examples

### Example 1: Quick Validation

```bash
# Fast test before full run
python3 run_historical_backtest.py --quick

# If looks good, run full
python3 run_historical_backtest.py
```

### Example 2: Optimize Position Sizing

```python
# Test different max position sizes
for size in [3, 5, 7]:
    config = {**PAPER_TRADING_CONFIG}
    config['risk_management']['max_position_size_pct'] = size

    backtest = HistoricalBacktest(config)
    report = await backtest.run()

    print(f"Size {size}%: Sharpe = {report['performance']['sharpe_ratio']:.2f}")
```

### Example 3: Sector Focus

```bash
# Test IT sector only
python3 run_historical_backtest.py --stocks TCS INFY WIPRO TECHM

# Test Banking sector
python3 run_historical_backtest.py --stocks HDFCBANK ICICIBANK SBIN AXISBANK

# Compare sector performance
```

---

**Status:** ✅ Ready to use - Historical backtest simulator fully implemented!

**Recommendation:** Run 6-month backtest on full watchlist before deploying live paper trading.
