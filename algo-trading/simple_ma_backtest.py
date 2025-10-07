#!/usr/bin/env python3
"""
Simple Moving Average Crossover Strategy - More Active Trading
Test with Rs 100,000 for last 1 year
"""

import backtrader as bt
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd

class SimpleSMAStrategy(bt.Strategy):
    """Simple SMA Crossover Strategy"""

    params = (
        ('sma_short', 20),
        ('sma_long', 50),
        ('position_size', 0.95),  # Use 95% of cash per trade
    )

    def __init__(self):
        self.sma_short = bt.indicators.SMA(self.data.close, period=self.params.sma_short)
        self.sma_long = bt.indicators.SMA(self.data.close, period=self.params.sma_long)
        self.crossover = bt.indicators.CrossOver(self.sma_short, self.sma_long)

    def next(self):
        if not self.position:
            if self.crossover > 0:  # Golden cross
                size = int((self.broker.cash * self.params.position_size) / self.data.close[0])
                self.buy(size=size)
                print(f'{self.data.datetime.date(0)}: BUY at ₹{self.data.close[0]:.2f}')
        else:
            if self.crossover < 0:  # Death cross
                self.sell(size=self.position.size)
                print(f'{self.data.datetime.date(0)}: SELL at ₹{self.data.close[0]:.2f}')


def run_simple_backtest(ticker, start_date, end_date, initial_cash=100000):
    """Run simple MA crossover backtest"""

    print(f"\n{'='*100}")
    print(f"📊 Simple MA Crossover Strategy: {ticker}")
    print(f"Period: {start_date} to {end_date}")
    print(f"Initial Capital: ₹{initial_cash:,}")
    print(f"{'='*100}\n")

    # Fetch data
    data = yf.download(ticker, start=start_date, end=end_date, progress=False)

    if data.empty:
        print(f"❌ No data for {ticker}")
        return None

    # Handle MultiIndex
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    # Initialize Cerebro
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(initial_cash)
    cerebro.broker.setcommission(commission=0.001)

    # Add data
    data_feed = bt.feeds.PandasData(dataname=data)
    cerebro.adddata(data_feed)

    # Add strategy
    cerebro.addstrategy(SimpleSMAStrategy)

    # Add analyzers
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')

    # Run
    print(f"💰 Starting Value: ₹{cerebro.broker.getvalue():,.2f}\n")
    results = cerebro.run()
    final_value = cerebro.broker.getvalue()

    # Extract results
    strategy = results[0]
    returns = strategy.analyzers.returns.get_analysis()
    drawdown = strategy.analyzers.drawdown.get_analysis()
    trades = strategy.analyzers.trades.get_analysis()

    total_return = ((final_value - initial_cash) / initial_cash) * 100
    total_trades = trades.get('total', {}).get('total', 0)
    won = trades.get('won', {}).get('total', 0)
    lost = trades.get('lost', {}).get('total', 0)
    win_rate = (won / total_trades * 100) if total_trades > 0 else 0

    # Print results
    print(f"\n{'='*100}")
    print(f"📈 RESULTS")
    print(f"{'='*100}")
    print(f"Final Value:    ₹{final_value:,.2f}")
    print(f"Total Return:   {total_return:.2f}%")
    print(f"Profit/Loss:    ₹{(final_value - initial_cash):,.2f}")
    print(f"Max Drawdown:   {drawdown.get('max', {}).get('drawdown', 0):.2f}%")
    print(f"Total Trades:   {total_trades}")
    print(f"Won Trades:     {won}")
    print(f"Lost Trades:    {lost}")
    print(f"Win Rate:       {win_rate:.2f}%")
    print(f"{'='*100}\n")

    # Calculate Buy & Hold comparison
    start_price = data['Close'].iloc[0]
    end_price = data['Close'].iloc[-1]
    buy_hold_return = ((end_price - start_price) / start_price) * 100
    buy_hold_value = initial_cash * (1 + buy_hold_return/100)

    print(f"📊 BUY & HOLD COMPARISON")
    print(f"{'='*100}")
    print(f"Buy & Hold Return:     {buy_hold_return:.2f}%")
    print(f"Buy & Hold Final Value: ₹{buy_hold_value:,.2f}")
    print(f"Strategy Outperformance: {total_return - buy_hold_return:.2f}%")
    print(f"{'='*100}\n")

    return {
        'ticker': ticker,
        'initial': initial_cash,
        'final': final_value,
        'return': total_return,
        'trades': total_trades,
        'win_rate': win_rate,
        'buy_hold_return': buy_hold_return
    }


# =============================================================================
# Main Test
# =============================================================================
if __name__ == '__main__':
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

    print("\n" + "="*100)
    print("🚀 TESTING SIMPLE MA CROSSOVER STRATEGY - LAST 1 YEAR WITH ₹1,00,000")
    print("="*100)

    results = []

    # Test on different stocks
    stocks = ['RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS', 'DELHIVERY.NS']

    for ticker in stocks:
        result = run_simple_backtest(ticker, start_date, end_date)
        if result:
            results.append(result)

    # Summary
    if results:
        print("\n" + "="*100)
        print("📊 SUMMARY - WHAT ₹1,00,000 WOULD BECOME")
        print("="*100)

        best = max(results, key=lambda x: x['return'])

        for r in sorted(results, key=lambda x: x['return'], reverse=True):
            strategy_emoji = "📈" if r['return'] > 0 else "📉"
            buyhold_emoji = "📈" if r['buy_hold_return'] > 0 else "📉"

            print(f"\n{r['ticker']}:")
            print(f"  {strategy_emoji} Strategy:      ₹{r['final']:,.2f} ({r['return']:+.2f}%)")
            print(f"  {buyhold_emoji} Buy & Hold:     ₹{r['initial'] * (1 + r['buy_hold_return']/100):,.2f} ({r['buy_hold_return']:+.2f}%)")
            print(f"  Trades: {r['trades']} | Win Rate: {r['win_rate']:.1f}%")

        print(f"\n{'='*100}")
        print(f"🏆 BEST PERFORMER: {best['ticker']}")
        print(f"   ₹1,00,000 → ₹{best['final']:,.2f}")
        print(f"   Gain: ₹{(best['final'] - 100000):,.2f} ({best['return']:.2f}%)")
        print(f"{'='*100}\n")
