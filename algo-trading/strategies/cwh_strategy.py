#!/usr/bin/env python3
"""
Cup with Handle (CWH) Pattern Strategy for Backtrader
Based on the analysis strategy documentation
"""

import backtrader as bt
import numpy as np
from scipy.signal import find_peaks


class CWHPatternStrategy(bt.Strategy):
    """
    Cup with Handle Pattern Trading Strategy

    Entry: Handle breakout with volume confirmation
    Exit: Technical target (Breakout + Cup Depth) or Stop Loss
    Stop Loss: Below handle low
    """

    params = (
        ('min_pattern_days', 100),       # Minimum data points for pattern detection
        ('lookback_period', 200),         # Days to analyze for pattern
        ('volume_threshold', 1.5),        # Volume spike multiplier for breakout
        ('min_cup_depth_pct', 0.12),      # Minimum 12% cup depth
        ('max_cup_depth_pct', 0.33),      # Maximum 33% cup depth
        ('max_handle_depth_ratio', 0.15), # Handle depth max 15% of cup depth
        ('min_handle_duration', 5),       # Minimum handle duration in days
        ('max_handle_duration_ratio', 0.30),  # Max 30% of cup duration
        ('risk_reward_ratio', 2.0),       # Minimum risk:reward ratio
        ('position_size_pct', 0.04),      # 4% of portfolio per trade
        ('print_log', True),
    )

    def __init__(self):
        # Keep track of pending orders and trades
        self.order = None
        self.entry_price = None
        self.target_price = None
        self.stop_loss = None

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

    def find_local_extrema(self, data, mode='min', window=10):
        """Find local minima or maxima in price data"""
        if len(data) < window * 2:
            return []

        prices = np.array(data)

        if mode == 'min':
            peaks, _ = find_peaks(-prices, distance=window)
        else:  # mode == 'max'
            peaks, _ = find_peaks(prices, distance=window)

        return peaks

    def identify_cwh_pattern(self):
        """
        Identify Cup with Handle pattern
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

        # Find troughs (local minima) and peaks (local maxima)
        troughs_idx = self.find_local_extrema(recent_lows, mode='min', window=15)
        peaks_idx = self.find_local_extrema(recent_highs, mode='max', window=15)

        if len(troughs_idx) < 2 or len(peaks_idx) < 2:
            return None

        # Look for cup formation: high -> low (cup bottom) -> high
        for i in range(len(peaks_idx) - 1):
            for j in range(len(troughs_idx)):
                if troughs_idx[j] <= peaks_idx[i]:
                    continue

                # Cup pattern: peak1 -> trough -> peak2
                peak1_idx = peaks_idx[i]
                cup_trough_idx = troughs_idx[j]

                # Find next peak after cup trough
                next_peaks = [p for p in peaks_idx if p > cup_trough_idx]
                if not next_peaks:
                    continue

                peak2_idx = next_peaks[0]

                # Get values
                peak1_high = recent_highs[peak1_idx]
                cup_low = recent_lows[cup_trough_idx]
                peak2_high = recent_highs[peak2_idx]

                # Validation 1: Cup depth
                cup_depth = peak1_high - cup_low
                cup_depth_pct = cup_depth / peak1_high

                if cup_depth_pct < self.params.min_cup_depth_pct or cup_depth_pct > self.params.max_cup_depth_pct:
                    continue

                # Validation 2: Both peaks should be similar (U-shape)
                if abs(peak2_high - peak1_high) / peak1_high > 0.05:  # 5% tolerance
                    continue

                # Validation 3: Look for handle after peak2
                handle_start_idx = peak2_idx
                handle_data = recent_lows[handle_start_idx:]

                if len(handle_data) < self.params.min_handle_duration:
                    continue

                # Find handle trough (should be shallow pullback)
                handle_low_idx = handle_start_idx + np.argmin(handle_data[:min(len(handle_data), 30)])
                handle_low = recent_lows[handle_low_idx]

                # Handle depth validation
                handle_depth = peak2_high - handle_low
                if handle_depth > cup_depth * self.params.max_handle_depth_ratio:
                    continue  # Handle too deep

                # Handle duration validation
                cup_duration = peak2_idx - peak1_idx
                handle_duration = handle_low_idx - handle_start_idx

                if handle_duration < self.params.min_handle_duration:
                    continue

                if handle_duration > cup_duration * self.params.max_handle_duration_ratio:
                    continue  # Handle too long

                # Check if current price is breaking above handle high (breakout)
                handle_high = peak2_high
                current_price = self.dataclose[0]

                if current_price < handle_high * 0.98:  # Need to be within 2% of breakout
                    continue

                # Calculate targets
                technical_target = current_price + cup_depth
                stop_loss = handle_low * 0.97  # 3% below handle low

                # Validation 4: Risk-reward check
                risk = current_price - stop_loss
                reward = technical_target - current_price

                if risk <= 0 or reward / risk < self.params.risk_reward_ratio:
                    continue

                # Pattern found!
                return {
                    'pattern_type': 'CWH',
                    'cup_peak1_idx': peak1_idx,
                    'cup_trough_idx': cup_trough_idx,
                    'cup_peak2_idx': peak2_idx,
                    'handle_low_idx': handle_low_idx,
                    'cup_depth': cup_depth,
                    'handle_depth': handle_depth,
                    'technical_target': technical_target,
                    'stop_loss': stop_loss,
                    'entry_price': current_price,
                    'risk_reward': reward / risk,
                    'cup_duration': cup_duration,
                    'handle_duration': handle_duration
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
            pattern = self.identify_cwh_pattern()

            if pattern:
                # Check volume confirmation
                if self.check_volume_confirmation():
                    # Calculate position size
                    cash = self.broker.getcash()
                    position_value = cash * self.params.position_size_pct
                    size = int(position_value / self.dataclose[0])

                    if size > 0:
                        self.log(f'CWH PATTERN DETECTED - BUY SIGNAL')
                        self.log(f'Entry: {self.dataclose[0]:.2f}, Target: {pattern["technical_target"]:.2f}, SL: {pattern["stop_loss"]:.2f}')
                        self.log(f'Cup Depth: {pattern["cup_depth"]:.2f}, Handle Depth: {pattern["handle_depth"]:.2f}')
                        self.log(f'Risk:Reward = 1:{pattern["risk_reward"]:.2f}')

                        # Enter long position
                        self.order = self.buy(size=size)
                        self.target_price = pattern['technical_target']
                        self.stop_loss = pattern['stop_loss']

        else:
            # We are in a position - check exit conditions
            current_price = self.dataclose[0]

            # Exit 1: Target reached
            if self.target_price and current_price >= self.target_price:
                self.log(f'TARGET REACHED - SELL SIGNAL at {current_price:.2f}')
                self.order = self.sell(size=self.position.size)

            # Exit 2: Stop loss hit
            elif self.stop_loss and current_price <= self.stop_loss:
                self.log(f'STOP LOSS HIT - SELL SIGNAL at {current_price:.2f}')
                self.order = self.sell(size=self.position.size)

            # Exit 3: Trailing stop (optional) - price drops below SMA20
            elif current_price < self.sma20[0]:
                self.log(f'TRAILING STOP (SMA20) - SELL SIGNAL at {current_price:.2f}')
                self.order = self.sell(size=self.position.size)

    def stop(self):
        """Called when backtest ends"""
        self.log(f'Final Portfolio Value: {self.broker.getvalue():.2f}', dt=self.datas[0].datetime.date(0))
