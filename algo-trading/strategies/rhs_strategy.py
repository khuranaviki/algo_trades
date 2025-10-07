#!/usr/bin/env python3
"""
Reverse Head & Shoulder (RHS) Pattern Strategy for Backtrader
Based on the analysis strategy documentation
"""

import backtrader as bt
import numpy as np
from scipy.signal import find_peaks


class RHSPatternStrategy(bt.Strategy):
    """
    Reverse Head and Shoulder Pattern Trading Strategy

    Entry: Neckline breakout with volume confirmation
    Exit: Technical target (Neckline + Pattern Depth) or Stop Loss
    Stop Loss: Below right shoulder low
    """

    params = (
        ('min_pattern_days', 100),      # Minimum data points for pattern detection
        ('lookback_period', 200),        # Days to analyze for pattern
        ('volume_threshold', 1.5),       # Volume spike multiplier for breakout
        ('pattern_symmetry_tolerance', 0.15),  # 15% tolerance for shoulder symmetry
        ('min_depth_ratio', 0.10),       # Minimum 10% depth from neckline to head
        ('max_depth_ratio', 0.35),       # Maximum 35% depth
        ('risk_reward_ratio', 2.0),      # Minimum risk:reward ratio
        ('stop_loss_pct', 0.08),         # 8% stop loss below entry
        ('position_size_pct', 0.04),     # 4% of portfolio per trade
        ('print_log', True),
    )

    def __init__(self):
        # Keep track of pending orders and trades
        self.order = None
        self.entry_price = None
        self.target_price = None
        self.stop_loss = None
        self.pattern_identified = False

        # Data references
        self.dataclose = self.datas[0].close
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low
        self.datavolume = self.datas[0].volume

        # Indicators
        self.sma20 = bt.indicators.SimpleMovingAverage(self.dataclose, period=20)
        self.sma50 = bt.indicators.SimpleMovingAverage(self.dataclose, period=50)

    def log(self, txt, dt=None):
        """Logging function"""
        if self.params.print_log:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()} {txt}')

    def notify_order(self, order):
        """Notification of order status"""
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED, Price: {order.executed.price:.2f}')
                self.entry_price = order.executed.price
            elif order.issell():
                self.log(f'SELL EXECUTED, Price: {order.executed.price:.2f}')
                self.entry_price = None

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

    def notify_trade(self, trade):
        """Notification of trade status"""
        if not trade.isclosed:
            return

        self.log(f'TRADE P&L: Gross {trade.pnl:.2f}, Net {trade.pnlcomm:.2f}')

    def find_local_minima(self, data, window=10):
        """Find local minima (troughs) in price data"""
        if len(data) < window * 2:
            return []

        prices = np.array(data)
        peaks, _ = find_peaks(-prices, distance=window)

        return peaks

    def identify_rhs_pattern(self):
        """
        Identify Reverse Head and Shoulder pattern
        Returns: dict with pattern info or None
        """
        # Need sufficient data
        if len(self.dataclose) < self.params.min_pattern_days:
            return None

        # Get recent data
        lookback = min(len(self.dataclose), self.params.lookback_period)
        recent_lows = [self.datalow[-i] for i in range(lookback, 0, -1)]
        recent_highs = [self.datahigh[-i] for i in range(lookback, 0, -1)]
        recent_closes = [self.dataclose[-i] for i in range(lookback, 0, -1)]

        # Find troughs (local minima)
        troughs_idx = self.find_local_minima(recent_lows, window=10)

        if len(troughs_idx) < 3:
            return None

        # Check last 3 troughs for RHS pattern
        # RHS: Left Shoulder > Head (deepest) < Right Shoulder
        for i in range(len(troughs_idx) - 2):
            ls_idx = troughs_idx[i]      # Left shoulder
            head_idx = troughs_idx[i+1]  # Head
            rs_idx = troughs_idx[i+2]    # Right shoulder

            ls_low = recent_lows[ls_idx]
            head_low = recent_lows[head_idx]
            rs_low = recent_lows[rs_idx]

            # Validation 1: Head should be lowest
            if not (head_low < ls_low and head_low < rs_low):
                continue

            # Validation 2: Right shoulder should be higher than left (bullish)
            if rs_low <= ls_low * (1 - self.params.pattern_symmetry_tolerance):
                continue

            # Calculate neckline (line connecting peaks between shoulders)
            # Find peaks between left shoulder and head, head and right shoulder
            ls_to_head_highs = recent_highs[ls_idx:head_idx+1]
            head_to_rs_highs = recent_highs[head_idx:rs_idx+1]

            if not ls_to_head_highs or not head_to_rs_highs:
                continue

            peak1 = max(ls_to_head_highs)
            peak2 = max(head_to_rs_highs)
            neckline = (peak1 + peak2) / 2  # Simplified neckline

            # Validation 3: Check pattern depth
            pattern_depth = neckline - head_low
            depth_ratio = pattern_depth / neckline

            if depth_ratio < self.params.min_depth_ratio or depth_ratio > self.params.max_depth_ratio:
                continue

            # Validation 4: Check if current price is near/above neckline (breakout)
            current_price = self.dataclose[0]
            if current_price < neckline * 0.98:  # Need to be within 2% of neckline
                continue

            # Calculate targets
            technical_target = neckline + pattern_depth
            stop_loss = rs_low * 0.95  # Below right shoulder

            # Validation 5: Risk-reward check
            risk = current_price - stop_loss
            reward = technical_target - current_price

            if risk <= 0 or reward / risk < self.params.risk_reward_ratio:
                continue

            # Pattern found!
            return {
                'pattern_type': 'RHS',
                'left_shoulder_idx': ls_idx,
                'head_idx': head_idx,
                'right_shoulder_idx': rs_idx,
                'neckline': neckline,
                'pattern_depth': pattern_depth,
                'technical_target': technical_target,
                'stop_loss': stop_loss,
                'entry_price': current_price,
                'risk_reward': reward / risk
            }

        return None

    def check_volume_confirmation(self):
        """Check if volume confirms the breakout"""
        if len(self.datavolume) < 20:
            return False

        avg_volume = sum([self.datavolume[-i] for i in range(1, 21)]) / 20
        current_volume = self.datavolume[0]

        return current_volume > avg_volume * self.params.volume_threshold

    def next(self):
        """Main strategy logic called for each bar"""

        # Check if we have an order pending
        if self.order:
            return

        # Check if we are already in a position
        if not self.position:
            # Look for entry signal
            pattern = self.identify_rhs_pattern()

            if pattern:
                # Check volume confirmation
                if self.check_volume_confirmation():
                    # Calculate position size
                    cash = self.broker.getcash()
                    position_value = cash * self.params.position_size_pct
                    size = int(position_value / self.dataclose[0])

                    if size > 0:
                        self.log(f'RHS PATTERN DETECTED - BUY SIGNAL')
                        self.log(f'Entry: {self.dataclose[0]:.2f}, Target: {pattern["technical_target"]:.2f}, SL: {pattern["stop_loss"]:.2f}')
                        self.log(f'Risk:Reward = 1:{pattern["risk_reward"]:.2f}')

                        # Enter long position
                        self.order = self.buy(size=size)
                        self.target_price = pattern['technical_target']
                        self.stop_loss = pattern['stop_loss']
                        self.pattern_identified = True

        else:
            # We are in a position - check exit conditions
            current_price = self.dataclose[0]

            # Exit 1: Target reached
            if self.target_price and current_price >= self.target_price:
                self.log(f'TARGET REACHED - SELL SIGNAL at {current_price:.2f}')
                self.order = self.sell(size=self.position.size)
                self.pattern_identified = False

            # Exit 2: Stop loss hit
            elif self.stop_loss and current_price <= self.stop_loss:
                self.log(f'STOP LOSS HIT - SELL SIGNAL at {current_price:.2f}')
                self.order = self.sell(size=self.position.size)
                self.pattern_identified = False

            # Exit 3: Trailing stop (optional) - price drops below SMA20
            elif current_price < self.sma20[0]:
                self.log(f'TRAILING STOP (SMA20) - SELL SIGNAL at {current_price:.2f}')
                self.order = self.sell(size=self.position.size)
                self.pattern_identified = False

    def stop(self):
        """Called when backtest ends"""
        self.log(f'Final Portfolio Value: {self.broker.getvalue():.2f}', dt=self.datas[0].datetime.date(0))
