#!/usr/bin/env python3
"""
V40 Validated Strategy with Historical Win Rate Analysis

Key Features:
1. Use 5 years of historical data for pattern detection
2. Validate each strategy has >70% win rate on that stock in past 5 years
3. Only trade stocks/strategies that pass validation
4. NO STOP LOSS - Exit at pattern-specific targets
5. 5% max position size
"""

import backtrader as bt
import numpy as np
from scipy.signal import find_peaks
import sys
import os
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from load_v40_from_excel import is_v40_stock, is_v40_next_stock


class V40ValidatedStrategy(bt.Strategy):
    """
    V40 Strategy with Historical Win Rate Validation

    Pre-filters stocks and strategies based on 5-year historical performance
    Only trades if strategy has >70% win rate on that specific stock
    """

    params = (
        # Position sizing
        ('max_position_pct', 0.05),
        ('max_total_exposure', 0.95),

        # Technical indicators
        ('sma_short', 20),
        ('sma_long', 50),
        ('rsi_period', 14),
        ('rsi_overbought', 70),

        # Pattern detection (5 year lookback)
        ('lookback_period', 250),       # 1 year for current pattern detection
        ('historical_years', 5),        # 5 years for validation
        ('volume_threshold', 1.3),
        ('min_golden_cross_target', 0.15),

        # Validation criteria
        ('min_win_rate', 0.70),         # 70% minimum win rate
        ('min_historical_trades', 5),   # Minimum 5 trades in history to validate

        # Trading period control
        ('trading_start_date', None),   # Only trade after this date

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
        self.entry_details = {}
        self.trade_log = []

        # Historical validation cache
        self.validated_strategies = {}  # {ticker: {strategy: win_rate}}
        self.validation_complete = {}   # {ticker: True/False}

        # Market regime tracking
        self.market_data = None
        self.market_sma_short = None
        self.market_sma_long = None
        self.in_bullish_market = False

        # Technical indicators
        self.sma_short = {}
        self.sma_long = {}
        self.rsi = {}
        self.crossover = {}

        # Identify NIFTYBEES data feed for market regime
        for d in self.datas:
            if d._name == 'NIFTYBEES.NS':
                self.market_data = d
                self.market_sma_short = bt.indicators.SMA(d.close, period=50)
                self.market_sma_long = bt.indicators.SMA(d.close, period=200)
                self.log("✅ Market regime filter enabled: Using NIFTYBEES.NS")
            else:
                self.sma_short[d] = bt.indicators.SMA(d.close, period=self.params.sma_short)
                self.sma_long[d] = bt.indicators.SMA(d.close, period=self.params.sma_long)
                self.rsi[d] = bt.indicators.RSI(d.close, period=self.params.rsi_period)
                self.crossover[d] = bt.indicators.CrossOver(self.sma_short[d], self.sma_long[d])

        self.log("="*80)
        self.log("INITIALIZING HISTORICAL VALIDATION (5 YEARS)")
        self.log("="*80)

    def start(self):
        """Called when strategy starts - perform historical validation"""
        self.log("Starting historical validation for all stocks...")

        for d in self.datas:
            ticker = d._name
            self.validate_stock_strategies(ticker, d)

        self.log("="*80)
        self.log("VALIDATION COMPLETE - Starting Live Trading")
        self.log("="*80)

    def validate_stock_strategies(self, ticker, data_feed):
        """
        Validate each strategy on 5 years of historical data
        Only allow strategies with >70% win rate
        """
        self.log(f"\nValidating {ticker}...")

        # Download 5 years of historical data
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365 * self.params.historical_years)

            hist_data = yf.download(ticker, start=start_date.strftime('%Y-%m-%d'),
                                   end=end_date.strftime('%Y-%m-%d'), progress=False)

            if hist_data.empty or len(hist_data) < 500:
                self.log(f"  ❌ {ticker}: Insufficient historical data")
                self.validation_complete[ticker] = True
                self.validated_strategies[ticker] = {}
                return

            if isinstance(hist_data.columns, pd.MultiIndex):
                hist_data.columns = hist_data.columns.get_level_values(0)

        except Exception as e:
            self.log(f"  ❌ {ticker}: Failed to fetch data - {str(e)}")
            self.validation_complete[ticker] = True
            self.validated_strategies[ticker] = {}
            return

        # Test each strategy
        strategies_to_test = ['Golden Cross', 'RHS', 'CWH']
        validated = {}

        for strategy_name in strategies_to_test:
            win_rate = self.backtest_strategy_on_history(ticker, hist_data, strategy_name)

            if win_rate is not None and win_rate >= self.params.min_win_rate:
                validated[strategy_name] = win_rate
                self.log(f"  ✅ {ticker} - {strategy_name}: {win_rate:.1f}% win rate (VALIDATED)")
            elif win_rate is not None:
                self.log(f"  ❌ {ticker} - {strategy_name}: {win_rate:.1f}% win rate (below 70%)")
            else:
                self.log(f"  ⚠️  {ticker} - {strategy_name}: Insufficient trades")

        self.validated_strategies[ticker] = validated
        self.validation_complete[ticker] = True

        if not validated:
            self.log(f"  🚫 {ticker}: NO STRATEGIES VALIDATED - Stock will be skipped")

    def backtest_strategy_on_history(self, ticker, hist_data, strategy_name):
        """
        Backtest a specific strategy on historical data
        Returns win rate or None if insufficient trades
        """
        trades = []

        # Calculate indicators on historical data
        hist_data['SMA20'] = hist_data['Close'].rolling(window=20).mean()
        hist_data['SMA50'] = hist_data['Close'].rolling(window=50).mean()
        hist_data['RSI'] = self.calculate_rsi(hist_data['Close'].values, 14)

        if strategy_name == 'Golden Cross':
            trades = self.simulate_golden_cross(hist_data)
        elif strategy_name == 'RHS':
            trades = self.simulate_rhs_pattern(hist_data)
        elif strategy_name == 'CWH':
            trades = self.simulate_cwh_pattern(hist_data)

        if len(trades) < self.params.min_historical_trades:
            return None

        wins = sum(1 for t in trades if t['pnl'] > 0)
        win_rate = (wins / len(trades)) * 100

        return win_rate

    def calculate_rsi(self, prices, period=14):
        """Calculate RSI"""
        deltas = np.diff(prices)
        seed = deltas[:period+1]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period
        rs = up / down if down != 0 else 0
        rsi = np.zeros_like(prices)
        rsi[:period] = 100. - 100. / (1. + rs)

        for i in range(period, len(prices)):
            delta = deltas[i - 1]
            if delta > 0:
                upval = delta
                downval = 0.
            else:
                upval = 0.
                downval = -delta

            up = (up * (period - 1) + upval) / period
            down = (down * (period - 1) + downval) / period
            rs = up / down if down != 0 else 0
            rsi[i] = 100. - 100. / (1. + rs)

        return rsi

    def simulate_golden_cross(self, hist_data):
        """Simulate Golden Cross trades on historical data"""
        trades = []
        in_position = False
        entry_price = 0
        entry_idx = 0
        target_price = 0

        for i in range(50, len(hist_data)):
            if pd.isna(hist_data['SMA20'].iloc[i]) or pd.isna(hist_data['SMA50'].iloc[i]):
                continue

            # Entry: Golden Cross
            if not in_position:
                if (hist_data['SMA20'].iloc[i] > hist_data['SMA50'].iloc[i] and
                    hist_data['SMA20'].iloc[i-1] <= hist_data['SMA50'].iloc[i-1] and
                    hist_data['RSI'].iloc[i] < 70):

                    entry_price = hist_data['Close'].iloc[i]
                    entry_idx = i

                    # Calculate target
                    distance = entry_price - hist_data['SMA50'].iloc[i]
                    target_price = entry_price + (distance * 2)
                    min_target = entry_price * 1.15
                    target_price = max(target_price, min_target)

                    in_position = True

            # Exit: Target reached or end of data
            elif in_position:
                current_price = hist_data['Close'].iloc[i]

                if current_price >= target_price:
                    pnl_pct = ((current_price - entry_price) / entry_price) * 100
                    trades.append({'pnl': pnl_pct, 'hold_days': i - entry_idx})
                    in_position = False

        # Close open position at end
        if in_position:
            final_price = hist_data['Close'].iloc[-1]
            pnl_pct = ((final_price - entry_price) / entry_price) * 100
            trades.append({'pnl': pnl_pct, 'hold_days': len(hist_data) - entry_idx})

        return trades

    def simulate_rhs_pattern(self, hist_data):
        """Simulate RHS pattern trades on historical data"""
        trades = []
        closes = hist_data['Close'].values
        volumes = hist_data['Volume'].values

        # Sliding window approach
        for i in range(150, len(hist_data) - 20):
            window = closes[i-150:i]

            # Find troughs
            troughs, _ = find_peaks(-window, distance=10, prominence=window.std() * 0.3)

            if len(troughs) < 3:
                continue

            last_troughs = troughs[-3:]
            left_shoulder = window[last_troughs[0]]
            head = window[last_troughs[1]]
            right_shoulder = window[last_troughs[2]]

            # Validate RHS pattern
            if not (head < left_shoulder * 0.95 and head < right_shoulder * 0.95):
                continue

            if abs(left_shoulder - right_shoulder) / left_shoulder > 0.10:
                continue

            # Calculate neckline
            neckline = (left_shoulder + right_shoulder) / 2 * 1.05

            # Check breakout
            if closes[i] >= neckline * 0.98:
                entry_price = closes[i]
                pattern_depth = neckline - head
                target_price = neckline + pattern_depth

                # Find exit
                for j in range(i+1, min(i+100, len(closes))):
                    if closes[j] >= target_price:
                        pnl_pct = ((closes[j] - entry_price) / entry_price) * 100
                        trades.append({'pnl': pnl_pct, 'hold_days': j - i})
                        break

        return trades

    def simulate_cwh_pattern(self, hist_data):
        """Simulate CWH pattern trades on historical data"""
        trades = []
        closes = hist_data['Close'].values

        # Sliding window approach
        for i in range(150, len(hist_data) - 20):
            window = closes[i-150:i]

            mid_point = len(window) // 2
            first_half_max = window[:mid_point].max()
            second_half_max = window[mid_point:].max()
            cup_bottom = window[mid_point-10:mid_point+10].min()

            # Validate cup
            cup_depth = first_half_max - cup_bottom
            if cup_depth / first_half_max < 0.10:
                continue

            if abs(first_half_max - second_half_max) / first_half_max > 0.05:
                continue

            # Check handle
            recent_high = window[-30:-10].max()
            handle_low = window[-10:].min()
            handle_depth = recent_high - handle_low

            if handle_depth > cup_depth * 0.15:
                continue

            # Check breakout
            if closes[i] >= second_half_max * 0.98:
                entry_price = closes[i]
                target_price = second_half_max + cup_depth

                # Find exit
                for j in range(i+1, min(i+100, len(closes))):
                    if closes[j] >= target_price:
                        pnl_pct = ((closes[j] - entry_price) / entry_price) * 100
                        trades.append({'pnl': pnl_pct, 'hold_days': j - i})
                        break

        return trades

    def log(self, txt, dt=None):
        """Logging function"""
        if self.params.print_log:
            dt = dt or self.datas[0].datetime.date(0) if len(self.datas) > 0 else None
            if dt:
                print(f'{dt.isoformat()} {txt}')
            else:
                print(txt)

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

    def is_strategy_validated(self, ticker, strategy_name):
        """Check if strategy is validated for this ticker"""
        if ticker not in self.validated_strategies:
            return False
        return strategy_name in self.validated_strategies[ticker]

    def calculate_golden_cross_target(self, d, entry_price):
        """Calculate target for Golden Cross entry"""
        sma50_value = self.sma_long[d][0]
        distance_from_sma = entry_price - sma50_value
        target_distance = distance_from_sma * 2
        calculated_target = entry_price + target_distance
        min_target = entry_price * (1 + self.params.min_golden_cross_target)
        target = max(calculated_target, min_target)
        target_pct = ((target - entry_price) / entry_price) * 100
        return target, target_pct, f"GC (SMA50 dist: {distance_from_sma:.2f})"

    def detect_rhs_pattern(self, d):
        """Detect RHS pattern (simplified for real-time)"""
        lookback = min(self.params.lookback_period, len(d.close))
        if lookback < 60:
            return False, None, None, None

        closes = np.array([d.close[-i] for i in range(lookback, 0, -1)])
        volumes = np.array([d.volume[-i] for i in range(lookback, 0, -1)])

        troughs, _ = find_peaks(-closes, distance=10, prominence=closes.std() * 0.3)

        if len(troughs) < 3:
            return False, None, None, None

        last_troughs = troughs[-3:]
        head = closes[last_troughs[1]]
        left_shoulder = closes[last_troughs[0]]
        right_shoulder = closes[last_troughs[2]]

        if not (head < left_shoulder * 0.95 and head < right_shoulder * 0.95):
            return False, None, None, None

        neckline = (left_shoulder + right_shoulder) / 2 * 1.05
        current_price = d.close[0]

        if current_price < neckline * 0.98:
            return False, None, None, None

        avg_volume = volumes[-20:].mean()
        if d.volume[0] < avg_volume * self.params.volume_threshold:
            return False, None, None, None

        pattern_depth = neckline - head
        target_price = neckline + pattern_depth
        target_pct = ((target_price - current_price) / current_price) * 100

        return True, target_price, target_pct, f"RHS (Neckline: {neckline:.2f})"

    def detect_cwh_pattern(self, d):
        """Detect CWH pattern (simplified for real-time)"""
        lookback = min(self.params.lookback_period, len(d.close))
        if lookback < 60:
            return False, None, None, None

        closes = np.array([d.close[-i] for i in range(lookback, 0, -1)])

        mid_point = len(closes) // 2
        first_half_max = closes[:mid_point].max()
        second_half_max = closes[mid_point:].max()
        cup_bottom = closes[mid_point-10:mid_point+10].min()

        cup_depth = first_half_max - cup_bottom
        if cup_depth / first_half_max < 0.10:
            return False, None, None, None

        current_price = d.close[0]
        if current_price < second_half_max * 0.98:
            return False, None, None, None

        target_price = second_half_max + cup_depth
        target_pct = ((target_price - current_price) / current_price) * 100

        return True, target_price, target_pct, f"CWH (Cup depth: {cup_depth:.2f})"

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

                self.entry_prices[ticker] = order.executed.price
                target_price = self.target_prices.get(ticker, 0)
                target_pct = ((target_price - order.executed.price) / order.executed.price) * 100

                self.log(f'BUY {ticker} @ ₹{order.executed.price:.2f} | {reason} (Validated)')
                self.log(f'  → Target: ₹{target_price:.2f} ({target_pct:.1f}%) | {details}')

                self.log_trade(dt, ticker, 'BUY', order.executed.price, order.executed.size, reason, target_pct=target_pct)

            elif order.issell():
                pnl_pct = None
                if ticker in self.entry_prices:
                    pnl_pct = ((order.executed.price - self.entry_prices[ticker]) / self.entry_prices[ticker]) * 100
                    self.log(f'SELL {ticker} @ ₹{order.executed.price:.2f} | P&L: {pnl_pct:+.2f}%')

                    reason = self.entry_reasons.get(ticker, 'Target Reached')
                    target_pct = ((self.target_prices.get(ticker, 0) - self.entry_prices[ticker]) / self.entry_prices[ticker]) * 100
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
        # Check if we're in the trading period
        if self.params.trading_start_date:
            current_date = self.datas[0].datetime.date(0)
            trading_start = datetime.strptime(self.params.trading_start_date, '%Y-%m-%d').date()
            if current_date < trading_start:
                return  # Don't trade yet, still in validation period

        # === MARKET REGIME CHECK ===
        # Update market regime status
        if self.market_data and self.market_sma_short and self.market_sma_long:
            if len(self.market_sma_short) > 0 and len(self.market_sma_long) > 0:
                prev_bullish = self.in_bullish_market
                self.in_bullish_market = self.market_sma_short[0] > self.market_sma_long[0]

                # Log regime changes
                if prev_bullish != self.in_bullish_market:
                    market_status = "BULLISH ✅" if self.in_bullish_market else "BEARISH ⛔"
                    self.log(f"MARKET REGIME CHANGE: {market_status} (SMA50: {self.market_sma_short[0]:.2f}, SMA200: {self.market_sma_long[0]:.2f})")

        for d in self.datas:
            ticker = d._name

            # Skip NIFTYBEES (market regime indicator only)
            if ticker == 'NIFTYBEES.NS':
                continue

            # Skip if validation not complete or ticker not validated
            if ticker not in self.validation_complete or not self.validation_complete[ticker]:
                continue

            if ticker not in self.validated_strategies or not self.validated_strategies[ticker]:
                continue

            if ticker in self.orders:
                continue

            position = self.getposition(d)

            # === ENTRY LOGIC ===
            if not position:
                # ONLY ENTER NEW POSITIONS IN BULLISH MARKET
                if self.market_data and not self.in_bullish_market:
                    continue  # Skip entry during bearish market
                entry_signal = False
                target_price = None
                target_pct = None
                reason = None
                details = None

                # 1. Check RHS Pattern (if validated)
                if self.is_strategy_validated(ticker, 'RHS'):
                    is_rhs, rhs_target, rhs_target_pct, rhs_details = self.detect_rhs_pattern(d)
                    if is_rhs:
                        entry_signal = True
                        target_price = rhs_target
                        target_pct = rhs_target_pct
                        reason = "RHS Breakout"
                        details = rhs_details

                # 2. Check CWH Pattern (if validated)
                if not entry_signal and self.is_strategy_validated(ticker, 'CWH'):
                    is_cwh, cwh_target, cwh_target_pct, cwh_details = self.detect_cwh_pattern(d)
                    if is_cwh:
                        entry_signal = True
                        target_price = cwh_target
                        target_pct = cwh_target_pct
                        reason = "CWH Breakout"
                        details = cwh_details

                # 3. Check Golden Cross (if validated)
                if not entry_signal and self.is_strategy_validated(ticker, 'Golden Cross'):
                    if self.crossover[d] > 0:
                        if self.rsi[d][0] < self.params.rsi_overbought:
                            if d.close[0] > self.sma_short[d][0]:
                                entry_signal = True
                                target_price, calc_target_pct, gc_details = self.calculate_golden_cross_target(d, d.close[0])
                                target_pct = calc_target_pct
                                reason = "Golden Cross"
                                details = gc_details

                # Execute entry
                if entry_signal and target_price and target_pct > 5:
                    portfolio_value = self.broker.getvalue()
                    position_value = portfolio_value * self.params.max_position_pct
                    size = int(position_value / d.close[0])

                    if size > 0:
                        win_rate = self.validated_strategies[ticker][reason.replace(' Breakout', '').replace(' ', ' ').strip()]
                        self.log(f'ENTRY: {ticker} - {reason} (Historical WR: {win_rate:.1f}%)')
                        self.entry_reasons[ticker] = reason
                        self.entry_details[ticker] = details
                        self.target_prices[ticker] = target_price
                        self.orders[ticker] = self.buy(data=d, size=size)

            # === EXIT LOGIC ===
            else:
                current_price = d.close[0]

                # ONLY EXIT: Target reached
                if ticker in self.target_prices and current_price >= self.target_prices[ticker]:
                    self.log(f'EXIT: {ticker} - TARGET REACHED @ ₹{current_price:.2f}')
                    self.entry_reasons[ticker] = "Target Reached"
                    self.orders[ticker] = self.sell(data=d, size=position.size)

    def stop(self):
        """Called when backtest ends"""
        self.log(f'='*80)
        self.log(f'Final Portfolio Value: ₹{self.broker.getvalue():,.2f}')

        # Print validation summary
        total_stocks = len(self.validated_strategies)
        validated_stocks = sum(1 for v in self.validated_strategies.values() if v)

        self.log(f'\nVALIDATION SUMMARY:')
        self.log(f'Total Stocks Analyzed: {total_stocks}')
        self.log(f'Stocks with Validated Strategies: {validated_stocks}')
        self.log(f'Stocks Rejected: {total_stocks - validated_stocks}')
        self.log(f'='*80)

    def get_trade_history(self):
        """Return trade history"""
        return self.trade_log

    def get_validation_summary(self):
        """Return validation summary"""
        return self.validated_strategies
