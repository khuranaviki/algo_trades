#!/usr/bin/env python3
"""
Enhanced V40 Portfolio Strategy - Combined Multiple Strategies

Combines:
1. Simple MA Crossover (Golden/Death Cross)
2. RHS Pattern Detection (Reverse Head & Shoulder)
3. CWH Pattern Detection (Cup with Handle)
4. Fundamental Screening

Entry Signals (ANY of these):
- Golden Cross + RSI favorable
- RHS Pattern Breakout + Volume
- CWH Pattern Breakout + Volume

Exit Signals:
- Strategy Target (20% V40, 30% V40 Next)
- Stop Loss (10%)
- Death Cross
- Pattern failure

Position Sizing: Maximum 5% per stock
"""

import backtrader as bt
import numpy as np
from scipy.signal import find_peaks
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from v40_universe import is_v40_stock, is_v40_next_stock


class V40EnhancedStrategy(bt.Strategy):
    """
    Enhanced V40 Strategy combining multiple technical patterns
    """

    params = (
        # Position sizing
        ('max_position_pct', 0.05),      # Max 5% per stock
        ('max_total_exposure', 0.95),    # Max 95% total exposure

        # Technical indicators
        ('sma_short', 20),
        ('sma_long', 50),
        ('rsi_period', 14),
        ('rsi_oversold', 40),
        ('rsi_overbought', 70),

        # Pattern detection
        ('min_pattern_bars', 80),        # Reduced from 100 for more signals
        ('volume_threshold', 1.3),       # Volume spike multiplier (relaxed from 1.5)
        ('pattern_lookback', 150),       # Reduced from 200

        # Targets and stops
        ('v40_target_pct', 0.20),
        ('v40_next_target_pct', 0.30),
        ('stop_loss_pct', 0.10),

        # Trade tracking
        ('print_log', True),
        ('track_trades', True),
    )

    def __init__(self):
        # Track positions
        self.entry_prices = {}
        self.target_prices = {}
        self.stop_losses = {}
        self.orders = {}
        self.entry_reasons = {}
        self.trade_log = []

        # Technical indicators for each data feed
        self.sma_short = {}
        self.sma_long = {}
        self.rsi = {}
        self.crossover = {}
        self.volume_sma = {}

        for d in self.datas:
            self.sma_short[d] = bt.indicators.SMA(d.close, period=self.params.sma_short)
            self.sma_long[d] = bt.indicators.SMA(d.close, period=self.params.sma_long)
            self.rsi[d] = bt.indicators.RSI(d.close, period=self.params.rsi_period)
            self.crossover[d] = bt.indicators.CrossOver(self.sma_short[d], self.sma_long[d])
            self.volume_sma[d] = bt.indicators.SMA(d.volume, period=20)

    def log(self, txt, dt=None):
        """Logging function"""
        if self.params.print_log:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()} {txt}')

    def log_trade(self, date, ticker, action, price, size, reason, pnl_pct=None):
        """Log trade for history"""
        if self.params.track_trades:
            self.trade_log.append({
                'date': date,
                'ticker': ticker,
                'action': action,
                'price': price,
                'size': size,
                'reason': reason,
                'pnl_pct': pnl_pct
            })

    def detect_rhs_pattern(self, d):
        """Simplified RHS pattern detection"""
        if len(d.close) < self.params.min_pattern_bars:
            return False, None

        lookback = min(len(d.close), self.params.pattern_lookback)
        lows = np.array([d.low[-i] for i in range(lookback, 0, -1)])
        highs = np.array([d.high[-i] for i in range(lookback, 0, -1)])
        closes = np.array([d.close[-i] for i in range(lookback, 0, -1)])

        # Find troughs
        troughs_idx, _ = find_peaks(-lows, distance=10)

        if len(troughs_idx) < 3:
            return False, None

        # Check last 3 troughs for RHS
        for i in range(len(troughs_idx) - 2):
            ls_idx = troughs_idx[i]
            head_idx = troughs_idx[i+1]
            rs_idx = troughs_idx[i+2]

            # RHS validation
            if (lows[head_idx] < lows[ls_idx] and
                lows[head_idx] < lows[rs_idx] and
                lows[rs_idx] > lows[ls_idx] * 0.95):  # Right shoulder higher

                # Simple neckline
                neckline = (np.max(highs[ls_idx:head_idx]) + np.max(highs[head_idx:rs_idx])) / 2

                # Check if we're near breakout
                if closes[-1] >= neckline * 0.98:
                    return True, neckline

        return False, None

    def detect_cwh_pattern(self, d):
        """Simplified CWH pattern detection"""
        if len(d.close) < self.params.min_pattern_bars:
            return False, None

        lookback = min(len(d.close), self.params.pattern_lookback)
        lows = np.array([d.low[-i] for i in range(lookback, 0, -1)])
        highs = np.array([d.high[-i] for i in range(lookback, 0, -1)])
        closes = np.array([d.close[-i] for i in range(lookback, 0, -1)])

        # Find significant lows (cup bottom)
        troughs_idx, _ = find_peaks(-lows, distance=15, prominence=lows.std()*0.5)

        if len(troughs_idx) < 1:
            return False, None

        # Look for cup formation
        for trough_idx in troughs_idx[-3:]:  # Check last 3 troughs
            if trough_idx < 30 or trough_idx > lookback - 30:
                continue

            cup_low = lows[trough_idx]

            # Find highs before and after cup
            pre_cup_high = np.max(highs[max(0, trough_idx-30):trough_idx])
            post_cup_high = np.max(highs[trough_idx:min(lookback, trough_idx+30)])

            # Cup depth check (12-33%)
            cup_depth_pct = (pre_cup_high - cup_low) / pre_cup_high
            if cup_depth_pct < 0.12 or cup_depth_pct > 0.33:
                continue

            # Handle formation (recent pullback)
            if len(highs) > trough_idx + 20:
                recent_high = post_cup_high
                recent_low = np.min(lows[-15:])

                handle_depth = (recent_high - recent_low) / recent_high
                if handle_depth < cup_depth_pct * 0.15:  # Handle < 15% of cup

                    # Check if breaking out
                    if closes[-1] >= recent_high * 0.98:
                        return True, recent_high

        return False, None

    def check_volume_confirmation(self, d):
        """Check volume confirmation"""
        if len(d.volume) < 20:
            return True  # Skip check if insufficient data

        current_vol = d.volume[0]
        avg_vol = self.volume_sma[d][0]

        return current_vol > avg_vol * self.params.volume_threshold

    def get_target_pct(self, ticker):
        """Get target percentage"""
        if is_v40_stock(ticker):
            return self.params.v40_target_pct
        else:
            return self.params.v40_next_target_pct

    def notify_order(self, order):
        """Order notification"""
        if order.status in [order.Submitted, order.Accepted]:
            return

        ticker = order.data._name
        dt = self.datas[0].datetime.date(0)

        if order.status in [order.Completed]:
            if order.isbuy():
                reason = self.entry_reasons.get(ticker, 'Unknown')
                self.log(f'BUY {ticker} @ ₹{order.executed.price:.2f} | Size: {order.executed.size} | Reason: {reason}')

                self.entry_prices[ticker] = order.executed.price
                target_pct = self.get_target_pct(ticker)
                self.target_prices[ticker] = order.executed.price * (1 + target_pct)
                self.stop_losses[ticker] = order.executed.price * (1 - self.params.stop_loss_pct)

                self.log(f'  → Target: ₹{self.target_prices[ticker]:.2f} ({target_pct*100:.0f}%), SL: ₹{self.stop_losses[ticker]:.2f}')

                # Log trade
                self.log_trade(dt, ticker, 'BUY', order.executed.price, order.executed.size, reason)

            elif order.issell():
                pnl_pct = None
                if ticker in self.entry_prices:
                    pnl_pct = ((order.executed.price - self.entry_prices[ticker]) / self.entry_prices[ticker]) * 100
                    self.log(f'SELL {ticker} @ ₹{order.executed.price:.2f} | P&L: {pnl_pct:+.2f}%')

                    # Log trade
                    reason = self.entry_reasons.get(ticker, 'Exit')
                    self.log_trade(dt, ticker, 'SELL', order.executed.price, order.executed.size, reason, pnl_pct)

                    # Clear tracking
                    del self.entry_prices[ticker]
                    if ticker in self.target_prices:
                        del self.target_prices[ticker]
                    if ticker in self.stop_losses:
                        del self.stop_losses[ticker]
                    if ticker in self.entry_reasons:
                        del self.entry_reasons[ticker]

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
                entry_reason = ""

                # Signal 1: Golden Cross
                if self.crossover[d] > 0 and self.rsi[d][0] < self.params.rsi_overbought:
                    if d.close[0] > self.sma_short[d][0]:
                        entry_signal = True
                        entry_reason = "Golden Cross"

                # Signal 2: RHS Pattern
                if not entry_signal:
                    rhs_detected, neckline = self.detect_rhs_pattern(d)
                    if rhs_detected and self.check_volume_confirmation(d):
                        entry_signal = True
                        entry_reason = f"RHS Breakout (Neckline: ₹{neckline:.2f})"

                # Signal 3: CWH Pattern
                if not entry_signal:
                    cwh_detected, handle_high = self.detect_cwh_pattern(d)
                    if cwh_detected and self.check_volume_confirmation(d):
                        entry_signal = True
                        entry_reason = f"CWH Breakout (Handle: ₹{handle_high:.2f})"

                # Execute entry
                if entry_signal:
                    portfolio_value = self.broker.getvalue()
                    position_value = portfolio_value * self.params.max_position_pct
                    size = int(position_value / d.close[0])

                    if size > 0:
                        self.log(f'ENTRY SIGNAL: {ticker} - {entry_reason}')
                        self.entry_reasons[ticker] = entry_reason
                        self.orders[ticker] = self.buy(data=d, size=size)

            # === EXIT LOGIC ===
            else:
                current_price = d.close[0]
                exit_reason = None

                # Exit 1: Target
                if ticker in self.target_prices and current_price >= self.target_prices[ticker]:
                    exit_reason = "Target Reached"

                # Exit 2: Stop Loss
                elif ticker in self.stop_losses and current_price <= self.stop_losses[ticker]:
                    exit_reason = "Stop Loss"

                # Exit 3: Death Cross
                elif self.crossover[d] < 0:
                    exit_reason = "Death Cross"

                # Exit 4: RSI Overbought
                elif self.rsi[d][0] > self.params.rsi_overbought:
                    exit_reason = "RSI Overbought"

                if exit_reason:
                    self.log(f'EXIT: {ticker} - {exit_reason} @ ₹{current_price:.2f}')
                    self.entry_reasons[ticker] = exit_reason  # Store exit reason
                    self.orders[ticker] = self.sell(data=d, size=position.size)

    def stop(self):
        """Called when backtest ends"""
        self.log(f'='*80)
        self.log(f'Final Portfolio Value: ₹{self.broker.getvalue():,.2f}')
        self.log(f'Total Trades Logged: {len(self.trade_log)}')
        self.log(f'='*80)

    def get_trade_history(self):
        """Return trade history"""
        return self.trade_log
