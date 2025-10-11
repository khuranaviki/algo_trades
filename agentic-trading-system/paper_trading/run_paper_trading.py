#!/usr/bin/env python3
"""
Automated Paper Trading Runner

Starts the paper trading engine and runs continuously during market hours.
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
import signal

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from paper_trading.engine import PaperTradingEngine
from config.paper_trading_config import PAPER_TRADING_CONFIG

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/paper_trading.log', mode='a')
    ]
)

logger = logging.getLogger(__name__)

# Global engine reference for signal handling
engine = None


def signal_handler(sig, frame):
    """Handle graceful shutdown on SIGINT/SIGTERM"""
    logger.info("\n🛑 Shutdown signal received")
    if engine and engine.is_running:
        logger.info("Stopping paper trading engine...")
        engine.is_running = False
    sys.exit(0)


async def main():
    """Main entry point"""
    global engine

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("=" * 80)
    logger.info("🤖 AGENTIC TRADING SYSTEM - PAPER TRADING MODE")
    logger.info("=" * 80)
    logger.info(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Configuration: {PAPER_TRADING_CONFIG.get('initial_capital', 0):,.0f} INR")
    logger.info(f"Watchlist: {len(PAPER_TRADING_CONFIG.get('watchlist', []))} stocks")
    logger.info(f"Update Interval: {PAPER_TRADING_CONFIG.get('update_interval_seconds', 60)}s")
    logger.info("=" * 80)
    logger.info("")

    try:
        # Initialize engine
        logger.info("🔧 Initializing paper trading engine...")
        engine = PaperTradingEngine(config=PAPER_TRADING_CONFIG)
        logger.info("✅ Engine initialized successfully")
        logger.info("")

        # Start trading
        logger.info("🚀 Starting paper trading...")
        await engine.start()

    except KeyboardInterrupt:
        logger.info("\n🛑 Interrupted by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        raise
    finally:
        if engine:
            logger.info("")
            logger.info("=" * 80)
            logger.info("📊 FINAL STATISTICS")
            logger.info("=" * 80)

            # Print final portfolio state
            portfolio = engine.portfolio
            logger.info(f"Total Value: ₹{portfolio.get_total_value():,.2f}")
            logger.info(f"Cash: ₹{portfolio.cash:,.2f}")
            logger.info(f"Positions: {len(portfolio.positions)}")
            logger.info(f"Total Return: {portfolio.get_total_return_pct():.2f}%")
            logger.info(f"Realized P&L: ₹{portfolio.get_realized_pnl():,.2f}")
            logger.info(f"Unrealized P&L: ₹{portfolio.get_unrealized_pnl():,.2f}")

            # Print engine stats
            logger.info("")
            logger.info("Trading Activity:")
            for key, value in engine.stats.items():
                logger.info(f"  {key}: {value}")

            logger.info("=" * 80)
            logger.info(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("=" * 80)


if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)

    # Run the async main function
    asyncio.run(main())
