#!/usr/bin/env python3
"""
V40 Validated Strategy Backtest with Market Regime Filter

Features:
1. Analyzes 5 years of historical data for each stock
2. Validates each strategy (Golden Cross, RHS, CWH) has >70% win rate
3. Only trades stocks/strategies that pass validation
4. Market regime filter: Only invest during bullish markets (NIFTYBEES SMA50 > SMA200)
5. Exit at pattern-specific targets (NO STOP LOSS)
"""

import backtrader as bt
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from load_v40_from_excel import load_all_v40_stocks, is_v40_stock, is_v40_next_stock
from strategies.v40_validated_strategy import V40ValidatedStrategy
import csv
import os


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


def run_validated_backtest(tickers, start_date, end_date, initial_cash=100000):
    """Run V40 validated strategy backtest"""

    print(f"\n{'='*100}")
    print(f"🔬 V40 VALIDATED STRATEGY - Historical Win Rate Analysis")
    print(f"{'='*100}")
    print(f"Backtest Period: {start_date} to {end_date}")
    print(f"Validation Period: 5 years prior to each trade")
    print(f"Initial Capital: ₹{initial_cash:,}")
    print(f"\nValidation Criteria:")
    print(f"  • Minimum Win Rate: 70%")
    print(f"  • Minimum Historical Trades: 5")
    print(f"  • Lookback Period: 5 years")
    print(f"\n🌍 Market Regime Filter:")
    print(f"  • Only invest when NIFTYBEES SMA50 > SMA200 (Bullish)")
    print(f"  • Stop new investments when SMA50 < SMA200 (Bearish)")
    print(f"  • Existing positions exit at targets regardless of regime")
    print(f"\nEntry Signals (if validated AND market is bullish):")
    print(f"  1. Golden Cross (SMA 20 > 50) + RSI < 70")
    print(f"  2. RHS Pattern Breakout")
    print(f"  3. CWH Pattern Breakout")
    print(f"\nExit: Pattern-specific targets (NO STOP LOSS)")
    print(f"Position Sizing: Max 5% per stock")
    print(f"Stock Universe: {len(tickers)} stocks from Excel file")
    print(f"{'='*100}\n")

    # Initialize Cerebro
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(initial_cash)
    cerebro.broker.setcommission(commission=0.001)

    # Add data feeds (need extra data for validation)
    # Fetch data starting 5 years before backtest start
    validation_start = (datetime.strptime(start_date, '%Y-%m-%d') - timedelta(days=365*5)).strftime('%Y-%m-%d')

    loaded = 0
    loaded_tickers = []
    print(f"📊 Loading data (including 5-year validation period)...\n")

    # First, add NIFTYBEES for market regime detection
    print(f"  Loading NIFTYBEES.NS for market regime detection...")
    niftybees_data = fetch_data('NIFTYBEES.NS', validation_start, end_date)
    if niftybees_data is not None and len(niftybees_data) > 500:
        niftybees_feed = bt.feeds.PandasData(dataname=niftybees_data, name='NIFTYBEES.NS')
        cerebro.adddata(niftybees_feed)
        print(f"  ✅ NIFTYBEES.NS loaded for market regime filter\n")
    else:
        print(f"  ⚠️  WARNING: Could not load NIFTYBEES.NS - market regime filter will be disabled\n")

    for ticker in tickers:
        # Fetch extended data for validation
        data = fetch_data(ticker, validation_start, end_date)
        if data is not None and len(data) > 500:  # Need substantial history
            data_feed = bt.feeds.PandasData(dataname=data, name=ticker)
            cerebro.adddata(data_feed)
            loaded += 1
            loaded_tickers.append(ticker)
            if loaded % 10 == 0:
                print(f"  Loaded {loaded} stocks...")

    print(f"\n✅ Loaded {loaded}/{len(tickers)} stocks with sufficient history\n")

    if loaded == 0:
        print("❌ No data loaded")
        return None, [], None

    # Add strategy with trading start date
    # Tell cerebro to only start trading from start_date (not validation_start)
    cerebro.addstrategy(V40ValidatedStrategy,
                       print_log=True,
                       track_trades=True,
                       trading_start_date=start_date)

    # Add analyzers
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')

    # Run
    print(f"💰 Starting Value: ₹{cerebro.broker.getvalue():,.2f}\n")
    print(f"{'='*100}")
    print("PHASE 1: HISTORICAL VALIDATION (This may take a while...)")
    print(f"{'='*100}\n")

    results = cerebro.run()
    strategy = results[0]

    final_value = cerebro.broker.getvalue()

    # Get trade history and validation summary
    trade_history = strategy.get_trade_history()
    validation_summary = strategy.get_validation_summary()

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
    max_dd = drawdown.get('max', {}).get('drawdown', 0)
    sharpe_ratio = sharpe.get('sharperatio', None)

    # Print results
    print(f"\n{'='*100}")
    print(f"📊 BACKTEST RESULTS")
    print(f"{'='*100}")
    print(f"💰 PERFORMANCE:")
    print(f"   Initial Capital:    ₹{initial_cash:>12,.2f}")
    print(f"   Final Value:        ₹{final_value:>12,.2f}")
    print(f"   Total Return:       {total_return:>12.2f}%")
    print(f"   Profit/Loss:        ₹{(final_value - initial_cash):>12,.2f}")
    print(f"   Max Drawdown:       {max_dd:>12.2f}%")
    if sharpe_ratio:
        print(f"   Sharpe Ratio:       {sharpe_ratio:>12.2f}")

    print(f"\n📈 TRADING:")
    print(f"   Total Trades:       {total_trades:>12}")
    print(f"   Won:                {won:>12} ({win_rate:.1f}%)")
    print(f"   Lost:               {lost:>12}")
    print(f"{'='*100}\n")

    # Validation summary
    print(f"{'='*100}")
    print(f"🔬 VALIDATION SUMMARY")
    print(f"{'='*100}")

    stocks_with_strategies = {}
    total_validated = 0
    total_rejected = 0

    for ticker, strategies in validation_summary.items():
        if strategies:
            stocks_with_strategies[ticker] = strategies
            total_validated += 1
        else:
            total_rejected += 1

    print(f"Total Stocks Analyzed:           {len(validation_summary)}")
    print(f"Stocks with Valid Strategies:    {total_validated}")
    print(f"Stocks Rejected (No Strategy):   {total_rejected}")
    print(f"\nValidated Stock-Strategy Pairs:")
    print(f"{'-'*100}")

    for ticker, strategies in sorted(stocks_with_strategies.items()):
        stock_type = "V40" if is_v40_stock(ticker) else "V40 Next"
        strategy_str = ", ".join([f"{s}: {wr:.1f}%" for s, wr in strategies.items()])
        print(f"  {ticker:<20} ({stock_type:<10}) → {strategy_str}")

    print(f"{'='*100}\n")

    # Strategy breakdown
    strategy_counts = {'Golden Cross': 0, 'RHS': 0, 'CWH': 0}
    for strategies in stocks_with_strategies.values():
        for strategy_name in strategies.keys():
            strategy_counts[strategy_name] = strategy_counts.get(strategy_name, 0) + 1

    print(f"{'='*100}")
    print(f"📊 STRATEGY VALIDATION BREAKDOWN")
    print(f"{'='*100}")
    print(f"Golden Cross validated on:  {strategy_counts.get('Golden Cross', 0):>3} stocks")
    print(f"RHS validated on:           {strategy_counts.get('RHS', 0):>3} stocks")
    print(f"CWH validated on:           {strategy_counts.get('CWH', 0):>3} stocks")
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
        'validated_stocks': total_validated,
        'rejected_stocks': total_rejected,
    }, trade_history, loaded_tickers, validation_summary


def export_trade_history(trade_history, filename='v40_validated_trades.csv'):
    """Export trade history to CSV"""
    if not trade_history:
        print("No trades to export")
        return

    os.makedirs('backtest_results', exist_ok=True)
    filepath = f'backtest_results/{filename}'

    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['date', 'ticker', 'action', 'price', 'size', 'reason', 'pnl_pct', 'target_pct'])
        writer.writeheader()
        writer.writerows(trade_history)

    print(f"✅ Trade history exported to: {filepath}")
    return filepath


def export_validation_summary(validation_summary, filename='v40_validation_summary.csv'):
    """Export validation summary to CSV"""
    os.makedirs('backtest_results', exist_ok=True)
    filepath = f'backtest_results/{filename}'

    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Ticker', 'Stock Type', 'Strategy', 'Win Rate %'])

        for ticker, strategies in sorted(validation_summary.items()):
            stock_type = "V40" if is_v40_stock(ticker) else "V40 Next"
            if strategies:
                for strategy_name, win_rate in strategies.items():
                    writer.writerow([ticker, stock_type, strategy_name, f"{win_rate:.2f}"])
            else:
                writer.writerow([ticker, stock_type, 'NONE', 'REJECTED'])

    print(f"✅ Validation summary exported to: {filepath}")
    return filepath


def print_trade_history(trade_history, max_rows=50):
    """Print formatted trade history"""
    if not trade_history:
        print("No trades executed")
        return

    print(f"\n{'='*130}")
    print(f"📝 DETAILED TRADE HISTORY (Showing first {max_rows} trades)")
    print(f"{'='*130}")
    print(f"{'Date':<12} {'Ticker':<15} {'Action':<6} {'Price':>10} {'Size':>6} {'Reason':<45} {'Target %':>10} {'P&L %':>10}")
    print(f"{'-'*130}")

    for i, trade in enumerate(trade_history[:max_rows]):
        pnl_str = f"{trade.get('pnl_pct', 0):+.2f}%" if trade.get('pnl_pct') else "-"
        target_str = f"{trade.get('target_pct', 0):.1f}%" if trade.get('target_pct') else "-"
        print(f"{str(trade['date']):<12} {trade['ticker']:<15} {trade['action']:<6} "
              f"₹{trade['price']:>8,.2f} {trade['size']:>6} {trade['reason']:<45} {target_str:>10} {pnl_str:>10}")

    if len(trade_history) > max_rows:
        print(f"... ({len(trade_history) - max_rows} more trades in CSV file)")
    print(f"{'='*130}\n")


def calculate_buy_and_hold(tickers, start_date, end_date, initial_cash=100000):
    """Calculate buy & hold returns"""
    print(f"{'='*100}")
    print(f"📊 BUY & HOLD COMPARISON")
    print(f"{'='*100}")

    total_bh = 0
    amount_per_stock = initial_cash / len(tickers)
    successful_stocks = []

    for ticker in tickers:
        data = fetch_data(ticker, start_date, end_date)
        if data is not None and len(data) > 0:
            sp = data['Close'].iloc[0]
            ep = data['Close'].iloc[-1]
            bh_ret = ((ep - sp) / sp) * 100
            bh_val = amount_per_stock * (1 + bh_ret / 100)
            total_bh += bh_val
            successful_stocks.append({'ticker': ticker, 'return': bh_ret, 'value': bh_val})

    successful_stocks.sort(key=lambda x: x['return'], reverse=True)

    print(f"Top 10 Performers:")
    for stock in successful_stocks[:10]:
        print(f"  {stock['ticker']:<20} {stock['return']:>7.2f}%  →  ₹{stock['value']:>10,.0f}")

    print(f"\n{'-'*100}")
    bh_return = ((total_bh - initial_cash) / initial_cash) * 100
    print(f"Buy & Hold Total:   ₹{total_bh:>10,.2f} ({bh_return:+.2f}%)")
    print(f"{'='*100}\n")

    return total_bh, bh_return


if __name__ == '__main__':
    # Test period: 2 years
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')

    # Load stocks from Excel
    print(f"\n{'='*100}")
    print(f"📂 LOADING V40 STOCKS FROM EXCEL")
    print(f"{'='*100}")

    all_stocks = load_all_v40_stocks()
    print(f"Total stocks to validate: {len(all_stocks)}")
    print(f"{'='*100}\n")

    # Run backtest
    result, trade_history, loaded_tickers, validation_summary = run_validated_backtest(
        tickers=all_stocks,
        start_date=start_date,
        end_date=end_date,
        initial_cash=100000
    )

    if result:
        # Export validation summary
        export_validation_summary(validation_summary)

        # Print trade history
        if trade_history:
            print_trade_history(trade_history)
            export_trade_history(trade_history)
        else:
            print("⚠️  NO TRADES EXECUTED - No stock-strategy pairs passed validation!")

        # Compare with Buy & Hold (only on validated stocks)
        validated_tickers = [t for t, s in validation_summary.items() if s]
        if validated_tickers:
            print(f"\n{'='*100}")
            print(f"📊 BUY & HOLD COMPARISON (Only validated stocks)")
            print(f"{'='*100}")
            total_bh, bh_return = calculate_buy_and_hold(validated_tickers, start_date, end_date)

            print(f"{'='*100}")
            print(f"📊 FINAL COMPARISON")
            print(f"{'='*100}")
            print(f"Validated Strategy:     ₹{result['final_value']:>10,.2f} ({result['total_return']:+.2f}%)")
            print(f"Buy & Hold (Validated): ₹{total_bh:>10,.2f} ({bh_return:+.2f}%)")

            diff = result['final_value'] - total_bh
            print(f"Difference:             ₹{diff:>10,.2f} ({(diff/total_bh*100):+.2f}%)")
            print(f"{'='*100}\n")

            # Compare with previous strategies
            print(f"{'='*100}")
            print(f"📊 STRATEGY EVOLUTION COMPARISON")
            print(f"{'='*100}")
            print(f"Enhanced (With SL):       ₹98,511   (-1.49%)")
            print(f"Fixed Target (20/30%):    ₹119,958  (+19.96%)")
            print(f"Dynamic Target:           ₹121,537  (+21.54%)")
            print(f"Validated (70% WR):       ₹{result['final_value']:>8,.0f} ({result['total_return']:+.2f}%)")
            print(f"{'='*100}\n")
