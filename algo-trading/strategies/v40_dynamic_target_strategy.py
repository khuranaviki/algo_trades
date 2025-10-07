#!/usr/bin/env python3
"""
V40 Dynamic Target Strategy

Key Changes:
1. NO STOP LOSS - Hold through volatility
2. Exit at PATTERN-SPECIFIC TARGETS:
   - Golden Cross: Target = Entry + (Entry - SMA50) * 2 [Minimum 15%]
   - RHS Pattern: Target = Neckline + Pattern Depth
   - CWH Pattern: Target = Breakout + Cup Depth
3. Use ONLY stocks from Excel file (81 stocks)
4. 5% max position size
"""

import backtrader as bt
import numpy as np
from scipy.signal import find_peaks
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from load_v40_from_excel import is_v40_stock, is_v40_next_stock


class V40DynamicTargetStrategy(bt.Strategy):
    """
    V40 Strategy - Dynamic Pattern-Based Targets (NO Stop Loss)

    Entry Signals:
    1. Golden Cross (SMA 20 > 50) + RSI < 70
    2. RHS Pattern Breakout
    3. CWH Pattern Breakout

    Exit: ONLY at pattern-specific target
    No stop loss - hold through downturns
    """

    params = (
        # Position sizing
        ('max_position_pct', 0.05),      # Max 5% per stock
        ('max_total_exposure', 0.95),    # Max 95% total exposure

        # Technical indicators
        ('sma_short', 20),
        ('sma_long', 50),
        ('rsi_period', 14),
        ('rsi_overbought', 70),

        # Pattern detection
        ('lookback_period', 150),
        ('volume_threshold', 1.3),       # 1.3x average volume

        # Minimum targets (safety net)
        ('min_golden_cross_target', 0.15),  # 15% minimum for golden cross

        # Trade tracking
        ('print_log', True),
        ('track_trades', True),
    )

    def __init__(self):
        # Track positions
        self.entry_prices = {}
        self.target_prices = {}
        self.orders = {}
        self.entry_reasons = {}
        self.entry_details = {}  # Store pattern details
        self.trade_log = []

        # Technical indicators for each data feed
        self.sma_short = {}
        self.sma_long = {}
        self.rsi = {}
        self.crossover = {}

        for d in self.datas:
            self.sma_short[d] = bt.indicators.SMA(d.close, period=self.params.sma_short)
            self.sma_long[d] = bt.indicators.SMA(d.close, period=self.params.sma_long)
            self.rsi[d] = bt.indicators.RSI(d.close, period=self.params.rsi_period)
            self.crossover[d] = bt.indicators.CrossOver(self.sma_short[d], self.sma_long[d])

    def log(self, txt, dt=None):
        """Logging function"""
        if self.params.print_log:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()} {txt}')

    def log_trade(self, date, ticker, action, price, size, reason, pnl_pct=None, target_pct=None):
        """Log trade for history"""
        if self.params.track_trades:
            self.trade_log.append({
                'date': date,
                'ticker': ticker,
                'action': action,
                'price': price,
                'size': size,
                'reason': reason,
                'pnl_pct': pnl_pct,
                'target_pct': target_pct
            })

    def calculate_golden_cross_target(self, d, entry_price):
        """
        Calculate target for Golden Cross entry
        Logic: Target = Entry + (Entry - SMA50) * 2
        Rationale: Price is above SMA50, target is 2x the distance upward
        """
        sma50_value = self.sma_long[d][0]
        distance_from_sma = entry_price - sma50_value

        # Target is entry + 2x distance from SMA50
        target_distance = distance_from_sma * 2
        calculated_target = entry_price + target_distance

        # Ensure minimum 15% target
        min_target = entry_price * (1 + self.params.min_golden_cross_target)
        target = max(calculated_target, min_target)

        target_pct = ((target - entry_price) / entry_price) * 100

        return target, target_pct, f"GC (SMA50 dist: {distance_from_sma:.2f})"

    def detect_rhs_pattern(self, d):
        """
        Detect Reverse Head & Shoulder pattern
        Returns: (is_pattern, target_price, target_pct, details)
        """
        lookback = min(self.params.lookback_period, len(d.close))
        if lookback < 60:
            return False, None, None, None

        # Get recent data
        closes = np.array([d.close[-i] for i in range(lookback, 0, -1)])
        volumes = np.array([d.volume[-i] for i in range(lookback, 0, -1)])

        # Find troughs (inverted peaks for lows)
        troughs, _ = find_peaks(-closes, distance=10, prominence=closes.std() * 0.3)

        if len(troughs) < 3:
            return False, None, None, None

        # Get last 3 troughs
        last_troughs = troughs[-3:]
        left_shoulder_idx = last_troughs[0]
        head_idx = last_troughs[1]
        right_shoulder_idx = last_troughs[2]

        left_shoulder = closes[left_shoulder_idx]
        head = closes[head_idx]
        right_shoulder = closes[right_shoulder_idx]

        # Validate RHS: Head < Both Shoulders
        if not (head < left_shoulder * 0.95 and head < right_shoulder * 0.95):
            return False, None, None, None

        # Shoulders should be roughly equal (within 5%)
        if abs(left_shoulder - right_shoulder) / left_shoulder > 0.10:
            return False, None, None, None

        # Calculate neckline (resistance level connecting shoulder peaks)
        # Find peaks after each trough to get neckline points
        neckline_candidates = []
        for trough_idx in last_troughs:
            # Look for peak after this trough
            search_start = trough_idx + 1
            search_end = min(trough_idx + 20, len(closes))
            if search_start < search_end:
                local_highs = closes[search_start:search_end]
                if len(local_highs) > 0:
                    neckline_candidates.append(local_highs.max())

        if len(neckline_candidates) < 2:
            return False, None, None, None

        neckline = np.mean(neckline_candidates)
        current_price = d.close[0]

        # Check if price is breaking above neckline
        if current_price < neckline * 0.98:
            return False, None, None, None

        # Check volume surge
        avg_volume = volumes[-20:].mean()
        current_volume = d.volume[0]
        if current_volume < avg_volume * self.params.volume_threshold:
            return False, None, None, None

        # Calculate target: Neckline + Pattern Depth
        pattern_depth = neckline - head
        target_price = neckline + pattern_depth
        target_pct = ((target_price - current_price) / current_price) * 100

        details = f"RHS (Neckline: {neckline:.2f}, Depth: {pattern_depth:.2f})"

        return True, target_price, target_pct, details

    def detect_cwh_pattern(self, d):
        """
        Detect Cup with Handle pattern
        Returns: (is_pattern, target_price, target_pct, details)
        """
        lookback = min(self.params.lookback_period, len(d.close))
        if lookback < 60:
            return False, None, None, None

        closes = np.array([d.close[-i] for i in range(lookback, 0, -1)])
        volumes = np.array([d.volume[-i] for i in range(lookback, 0, -1)])

        # Find cup: U-shaped pattern
        mid_point = len(closes) // 2
        first_half_max = closes[:mid_point].max()
        second_half_max = closes[mid_point:].max()
        cup_bottom = closes[mid_point-10:mid_point+10].min()

        # Cup should be deep enough (>10%)
        cup_depth = first_half_max - cup_bottom
        if cup_depth / first_half_max < 0.10:
            return False, None, None, None

        # Both sides should reach similar heights
        if abs(first_half_max - second_half_max) / first_half_max > 0.05:
            return False, None, None, None

        # Handle: Recent pullback (last 20 days)
        recent_high = closes[-30:-10].max()
        handle_low = closes[-10:].min()
        handle_depth = recent_high - handle_low

        # Handle should be shallow (< 15% of cup depth)
        if handle_depth > cup_depth * 0.15:
            return False, None, None, None

        current_price = d.close[0]
        breakout_level = second_half_max

        # Check if breaking out above cup rim
        if current_price < breakout_level * 0.98:
            return False, None, None, None

        # Volume confirmation
        avg_volume = volumes[-20:].mean()
        current_volume = d.volume[0]
        if current_volume < avg_volume * self.params.volume_threshold:
            return False, None, None, None

        # Target: Breakout + Cup Depth
        target_price = breakout_level + cup_depth
        target_pct = ((target_price - current_price) / current_price) * 100

        details = f"CWH (Breakout: {breakout_level:.2f}, Cup Depth: {cup_depth:.2f})"

        return True, target_price, target_pct, details

    def notify_order(self, order):
        """Order notification"""
        if order.status in [order.Submitted, order.Accepted]:
            return

        ticker = order.data._name
        dt = self.datas[0].datetime.date(0)

        if order.status in [order.Completed]:
            if order.isbuy():
                reason = self.entry_reasons.get(ticker, 'Unknown')
                details = self.entry_details.get(ticker, '')
                stock_type = "V40" if is_v40_stock(ticker) else "V40 Next"

                self.entry_prices[ticker] = order.executed.price
                target_price = self.target_prices.get(ticker, 0)
                target_pct = ((target_price - order.executed.price) / order.executed.price) * 100

                self.log(f'BUY {ticker} ({stock_type}) @ ₹{order.executed.price:.2f} | Size: {order.executed.size}')
                self.log(f'  → Target: ₹{target_price:.2f} ({target_pct:.1f}%) | {details} | NO STOP LOSS')

                # Log trade
                self.log_trade(dt, ticker, 'BUY', order.executed.price, order.executed.size, reason, target_pct=target_pct)

            elif order.issell():
                pnl_pct = None
                target_pct = None
                if ticker in self.entry_prices:
                    pnl_pct = ((order.executed.price - self.entry_prices[ticker]) / self.entry_prices[ticker]) * 100
                    target_pct = ((self.target_prices.get(ticker, 0) - self.entry_prices[ticker]) / self.entry_prices[ticker]) * 100
                    self.log(f'SELL {ticker} @ ₹{order.executed.price:.2f} | P&L: {pnl_pct:+.2f}% | Target: {target_pct:.1f}%')

                    # Log trade
                    reason = self.entry_reasons.get(ticker, 'Target Reached')
                    self.log_trade(dt, ticker, 'SELL', order.executed.price, order.executed.size, reason, pnl_pct, target_pct)

                    # Clear tracking
                    del self.entry_prices[ticker]
                    if ticker in self.target_prices:
                        del self.target_prices[ticker]
                    if ticker in self.entry_reasons:
                        del self.entry_reasons[ticker]
                    if ticker in self.entry_details:
                        del self.entry_details[ticker]

        if ticker in self.orders:
            del self.orders[ticker]

    def next(self):
        """Main strategy logic"""
        for d in self.datas:
            ticker = d._name

            if ticker in self.orders:
                continue

            position = self.getposition(d)

            # === ENTRY LOGIC ===
            if not position:
                entry_signal = False
                target_price = None
                target_pct = None
                reason = None
                details = None

                # 1. Check RHS Pattern
                is_rhs, rhs_target, rhs_target_pct, rhs_details = self.detect_rhs_pattern(d)
                if is_rhs:
                    entry_signal = True
                    target_price = rhs_target
                    target_pct = rhs_target_pct
                    reason = "RHS Breakout"
                    details = rhs_details

                # 2. Check CWH Pattern
                if not entry_signal:
                    is_cwh, cwh_target, cwh_target_pct, cwh_details = self.detect_cwh_pattern(d)
                    if is_cwh:
                        entry_signal = True
                        target_price = cwh_target
                        target_pct = cwh_target_pct
                        reason = "CWH Breakout"
                        details = cwh_details

                # 3. Check Golden Cross
                if not entry_signal:
                    if self.crossover[d] > 0:
                        if self.rsi[d][0] < self.params.rsi_overbought:
                            if d.close[0] > self.sma_short[d][0]:
                                entry_signal = True
                                target_price, calc_target_pct, gc_details = self.calculate_golden_cross_target(d, d.close[0])
                                target_pct = calc_target_pct
                                reason = "Golden Cross"
                                details = gc_details

                # Execute entry
                if entry_signal and target_price and target_pct > 5:  # Minimum 5% target
                    # Calculate position size (5% of portfolio)
                    portfolio_value = self.broker.getvalue()
                    position_value = portfolio_value * self.params.max_position_pct
                    size = int(position_value / d.close[0])

                    if size > 0:
                        self.log(f'ENTRY SIGNAL: {ticker} - {reason} | Target: {target_pct:.1f}%')
                        self.entry_reasons[ticker] = reason
                        self.entry_details[ticker] = details
                        self.target_prices[ticker] = target_price
                        self.orders[ticker] = self.buy(data=d, size=size)

            # === EXIT LOGIC ===
            else:
                current_price = d.close[0]

                # ONLY EXIT: Target reached
                if ticker in self.target_prices and current_price >= self.target_prices[ticker]:
                    target_pct = ((self.target_prices[ticker] - self.entry_prices[ticker]) / self.entry_prices[ticker]) * 100
                    self.log(f'EXIT: {ticker} - TARGET REACHED ({target_pct:.1f}%) @ ₹{current_price:.2f}')
                    self.entry_reasons[ticker] = f"Target Reached ({self.entry_reasons.get(ticker, 'Unknown')})"
                    self.orders[ticker] = self.sell(data=d, size=position.size)

                # NO STOP LOSS - Hold through downturns

    def stop(self):
        """Called when backtest ends"""
        self.log(f'='*80)
        self.log(f'Final Portfolio Value: ₹{self.broker.getvalue():,.2f}')
        self.log(f'Total Trades Logged: {len(self.trade_log)//2}')  # Divide by 2 (buy + sell)
        self.log(f'='*80)

    def get_trade_history(self):
        """Return trade history"""
        return self.trade_log
