#!/usr/bin/env python3
"""
V40 Portfolio Strategy Backtesting
Tests the combined fundamental + technical strategy with 5% position sizing
"""

import backtrader as bt
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from v40_universe import get_all_v40_universe, get_v40_universe, get_v40_next_universe, get_stock_info
from strategies.v40_portfolio_strategy import V40PortfolioStrategy, V40PortfolioStrategyRelaxed


def fetch_data(ticker, start_date, end_date):
    """Fetch OHLCV data"""
    try:
        data = yf.download(ticker, start=start_date, end=end_date, progress=False)
        if data.empty:
            return None

        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        return data
    except:
        return None


def run_v40_backtest(
    tickers,
    start_date,
    end_date,
    initial_cash=100000,
    relaxed_mode=True,
    print_log=False
):
    """
    Run V40 portfolio backtest

    Args:
        tickers: List of V40/V40 Next tickers
        start_date: Start date
        end_date: End date
        initial_cash: Starting capital
        relaxed_mode: If True, skip fundamental screening (technical only)
        print_log: Print detailed logs
    """

    print(f"\n{'='*100}")
    print(f"🚀 V40 PORTFOLIO STRATEGY BACKTEST")
    print(f"{'='*100}")
    print(f"Mode: {'RELAXED (Technical Only)' if relaxed_mode else 'STRICT (Fundamental + Technical)'}")
    print(f"Period: {start_date} to {end_date}")
    print(f"Initial Capital: ₹{initial_cash:,}")
    print(f"Universe: {len(tickers)} stocks")
    print(f"Position Sizing: Max 5% per stock")
    print(f"{'='*100}\n")

    # Initialize Cerebro
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(initial_cash)
    cerebro.broker.setcommission(commission=0.001)

    # Add data feeds
    loaded = 0
    for ticker in tickers:
        data = fetch_data(ticker, start_date, end_date)
        if data is not None:
            data_feed = bt.feeds.PandasData(dataname=data, name=ticker)
            cerebro.adddata(data_feed)
            loaded += 1
            if print_log:
                print(f"✅ Loaded {ticker}")

    print(f"\n📊 Loaded {loaded}/{len(tickers)} stocks\n")

    if loaded == 0:
        print("❌ No data loaded, aborting backtest")
        return None

    # Add strategy
    if relaxed_mode:
        cerebro.addstrategy(V40PortfolioStrategyRelaxed, print_log=print_log)
    else:
        cerebro.addstrategy(V40PortfolioStrategy, print_log=print_log)

    # Add analyzers
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')

    # Run
    print(f"💰 Starting Portfolio Value: ₹{cerebro.broker.getvalue():,.2f}\n")
    print(f"{'='*100}")
    print(f"🔄 Running Backtest...")
    print(f"{'='*100}\n")

    results = cerebro.run()
    strategy = results[0]

    final_value = cerebro.broker.getvalue()

    # Extract analytics
    returns = strategy.analyzers.returns.get_analysis()
    drawdown = strategy.analyzers.drawdown.get_analysis()
    trades = strategy.analyzers.trades.get_analysis()
    sharpe = strategy.analyzers.sharpe.get_analysis()

    # Calculate metrics
    total_return = ((final_value - initial_cash) / initial_cash) * 100
    total_trades = trades.get('total', {}).get('total', 0)
    won = trades.get('won', {}).get('total', 0)
    lost = trades.get('lost', {}).get('total', 0)
    win_rate = (won / total_trades * 100) if total_trades > 0 else 0

    avg_pnl = trades.get('pnl', {}).get('net', {}).get('average', 0)
    max_dd = drawdown.get('max', {}).get('drawdown', 0)
    sharpe_ratio = sharpe.get('sharperatio', None)

    # Print results
    print(f"\n{'='*100}")
    print(f"📊 BACKTEST RESULTS")
    print(f"{'='*100}")
    print(f"💰 PORTFOLIO PERFORMANCE:")
    print(f"   Initial Capital:    ₹{initial_cash:>12,.2f}")
    print(f"   Final Value:        ₹{final_value:>12,.2f}")
    print(f"   Total Return:       {total_return:>12.2f}%")
    print(f"   Profit/Loss:        ₹{(final_value - initial_cash):>12,.2f}")
    print(f"   Max Drawdown:       {max_dd:>12.2f}%")
    if sharpe_ratio:
        print(f"   Sharpe Ratio:       {sharpe_ratio:>12.2f}")

    print(f"\n📈 TRADING STATISTICS:")
    print(f"   Total Trades:       {total_trades:>12}")
    print(f"   Won Trades:         {won:>12}")
    print(f"   Lost Trades:        {lost:>12}")
    print(f"   Win Rate:           {win_rate:>12.2f}%")
    if avg_pnl:
        print(f"   Avg P&L per Trade:  ₹{avg_pnl:>12,.2f}")

    print(f"{'='*100}\n")

    return {
        'initial_cash': initial_cash,
        'final_value': final_value,
        'total_return': total_return,
        'max_drawdown': max_dd,
        'sharpe_ratio': sharpe_ratio,
        'total_trades': total_trades,
        'won': won,
        'lost': lost,
        'win_rate': win_rate,
        'avg_pnl': avg_pnl,
    }


if __name__ == '__main__':
    # Test period: Last 1 year
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

    print("\n" + "="*100)
    print("V40 PORTFOLIO STRATEGY - COMPREHENSIVE BACKTEST")
    print("="*100)
    print("\nStrategy Rules:")
    print("  ✓ Buy: Fundamental pass + Golden Cross (SMA 20 > SMA 50) + RSI < 70")
    print("  ✓ Sell: Target (20% for V40, 30% for V40 Next) OR Stop Loss (10%) OR Death Cross")
    print("  ✓ Position Size: Max 5% per stock")
    print("  ✓ Max Exposure: 95% of portfolio")
    print("="*100)

    # Test 1: V40 stocks only
    print("\n\n" + "="*100)
    print("TEST 1: V40 STOCKS (Premium Quality)")
    print("="*100)
    v40_stocks = get_v40_universe()[:10]  # Test on first 10 for speed
    result_v40 = run_v40_backtest(
        tickers=v40_stocks,
        start_date=start_date,
        end_date=end_date,
        initial_cash=100000,
        relaxed_mode=True,
        print_log=False
    )

    # Test 2: V40 Next stocks
    print("\n\n" + "="*100)
    print("TEST 2: V40 NEXT STOCKS (High Growth)")
    print("="*100)
    v40_next_stocks = get_v40_next_universe()[:10]  # Test on first 10
    result_v40_next = run_v40_backtest(
        tickers=v40_next_stocks,
        start_date=start_date,
        end_date=end_date,
        initial_cash=100000,
        relaxed_mode=True,
        print_log=False
    )

    # Test 3: Combined portfolio
    print("\n\n" + "="*100)
    print("TEST 3: COMBINED V40 + V40 NEXT PORTFOLIO")
    print("="*100)
    all_stocks = get_all_v40_universe()[:20]  # Test on 20 stocks
    result_combined = run_v40_backtest(
        tickers=all_stocks,
        start_date=start_date,
        end_date=end_date,
        initial_cash=100000,
        relaxed_mode=True,
        print_log=False
    )

    # Summary comparison
    print("\n\n" + "="*100)
    print("📊 SUMMARY COMPARISON")
    print("="*100)

    results = [
        ('V40 Stocks', result_v40),
        ('V40 Next Stocks', result_v40_next),
        ('Combined Portfolio', result_combined)
    ]

    print(f"\n{'Strategy':<25} {'Return':<15} {'Win Rate':<15} {'Trades':<10} {'Max DD'}")
    print("-"*100)

    for name, result in results:
        if result:
            print(f"{name:<25} {result['total_return']:>6.2f}%      "
                  f"{result['win_rate']:>6.2f}%      "
                  f"{result['total_trades']:>5}      "
                  f"{result['max_drawdown']:>6.2f}%")

    # Best performer
    best = max([r for _, r in results if r], key=lambda x: x['total_return'])

    print("\n" + "="*100)
    print("🏆 BEST PERFORMER")
    print("="*100)
    best_name = [name for name, r in results if r == best][0]
    print(f"Strategy: {best_name}")
    print(f"Return:   {best['total_return']:.2f}%")
    print(f"₹1,00,000 → ₹{best['final_value']:,.2f}")
    print(f"Profit:   ₹{(best['final_value'] - 100000):,.2f}")
    print("="*100 + "\n")
