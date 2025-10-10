#!/usr/bin/env python3
"""
Historical Backtest Runner

Run the paper trading system over past 6 months to see what would have happened.

Usage:
    # 6-month backtest (default)
    python3 run_historical_backtest.py

    # Custom period
    python3 run_historical_backtest.py --months 3

    # Specific dates
    python3 run_historical_backtest.py --start 2025-04-01 --end 2025-10-01

    # Quick test (3 stocks, 1 month)
    python3 run_historical_backtest.py --quick
"""

import asyncio
import sys
import logging
from datetime import datetime, timedelta
import argparse

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'historical_backtest_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)

from paper_trading.historical_backtest import HistoricalBacktest
from config.paper_trading_config import PAPER_TRADING_CONFIG


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Historical Backtest Runner')

    parser.add_argument(
        '--months',
        type=int,
        default=6,
        help='Number of months to backtest (default: 6)'
    )

    parser.add_argument(
        '--start',
        type=str,
        help='Start date (YYYY-MM-DD)'
    )

    parser.add_argument(
        '--end',
        type=str,
        help='End date (YYYY-MM-DD)'
    )

    parser.add_argument(
        '--quick',
        action='store_true',
        help='Quick test mode (3 stocks, 1 month)'
    )

    parser.add_argument(
        '--stocks',
        type=str,
        nargs='+',
        help='Specific stocks to test (default: all watchlist)'
    )

    return parser.parse_args()


async def run_backtest(config: dict):
    """Run historical backtest"""

    print("\n" + "="*80)
    print("  HISTORICAL BACKTEST SIMULATION")
    print("  Replaying past period as if system was live")
    print("="*80)

    print(f"\n⚙️  Configuration:")
    print(f"   Period: {config['start_date'].date()} to {config['end_date'].date()}")
    print(f"   Duration: {(config['end_date'] - config['start_date']).days} days")
    print(f"   Initial Capital: ₹{config['initial_capital']:,}")
    print(f"   Watchlist: {', '.join(config['watchlist'])}")
    print(f"   Stocks: {len(config['watchlist'])}")

    # Create backtest engine
    backtest = HistoricalBacktest(config)

    # Run backtest
    print(f"\n🚀 Starting backtest...")
    print(f"   This will take a few minutes...\n")

    try:
        report = await backtest.run()

        # Save report
        output_file = f"backtest_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        backtest.save_report(output_file)

        # Print summary
        print_summary(report)

        return report

    except Exception as e:
        print(f"\n❌ Backtest failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def print_summary(report: dict):
    """Print backtest summary"""

    perf = report['performance']
    activity = report['activity']

    print("\n" + "="*80)
    print("  BACKTEST SUMMARY")
    print("="*80)

    # Performance
    print(f"\n💰 RETURNS:")
    print(f"   Total Return:     {perf['total_return_pct']:+.2f}%")
    print(f"   Final Value:      ₹{perf['total_value']:,.0f}")
    print(f"   Profit/Loss:      ₹{perf['total_value'] - perf.get('initial_capital', 1000000):+,.0f}")

    # Risk-adjusted metrics
    print(f"\n📊 RISK METRICS:")
    print(f"   Sharpe Ratio:     {perf['sharpe_ratio']:.2f}")
    print(f"   Max Drawdown:     {perf['max_drawdown_pct']:.2f}%")
    print(f"   Volatility:       {calculate_volatility(report):.2f}%")

    # Trading activity
    print(f"\n📈 TRADING ACTIVITY:")
    print(f"   BUY Signals:      {activity['signals_detected']}")
    print(f"   Trades Executed:  {activity['trades_executed']}")
    print(f"   Execution Rate:   {activity['execution_rate']*100:.1f}%")
    print(f"   Win Rate:         {perf['win_rate']:.1f}%")

    # Trade stats
    if perf['closed_trades'] > 0:
        print(f"\n💹 TRADE STATISTICS:")
        print(f"   Avg Win:          {perf['avg_win_pct']:+.2f}%")
        print(f"   Avg Loss:         {perf['avg_loss_pct']:+.2f}%")
        print(f"   Profit Factor:    {calculate_profit_factor(report):.2f}")
        print(f"   Avg Trade:        {perf['realized_pnl']/perf['closed_trades']:+,.0f}")

    # Best/worst trades
    print_best_worst_trades(report)

    # Monthly breakdown
    print_monthly_breakdown(report)

    print("\n" + "="*80)

    # Grade performance
    grade = grade_performance(perf)
    print(f"\n🎯 PERFORMANCE GRADE: {grade}")
    print("="*80 + "\n")


def calculate_volatility(report: dict) -> float:
    """Calculate annualized volatility"""
    import numpy as np

    daily_results = report['daily_results']
    if len(daily_results) < 2:
        return 0.0

    returns = [r['daily_return'] for r in daily_results[1:]]
    return np.std(returns) * np.sqrt(252)


def calculate_profit_factor(report: dict) -> float:
    """Calculate profit factor (gross profit / gross loss)"""
    trades = report['trades']
    sell_trades = [t for t in trades if t['action'] == 'SELL' and 'pnl' in t]

    if not sell_trades:
        return 0.0

    gross_profit = sum(t['pnl'] for t in sell_trades if t['pnl'] > 0)
    gross_loss = abs(sum(t['pnl'] for t in sell_trades if t['pnl'] < 0))

    if gross_loss == 0:
        return float('inf') if gross_profit > 0 else 0.0

    return gross_profit / gross_loss


def print_best_worst_trades(report: dict):
    """Print best and worst trades"""
    trades = report['trades']
    sell_trades = [t for t in trades if t['action'] == 'SELL' and 'pnl_pct' in t]

    if not sell_trades:
        return

    # Sort by P&L %
    sorted_trades = sorted(sell_trades, key=lambda x: x['pnl_pct'], reverse=True)

    print(f"\n🏆 TOP 3 TRADES:")
    for i, trade in enumerate(sorted_trades[:3], 1):
        print(
            f"   {i}. {trade['ticker']:12s} {trade['date'].date()} | "
            f"₹{trade['pnl']:+8,.0f} ({trade['pnl_pct']:+6.2f}%) | {trade['reason']}"
        )

    print(f"\n❌ WORST 3 TRADES:")
    for i, trade in enumerate(sorted_trades[-3:][::-1], 1):
        print(
            f"   {i}. {trade['ticker']:12s} {trade['date'].date()} | "
            f"₹{trade['pnl']:+8,.0f} ({trade['pnl_pct']:+6.2f}%) | {trade['reason']}"
        )


def print_monthly_breakdown(report: dict):
    """Print monthly performance breakdown"""
    import pandas as pd

    daily_df = pd.DataFrame(report['daily_results'])
    daily_df['date'] = pd.to_datetime(daily_df['date'])
    daily_df['month'] = daily_df['date'].dt.to_period('M')

    monthly = daily_df.groupby('month').agg({
        'total_value': 'last',
        'daily_return': 'sum'
    }).reset_index()

    print(f"\n📅 MONTHLY BREAKDOWN:")
    print(f"   {'Month':<10} {'Return':<10} {'Ending Value'}")
    print(f"   {'-'*40}")

    for _, row in monthly.iterrows():
        month_str = str(row['month'])
        return_str = f"{row['daily_return']:+.2f}%"
        value_str = f"₹{row['total_value']:,.0f}"
        print(f"   {month_str:<10} {return_str:<10} {value_str}")


def grade_performance(perf: dict) -> str:
    """Grade performance (A+ to F)"""
    score = 0

    # Return (max 30 points)
    ret = perf['total_return_pct']
    if ret >= 15:
        score += 30
    elif ret >= 8:
        score += 20
    elif ret >= 3:
        score += 10
    elif ret >= 0:
        score += 5

    # Sharpe (max 25 points)
    sharpe = perf['sharpe_ratio']
    if sharpe >= 1.8:
        score += 25
    elif sharpe >= 1.2:
        score += 20
    elif sharpe >= 0.8:
        score += 10
    elif sharpe >= 0:
        score += 5

    # Win rate (max 20 points)
    win_rate = perf['win_rate']
    if win_rate >= 75:
        score += 20
    elif win_rate >= 65:
        score += 15
    elif win_rate >= 55:
        score += 10
    elif win_rate >= 45:
        score += 5

    # Drawdown (max 15 points)
    dd = perf['max_drawdown_pct']
    if dd <= 5:
        score += 15
    elif dd <= 10:
        score += 10
    elif dd <= 15:
        score += 5

    # Number of trades (max 10 points)
    trades = perf['closed_trades']
    if trades >= 10:
        score += 10
    elif trades >= 5:
        score += 5
    elif trades >= 1:
        score += 2

    # Grade
    if score >= 90:
        return "A+ (Excellent)"
    elif score >= 80:
        return "A (Very Good)"
    elif score >= 70:
        return "B+ (Good)"
    elif score >= 60:
        return "B (Above Average)"
    elif score >= 50:
        return "C+ (Average)"
    elif score >= 40:
        return "C (Below Average)"
    else:
        return "D (Poor)"


async def main():
    """Main function"""

    args = parse_args()

    # Determine backtest period
    if args.start and args.end:
        start_date = datetime.strptime(args.start, '%Y-%m-%d')
        end_date = datetime.strptime(args.end, '%Y-%m-%d')
    else:
        end_date = datetime.now()
        months = 1 if args.quick else args.months
        start_date = end_date - timedelta(days=months * 30)

    # Build config
    config = {
        **PAPER_TRADING_CONFIG,
        'start_date': start_date,
        'end_date': end_date
    }

    # Quick mode: 3 stocks only
    if args.quick:
        config['watchlist'] = ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS']

    # Custom stocks
    if args.stocks:
        config['watchlist'] = [s if '.NS' in s else f"{s}.NS" for s in args.stocks]

    # Run backtest
    await run_backtest(config)


if __name__ == '__main__':
    try:
        asyncio.run(main())
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n\n⚠️  Backtest interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
