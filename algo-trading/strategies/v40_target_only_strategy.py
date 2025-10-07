#!/usr/bin/env python3
"""
V40 Target-Only Strategy

Key Changes:
1. NO STOP LOSS - Hold through volatility
2. Exit ONLY at target (20% for V40, 30% for V40 Next)
3. Use ONLY stocks from Excel file (81 stocks)
4. 5% max position size
5. Entry: Golden Cross + RSI favorable
"""

import backtrader as bt
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from load_v40_from_excel import is_v40_stock, is_v40_next_stock


class V40TargetOnlyStrategy(bt.Strategy):
    """
    V40 Strategy - Target Only (NO Stop Loss)

    Entry: Golden Cross (SMA 20 > 50) + RSI < 70
    Exit: ONLY at target (20-30%)
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

        # Targets (NO STOP LOSS)
        ('v40_target_pct', 0.20),        # 20% target for V40
        ('v40_next_target_pct', 0.30),   # 30% target for V40 Next

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

    def get_target_pct(self, ticker):
        """Get target percentage based on V40 vs V40 Next"""
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
                reason = self.entry_reasons.get(ticker, 'Golden Cross')
                stock_type = "V40" if is_v40_stock(ticker) else "V40 Next"
                self.log(f'BUY {ticker} ({stock_type}) @ ₹{order.executed.price:.2f} | Size: {order.executed.size}')

                self.entry_prices[ticker] = order.executed.price
                target_pct = self.get_target_pct(ticker)
                self.target_prices[ticker] = order.executed.price * (1 + target_pct)

                self.log(f'  → Target: ₹{self.target_prices[ticker]:.2f} ({target_pct*100:.0f}%) | NO STOP LOSS')

                # Log trade
                self.log_trade(dt, ticker, 'BUY', order.executed.price, order.executed.size, reason)

            elif order.issell():
                pnl_pct = None
                if ticker in self.entry_prices:
                    pnl_pct = ((order.executed.price - self.entry_prices[ticker]) / self.entry_prices[ticker]) * 100
                    self.log(f'SELL {ticker} @ ₹{order.executed.price:.2f} | P&L: {pnl_pct:+.2f}%')

                    # Log trade
                    reason = self.entry_reasons.get(ticker, 'Target Reached')
                    self.log_trade(dt, ticker, 'SELL', order.executed.price, order.executed.size, reason, pnl_pct)

                    # Clear tracking
                    del self.entry_prices[ticker]
                    if ticker in self.target_prices:
                        del self.target_prices[ticker]
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
                # Entry Signal: Golden Cross + RSI not overbought
                if self.crossover[d] > 0:
                    if self.rsi[d][0] < self.params.rsi_overbought:
                        if d.close[0] > self.sma_short[d][0]:
                            # Calculate position size (5% of portfolio)
                            portfolio_value = self.broker.getvalue()
                            position_value = portfolio_value * self.params.max_position_pct
                            size = int(position_value / d.close[0])

                            if size > 0:
                                self.log(f'ENTRY SIGNAL: {ticker} - Golden Cross + RSI {self.rsi[d][0]:.1f}')
                                self.entry_reasons[ticker] = "Golden Cross"
                                self.orders[ticker] = self.buy(data=d, size=size)

            # === EXIT LOGIC ===
            else:
                current_price = d.close[0]

                # ONLY EXIT: Target reached
                if ticker in self.target_prices and current_price >= self.target_prices[ticker]:
                    target_pct = self.get_target_pct(ticker)
                    self.log(f'EXIT: {ticker} - TARGET REACHED ({target_pct*100:.0f}%) @ ₹{current_price:.2f}')
                    self.entry_reasons[ticker] = "Target Reached"
                    self.orders[ticker] = self.sell(data=d, size=position.size)

                # NO STOP LOSS - Hold through downturns
                # NO Death Cross exit - Hold for full target
                # NO RSI Overbought exit - Hold for full target

    def stop(self):
        """Called when backtest ends"""
        self.log(f'='*80)
        self.log(f'Final Portfolio Value: ₹{self.broker.getvalue():,.2f}')
        self.log(f'Total Trades Logged: {len(self.trade_log)}')
        self.log(f'='*80)

    def get_trade_history(self):
        """Return trade history"""
        return self.trade_log
