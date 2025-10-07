#!/usr/bin/env python3
"""
V40 Portfolio Strategy - Combined Fundamental + Technical with 5% Position Sizing

Entry Signals:
1. Fundamental: Revenue growth >15%, ROCE >18%, ROE >15%, D/E <1.5
2. Technical: Golden Cross (SMA 20 > SMA 50) + RSI not overbought

Exit Signals:
1. Strategy Target: 20% gain for V40, 30% gain for V40 Next
2. Stop Loss: 10% loss
3. Technical: Death Cross or RSI overbought

Position Sizing: Maximum 5% per stock
"""

import backtrader as bt
import sys
import os

# Import V40 universe
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from v40_universe import is_v40_stock, is_v40_next_stock


class V40PortfolioStrategy(bt.Strategy):
    """
    V40 Portfolio Strategy with Fundamental + Technical Signals

    Maximum 5% position size per stock
    Sells at strategy targets (20% for V40, 30% for V40 Next)
    """

    params = (
        # Position sizing
        ('max_position_pct', 0.05),      # Max 5% per stock
        ('max_total_exposure', 0.95),    # Max 95% total portfolio exposure

        # Technical indicators
        ('sma_short', 20),
        ('sma_long', 50),
        ('rsi_period', 14),
        ('rsi_oversold', 40),
        ('rsi_overbought', 70),

        # Fundamental filters (passed from outside)
        ('fundamental_data', {}),        # Dict of {ticker: {metrics}}

        # Target and stop loss
        ('v40_target_pct', 0.20),        # 20% target for V40
        ('v40_next_target_pct', 0.30),   # 30% target for V40 Next
        ('stop_loss_pct', 0.10),         # 10% stop loss

        ('print_log', True),
    )

    def __init__(self):
        # Track positions
        self.entry_prices = {}
        self.target_prices = {}
        self.stop_losses = {}
        self.orders = {}

        # Track which stocks passed fundamental screening
        self.fundamental_passed = {}

        # Technical indicators for each data feed
        self.sma_short = {}
        self.sma_long = {}
        self.rsi = {}
        self.crossover = {}

        for i, d in enumerate(self.datas):
            ticker = d._name

            # Create indicators
            self.sma_short[d] = bt.indicators.SMA(d.close, period=self.params.sma_short)
            self.sma_long[d] = bt.indicators.SMA(d.close, period=self.params.sma_long)
            self.rsi[d] = bt.indicators.RSI(d.close, period=self.params.rsi_period)
            self.crossover[d] = bt.indicators.CrossOver(self.sma_short[d], self.sma_long[d])

            # Check fundamental screening
            self.fundamental_passed[ticker] = self.passes_fundamental_screening(ticker)

    def log(self, txt, dt=None):
        """Logging function"""
        if self.params.print_log:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()} {txt}')

    def passes_fundamental_screening(self, ticker):
        """Check if stock passes fundamental screening criteria"""
        fund_data = self.params.fundamental_data.get(ticker, {})

        if not fund_data:
            # No fundamental data - allow entry based on V40 membership
            return True

        # Extract metrics (handle None/missing values)
        try:
            revenue_growth = float(fund_data.get('revenue_growth_yoy', 0) or 0)
            roce = float(fund_data.get('roce', 0) or 0)
            roe = float(fund_data.get('roe', 0) or 0)
            debt_equity = float(fund_data.get('debt_to_equity', 999) or 999)

            # V40 vs V40 Next criteria
            if is_v40_stock(ticker):
                min_rev_growth = 15.0
                min_roce = 18.0
                min_roe = 15.0
                max_de = 1.5
            else:  # V40 Next
                min_rev_growth = 20.0
                min_roce = 15.0
                min_roe = 12.0
                max_de = 2.0

            # Check criteria
            passes = (
                revenue_growth >= min_rev_growth and
                roce >= min_roce and
                roe >= min_roe and
                debt_equity <= max_de
            )

            if passes:
                self.log(f'{ticker} PASSED Fundamental Screening: Rev Growth {revenue_growth:.1f}%, ROCE {roce:.1f}%, ROE {roe:.1f}%')
            else:
                self.log(f'{ticker} FAILED Fundamental Screening')

            return passes

        except Exception as e:
            # On error, default to True (allow entry based on V40 membership)
            return True

    def get_target_pct(self, ticker):
        """Get target percentage based on V40 vs V40 Next"""
        if is_v40_stock(ticker):
            return self.params.v40_target_pct
        else:
            return self.params.v40_next_target_pct

    def get_current_exposure(self):
        """Calculate current portfolio exposure (% of portfolio value in positions)"""
        total_value = self.broker.getvalue()
        positions_value = 0

        for d in self.datas:
            pos = self.getposition(d)
            if pos.size > 0:
                positions_value += pos.size * d.close[0]

        return positions_value / total_value if total_value > 0 else 0

    def get_position_count(self):
        """Get number of open positions"""
        return sum(1 for d in self.datas if self.getposition(d).size > 0)

    def notify_order(self, order):
        """Notification of order status"""
        if order.status in [order.Submitted, order.Accepted]:
            return

        ticker = order.data._name

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY {ticker} @ ₹{order.executed.price:.2f}, Size: {order.executed.size}')

                # Set entry tracking
                self.entry_prices[ticker] = order.executed.price

                target_pct = self.get_target_pct(ticker)
                self.target_prices[ticker] = order.executed.price * (1 + target_pct)
                self.stop_losses[ticker] = order.executed.price * (1 - self.params.stop_loss_pct)

                self.log(f'  Target: ₹{self.target_prices[ticker]:.2f} ({target_pct*100:.0f}%), SL: ₹{self.stop_losses[ticker]:.2f}')

            elif order.issell():
                self.log(f'SELL {ticker} @ ₹{order.executed.price:.2f}, Size: {order.executed.size}')

                # Calculate P&L
                if ticker in self.entry_prices:
                    pnl_pct = ((order.executed.price - self.entry_prices[ticker]) / self.entry_prices[ticker]) * 100
                    self.log(f'  P&L: {pnl_pct:+.2f}%')

                    # Clear tracking
                    del self.entry_prices[ticker]
                    if ticker in self.target_prices:
                        del self.target_prices[ticker]
                    if ticker in self.stop_losses:
                        del self.stop_losses[ticker]

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f'{ticker} Order Canceled/Margin/Rejected')

        # Clear order reference
        if ticker in self.orders:
            del self.orders[ticker]

    def next(self):
        """Main strategy logic"""

        for i, d in enumerate(self.datas):
            ticker = d._name

            # Skip if we have pending order for this stock
            if ticker in self.orders:
                continue

            # Get position
            position = self.getposition(d)

            # === ENTRY LOGIC ===
            if not position:
                # Check fundamental screening
                if not self.fundamental_passed.get(ticker, False):
                    continue

                # Check if we can add more positions (exposure check)
                current_exposure = self.get_current_exposure()
                if current_exposure >= self.params.max_total_exposure:
                    continue

                # Technical Entry Signals
                # 1. Golden Cross
                if self.crossover[d] > 0:
                    # 2. RSI not overbought
                    if self.rsi[d][0] < self.params.rsi_overbought:
                        # 3. Price above short SMA (confirmation)
                        if d.close[0] > self.sma_short[d][0]:
                            # Calculate position size (5% of portfolio)
                            portfolio_value = self.broker.getvalue()
                            position_value = portfolio_value * self.params.max_position_pct
                            size = int(position_value / d.close[0])

                            if size > 0:
                                self.log(f'ENTRY SIGNAL: {ticker} - Golden Cross + RSI {self.rsi[d][0]:.1f}')
                                self.orders[ticker] = self.buy(data=d, size=size)

            # === EXIT LOGIC ===
            else:
                current_price = d.close[0]

                # Exit 1: Target reached
                if ticker in self.target_prices and current_price >= self.target_prices[ticker]:
                    self.log(f'EXIT: {ticker} - Target Reached @ ₹{current_price:.2f}')
                    self.orders[ticker] = self.sell(data=d, size=position.size)

                # Exit 2: Stop loss hit
                elif ticker in self.stop_losses and current_price <= self.stop_losses[ticker]:
                    self.log(f'EXIT: {ticker} - Stop Loss @ ₹{current_price:.2f}')
                    self.orders[ticker] = self.sell(data=d, size=position.size)

                # Exit 3: Death Cross
                elif self.crossover[d] < 0:
                    self.log(f'EXIT: {ticker} - Death Cross @ ₹{current_price:.2f}')
                    self.orders[ticker] = self.sell(data=d, size=position.size)

                # Exit 4: RSI Overbought
                elif self.rsi[d][0] > self.params.rsi_overbought:
                    self.log(f'EXIT: {ticker} - RSI Overbought ({self.rsi[d][0]:.1f}) @ ₹{current_price:.2f}')
                    self.orders[ticker] = self.sell(data=d, size=position.size)

    def stop(self):
        """Called when backtest ends"""
        self.log(f'='*80)
        self.log(f'Final Portfolio Value: ₹{self.broker.getvalue():,.2f}')
        self.log(f'='*80)


class V40PortfolioStrategyRelaxed(V40PortfolioStrategy):
    """
    Relaxed version of V40 strategy for testing
    Uses only technical signals without strict fundamental screening
    """

    def passes_fundamental_screening(self, ticker):
        """Always pass - use only technical signals"""
        self.log(f'{ticker} Auto-Passed (Relaxed Mode - V40 membership only)')
        return True
