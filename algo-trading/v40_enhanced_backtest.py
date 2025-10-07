#!/usr/bin/env python3
"""
Enhanced V40 Strategy Backtest with Trade History Export
Combines Golden Cross, RHS, and CWH patterns
"""

import backtrader as bt
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from v40_universe import get_v40_universe, get_v40_next_universe
from strategies.v40_enhanced_strategy import V40EnhancedStrategy
import csv


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


def run_enhanced_backtest(tickers, start_date, end_date, initial_cash=100000):
    """Run enhanced V40 backtest with trade history"""

    print(f"\n{'='*100}")
    print(f"🚀 ENHANCED V40 PORTFOLIO STRATEGY - Multi-Pattern Detection")
    print(f"{'='*100}")
    print(f"Period: {start_date} to {end_date}")
    print(f"Initial Capital: ₹{initial_cash:,}")
    print(f"\nEntry Signals: Golden Cross OR RHS Breakout OR CWH Breakout")
    print(f"Exit Signals: Target (20-30%) OR Stop Loss (10%) OR Death Cross OR RSI Overbought")
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

    print(f"📊 Loaded {loaded}/{len(tickers)} stocks\n")

    if loaded == 0:
        print("❌ No data loaded")
        return None, []

    # Add strategy
    cerebro.addstrategy(V40EnhancedStrategy, print_log=False, track_trades=True)

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

    # Analyze entry reasons
    entry_reasons = {}
    exit_reasons = {}
    for trade in trade_history:
        if trade['action'] == 'BUY':
            reason = trade['reason']
            entry_reasons[reason] = entry_reasons.get(reason, 0) + 1
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

    print(f"\n{'='*100}\n")

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
    }, trade_history


def export_trade_history(trade_history, filename='trade_history.csv'):
    """Export trade history to CSV"""
    if not trade_history:
        print("No trades to export")
        return

    filepath = f'backtest_results/{filename}'

    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['date', 'ticker', 'action', 'price', 'size', 'reason', 'pnl_pct'])
        writer.writeheader()
        writer.writerows(trade_history)

    print(f"✅ Trade history exported to: {filepath}")
    return filepath


def print_trade_history(trade_history):
    """Print formatted trade history"""
    print(f"\n{'='*120}")
    print(f"📝 DETAILED TRADE HISTORY")
    print(f"{'='*120}")
    print(f"{'Date':<12} {'Ticker':<15} {'Action':<6} {'Price':>10} {'Size':>6} {'Reason':<40} {'P&L %':>10}")
    print(f"{'-'*120}")

    for trade in trade_history:
        pnl_str = f"{trade.get('pnl_pct', 0):+.2f}%" if trade.get('pnl_pct') else "-"
        print(f"{str(trade['date']):<12} {trade['ticker']:<15} {trade['action']:<6} "
              f"₹{trade['price']:>8,.2f} {trade['size']:>6} {trade['reason']:<40} {pnl_str:>10}")

    print(f"{'='*120}\n")


if __name__ == '__main__':
    # Test period: 2 years for better pattern capture
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')

    # Select diverse V40 stocks
    stocks = [
        # V40 Premium
        'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'LT.NS',
        'MARUTI.NS', 'ASIANPAINT.NS', 'TITAN.NS', 'BAJFINANCE.NS',
        # V40 Next (High Growth)
        'DELHIVERY.NS', 'LALPATHLAB.NS', 'DIXON.NS', 'PERSISTENT.NS',
        'COFORGE.NS', 'MPHASIS.NS'
    ]

    # Run backtest
    result, trade_history = run_enhanced_backtest(
        tickers=stocks,
        start_date=start_date,
        end_date=end_date,
        initial_cash=100000
    )

    # Print trade history
    if trade_history:
        print_trade_history(trade_history)

        # Export to CSV
        export_trade_history(trade_history, 'v40_enhanced_trades.csv')

    # Compare with Buy & Hold
    if result:
        print(f"{'='*100}")
        print(f"📊 BUY & HOLD COMPARISON")
        print(f"{'='*100}")

        total_bh = 0
        amount_per_stock = 100000 / len(stocks)

        for ticker in stocks:
            data = fetch_data(ticker, start_date, end_date)
            if data is not None:
                sp = data['Close'].iloc[0]
                ep = data['Close'].iloc[-1]
                bh_ret = ((ep - sp) / sp) * 100
                bh_val = amount_per_stock * (1 + bh_ret / 100)
                total_bh += bh_val
                print(f"{ticker:<15} {bh_ret:>7.2f}%  →  ₹{bh_val:>10,.0f}")

        print(f"{'-'*100}")
        print(f"Buy & Hold Total:   ₹{total_bh:>10,.2f} ({((total_bh-100000)/100000*100):+.2f}%)")
        print(f"Strategy Total:     ₹{result['final_value']:>10,.2f} ({result['total_return']:+.2f}%)")

        diff = result['final_value'] - total_bh
        print(f"Difference:         ₹{diff:>10,.2f} ({(diff/total_bh*100):+.2f}%)")
        print(f"{'='*100}\n")
