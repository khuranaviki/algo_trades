"""
Historical Backtest Simulator

Simulates the paper trading system running over historical period.
Replays past 6 months day-by-day as if system was live.

Key features:
- Day-by-day simulation with real historical prices
- Exact same logic as paper trading engine
- Full orchestrator analysis at each decision point
- Realistic transaction costs and slippage
- Complete trade log and performance metrics
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
from tqdm import tqdm
import json

from .portfolio import Portfolio
from .order_executor import OrderExecutor
from .risk_manager import RiskManager
from agents.orchestrator import Orchestrator


class HistoricalBacktest:
    """Historical backtest simulator with day-by-day replay"""

    def __init__(self, config: Dict[str, Any]):
        """
        Args:
            config: Backtest configuration
        """
        self.config = config

        # Backtest period
        self.start_date = config.get('start_date')
        self.end_date = config.get('end_date')
        self.watchlist = config.get('watchlist', [])

        # Components
        self.portfolio = Portfolio(config.get('initial_capital', 1000000))
        self.order_executor = OrderExecutor(
            slippage_pct=config.get('slippage_pct', 0.05),
            use_realistic_costs=True
        )
        self.risk_manager = RiskManager(config.get('risk_management', {}))
        self.orchestrator = Orchestrator(config.get('orchestrator', {}))

        # Historical data cache
        self.historical_data = {}
        self.trading_days = []

        # Results tracking
        self.daily_results = []
        self.all_signals = []
        self.all_trades = []

        self.logger = logging.getLogger(__name__)

    async def run(self):
        """Run historical backtest"""
        self.logger.info("=" * 80)
        self.logger.info("📊 HISTORICAL BACKTEST SIMULATOR")
        self.logger.info("=" * 80)
        self.logger.info(f"Period: {self.start_date} to {self.end_date}")
        self.logger.info(f"Watchlist: {len(self.watchlist)} stocks")
        self.logger.info(f"Initial Capital: ₹{self.portfolio.initial_capital:,.0f}")
        self.logger.info("=" * 80)

        # Step 1: Fetch all historical data
        await self._fetch_historical_data()

        # Step 2: Generate trading days
        self._generate_trading_days()

        # Step 3: Run day-by-day simulation
        await self._run_simulation()

        # Step 4: Generate report
        report = self._generate_report()

        return report

    async def _fetch_historical_data(self):
        """Fetch historical data for all stocks in watchlist"""
        self.logger.info("\n📥 Fetching historical data...")
        self.logger.info(f"Backtest period: {self.start_date.date()} to {self.end_date.date()}")

        import yfinance as yf

        for ticker in tqdm(self.watchlist, desc="Downloading"):
            try:
                # Fetch data with 5+ years BEFORE backtest start
                # This ensures we have full 5-year lookback at every point in backtest
                buffer_days = 2190  # 6 years (to be safe, accounts for weekends/holidays)
                fetch_start = self.start_date - timedelta(days=buffer_days)

                self.logger.debug(
                    f"Fetching {ticker} from {fetch_start.date()} to {self.end_date.date()} "
                    f"(~{buffer_days} days buffer)"
                )

                stock = yf.Ticker(ticker)
                df = stock.history(start=fetch_start, end=self.end_date, interval='1d')

                if df.empty:
                    self.logger.warning(f"⚠️ No data for {ticker}")
                    continue

                # Store with proper column names
                df.columns = [col.lower() for col in df.columns]
                self.historical_data[ticker] = df

                self.logger.debug(
                    f"✅ {ticker}: {len(df)} days "
                    f"({df.index[0].date()} to {df.index[-1].date()})"
                )

            except Exception as e:
                self.logger.error(f"❌ Failed to fetch {ticker}: {e}")

        self.logger.info(f"✅ Downloaded data for {len(self.historical_data)} stocks")

    def _generate_trading_days(self):
        """Generate list of trading days in backtest period"""
        # Use first stock's dates as reference
        if not self.historical_data:
            raise ValueError("No historical data loaded")

        reference_ticker = list(self.historical_data.keys())[0]
        df = self.historical_data[reference_ticker]

        # Convert start/end dates to timezone-aware if df.index is timezone-aware
        start_date = self.start_date
        end_date = self.end_date

        if df.index.tz is not None:
            # Make dates timezone-aware to match df.index
            import pytz
            if start_date.tzinfo is None:
                start_date = start_date.replace(tzinfo=pytz.UTC).astimezone(df.index.tz)
            if end_date.tzinfo is None:
                end_date = end_date.replace(tzinfo=pytz.UTC).astimezone(df.index.tz)

        # Filter to backtest period
        mask = (df.index >= start_date) & (df.index <= end_date)
        dates = df[mask].index

        self.trading_days = [d.to_pydatetime() for d in dates]

        self.logger.info(f"📅 Trading days in period: {len(self.trading_days)}")

    async def _run_simulation(self):
        """Run day-by-day simulation"""
        self.logger.info("\n🔄 Running simulation...")
        self.logger.info(f"Simulating {len(self.trading_days)} trading days\n")

        for day_idx, current_date in enumerate(tqdm(self.trading_days, desc="Simulating")):
            # Simulate trading day
            await self._simulate_trading_day(current_date, day_idx)

            # Take daily snapshot
            self.portfolio.take_snapshot()

            # Record daily result
            self.daily_results.append({
                'date': current_date,
                'total_value': self.portfolio.get_total_value(),
                'cash': self.portfolio.cash,
                'num_positions': len(self.portfolio.positions),
                'daily_return': self._calculate_daily_return(),
                'cumulative_return': self.portfolio.get_total_return_pct()
            })

        self.logger.info(f"\n✅ Simulation complete: {len(self.trading_days)} days")

    async def _simulate_trading_day(self, current_date: datetime, day_idx: int):
        """
        Simulate a single trading day

        Args:
            current_date: Date to simulate
            day_idx: Index in trading_days list
        """
        # Update position prices first
        current_prices = self._get_prices_for_date(current_date)
        self.portfolio.update_prices(current_prices)

        # Check existing positions for exits
        for ticker in list(self.portfolio.positions.keys()):
            await self._check_position_exit(ticker, current_date, current_prices[ticker])

        # Check for new entry signals
        for ticker in self.watchlist:
            if ticker not in self.portfolio.positions:
                await self._check_entry_signal(ticker, current_date, day_idx)

    def _get_prices_for_date(self, date: datetime) -> Dict[str, float]:
        """Get closing prices for all stocks on given date"""
        prices = {}

        for ticker, df in self.historical_data.items():
            try:
                # Convert date to match timezone if needed
                query_date = date
                if df.index.tz is not None and date.tzinfo is None:
                    import pytz
                    query_date = date.replace(tzinfo=pytz.UTC).astimezone(df.index.tz)

                # Get price for this date (or closest previous date)
                price_series = df.loc[:query_date, 'close']
                if len(price_series) > 0:
                    prices[ticker] = float(price_series.iloc[-1])
            except Exception as e:
                self.logger.debug(f"Could not get price for {ticker} on {date}: {e}")

        return prices

    def _get_historical_data_until(self, ticker: str, date: datetime) -> pd.DataFrame:
        """Get historical data for ticker up to (but not including) date"""
        if ticker not in self.historical_data:
            return pd.DataFrame()

        df = self.historical_data[ticker]

        # Convert date to match timezone if needed
        if df.index.tz is not None and date.tzinfo is None:
            import pytz
            date = date.replace(tzinfo=pytz.UTC).astimezone(df.index.tz)

        return df.loc[:date].iloc[:-1]  # Exclude current day

    async def _check_entry_signal(self, ticker: str, current_date: datetime, day_idx: int):
        """
        Check if entry signal exists for ticker on this date

        Args:
            ticker: Stock ticker
            current_date: Current date
            day_idx: Day index (for lookback check)
        """
        # Get data up to (but not including) current date
        historical_df = self._get_historical_data_until(ticker, current_date)

        # CRITICAL: Must have 5 years (1825 days) of data before current date
        # This ensures we have sufficient history for:
        # - 200-day MA calculation
        # - Full pattern formation
        # - 5-year backtest validation
        min_required_days = 1250  # ~5 years of trading days

        if len(historical_df) < min_required_days:
            self.logger.debug(
                f"{ticker} on {current_date.date()}: Insufficient data "
                f"({len(historical_df)} days, need {min_required_days})"
            )
            return

        try:
            # Get current price
            current_price = float(self.historical_data[ticker].loc[current_date, 'close'])

            # Run orchestrator analysis
            # NOTE: This uses data up to (but not including) current_date
            # Preventing look-ahead bias
            result = await self.orchestrator.analyze(ticker, {
                'company_name': self._get_company_name(ticker),
                'market_regime': 'neutral',
                'current_date': current_date  # For time-aware analysis
            })

            decision = result.get('decision', 'HOLD')
            score = result.get('composite_score', 0)

            # Store signal
            self.all_signals.append({
                'date': current_date,
                'ticker': ticker,
                'decision': decision,
                'score': score,
                'confidence': result.get('confidence', 0),
                'technical_signal': result.get('technical_signal', {}),
                'used_llm': result.get('used_llm_synthesis', False)
            })

            # If BUY signal, attempt to execute
            if decision in ['BUY', 'STRONG BUY']:
                await self._execute_buy(ticker, current_date, current_price, result)

        except Exception as e:
            self.logger.debug(f"Analysis failed for {ticker} on {current_date}: {e}")

    async def _execute_buy(
        self,
        ticker: str,
        date: datetime,
        price: float,
        analysis: Dict[str, Any]
    ):
        """Execute BUY order in backtest"""

        # Calculate position size
        quantity = self.risk_manager.calculate_safe_position_size(
            portfolio=self.portfolio,
            analysis={
                **analysis,
                'ticker': ticker,
                'current_price': price
            }
        )

        if quantity == 0:
            return

        # Risk checks
        can_open, reasons = self.risk_manager.can_open_position(
            portfolio=self.portfolio,
            ticker=ticker,
            analysis={
                **analysis,
                'ticker': ticker,
                'current_price': price,
                'quantity': quantity
            }
        )

        if not can_open:
            self.logger.debug(f"Risk check blocked {ticker} on {date}")
            return

        # Execute order
        try:
            order_result = self.order_executor.execute_market_order(
                ticker=ticker,
                action='BUY',
                quantity=quantity,
                current_price=price
            )

            # Open position
            trade = self.portfolio.open_position(
                ticker=ticker,
                quantity=order_result['quantity'],
                price=order_result['fill_price'],
                stop_loss=analysis.get('stop_loss'),
                target=analysis.get('target_price'),
                reason=f"BUY signal on {date.date()}",
                transaction_cost=order_result['transaction_cost']
            )

            self.all_trades.append({
                'date': date,
                'action': 'BUY',
                'ticker': ticker,
                'quantity': quantity,
                'price': order_result['fill_price'],
                'cost': order_result['total_cost'],
                'stop_loss': analysis.get('stop_loss'),
                'target': analysis.get('target_price')
            })

            self.logger.info(
                f"✅ {date.date()} | BOUGHT {ticker}: {quantity} shares @ ₹{price:.2f}"
            )

        except Exception as e:
            self.logger.error(f"❌ Buy execution failed for {ticker}: {e}")

    async def _check_position_exit(self, ticker: str, date: datetime, current_price: float):
        """Check if position should be exited"""

        position = self.portfolio.positions[ticker]

        # Check stop loss
        if self.order_executor.check_stop_loss(position, current_price):
            await self._close_position(ticker, date, current_price, 'stop_loss_hit')
            return

        # Check target
        if self.order_executor.check_target(position, current_price):
            await self._close_position(ticker, date, current_price, 'target_reached')
            return

        # NO HOLDING PERIOD LIMIT for backtest
        # Let positions run until stop loss or target hit
        # (Pattern validation uses 60-day limit, but actual trades have no time limit)

    async def _close_position(self, ticker: str, date: datetime, price: float, reason: str):
        """Close position in backtest"""

        if ticker not in self.portfolio.positions:
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

            # Close position
            trade = self.portfolio.close_position(
                ticker=ticker,
                price=order_result['fill_price'],
                reason=reason,
                transaction_cost=order_result['transaction_cost']
            )

            self.all_trades.append({
                'date': date,
                'action': 'SELL',
                'ticker': ticker,
                'quantity': trade.quantity,
                'price': order_result['fill_price'],
                'proceeds': order_result['total_cost'],
                'pnl': trade.realized_pnl,
                'pnl_pct': trade.realized_pnl_pct,
                'reason': reason
            })

            pnl_emoji = "🟢" if trade.realized_pnl > 0 else "🔴"
            self.logger.info(
                f"{pnl_emoji} {date.date()} | SOLD {ticker}: "
                f"P&L = ₹{trade.realized_pnl:+,.0f} ({trade.realized_pnl_pct:+.2f}%) | {reason}"
            )

        except Exception as e:
            self.logger.error(f"❌ Sell execution failed for {ticker}: {e}")

    def _calculate_daily_return(self) -> float:
        """Calculate daily return percentage"""
        if len(self.daily_results) == 0:
            return 0.0

        prev_value = self.daily_results[-1]['total_value']
        current_value = self.portfolio.get_total_value()

        if prev_value == 0:
            return 0.0

        return ((current_value - prev_value) / prev_value) * 100

    def _get_company_name(self, ticker: str) -> str:
        """Get company name for ticker"""
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

    def _generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive backtest report"""
        self.logger.info("\n" + "=" * 80)
        self.logger.info("📊 BACKTEST RESULTS")
        self.logger.info("=" * 80)

        # Performance metrics
        metrics = self.portfolio.get_performance_metrics()

        # Trade analysis
        trades_df = pd.DataFrame(self.all_trades)
        signals_df = pd.DataFrame(self.all_signals)

        # Calculate additional metrics
        num_trades = len([t for t in self.all_trades if t['action'] == 'SELL'])
        num_signals = len([s for s in self.all_signals if s['decision'] in ['BUY', 'STRONG BUY']])

        # Print summary
        self.logger.info(f"\n💰 PORTFOLIO:")
        self.logger.info(f"   Initial Capital:  ₹{self.portfolio.initial_capital:,.0f}")
        self.logger.info(f"   Final Value:      ₹{metrics['total_value']:,.0f}")
        self.logger.info(f"   Total Return:     {metrics['total_return_pct']:+.2f}%")
        self.logger.info(f"   Cash:             ₹{metrics['cash']:,.0f}")

        self.logger.info(f"\n📈 PERFORMANCE:")
        self.logger.info(f"   Sharpe Ratio:     {metrics['sharpe_ratio']:.2f}")
        self.logger.info(f"   Max Drawdown:     {metrics['max_drawdown_pct']:.2f}%")
        self.logger.info(f"   Win Rate:         {metrics['win_rate']:.1f}%")
        self.logger.info(f"   Avg Win:          {metrics['avg_win_pct']:+.2f}%")
        self.logger.info(f"   Avg Loss:         {metrics['avg_loss_pct']:+.2f}%")

        self.logger.info(f"\n📊 ACTIVITY:")
        self.logger.info(f"   BUY Signals:      {num_signals}")
        self.logger.info(f"   Trades Executed:  {num_trades}")
        self.logger.info(f"   Signal->Trade:    {num_trades/num_signals*100:.1f}%" if num_signals > 0 else "   Signal->Trade:    N/A")
        self.logger.info(f"   LLM Used:         {sum(1 for s in self.all_signals if s['used_llm'])} times")

        self.logger.info("\n" + "=" * 80)

        # Return comprehensive report
        return {
            'config': self.config,
            'period': {
                'start': self.start_date,
                'end': self.end_date,
                'trading_days': len(self.trading_days)
            },
            'performance': metrics,
            'activity': {
                'signals_detected': num_signals,
                'trades_executed': num_trades,
                'execution_rate': num_trades/num_signals if num_signals > 0 else 0
            },
            'trades': self.all_trades,
            'signals': self.all_signals,
            'daily_results': self.daily_results
        }

    def save_report(self, filename: str):
        """Save backtest report to file"""
        report = self._generate_report()

        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        self.logger.info(f"💾 Report saved to: {filename}")
