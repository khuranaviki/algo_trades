#!/usr/bin/env python3
"""
Test all strategies for last 1 year with Rs 100,000 initial capital
"""

from datetime import datetime, timedelta
from backtest_engine import BacktestEngine
from strategies.rhs_strategy import RHSPatternStrategy
from strategies.cwh_strategy import CWHPatternStrategy
from strategies.fundamental_screen_strategy import FundamentalScreenStrategy

# Calculate date range
end_date = datetime.now().strftime('%Y-%m-%d')
start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

print("\n" + "="*100)
print(f"📊 BACKTESTING STRATEGIES FOR LAST 1 YEAR")
print(f"Period: {start_date} to {end_date}")
print(f"Initial Capital: ₹100,000")
print("="*100)

# Initialize engine
engine = BacktestEngine(initial_cash=100000, commission=0.001)

# List to store all results
all_results = []

# =============================================================================
# Test 1: RHS Strategy on Blue Chip Stocks
# =============================================================================
print("\n" + "="*100)
print("Test 1: RHS Pattern Strategy on RELIANCE.NS")
print("="*100)

try:
    results = engine.run_backtest(
        strategy_class=RHSPatternStrategy,
        tickers=['RELIANCE.NS'],
        start_date=start_date,
        end_date=end_date,
        strategy_params={'print_log': False}
    )
    if results:
        all_results.append(results)
except Exception as e:
    print(f"Error in RHS test: {e}")

# =============================================================================
# Test 2: CWH Strategy on IT Stock
# =============================================================================
print("\n" + "="*100)
print("Test 2: CWH Pattern Strategy on TCS.NS")
print("="*100)

try:
    results = engine.run_backtest(
        strategy_class=CWHPatternStrategy,
        tickers=['TCS.NS'],
        start_date=start_date,
        end_date=end_date,
        strategy_params={'print_log': False}
    )
    if results:
        all_results.append(results)
except Exception as e:
    print(f"Error in CWH test: {e}")

# =============================================================================
# Test 3: Fundamental Strategy on Multiple Stocks
# =============================================================================
print("\n" + "="*100)
print("Test 3: Fundamental Screening Strategy on IT Stocks")
print("="*100)

try:
    results = engine.run_backtest(
        strategy_class=FundamentalScreenStrategy,
        tickers=['INFY.NS', 'WIPRO.NS', 'HCLTECH.NS'],
        start_date=start_date,
        end_date=end_date,
        strategy_params={'print_log': False}
    )
    if results:
        all_results.append(results)
except Exception as e:
    print(f"Error in Fundamental test: {e}")

# =============================================================================
# Test 4: RHS on Portfolio
# =============================================================================
print("\n" + "="*100)
print("Test 4: RHS Strategy on Diversified Portfolio")
print("="*100)

try:
    results = engine.run_backtest(
        strategy_class=RHSPatternStrategy,
        tickers=['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS'],
        start_date=start_date,
        end_date=end_date,
        strategy_params={'print_log': False}
    )
    if results:
        all_results.append(results)
except Exception as e:
    print(f"Error in Portfolio test: {e}")

# =============================================================================
# Test 5: CWH on Mid-Caps
# =============================================================================
print("\n" + "="*100)
print("Test 5: CWH Strategy on DELHIVERY.NS")
print("="*100)

try:
    results = engine.run_backtest(
        strategy_class=CWHPatternStrategy,
        tickers=['DELHIVERY.NS'],
        start_date='2024-01-01',  # Use specific date
        end_date=end_date,
        strategy_params={'print_log': False}
    )
    if results:
        all_results.append(results)
except Exception as e:
    print(f"Error in DELHIVERY test: {e}")

# =============================================================================
# Summary & Comparison
# =============================================================================
if all_results:
    print("\n" + "="*100)
    print("📊 COMPREHENSIVE RESULTS SUMMARY")
    print("="*100 + "\n")

    from utils.performance_analyzer import PerformanceAnalyzer
    analyzer = PerformanceAnalyzer()

    comparison_df = analyzer.compare_strategies(all_results)
    analyzer.print_comparison(comparison_df)

    # Find best performing strategy
    best = max(all_results, key=lambda x: x.get('total_return', -999))

    print("\n" + "="*100)
    print("🏆 BEST PERFORMING STRATEGY")
    print("="*100)
    print(f"Strategy:      {best['strategy']}")
    print(f"Tickers:       {', '.join(best['tickers'])}")
    print(f"Initial Cash:  ₹{best['initial_cash']:,.2f}")
    print(f"Final Value:   ₹{best['final_value']:,.2f}")
    print(f"Total Return:  {best['total_return']:.2f}%")
    print(f"Profit/Loss:   ₹{(best['final_value'] - best['initial_cash']):,.2f}")
    print(f"Win Rate:      {best['win_rate']:.2f}%")
    print(f"Total Trades:  {best['total_trades']}")
    print("="*100 + "\n")

    # Calculate if we had just held the stocks
    print("="*100)
    print("📈 BUY & HOLD COMPARISON")
    print("="*100)

    import yfinance as yf

    for ticker in ['RELIANCE.NS', 'TCS.NS', 'DELHIVERY.NS']:
        try:
            data = yf.download(ticker, start=start_date, end=end_date, progress=False)
            if not data.empty:
                if isinstance(data.columns, pd.MultiIndex):
                    data.columns = data.columns.get_level_values(0)

                start_price = data['Close'].iloc[0]
                end_price = data['Close'].iloc[-1]
                buy_hold_return = ((end_price - start_price) / start_price) * 100

                final_value = 100000 * (1 + buy_hold_return/100)

                print(f"\n{ticker}:")
                print(f"  Buy & Hold Return: {buy_hold_return:.2f}%")
                print(f"  ₹100,000 would be: ₹{final_value:,.2f}")
        except Exception as e:
            print(f"Error calculating buy & hold for {ticker}: {e}")

    print("\n" + "="*100 + "\n")

else:
    print("\n❌ No successful backtests. Strategies may not have found entry signals in the last year.")
    print("This is normal - pattern-based strategies only trade when specific conditions are met.\n")

import pandas as pd
