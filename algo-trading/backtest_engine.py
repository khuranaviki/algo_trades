#!/usr/bin/env python3
"""
Main Backtesting Engine for Algorithmic Trading Strategies
Supports multiple strategies and data feeds
"""

import backtrader as bt
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import os
import json
from typing import List, Dict, Optional
import argparse

# Import strategies
from strategies.rhs_strategy import RHSPatternStrategy
from strategies.cwh_strategy import CWHPatternStrategy
from strategies.fundamental_screen_strategy import FundamentalScreenStrategy, MultibaggerScreenStrategy


class BacktestEngine:
    """
    Main backtesting engine for running algorithmic trading strategies
    """

    def __init__(self, initial_cash=100000, commission=0.001):
        """
        Initialize backtest engine

        Args:
            initial_cash: Starting portfolio value
            commission: Commission per trade (0.001 = 0.1%)
        """
        self.initial_cash = initial_cash
        self.commission = commission
        self.results = {}

    def fetch_data(self, ticker: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """
        Fetch historical data from Yahoo Finance

        Args:
            ticker: Stock ticker symbol (e.g., 'RELIANCE.NS')
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format

        Returns:
            DataFrame with OHLCV data or None
        """
        try:
            print(f"📊 Fetching data for {ticker} from {start_date} to {end_date}...")
            data = yf.download(ticker, start=start_date, end=end_date, progress=False)

            if data.empty:
                print(f"❌ No data found for {ticker}")
                return None

            # Handle MultiIndex columns from yfinance
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)

            print(f"✅ Fetched {len(data)} bars for {ticker}")
            return data

        except Exception as e:
            print(f"❌ Error fetching data for {ticker}: {e}")
            return None

    def run_backtest(
        self,
        strategy_class,
        tickers: List[str],
        start_date: str,
        end_date: str,
        strategy_params: Dict = None,
        fundamental_data: Dict = None
    ) -> Dict:
        """
        Run backtest for a given strategy

        Args:
            strategy_class: Strategy class to backtest
            tickers: List of ticker symbols
            start_date: Start date for backtest
            end_date: End date for backtest
            strategy_params: Optional parameters for strategy
            fundamental_data: Optional fundamental data dict {ticker: {metrics}}

        Returns:
            Dictionary with backtest results
        """
        print(f"\n{'='*80}")
        print(f"🚀 Running Backtest: {strategy_class.__name__}")
        print(f"{'='*80}")

        # Initialize Cerebro engine
        cerebro = bt.Cerebro()

        # Set initial cash
        cerebro.broker.setcash(self.initial_cash)

        # Set commission
        cerebro.broker.setcommission(commission=self.commission)

        # Add strategy
        if strategy_params:
            cerebro.addstrategy(strategy_class, **strategy_params)
        else:
            cerebro.addstrategy(strategy_class)

        # Add data feeds
        data_loaded = False
        for ticker in tickers:
            data = self.fetch_data(ticker, start_date, end_date)

            if data is not None:
                # Convert to Backtrader data feed
                data_feed = bt.feeds.PandasData(
                    dataname=data,
                    name=ticker,
                    datetime=None,  # Use index as datetime
                    open='Open',
                    high='High',
                    low='Low',
                    close='Close',
                    volume='Volume',
                    openinterest=-1
                )
                cerebro.adddata(data_feed)
                data_loaded = True
                print(f"✅ Added data feed: {ticker}")

        if not data_loaded:
            print("❌ No data loaded, aborting backtest")
            return {}

        # Add analyzers
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')

        # Print starting conditions
        start_value = cerebro.broker.getvalue()
        print(f"\n💰 Starting Portfolio Value: ₹{start_value:,.2f}")

        # Run backtest
        print(f"\n🔄 Running backtest...\n")
        results = cerebro.run()

        # Print ending conditions
        end_value = cerebro.broker.getvalue()
        print(f"\n💰 Final Portfolio Value: ₹{end_value:,.2f}")

        # Extract results
        strategy_results = results[0]

        # Get analyzer results
        sharpe = strategy_results.analyzers.sharpe.get_analysis()
        drawdown = strategy_results.analyzers.drawdown.get_analysis()
        returns = strategy_results.analyzers.returns.get_analysis()
        trades = strategy_results.analyzers.trades.get_analysis()

        # Calculate metrics
        total_return = ((end_value - start_value) / start_value) * 100
        sharpe_ratio = sharpe.get('sharperatio', 0)
        max_drawdown = drawdown.get('max', {}).get('drawdown', 0)

        # Trade statistics
        total_trades = trades.get('total', {}).get('total', 0)
        won_trades = trades.get('won', {}).get('total', 0)
        lost_trades = trades.get('lost', {}).get('total', 0)
        win_rate = (won_trades / total_trades * 100) if total_trades > 0 else 0

        # Compile results
        results_dict = {
            'strategy': strategy_class.__name__,
            'tickers': tickers,
            'start_date': start_date,
            'end_date': end_date,
            'initial_cash': start_value,
            'final_value': end_value,
            'total_return': total_return,
            'total_return_pct': f"{total_return:.2f}%",
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'max_drawdown_pct': f"{max_drawdown:.2f}%",
            'total_trades': total_trades,
            'won_trades': won_trades,
            'lost_trades': lost_trades,
            'win_rate': win_rate,
            'win_rate_pct': f"{win_rate:.2f}%",
        }

        # Print summary
        self.print_results(results_dict)

        # Plot results (optional - requires matplotlib)
        # cerebro.plot(style='candlestick')

        return results_dict

    def print_results(self, results: Dict):
        """Print formatted backtest results"""
        print(f"\n{'='*80}")
        print(f"📊 BACKTEST RESULTS: {results['strategy']}")
        print(f"{'='*80}")
        print(f"Tickers:          {', '.join(results['tickers'])}")
        print(f"Period:           {results['start_date']} to {results['end_date']}")
        print(f"\n💰 PERFORMANCE:")
        print(f"Initial Cash:     ₹{results['initial_cash']:,.2f}")
        print(f"Final Value:      ₹{results['final_value']:,.2f}")
        print(f"Total Return:     {results['total_return_pct']} (₹{results['final_value'] - results['initial_cash']:,.2f})")
        print(f"Sharpe Ratio:     {results['sharpe_ratio']:.2f}")
        print(f"Max Drawdown:     {results['max_drawdown_pct']}")
        print(f"\n📈 TRADING STATISTICS:")
        print(f"Total Trades:     {results['total_trades']}")
        print(f"Won Trades:       {results['won_trades']}")
        print(f"Lost Trades:      {results['lost_trades']}")
        print(f"Win Rate:         {results['win_rate_pct']}")
        print(f"{'='*80}\n")

    def save_results(self, results: Dict, filename: str):
        """Save backtest results to JSON file"""
        filepath = os.path.join('backtest_results', filename)
        os.makedirs('backtest_results', exist_ok=True)

        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        print(f"✅ Results saved to: {filepath}")


def main():
    """Main function for running backtests from command line"""
    parser = argparse.ArgumentParser(description='Run algorithmic trading backtests')
    parser.add_argument('--strategy', type=str, required=True,
                        choices=['rhs', 'cwh', 'fundamental', 'multibagger'],
                        help='Strategy to backtest')
    parser.add_argument('--tickers', type=str, nargs='+', required=True,
                        help='Stock tickers to backtest (e.g., RELIANCE.NS TCS.NS)')
    parser.add_argument('--start', type=str, required=True,
                        help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, required=True,
                        help='End date (YYYY-MM-DD)')
    parser.add_argument('--cash', type=float, default=100000,
                        help='Initial cash (default: 100000)')
    parser.add_argument('--commission', type=float, default=0.001,
                        help='Commission rate (default: 0.001 = 0.1%%)')
    parser.add_argument('--save', action='store_true',
                        help='Save results to file')

    args = parser.parse_args()

    # Map strategy names to classes
    strategy_map = {
        'rhs': RHSPatternStrategy,
        'cwh': CWHPatternStrategy,
        'fundamental': FundamentalScreenStrategy,
        'multibagger': MultibaggerScreenStrategy,
    }

    # Initialize engine
    engine = BacktestEngine(initial_cash=args.cash, commission=args.commission)

    # Run backtest
    strategy_class = strategy_map[args.strategy]
    results = engine.run_backtest(
        strategy_class=strategy_class,
        tickers=args.tickers,
        start_date=args.start,
        end_date=args.end
    )

    # Save results if requested
    if args.save and results:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{args.strategy}_{timestamp}.json"
        engine.save_results(results, filename)


if __name__ == '__main__':
    # Example usage
    print("Algorithmic Trading Backtest Engine")
    print("Run with --help for usage information\n")

    # Run example backtest if no args provided
    import sys
    if len(sys.argv) == 1:
        print("Running example backtest...")

        engine = BacktestEngine(initial_cash=100000)

        # Example: RHS Strategy on Indian stocks
        results = engine.run_backtest(
            strategy_class=RHSPatternStrategy,
            tickers=['RELIANCE.NS'],
            start_date='2023-01-01',
            end_date='2024-12-31',
            strategy_params={'print_log': False}  # Reduce verbosity
        )

        # Save results
        if results:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            engine.save_results(results, f'example_rhs_{timestamp}.json')
    else:
        main()
