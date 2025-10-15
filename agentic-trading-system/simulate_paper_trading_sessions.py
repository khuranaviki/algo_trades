#!/usr/bin/env python3
"""
Simulate Paper Trading Sessions

Simulates what would have happened if paper trading ran for the last 7 trading days.
Uses the exact same logic as the live paper trading system.
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf
import pytz

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from paper_trading.portfolio import Portfolio
from paper_trading.order_executor import OrderExecutor
from paper_trading.risk_manager import RiskManager
from agents.orchestrator import Orchestrator
from config.paper_trading_config import PAPER_TRADING_CONFIG

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/paper_trading_simulation.log', mode='w')
    ]
)

logger = logging.getLogger(__name__)


def get_september_2025_trading_days():
    """Get all weekdays in September 2025"""
    trading_days = []

    # September 2025: 1st to 30th
    for day in range(1, 31):
        date = datetime(2025, 9, day).date()
        # Skip weekends (Saturday=5, Sunday=6)
        if date.weekday() < 5:
            trading_days.append(date)

    return trading_days


async def simulate_trading_day(date, portfolio, orchestrator, order_executor, risk_manager, watchlist):
    """Simulate one trading day"""
    logger.info(f"\n{'='*80}")
    logger.info(f"📅 SIMULATING: {date.strftime('%A, %B %d, %Y')}")
    logger.info(f"{'='*80}")

    day_stats = {
        'date': date,
        'signals_detected': 0,
        'positions_opened': 0,
        'positions_closed': 0,
        'starting_value': portfolio.get_total_value(),
        'ending_value': 0,
        'daily_return': 0
    }

    # Get historical data for this day (we use the day's close as the "trading price")
    for ticker in watchlist:
        try:
            # Download data for the specific day
            stock = yf.Ticker(ticker)
            start_date = date - timedelta(days=365*5)  # 5 years for technical analysis
            end_date = date + timedelta(days=1)

            df = stock.history(start=start_date, end=end_date, interval='1d')

            if df.empty:
                logger.warning(f"⚠️ No data for {ticker} on {date}")
                continue

            # Convert index to date-only for matching (handle timezone-aware dates)
            df.index = pd.to_datetime(df.index).date

            # Check if date exists
            if date not in df.index:
                logger.warning(f"⚠️ No data for {ticker} on {date}")
                continue

            # Get the price for this specific day
            day_data = df.loc[date]
            current_price = day_data['Close']

            logger.info(f"\n📊 Analyzing {ticker} @ ₹{current_price:.2f}")

            # Prepare data for orchestrator (last 5 years up to this date)
            price_data = {
                'ticker': ticker,
                'current_price': current_price,
                'open': day_data['Open'],
                'high': day_data['High'],
                'low': day_data['Low'],
                'close': day_data['Close'],
                'volume': day_data['Volume'],
                'history': df.loc[:date]  # All history up to this date (using date object)
            }

            # Get decision from orchestrator
            decision = await orchestrator.analyze(ticker, price_data)

            # Handle both 'action' and 'decision' keys (error responses use 'decision')
            action = decision.get('action') or decision.get('decision', 'HOLD')
            confidence = decision.get('confidence', 0) / 100 if decision.get('confidence', 0) > 1 else decision.get('confidence', 0)

            if action == 'BUY' and confidence >= 0.6:
                day_stats['signals_detected'] += 1
                logger.info(f"🟢 BUY Signal: {ticker} (Confidence: {confidence:.2%})")

                # Check if we already have a position
                if ticker in portfolio.positions:
                    logger.info(f"⚠️ Already holding {ticker}, skipping")
                    continue

                # Calculate position size
                position_size = risk_manager.calculate_position_size(
                    portfolio=portfolio,
                    entry_price=current_price,
                    stop_loss_price=current_price * 0.95  # 5% stop loss
                )

                if position_size > 0:
                    # Check risk limits
                    if risk_manager.check_trade_allowed(portfolio, ticker, position_size, current_price):
                        # Execute order
                        result = order_executor.execute_order(
                            ticker=ticker,
                            action='BUY',
                            quantity=position_size,
                            current_price=current_price,
                            portfolio=portfolio
                        )

                        if result['status'] == 'executed':
                            day_stats['positions_opened'] += 1
                            logger.info(f"✅ POSITION OPENED: {ticker} x {position_size} @ ₹{result['executed_price']:.2f}")
                    else:
                        logger.info(f"🚫 Risk limit exceeded for {ticker}")

            elif action == 'SELL' and ticker in portfolio.positions:
                day_stats['signals_detected'] += 1
                logger.info(f"🔴 SELL Signal: {ticker} (Confidence: {confidence:.2%})")

                position = portfolio.positions[ticker]
                result = order_executor.execute_order(
                    ticker=ticker,
                    action='SELL',
                    quantity=position['quantity'],
                    current_price=current_price,
                    portfolio=portfolio
                )

                if result['status'] == 'executed':
                    day_stats['positions_closed'] += 1
                    pnl = (current_price - position['entry_price']) * position['quantity']
                    logger.info(f"✅ POSITION CLOSED: {ticker} x {position['quantity']} @ ₹{result['executed_price']:.2f} | P&L: ₹{pnl:,.2f}")

            else:
                logger.info(f"⚪ HOLD: {ticker} (Action: {action}, Confidence: {confidence:.2%})")

        except Exception as e:
            logger.error(f"❌ Error analyzing {ticker}: {e}")
            import traceback
            traceback.print_exc()

    # Update portfolio with end-of-day prices
    for ticker, position in list(portfolio.positions.items()):
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(start=date, end=date + timedelta(days=1), interval='1d')
            if not df.empty:
                eod_price = df.iloc[-1]['Close']
                portfolio.update_position_price(ticker, eod_price)
        except Exception as e:
            logger.error(f"❌ Error updating {ticker} price: {e}")

    # Take snapshot
    portfolio.take_snapshot()

    # Calculate day stats
    day_stats['ending_value'] = portfolio.get_total_value()
    day_stats['daily_return'] = ((day_stats['ending_value'] - day_stats['starting_value']) / day_stats['starting_value']) * 100

    logger.info(f"\n📊 Day Summary:")
    logger.info(f"  Starting Value: ₹{day_stats['starting_value']:,.2f}")
    logger.info(f"  Ending Value: ₹{day_stats['ending_value']:,.2f}")
    logger.info(f"  Daily Return: {day_stats['daily_return']:.2f}%")
    logger.info(f"  Signals Detected: {day_stats['signals_detected']}")
    logger.info(f"  Positions Opened: {day_stats['positions_opened']}")
    logger.info(f"  Positions Closed: {day_stats['positions_closed']}")
    logger.info(f"  Active Positions: {len(portfolio.positions)}")

    return day_stats


async def main():
    """Run simulation"""
    logger.info("="*80)
    logger.info("🔄 PAPER TRADING SIMULATION - SEPTEMBER 2025")
    logger.info("="*80)

    # Initialize components
    config = PAPER_TRADING_CONFIG
    portfolio = Portfolio(config['initial_capital'])
    order_executor = OrderExecutor(
        slippage_pct=config.get('slippage_pct', 0.05),
        use_realistic_costs=config.get('use_realistic_costs', True)
    )
    risk_manager = RiskManager(config.get('risk_management', {}))
    orchestrator = Orchestrator(config.get('orchestrator', {}))
    watchlist = config['watchlist']

    logger.info(f"Initial Capital: ₹{portfolio.initial_capital:,.0f}")
    logger.info(f"Watchlist: {', '.join(watchlist)}")
    logger.info("="*80)

    # Get September 2025 trading days
    trading_days = get_september_2025_trading_days()
    logger.info(f"\nSimulating {len(trading_days)} trading sessions in September 2025:")
    logger.info(f"  Period: {trading_days[0].strftime('%B %d, %Y')} to {trading_days[-1].strftime('%B %d, %Y')}")

    # Run simulation for each day
    all_stats = []
    for trading_day in trading_days:
        day_stats = await simulate_trading_day(
            date=trading_day,
            portfolio=portfolio,
            orchestrator=orchestrator,
            order_executor=order_executor,
            risk_manager=risk_manager,
            watchlist=watchlist
        )
        all_stats.append(day_stats)

    # Final summary
    logger.info("\n" + "="*80)
    logger.info("📈 FINAL SIMULATION RESULTS")
    logger.info("="*80)

    logger.info(f"\nPortfolio Summary:")
    logger.info(f"  Initial Capital: ₹{portfolio.initial_capital:,.2f}")
    logger.info(f"  Final Value: ₹{portfolio.get_total_value():,.2f}")
    logger.info(f"  Total Return: {portfolio.get_total_return_pct():.2f}%")
    logger.info(f"  Realized P&L: ₹{portfolio.get_realized_pnl():,.2f}")
    logger.info(f"  Unrealized P&L: ₹{portfolio.get_unrealized_pnl():,.2f}")
    logger.info(f"  Cash: ₹{portfolio.cash:,.2f}")
    logger.info(f"  Active Positions: {len(portfolio.positions)}")

    if portfolio.positions:
        logger.info(f"\nOpen Positions:")
        for ticker, pos in portfolio.positions.items():
            pnl_pct = ((pos['current_price'] - pos['entry_price']) / pos['entry_price']) * 100
            logger.info(f"  {ticker}: {pos['quantity']} shares @ ₹{pos['entry_price']:.2f} → ₹{pos['current_price']:.2f} ({pnl_pct:+.2f}%)")

    # Daily breakdown
    logger.info(f"\nDaily Performance:")
    logger.info(f"{'Date':<12} {'Return':<10} {'Signals':<10} {'Opened':<10} {'Closed':<10} {'Value':>15}")
    logger.info("-" * 80)
    for stat in all_stats:
        logger.info(
            f"{stat['date'].strftime('%Y-%m-%d'):<12} "
            f"{stat['daily_return']:>7.2f}%  "
            f"{stat['signals_detected']:>7}    "
            f"{stat['positions_opened']:>7}    "
            f"{stat['positions_closed']:>7}    "
            f"₹{stat['ending_value']:>13,.2f}"
        )

    total_signals = sum(s['signals_detected'] for s in all_stats)
    total_opened = sum(s['positions_opened'] for s in all_stats)
    total_closed = sum(s['positions_closed'] for s in all_stats)

    logger.info("-" * 80)
    logger.info(f"{'TOTALS':<12} {portfolio.get_total_return_pct():>7.2f}%  {total_signals:>7}    {total_opened:>7}    {total_closed:>7}")

    logger.info("\n" + "="*80)
    logger.info("✅ SIMULATION COMPLETED")
    logger.info("="*80)


if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)

    # Run simulation
    asyncio.run(main())
