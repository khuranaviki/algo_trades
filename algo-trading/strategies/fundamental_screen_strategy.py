#!/usr/bin/env python3
"""
Fundamental Screening Strategy for Backtrader
Based on the analysis strategy documentation
Combines fundamental filters with technical entries
"""

import backtrader as bt
import pandas as pd
from typing import Dict, Optional


class FundamentalScreenStrategy(bt.Strategy):
    """
    Fundamental Screening + Technical Entry Strategy

    Screening Criteria:
    - Revenue Growth > 20% YoY
    - ROCE > 20%
    - ROE > 15%
    - Debt-to-Equity < 1.0
    - Market Cap < 50,000 Cr (multibagger potential)

    Entry: SMA crossover with RSI confirmation
    Exit: Target (20% gain) or Stop Loss (10% loss)
    """

    params = (
        # Fundamental filters
        ('min_revenue_growth', 20.0),    # Minimum 20% revenue growth
        ('min_roce', 20.0),              # Minimum 20% ROCE
        ('min_roe', 15.0),               # Minimum 15% ROE
        ('max_debt_equity', 1.0),        # Maximum 1.0 D/E ratio
        ('max_market_cap', 50000),       # Max market cap in Cr for multibagger

        # Technical entry signals
        ('sma_short', 20),
        ('sma_long', 50),
        ('rsi_period', 14),
        ('rsi_oversold', 40),            # Relaxed from 30 for quality stocks
        ('rsi_overbought', 70),

        # Risk management
        ('target_pct', 0.20),            # 20% target
        ('stop_loss_pct', 0.10),         # 10% stop loss
        ('position_size_pct', 0.03),     # 3% of portfolio per trade
        ('max_positions', 5),            # Maximum concurrent positions

        # Fundamental data (passed from outside)
        ('fundamental_data', None),

        ('print_log', True),
    )

    def __init__(self):
        # Keep track of pending orders and trades
        self.order = None
        self.entry_prices = {}
        self.target_prices = {}
        self.stop_losses = {}

        # Data references
        self.dataclose = self.datas[0].close

        # Technical Indicators
        self.sma_short = bt.indicators.SimpleMovingAverage(
            self.dataclose, period=self.params.sma_short
        )
        self.sma_long = bt.indicators.SimpleMovingAverage(
            self.dataclose, period=self.params.sma_long
        )
        self.rsi = bt.indicators.RSI(
            self.dataclose, period=self.params.rsi_period
        )

        # Crossover signal
        self.crossover = bt.indicators.CrossOver(self.sma_short, self.sma_long)

        # Track if stock passes fundamental screen
        self.fundamental_pass = self.screen_fundamentals()

    def log(self, txt, dt=None):
        """Logging function"""
        if self.params.print_log:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()} {txt}')

    def screen_fundamentals(self) -> bool:
        """
        Screen stock based on fundamental criteria
        Returns True if stock passes all filters
        """
        if not self.params.fundamental_data:
            self.log('WARNING: No fundamental data provided, skipping fundamental screening')
            return True  # Default to True if no data

        fd = self.params.fundamental_data

        # Extract metrics (handle None values)
        try:
            revenue_growth = float(fd.get('revenue_growth_yoy', 0) or 0)
            roce = float(fd.get('roce', 0) or 0)
            roe = float(fd.get('roe', 0) or 0)
            debt_equity = float(fd.get('debt_to_equity', 999) or 999)
            market_cap = float(fd.get('market_cap', 999999) or 999999)

            # Apply filters
            filters = {
                'Revenue Growth': revenue_growth >= self.params.min_revenue_growth,
                'ROCE': roce >= self.params.min_roce,
                'ROE': roe >= self.params.min_roe,
                'Debt/Equity': debt_equity <= self.params.max_debt_equity,
                'Market Cap': market_cap <= self.params.max_market_cap,
            }

            passed = all(filters.values())

            if passed:
                self.log(f'FUNDAMENTAL SCREEN PASSED')
                self.log(f'  Revenue Growth: {revenue_growth:.1f}%')
                self.log(f'  ROCE: {roce:.1f}%, ROE: {roe:.1f}%')
                self.log(f'  D/E: {debt_equity:.2f}, Market Cap: {market_cap:.0f} Cr')
            else:
                failed_filters = [k for k, v in filters.items() if not v]
                self.log(f'FUNDAMENTAL SCREEN FAILED: {", ".join(failed_filters)}')

            return passed

        except Exception as e:
            self.log(f'Error in fundamental screening: {e}')
            return False

    def notify_order(self, order):
        """Notification of order status"""
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED, Price: {order.executed.price:.2f}, Size: {order.executed.size}')

                # Set entry price and targets
                ticker = order.data._name
                self.entry_prices[ticker] = order.executed.price
                self.target_prices[ticker] = order.executed.price * (1 + self.params.target_pct)
                self.stop_losses[ticker] = order.executed.price * (1 - self.params.stop_loss_pct)

                self.log(f'  Target: {self.target_prices[ticker]:.2f}, Stop Loss: {self.stop_losses[ticker]:.2f}')

            elif order.issell():
                self.log(f'SELL EXECUTED, Price: {order.executed.price:.2f}, Size: {order.executed.size}')

                # Clear tracking for this ticker
                ticker = order.data._name
                if ticker in self.entry_prices:
                    pnl_pct = ((order.executed.price - self.entry_prices[ticker]) / self.entry_prices[ticker]) * 100
                    self.log(f'  P&L: {pnl_pct:.2f}%')

                    del self.entry_prices[ticker]
                    del self.target_prices[ticker]
                    del self.stop_losses[ticker]

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

    def notify_trade(self, trade):
        """Notification of trade status"""
        if not trade.isclosed:
            return

        self.log(f'TRADE CLOSED - P&L: Gross {trade.pnl:.2f}, Net {trade.pnlcomm:.2f}')

    def get_num_positions(self):
        """Get number of current open positions"""
        return sum(1 for d in self.datas if self.getposition(d).size > 0)

    def next(self):
        """Main strategy logic called for each bar"""

        # Skip if stock didn't pass fundamental screen
        if not self.fundamental_pass:
            return

        # Check if we have an order pending
        if self.order:
            return

        # Check if we already have maximum positions
        num_positions = self.get_num_positions()

        # Check if we are already in a position for this data feed
        if not self.position:
            # Only enter if we have room for more positions
            if num_positions >= self.params.max_positions:
                return

            # Entry Signal 1: Golden Cross (SMA short crosses above SMA long)
            if self.crossover > 0:
                # Entry Signal 2: RSI confirmation (not overbought, preferably oversold-to-neutral)
                if self.rsi[0] < self.params.rsi_overbought:
                    # Entry Signal 3: Price above SMA short (uptrend confirmation)
                    if self.dataclose[0] > self.sma_short[0]:
                        # Calculate position size
                        cash = self.broker.getcash()
                        position_value = cash * self.params.position_size_pct
                        size = int(position_value / self.dataclose[0])

                        if size > 0:
                            self.log(f'BUY SIGNAL - Golden Cross + RSI {self.rsi[0]:.1f}')
                            self.order = self.buy(size=size)

        else:
            # We are in a position - check exit conditions
            current_price = self.dataclose[0]
            ticker = self.data._name

            # Exit 1: Target reached
            if ticker in self.target_prices and current_price >= self.target_prices[ticker]:
                self.log(f'TARGET REACHED - SELL SIGNAL at {current_price:.2f}')
                self.order = self.sell(size=self.position.size)

            # Exit 2: Stop loss hit
            elif ticker in self.stop_losses and current_price <= self.stop_losses[ticker]:
                self.log(f'STOP LOSS HIT - SELL SIGNAL at {current_price:.2f}')
                self.order = self.sell(size=self.position.size)

            # Exit 3: Death Cross (SMA short crosses below SMA long)
            elif self.crossover < 0:
                self.log(f'DEATH CROSS - SELL SIGNAL at {current_price:.2f}')
                self.order = self.sell(size=self.position.size)

            # Exit 4: RSI overbought
            elif self.rsi[0] > self.params.rsi_overbought:
                self.log(f'RSI OVERBOUGHT ({self.rsi[0]:.1f}) - SELL SIGNAL at {current_price:.2f}')
                self.order = self.sell(size=self.position.size)

    def stop(self):
        """Called when backtest ends"""
        self.log(f'Final Portfolio Value: {self.broker.getvalue():.2f}', dt=self.datas[0].datetime.date(0))


class MultibaggerScreenStrategy(FundamentalScreenStrategy):
    """
    Aggressive Multibagger Screening Strategy
    Targets small-cap, high-growth stocks with excellent fundamentals
    """

    params = (
        # More aggressive fundamental filters for multibaggers
        ('min_revenue_growth', 25.0),    # 25% revenue growth
        ('min_roce', 25.0),              # 25% ROCE
        ('min_roe', 20.0),               # 20% ROE
        ('max_debt_equity', 0.5),        # Low debt
        ('max_market_cap', 10000),       # Small cap <10,000 Cr

        # Technical entry signals
        ('sma_short', 20),
        ('sma_long', 50),
        ('rsi_period', 14),
        ('rsi_oversold', 35),
        ('rsi_overbought', 75),

        # More aggressive risk management
        ('target_pct', 0.30),            # 30% target
        ('stop_loss_pct', 0.12),         # 12% stop loss
        ('position_size_pct', 0.05),     # 5% of portfolio per trade
        ('max_positions', 3),            # Max 3 positions (concentrated)

        # Fundamental data
        ('fundamental_data', None),

        ('print_log', True),
    )
