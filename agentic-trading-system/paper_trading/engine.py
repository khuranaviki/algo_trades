"""
Paper Trading Engine

Main orchestrator for simulated trading:
- Monitors watchlist for signals
- Executes orders through simulator
- Manages positions (stops, targets)
- Enforces risk limits
"""

import asyncio
import logging
from datetime import datetime, time
from typing import Dict, List, Optional, Any
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .portfolio import Portfolio
from .order_executor import OrderExecutor
from .data_stream import LiveDataStream
from .risk_manager import RiskManager
from agents.orchestrator import Orchestrator


class PaperTradingEngine:
    """Main paper trading orchestrator"""

    def __init__(self, config: Dict[str, Any]):
        """
        Args:
            config: Complete configuration dict
        """
        self.config = config

        # Initialize components
        self.portfolio = Portfolio(config.get('initial_capital', 1000000))
        self.order_executor = OrderExecutor(
            slippage_pct=config.get('slippage_pct', 0.05),
            use_realistic_costs=config.get('use_realistic_costs', True)
        )

        self.watchlist = config.get('watchlist', [])
        self.data_stream = LiveDataStream(
            tickers=self.watchlist,
            update_interval=config.get('update_interval_seconds', 60),
            max_cache_days=config.get('cache_max_days', 1825)
        )

        self.risk_manager = RiskManager(config.get('risk_management', {}))

        # Initialize orchestrator for decision making
        self.orchestrator = Orchestrator(config.get('orchestrator', {}))

        # State
        self.is_running = False
        self.last_scan_time = None
        self.scan_results = {}

        # Statistics
        self.stats = {
            'scans_completed': 0,
            'signals_detected': 0,
            'orders_executed': 0,
            'positions_opened': 0,
            'positions_closed': 0,
            'risk_blocks': 0
        }

        self.logger = logging.getLogger(__name__)

    async def start(self):
        """Start paper trading engine"""
        self.logger.info("=" * 80)
        self.logger.info("🚀 PAPER TRADING ENGINE STARTING")
        self.logger.info("=" * 80)
        self.logger.info(f"Initial Capital: ₹{self.portfolio.initial_capital:,.0f}")
        self.logger.info(f"Watchlist: {len(self.watchlist)} stocks")
        self.logger.info(f"Update Interval: {self.config.get('update_interval_seconds', 60)}s")
        self.logger.info("=" * 80)

        self.is_running = True

        try:
            # Start data stream
            self.logger.info("📡 Starting data stream...")
            await self.data_stream.start()

            # Start main monitoring loop
            await self._run_monitoring_loop()

        except KeyboardInterrupt:
            self.logger.info("\n⚠️ Shutdown requested by user")
            await self.stop()
        except Exception as e:
            self.logger.error(f"❌ Fatal error: {e}")
            import traceback
            traceback.print_exc()
            await self.stop()

    async def _run_monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_running:
            try:
                market_status = self.data_stream.is_market_open()

                if market_status['open']:
                    # Market is open - run scan and trade
                    await self._scan_and_trade()

                    # Take daily snapshot
                    self.portfolio.take_snapshot()

                    # Log status
                    self._log_status()

                else:
                    # Market closed
                    reason = market_status.get('reason', 'closed')
                    opens_at = market_status.get('opens_at')

                    if reason == 'before_market':
                        self.logger.info(
                            f"⏰ Market not yet open. Opens at {opens_at.strftime('%H:%M')} IST"
                        )
                    elif reason == 'after_market':
                        self.logger.info(
                            f"🌙 Market closed. Opens at {opens_at.strftime('%Y-%m-%d %H:%M')} IST"
                        )
                    elif reason == 'weekend':
                        self.logger.info(
                            f"📅 Weekend. Market opens {opens_at.strftime('%A, %Y-%m-%d at %H:%M')} IST"
                        )

                # Sleep until next update
                await asyncio.sleep(self.config.get('update_interval_seconds', 60))

            except Exception as e:
                self.logger.error(f"❌ Error in monitoring loop: {e}")
                import traceback
                traceback.print_exc()
                await asyncio.sleep(5)  # Brief pause before retry

    async def _scan_and_trade(self):
        """Scan watchlist and execute trades"""
        self.logger.info(f"\n{'='*80}")
        self.logger.info(f"📊 SCANNING WATCHLIST ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
        self.logger.info(f"{'='*80}")

        for ticker in self.watchlist:
            try:
                # Get latest price
                price_data = await self.data_stream.get_latest_price(ticker)

                if not price_data:
                    self.logger.warning(f"⚠️ No price data for {ticker}, skipping")
                    continue

                # Check existing positions for exit signals
                if ticker in self.portfolio.positions:
                    await self._manage_position(ticker, price_data)

                # Check for new entry signals (if not already in position)
                else:
                    await self._check_entry_signal(ticker, price_data)

            except Exception as e:
                self.logger.error(f"❌ Error processing {ticker}: {e}")
                continue

        self.stats['scans_completed'] += 1
        self.last_scan_time = datetime.now()

    async def _check_entry_signal(self, ticker: str, price_data: Dict[str, Any]):
        """
        Check if orchestrator signals BUY

        Args:
            ticker: Stock ticker
            price_data: Latest price data
        """
        current_price = price_data['price']

        # Check if we have sufficient historical data
        if not self.data_stream.cache.has_sufficient_data(ticker, min_days=200):
            self.logger.debug(f"⏳ {ticker}: Insufficient data for analysis")
            return

        # Run orchestrator analysis
        self.logger.info(f"\n🔍 Analyzing {ticker} @ ₹{current_price:.2f}")

        try:
            result = await self.orchestrator.analyze(ticker, {
                'company_name': self._get_company_name(ticker),
                'market_regime': self._detect_market_regime()
            })

            # Store result
            self.scan_results[ticker] = result

            decision = result.get('decision', 'HOLD')
            score = result.get('composite_score', 0)
            confidence = result.get('confidence', 0)

            self.logger.info(
                f"   Decision: {decision} | Score: {score:.1f}/100 | Confidence: {confidence}%"
            )

            if decision in ['BUY', 'STRONG BUY']:
                self.stats['signals_detected'] += 1
                await self._execute_buy(ticker, price_data, result)

        except Exception as e:
            self.logger.error(f"❌ Analysis failed for {ticker}: {e}")

    async def _execute_buy(
        self,
        ticker: str,
        price_data: Dict[str, Any],
        analysis: Dict[str, Any]
    ):
        """
        Execute BUY order

        Args:
            ticker: Stock ticker
            price_data: Latest price data
            analysis: Orchestrator analysis result
        """
        current_price = price_data['price']

        # Calculate position size
        quantity = self.risk_manager.calculate_safe_position_size(
            portfolio=self.portfolio,
            analysis={
                **analysis,
                'ticker': ticker,
                'current_price': current_price
            }
        )

        if quantity == 0:
            self.logger.warning(f"⚠️ Position size calculated as 0 for {ticker}")
            return

        estimated_cost = quantity * current_price

        # Risk checks
        can_open, reasons = self.risk_manager.can_open_position(
            portfolio=self.portfolio,
            ticker=ticker,
            analysis={
                **analysis,
                'ticker': ticker,
                'current_price': current_price,
                'quantity': quantity
            }
        )

        if not can_open:
            self.logger.warning(f"🚫 Risk check BLOCKED {ticker}:")
            for reason in reasons:
                self.logger.warning(f"   • {reason}")
            self.stats['risk_blocks'] += 1
            return

        # Execute order
        try:
            order_result = self.order_executor.execute_market_order(
                ticker=ticker,
                action='BUY',
                quantity=quantity,
                current_price=current_price,
                bid=price_data.get('bid'),
                ask=price_data.get('ask')
            )

            # Open position in portfolio
            trade = self.portfolio.open_position(
                ticker=ticker,
                quantity=order_result['quantity'],
                price=order_result['fill_price'],
                stop_loss=None,
                target=analysis.get('target_price'),
                reason=analysis.get('decision_reasoning', ''),
                transaction_cost=order_result['transaction_cost']
            )

            self.stats['orders_executed'] += 1
            self.stats['positions_opened'] += 1

            self.logger.info(
                f"\n{'='*80}\n"
                f"✅ POSITION OPENED: {ticker}\n"
                f"{'='*80}\n"
                f"   Quantity:     {quantity} shares\n"
                f"   Entry Price:  ₹{order_result['fill_price']:.2f}\n"
                f"   Total Cost:   ₹{order_result['total_cost']:,.2f}\n"
                f"   Target:       ₹{analysis.get('target_price', 0):.2f}\n"
                f"   Score:        {analysis.get('composite_score', 0):.1f}/100\n"
                f"{'='*80}\n"
            )

        except Exception as e:
            self.logger.error(f"❌ Order execution failed for {ticker}: {e}")

    async def _manage_position(self, ticker: str, price_data: Dict[str, Any]):
        """
        Manage existing position

        Checks:
        - Target
        - Exit signals from orchestrator

        Args:
            ticker: Stock ticker
            price_data: Latest price data
        """
        position = self.portfolio.positions[ticker]
        current_price = price_data['price']

        # Update position price
        position.current_price = current_price

        self.logger.debug(
            f"   {ticker}: ₹{current_price:.2f} | "
            f"P&L: {position.unrealized_pnl_pct:+.2f}% (₹{position.unrealized_pnl:+,.0f})"
        )

        # Check target
        if self.order_executor.check_target(position, current_price):
            await self._close_position(ticker, current_price, 'target_reached')
            return

        # Re-analyze for exit signals (every 10th scan to reduce cost)
        if self.stats['scans_completed'] % 10 == 0:
            try:
                result = await self.orchestrator.analyze(ticker, {
                    'company_name': self._get_company_name(ticker),
                    'market_regime': self._detect_market_regime()
                })

                decision = result.get('decision')

                if decision == 'SELL':
                    self.logger.warning(
                        f"⚠️ SELL signal detected for {ticker} "
                        f"(currently holding with P&L: {position.unrealized_pnl_pct:+.2f}%)"
                    )
                    await self._close_position(ticker, current_price, 'sell_signal')

            except Exception as e:
                self.logger.error(f"❌ Re-analysis failed for {ticker}: {e}")

    async def _close_position(self, ticker: str, price: float, reason: str):
        """
        Close position

        Args:
            ticker: Stock ticker
            price: Current price
            reason: Exit reason
        """
        if ticker not in self.portfolio.positions:
            self.logger.warning(f"⚠️ No position to close for {ticker}")
            return

        position = self.portfolio.positions[ticker]

        try:
            # Execute sell order
            order_result = self.order_executor.execute_market_order(
                ticker=ticker,
                action='SELL',
                quantity=position.quantity,
                current_price=price
            )

            # Close position in portfolio
            trade = self.portfolio.close_position(
                ticker=ticker,
                price=order_result['fill_price'],
                reason=reason,
                transaction_cost=order_result['transaction_cost']
            )

            self.stats['orders_executed'] += 1
            self.stats['positions_closed'] += 1

            pnl_emoji = "🟢" if trade.realized_pnl > 0 else "🔴"

            self.logger.info(
                f"\n{'='*80}\n"
                f"{pnl_emoji} POSITION CLOSED: {ticker}\n"
                f"{'='*80}\n"
                f"   Quantity:     {trade.quantity} shares\n"
                f"   Exit Price:   ₹{order_result['fill_price']:.2f}\n"
                f"   Realized P&L: ₹{trade.realized_pnl:+,.2f} ({trade.realized_pnl_pct:+.2f}%)\n"
                f"   Reason:       {reason}\n"
                f"   Days Held:    {position.days_held}\n"
                f"{'='*80}\n"
            )

        except Exception as e:
            self.logger.error(f"❌ Failed to close position for {ticker}: {e}")

    def _get_company_name(self, ticker: str) -> str:
        """Get company name for ticker"""
        # Simplified mapping (expand in production)
        company_names = {
            'RELIANCE.NS': 'Reliance Industries',
            'TCS.NS': 'Tata Consultancy Services',
            'INFY.NS': 'Infosys',
            'HDFCBANK.NS': 'HDFC Bank',
            'ICICIBANK.NS': 'ICICI Bank',
            'BAJFINANCE.NS': 'Bajaj Finance',
            'BHARTIARTL.NS': 'Bharti Airtel',
            'MARUTI.NS': 'Maruti Suzuki',
            'TATAMOTORS.NS': 'Tata Motors',
            'TITAN.NS': 'Titan Company'
        }
        return company_names.get(ticker, ticker.replace('.NS', ''))

    def _detect_market_regime(self) -> str:
        """
        Detect current market regime

        In production, this would analyze Nifty 50 trends
        For now, simplified
        """
        # TODO: Implement proper market regime detection
        # - Analyze Nifty 50 trend
        # - Check VIX levels
        # - Assess breadth indicators
        return 'neutral'

    def _log_status(self):
        """Log current status"""
        total_value = self.portfolio.get_total_value()
        total_return_pct = self.portfolio.get_total_return_pct()
        metrics = self.portfolio.get_performance_metrics()

        self.logger.info(
            f"\n📈 Portfolio: ₹{total_value:,.0f} | "
            f"Return: {total_return_pct:+.2f}% | "
            f"Positions: {len(self.portfolio.positions)} | "
            f"Cash: ₹{self.portfolio.cash:,.0f}"
        )

        if metrics['closed_trades'] > 0:
            self.logger.info(
                f"   Trades: {metrics['closed_trades']} | "
                f"Win Rate: {metrics['win_rate']:.1f}% | "
                f"Sharpe: {metrics['sharpe_ratio']:.2f}"
            )

    async def stop(self):
        """Stop paper trading engine"""
        self.logger.info("\n" + "=" * 80)
        self.logger.info("🛑 STOPPING PAPER TRADING ENGINE")
        self.logger.info("=" * 80)

        self.is_running = False

        # Stop data stream
        self.data_stream.stop()

        # Generate final report
        self._generate_final_report()

        self.logger.info("✅ Engine stopped successfully")

    def _generate_final_report(self):
        """Generate final performance report"""
        metrics = self.portfolio.get_performance_metrics()

        self.logger.info("\n" + "=" * 80)
        self.logger.info("📊 FINAL PERFORMANCE REPORT")
        self.logger.info("=" * 80)

        self.logger.info(f"\n💰 Portfolio:")
        self.logger.info(f"   Initial Capital:  ₹{self.portfolio.initial_capital:,.0f}")
        self.logger.info(f"   Final Value:      ₹{metrics['total_value']:,.0f}")
        self.logger.info(f"   Total Return:     {metrics['total_return_pct']:+.2f}%")
        self.logger.info(f"   Cash:             ₹{metrics['cash']:,.0f}")

        self.logger.info(f"\n📈 Performance:")
        self.logger.info(f"   Sharpe Ratio:     {metrics['sharpe_ratio']:.2f}")
        self.logger.info(f"   Max Drawdown:     {metrics['max_drawdown_pct']:.2f}%")
        self.logger.info(f"   Win Rate:         {metrics['win_rate']:.1f}%")
        self.logger.info(f"   Avg Win:          {metrics['avg_win_pct']:+.2f}%")
        self.logger.info(f"   Avg Loss:         {metrics['avg_loss_pct']:+.2f}%")

        self.logger.info(f"\n📊 Trading Activity:")
        self.logger.info(f"   Total Trades:     {metrics['total_trades']}")
        self.logger.info(f"   Closed Trades:    {metrics['closed_trades']}")
        self.logger.info(f"   Open Positions:   {metrics['num_positions']}")
        self.logger.info(f"   Scans Completed:  {self.stats['scans_completed']}")
        self.logger.info(f"   Signals Detected: {self.stats['signals_detected']}")
        self.logger.info(f"   Risk Blocks:      {self.stats['risk_blocks']}")

        self.logger.info("\n" + "=" * 80)

        # Get risk report
        risk_report = self.risk_manager.get_risk_report(self.portfolio)

        self.logger.info("\n🛡️  RISK REPORT:")
        self.logger.info(f"   Drawdown:         {risk_report['current_drawdown_pct']:.2f}%")
        self.logger.info(f"   Max Position:     {risk_report['max_position_size_pct']:.2f}%")
        self.logger.info(f"   Position Util:    {risk_report['utilization']['positions']:.1f}%")
        self.logger.info(f"   Drawdown Util:    {risk_report['utilization']['drawdown']:.1f}%")

        if risk_report['sector_exposure']:
            self.logger.info("\n   Sector Exposure:")
            for sector, pct in sorted(risk_report['sector_exposure'].items(), key=lambda x: -x[1]):
                self.logger.info(f"      {sector:15s}: {pct:.1f}%")

        self.logger.info("\n" + "=" * 80)
