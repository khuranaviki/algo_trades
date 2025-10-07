#!/usr/bin/env python3
"""
V40 Target-Only Strategy Backtest
NO STOP LOSS - Exit ONLY at targets
Uses stocks from Excel file (81 stocks)
"""

import backtrader as bt
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from load_v40_from_excel import load_all_v40_stocks, is_v40_stock, is_v40_next_stock
from strategies.v40_target_only_strategy import V40TargetOnlyStrategy
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


def run_target_only_backtest(tickers, start_date, end_date, initial_cash=100000):
    """Run V40 target-only backtest (NO STOP LOSS)"""

    print(f"\n{'='*100}")
    print(f"🎯 V40 TARGET-ONLY STRATEGY - NO STOP LOSS")
    print(f"{'='*100}")
    print(f"Period: {start_date} to {end_date}")
    print(f"Initial Capital: ₹{initial_cash:,}")
    print(f"\nEntry Signals: Golden Cross (SMA 20 > 50) + RSI < 70")
    print(f"Exit Signals: TARGET ONLY (20% V40, 30% V40 Next)")
    print(f"Stop Loss: NONE - Hold through downturns")
    print(f"Position Sizing: Max 5% per stock")
    print(f"Stock Universe: {len(tickers)} stocks from Excel file")
    print(f"{'='*100}\n")

    # Initialize Cerebro
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(initial_cash)
    cerebro.broker.setcommission(commission=0.001)

    # Add data feeds
    loaded = 0
    loaded_tickers = []
    for ticker in tickers:
        data = fetch_data(ticker, start_date, end_date)
        if data is not None and len(data) > 60:  # Need enough data for SMA 50
            data_feed = bt.feeds.PandasData(dataname=data, name=ticker)
            cerebro.adddata(data_feed)
            loaded += 1
            loaded_tickers.append(ticker)

    print(f"📊 Loaded {loaded}/{len(tickers)} stocks\n")

    if loaded == 0:
        print("❌ No data loaded")
        return None, []

    # Add strategy
    cerebro.addstrategy(V40TargetOnlyStrategy, print_log=False, track_trades=True)

    # Add analyzers
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')

    # Run
    print(f"💰 Starting Value: ₹{cerebro.broker.getvalue():,.2f}\n")
    print("Running backtest...\n")

    results = cerebro.run()
    strategy = results[0]

    final_value = cerebro.broker.getvalue()

    # Get trade history
    trade_history = strategy.get_trade_history()

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
    print(f"{'='*100}")
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

    # Analyze entry/exit reasons
    entry_reasons = {}
    exit_reasons = {}
    v40_trades = 0
    v40_next_trades = 0

    for trade in trade_history:
        if trade['action'] == 'BUY':
            reason = trade['reason']
            entry_reasons[reason] = entry_reasons.get(reason, 0) + 1
            if is_v40_stock(trade['ticker']):
                v40_trades += 1
            elif is_v40_next_stock(trade['ticker']):
                v40_next_trades += 1
        elif trade['action'] == 'SELL' and trade.get('pnl_pct'):
            reason = trade['reason']
            exit_reasons[reason] = exit_reasons.get(reason, 0) + 1

    print(f"{'='*100}")
    print(f"📊 ENTRY SIGNALS BREAKDOWN")
    print(f"{'='*100}")
    for reason, count in sorted(entry_reasons.items(), key=lambda x: x[1], reverse=True):
        print(f"   {reason:<30} {count:>5} trades")

    print(f"\n{'='*100}")
    print(f"📊 EXIT REASONS BREAKDOWN")
    print(f"{'='*100}")
    for reason, count in sorted(exit_reasons.items(), key=lambda x: x[1], reverse=True):
        print(f"   {reason:<30} {count:>5} trades")

    print(f"\n{'='*100}")
    print(f"📊 STOCK CLASSIFICATION BREAKDOWN")
    print(f"{'='*100}")
    print(f"   V40 Trades:         {v40_trades:>5} (20% target)")
    print(f"   V40 Next Trades:    {v40_next_trades:>5} (30% target)")
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
    }, trade_history, loaded_tickers


def export_trade_history(trade_history, filename='v40_target_only_trades.csv'):
    """Export trade history to CSV"""
    if not trade_history:
        print("No trades to export")
        return

    # Create directory if needed
    os.makedirs('backtest_results', exist_ok=True)
    filepath = f'backtest_results/{filename}'

    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['date', 'ticker', 'action', 'price', 'size', 'reason', 'pnl_pct'])
        writer.writeheader()
        writer.writerows(trade_history)

    print(f"✅ Trade history exported to: {filepath}")
    return filepath


def print_trade_history(trade_history, max_rows=50):
    """Print formatted trade history"""
    print(f"\n{'='*120}")
    print(f"📝 DETAILED TRADE HISTORY (Showing first {max_rows} trades)")
    print(f"{'='*120}")
    print(f"{'Date':<12} {'Ticker':<15} {'Action':<6} {'Price':>10} {'Size':>6} {'Reason':<40} {'P&L %':>10}")
    print(f"{'-'*120}")

    for i, trade in enumerate(trade_history[:max_rows]):
        pnl_str = f"{trade.get('pnl_pct', 0):+.2f}%" if trade.get('pnl_pct') else "-"
        print(f"{str(trade['date']):<12} {trade['ticker']:<15} {trade['action']:<6} "
              f"₹{trade['price']:>8,.2f} {trade['size']:>6} {trade['reason']:<40} {pnl_str:>10}")

    if len(trade_history) > max_rows:
        print(f"... ({len(trade_history) - max_rows} more trades in CSV file)")
    print(f"{'='*120}\n")


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
            stock_type = "V40" if is_v40_stock(ticker) else "V40 Next"
            successful_stocks.append({
                'ticker': ticker,
                'type': stock_type,
                'return': bh_ret,
                'value': bh_val
            })

    # Sort by return
    successful_stocks.sort(key=lambda x: x['return'], reverse=True)

    print(f"{'Ticker':<15} {'Type':<10} {'Return':>10} {'Value':>15}")
    print(f"{'-'*100}")
    for stock in successful_stocks:
        print(f"{stock['ticker']:<15} {stock['type']:<10} {stock['return']:>9.2f}%  →  ₹{stock['value']:>12,.0f}")

    print(f"{'-'*100}")
    bh_return = ((total_bh - initial_cash) / initial_cash) * 100
    print(f"Buy & Hold Total:   ₹{total_bh:>10,.2f} ({bh_return:+.2f}%)")
    print(f"Stocks Loaded:      {len(successful_stocks)}/{len(tickers)}")
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
    print(f"Total stocks loaded: {len(all_stocks)}")
    print(f"{'='*100}\n")

    # Run backtest
    result, trade_history, loaded_tickers = run_target_only_backtest(
        tickers=all_stocks,
        start_date=start_date,
        end_date=end_date,
        initial_cash=100000
    )

    # Print trade history
    if trade_history:
        print_trade_history(trade_history)
        export_trade_history(trade_history)

    # Compare with Buy & Hold
    if result:
        total_bh, bh_return = calculate_buy_and_hold(loaded_tickers, start_date, end_date)

        print(f"{'='*100}")
        print(f"📊 STRATEGY COMPARISON")
        print(f"{'='*100}")
        print(f"Strategy Total:     ₹{result['final_value']:>10,.2f} ({result['total_return']:+.2f}%)")
        print(f"Buy & Hold Total:   ₹{total_bh:>10,.2f} ({bh_return:+.2f}%)")

        diff = result['final_value'] - total_bh
        print(f"Difference:         ₹{diff:>10,.2f} ({(diff/total_bh*100):+.2f}%)")
        print(f"{'='*100}\n")
