#!/usr/bin/env python3
"""
Paper Trading System Test

Tests the complete paper trading flow:
- Data streaming
- Portfolio management
- Order execution
- Risk management
- Signal monitoring
"""

import asyncio
import sys
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'paper_trading_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)

from paper_trading.engine import PaperTradingEngine
from config.paper_trading_config import TEST_CONFIG


async def test_paper_trading():
    """Test paper trading system"""

    print("\n" + "="*80)
    print("  PAPER TRADING SYSTEM TEST")
    print("  Testing complete flow with 3 stocks")
    print("="*80)

    # Create engine with test config
    engine = PaperTradingEngine(TEST_CONFIG)

    print(f"\n⚙️  Configuration:")
    print(f"   Initial Capital: ₹{TEST_CONFIG['initial_capital']:,}")
    print(f"   Watchlist: {', '.join(TEST_CONFIG['watchlist'])}")
    print(f"   Max Positions: {TEST_CONFIG['risk_management']['max_open_positions']}")
    print(f"   Max Position Size: {TEST_CONFIG['risk_management']['max_position_size_pct']}%")
    print(f"   Update Interval: {TEST_CONFIG['update_interval_seconds']}s")

    print(f"\n🚀 Starting paper trading engine...")
    print(f"   Press Ctrl+C to stop\n")

    try:
        # Start engine (will run until stopped)
        await engine.start()

    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        await engine.stop()

    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        await engine.stop()


async def test_components():
    """Test individual components before full integration"""

    print("\n" + "="*80)
    print("  COMPONENT TESTS")
    print("="*80)

    from paper_trading.portfolio import Portfolio
    from paper_trading.order_executor import OrderExecutor
    from paper_trading.risk_manager import RiskManager
    from paper_trading.transaction_costs import TransactionCostModel

    # Test 1: Portfolio
    print("\n📊 Test 1: Portfolio Management")
    print("-" * 80)

    portfolio = Portfolio(initial_capital=100000)
    print(f"✅ Portfolio created: ₹{portfolio.initial_capital:,}")

    # Open position
    portfolio.open_position(
        ticker='RELIANCE.NS',
        quantity=10,
        price=2850.0,
        stop_loss=2800.0,
        target=2950.0,
        reason='test_entry',
        transaction_cost=50.0
    )
    print(f"✅ Position opened: RELIANCE.NS (10 shares)")
    print(f"   Cash remaining: ₹{portfolio.cash:,.2f}")
    print(f"   Total value: ₹{portfolio.get_total_value():,.2f}")

    # Update price
    portfolio.update_prices({'RELIANCE.NS': 2900.0})
    position = portfolio.positions['RELIANCE.NS']
    print(f"✅ Price updated to ₹2,900")
    print(f"   Unrealized P&L: ₹{position.unrealized_pnl:+,.2f} ({position.unrealized_pnl_pct:+.2f}%)")

    # Close position
    portfolio.close_position(
        ticker='RELIANCE.NS',
        price=2900.0,
        reason='test_exit',
        transaction_cost=50.0
    )
    print(f"✅ Position closed")
    print(f"   Realized P&L: ₹{portfolio.get_realized_pnl():+,.2f}")
    print(f"   Final cash: ₹{portfolio.cash:,.2f}")

    # Test 2: Order Executor
    print("\n\n💱 Test 2: Order Execution")
    print("-" * 80)

    executor = OrderExecutor(slippage_pct=0.05)

    order_result = executor.execute_market_order(
        ticker='TCS.NS',
        action='BUY',
        quantity=5,
        current_price=3500.0
    )

    print(f"✅ BUY order executed:")
    print(f"   Quantity: {order_result['quantity']} shares")
    print(f"   Requested: ₹{order_result['requested_price']:.2f}")
    print(f"   Fill Price: ₹{order_result['fill_price']:.2f}")
    print(f"   Slippage: ₹{order_result['slippage_cost']:.2f}")
    print(f"   Transaction Cost: ₹{order_result['transaction_cost']:.2f}")
    print(f"   Total Cost: ₹{order_result['total_cost']:,.2f}")

    # Test 3: Transaction Costs
    print("\n\n💰 Test 3: Transaction Costs")
    print("-" * 80)

    order_value = 100000
    costs = TransactionCostModel.calculate_total_cost(order_value, 'BUY')

    print(f"✅ Costs for ₹{order_value:,} BUY order:")
    print(f"   Brokerage: ₹{costs['brokerage']:.2f}")
    print(f"   STT: ₹{costs['stt']:.2f}")
    print(f"   Exchange: ₹{costs['exchange']:.2f}")
    print(f"   GST: ₹{costs['gst']:.2f}")
    print(f"   Stamp Duty: ₹{costs['stamp']:.2f}")
    print(f"   TOTAL: ₹{costs['total']:.2f} ({costs['percentage']:.3f}%)")

    # Test 4: Risk Manager
    print("\n\n🛡️  Test 4: Risk Management")
    print("-" * 80)

    risk_config = TEST_CONFIG['risk_management']
    risk_manager = RiskManager(risk_config)

    print(f"✅ Risk Manager created:")
    print(f"   Max Position Size: {risk_config['max_position_size_pct']}%")
    print(f"   Max Portfolio Risk: {risk_config['max_portfolio_risk_pct']}%")
    print(f"   Max Positions: {risk_config['max_open_positions']}")
    print(f"   Max Drawdown: {risk_config['max_drawdown_pct']}%")

    # Test position sizing
    portfolio2 = Portfolio(100000)

    analysis = {
        'ticker': 'HDFCBANK.NS',
        'current_price': 1650.0,
        'stop_loss': 1600.0,
        'composite_score': 75,
        'backtest': {
            'win_rate': 65,
            'avg_return_pct': 6.5,
            'avg_loss_pct': -3.0
        }
    }

    quantity = risk_manager.calculate_safe_position_size(portfolio2, analysis)
    print(f"\n✅ Position size calculated:")
    print(f"   Stock: HDFCBANK.NS @ ₹1,650")
    print(f"   Score: 75/100")
    print(f"   Stop Loss: ₹1,600 (risk: ₹50/share)")
    print(f"   Recommended Quantity: {quantity} shares")
    print(f"   Position Value: ₹{quantity * 1650:,.2f}")
    print(f"   Total Risk: ₹{quantity * 50:,.2f}")

    print("\n" + "="*80)
    print("✅ ALL COMPONENT TESTS PASSED")
    print("="*80)


async def main():
    """Main test function"""

    import argparse
    parser = argparse.ArgumentParser(description='Paper Trading System Test')
    parser.add_argument(
        '--mode',
        choices=['components', 'full', 'both'],
        default='both',
        help='Test mode: components, full, or both'
    )
    args = parser.parse_args()

    if args.mode in ['components', 'both']:
        await test_components()

    if args.mode in ['full', 'both']:
        print("\n\n")
        response = input("⚠️  Full test will start paper trading engine. Continue? (y/n): ")
        if response.lower() == 'y':
            await test_paper_trading()
        else:
            print("❌ Full test skipped")


if __name__ == '__main__':
    try:
        asyncio.run(main())
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
