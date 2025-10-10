"""
Backtest Validator Agent

Critical agent that validates technical strategies have 70%+ historical win rates.
Uses 5-year historical data to ensure patterns are statistically significant.

VETO POWER: If win rate < 70%, the trade is REJECTED.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
import logging

from agents.base_agent import BaseAgent
from tools.data_fetchers.market_data import MarketDataFetcher
from tools.caching.cache_client import CacheClient
from tools.storage.database import DatabaseClient


class BacktestValidator(BaseAgent):
    """
    Validates technical patterns using historical backtesting

    Core responsibility: Ensure strategy has 70%+ win rate over 5 years

    Process:
    1. Get 5 years of historical data
    2. Simulate pattern detection + entries
    3. Calculate win rate, avg return, sharpe, drawdown
    4. Cache results for 90 days
    5. Return VALIDATED or NOT_VALIDATED
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Backtest Validator

        Args:
            config: Configuration dict with backtest settings
        """
        super().__init__("Backtest Validator", config)

        self.market_data = MarketDataFetcher()
        self.cache = CacheClient()
        self.db = DatabaseClient()

        # Backtest settings
        self.historical_years = config.get('historical_years', 5)
        self.min_win_rate = config.get('min_win_rate', 70.0)
        self.min_trades = config.get('min_trades', 10)
        self.min_sharpe = config.get('min_sharpe', 1.0)
        self.max_drawdown = config.get('max_drawdown', -30.0)
        self.initial_capital = config.get('initial_capital', 100000)
        self.position_size = config.get('position_size', 0.05)  # 5%

        # Market regime filter (from V40)
        self.use_market_filter = config.get('use_market_regime_filter', True)
        self.market_index = config.get('market_index', '^NSEI')
        self.market_sma_period = config.get('market_sma_period', 50)

    async def analyze(self, ticker: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate technical pattern using historical backtest

        Args:
            ticker: Stock ticker
            context: Dict with pattern info and market data

        Returns:
            Dict with validation results
        """
        if not self.validate_input(ticker):
            return self._error_response(ticker, "Invalid ticker")

        pattern = context.get('pattern')
        strategy = context.get('strategy')

        if not pattern and not strategy:
            return self._error_response(ticker, "No pattern or strategy provided")

        self.logger.info(f"Validating {strategy or pattern} for {ticker}")

        # Check cache first (90-day TTL)
        cache_key = f"{ticker}:{strategy or pattern}"
        cached_result = self.cache.get_backtest_result(ticker, strategy or pattern)

        if cached_result:
            self.logger.info(f"Cache HIT: Backtest for {cache_key}")
            return self._format_cached_result(cached_result)

        # Cache miss - run backtest
        self.logger.info(f"Cache MISS: Running backtest for {cache_key}")

        # Get historical data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.historical_years * 365)

        hist_data = self.market_data.get_historical_data_range(
            ticker,
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d")
        )

        if hist_data.empty:
            return self._error_response(ticker, "No historical data available")

        # Get market regime data if enabled
        market_data = None
        if self.use_market_filter:
            market_data = self.market_data.get_historical_data_range(
                self.market_index,
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d")
            )

        # Run backtest simulation
        backtest_results = await self._run_pattern_backtest(
            ticker,
            hist_data,
            pattern or strategy,
            market_data,
            context
        )

        # Validate results
        validation = self._validate_results(backtest_results)

        # Cache results (90 days)
        self.cache.cache_backtest_result(
            ticker,
            strategy or pattern,
            backtest_results,
            ttl=7776000  # 90 days
        )

        # Save to database
        self.db.save_backtest(backtest_results)

        self.analysis_count += 1

        return {
            'agent': self.name,
            'ticker': ticker,
            'strategy': strategy or pattern,
            'validated': validation['validated'],
            'score': validation['score'],
            'win_rate': backtest_results['win_rate'],
            'total_trades': backtest_results['total_trades'],
            'avg_return': backtest_results['avg_return'],
            'sharpe_ratio': backtest_results['sharpe_ratio'],
            'max_drawdown': backtest_results['max_drawdown'],
            'recommendation': validation['recommendation'],
            'concerns': validation['concerns'],
            'details': backtest_results,
            'timestamp': datetime.now().isoformat()
        }

    async def _run_pattern_backtest(
        self,
        ticker: str,
        hist_data: pd.DataFrame,
        pattern: str,
        market_data: Optional[pd.DataFrame],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run backtest simulation for a pattern

        Args:
            ticker: Stock ticker
            hist_data: Historical OHLCV data
            pattern: Pattern name (RHS, CWH, etc.)
            market_data: Optional market index data for regime filter
            context: Additional context

        Returns:
            Dict with backtest results
        """
        trades = []

        # Add market regime filter if available
        if market_data is not None and not market_data.empty:
            hist_data = self._apply_market_regime_filter(hist_data, market_data)

        # Detect pattern occurrences in historical data
        pattern_signals = self._detect_pattern_signals(hist_data, pattern, context)

        if not pattern_signals:
            return self._empty_backtest_result(ticker, pattern, "No patterns found")

        # Simulate trades
        for signal in pattern_signals:
            trade_result = self._simulate_trade(
                hist_data,
                signal,
                self.position_size
            )
            if trade_result:
                trades.append(trade_result)

        # Calculate metrics
        if not trades:
            return self._empty_backtest_result(ticker, pattern, "No valid trades")

        metrics = self._calculate_metrics(trades)

        return {
            'ticker': ticker,
            'strategy': pattern,
            'pattern': pattern,
            'start_date': hist_data.index[0].strftime("%Y-%m-%d"),
            'end_date': hist_data.index[-1].strftime("%Y-%m-%d"),
            'win_rate': metrics['win_rate'],
            'total_trades': metrics['total_trades'],
            'winning_trades': metrics['winning_trades'],
            'losing_trades': metrics['losing_trades'],
            'avg_return': metrics['avg_return'],
            'avg_win': metrics['avg_win'],
            'avg_loss': metrics['avg_loss'],
            'best_trade': metrics['best_trade'],
            'worst_trade': metrics['worst_trade'],
            'sharpe_ratio': metrics['sharpe_ratio'],
            'max_drawdown': metrics['max_drawdown'],
            'profit_factor': metrics['profit_factor'],
            'validated': metrics['win_rate'] >= self.min_win_rate,
            'trades': trades,
            'details': {
                'market_filter_used': self.use_market_filter,
                'historical_years': self.historical_years,
                'position_size': self.position_size
            }
        }

    def _detect_pattern_signals(
        self,
        data: pd.DataFrame,
        pattern: str,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Detect pattern occurrences in historical data

        Args:
            data: Historical OHLCV data
            pattern: Pattern name
            context: Additional context with pattern params

        Returns:
            List of signal dicts with entry points
        """
        signals = []

        pattern_lower = pattern.lower()

        if 'rhs' in pattern_lower or 'rounding_bottom' in pattern_lower:
            signals = self._detect_rhs_pattern(data, context)
        elif 'cwh' in pattern_lower or 'cup_with_handle' in pattern_lower:
            signals = self._detect_cwh_pattern(data, context)
        elif 'golden_cross' in pattern_lower:
            signals = self._detect_golden_cross(data, context)
        else:
            # Generic breakout detection
            signals = self._detect_generic_breakout(data, context)

        self.logger.info(f"Detected {len(signals)} {pattern} signals")
        return signals

    def _detect_rhs_pattern(
        self,
        data: pd.DataFrame,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect Rounding Bottom (RHS) pattern"""
        signals = []
        window = 60  # 60-day rounding bottom

        for i in range(window, len(data) - 10):
            window_data = data.iloc[i-window:i]

            # Simple RHS detection: U-shaped price movement
            if len(window_data) < window:
                continue

            # Find lowest point in middle third
            mid_start = window // 3
            mid_end = 2 * window // 3
            mid_section = window_data.iloc[mid_start:mid_end]

            if mid_section.empty:
                continue

            lowest_price = mid_section['Low'].min()
            current_price = data.iloc[i]['Close']

            # Check if price has recovered 70%+ from low
            recovery = (current_price - lowest_price) / lowest_price

            if recovery >= 0.15:  # 15% recovery from low
                # Check volume surge
                avg_volume = window_data['Volume'].mean()
                recent_volume = data.iloc[i-5:i]['Volume'].mean()

                if recent_volume > avg_volume * 1.5:  # 50% volume increase
                    signals.append({
                        'date': data.index[i],
                        'entry_price': data.iloc[i]['Close'],
                        'pattern_type': 'RHS',
                        'recovery_pct': recovery * 100,
                        'volume_ratio': recent_volume / avg_volume
                    })

        return signals

    def _detect_cwh_pattern(
        self,
        data: pd.DataFrame,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect Cup with Handle pattern"""
        signals = []
        window = 90  # 90-day cup formation

        for i in range(window, len(data) - 20):
            window_data = data.iloc[i-window:i]

            if len(window_data) < window:
                continue

            # Find cup depth
            highest_price = window_data['High'].max()
            lowest_price = window_data['Low'].min()
            depth = (highest_price - lowest_price) / highest_price

            # Cup should be 15-40% deep
            if depth < 0.15 or depth > 0.40:
                continue

            # Check for handle (last 20 days)
            handle_data = data.iloc[i-20:i]
            handle_depth = (handle_data['High'].max() - handle_data['Low'].min()) / handle_data['High'].max()

            # Handle should be shallow (< 15%)
            if handle_depth < 0.15:
                current_price = data.iloc[i]['Close']

                # Check if breaking out of handle
                if current_price >= handle_data['High'].max() * 0.98:
                    signals.append({
                        'date': data.index[i],
                        'entry_price': data.iloc[i]['Close'],
                        'pattern_type': 'CWH',
                        'cup_depth_pct': depth * 100,
                        'handle_depth_pct': handle_depth * 100
                    })

        return signals

    def _detect_golden_cross(
        self,
        data: pd.DataFrame,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect Golden Cross (50 SMA crosses above 200 SMA)"""
        signals = []

        # Calculate SMAs
        data['SMA_50'] = data['Close'].rolling(window=50).mean()
        data['SMA_200'] = data['Close'].rolling(window=200).mean()

        for i in range(201, len(data)):
            prev_below = data.iloc[i-1]['SMA_50'] < data.iloc[i-1]['SMA_200']
            curr_above = data.iloc[i]['SMA_50'] >= data.iloc[i]['SMA_200']

            if prev_below and curr_above:
                signals.append({
                    'date': data.index[i],
                    'entry_price': data.iloc[i]['Close'],
                    'pattern_type': 'GOLDEN_CROSS',
                    'sma_50': data.iloc[i]['SMA_50'],
                    'sma_200': data.iloc[i]['SMA_200']
                })

        return signals

    def _detect_generic_breakout(
        self,
        data: pd.DataFrame,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generic breakout detection (52-week high)"""
        signals = []
        window = 252  # ~1 year

        for i in range(window, len(data)):
            window_data = data.iloc[i-window:i]
            current_price = data.iloc[i]['Close']
            prev_high = window_data['High'].max()

            if current_price >= prev_high * 1.02:  # 2% above previous high
                signals.append({
                    'date': data.index[i],
                    'entry_price': current_price,
                    'pattern_type': 'BREAKOUT',
                    'prev_high': prev_high
                })

        return signals

    def _apply_market_regime_filter(
        self,
        stock_data: pd.DataFrame,
        market_data: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Apply market regime filter (from V40)
        Only allow trades when market is above 50 SMA
        """
        # Calculate market SMA
        market_data['SMA_50'] = market_data['Close'].rolling(window=self.market_sma_period).mean()
        market_data['bullish'] = market_data['Close'] > market_data['SMA_50']

        # Align dates
        stock_data = stock_data.copy()
        stock_data['market_bullish'] = False

        for date in stock_data.index:
            if date in market_data.index:
                stock_data.loc[date, 'market_bullish'] = market_data.loc[date, 'bullish']

        return stock_data

    def _simulate_trade(
        self,
        data: pd.DataFrame,
        signal: Dict[str, Any],
        position_size: float
    ) -> Optional[Dict[str, Any]]:
        """
        Simulate a single trade from entry to exit

        Args:
            data: Historical price data
            signal: Entry signal
            position_size: Position size (% of capital)

        Returns:
            Trade result dict or None
        """
        entry_date = signal['date']
        entry_price = signal['entry_price']

        # Find entry index
        try:
            entry_idx = data.index.get_loc(entry_date)
        except KeyError:
            return None

        # Define exit strategy (no stop loss, time-based exit)
        max_holding_days = 180
        exit_idx = min(entry_idx + max_holding_days, len(data) - 1)

        # Check for profit targets (10%, 20%, 30%)
        actual_exit_idx = entry_idx
        exit_reason = 'TIME'

        for i in range(entry_idx + 1, exit_idx + 1):
            current_price = data.iloc[i]['Close']
            return_pct = (current_price - entry_price) / entry_price * 100

            # Take profit at 30%
            if return_pct >= 30:
                actual_exit_idx = i
                exit_reason = 'TARGET_30'
                break
            # Take profit at 20%
            elif return_pct >= 20:
                actual_exit_idx = i
                exit_reason = 'TARGET_20'
                break
            # Take profit at 10%
            elif return_pct >= 10:
                actual_exit_idx = i
                exit_reason = 'TARGET_10'
                break

        exit_date = data.index[actual_exit_idx]
        exit_price = data.iloc[actual_exit_idx]['Close']

        # Calculate return
        return_pct = (exit_price - entry_price) / entry_price * 100
        holding_days = (exit_date - entry_date).days

        return {
            'entry_date': entry_date.strftime("%Y-%m-%d"),
            'exit_date': exit_date.strftime("%Y-%m-%d"),
            'entry_price': entry_price,
            'exit_price': exit_price,
            'return_pct': return_pct,
            'holding_days': holding_days,
            'exit_reason': exit_reason,
            'winner': return_pct > 0,
            'pattern_type': signal.get('pattern_type', 'UNKNOWN')
        }

    def _calculate_metrics(self, trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate backtest metrics from trades"""

        total_trades = len(trades)
        winners = [t for t in trades if t['winner']]
        losers = [t for t in trades if not t['winner']]

        winning_trades = len(winners)
        losing_trades = len(losers)
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        returns = [t['return_pct'] for t in trades]
        avg_return = np.mean(returns) if returns else 0
        avg_win = np.mean([t['return_pct'] for t in winners]) if winners else 0
        avg_loss = np.mean([t['return_pct'] for t in losers]) if losers else 0

        best_trade = max(returns) if returns else 0
        worst_trade = min(returns) if returns else 0

        # Sharpe ratio (simplified)
        if returns:
            sharpe_ratio = np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
        else:
            sharpe_ratio = 0

        # Max drawdown
        cumulative_returns = np.cumsum(returns)
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdown = cumulative_returns - running_max
        max_drawdown = np.min(drawdown) if len(drawdown) > 0 else 0

        # Profit factor
        total_wins = sum([t['return_pct'] for t in winners])
        total_losses = abs(sum([t['return_pct'] for t in losers]))
        profit_factor = total_wins / total_losses if total_losses > 0 else 0

        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': round(win_rate, 2),
            'avg_return': round(avg_return, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'best_trade': round(best_trade, 2),
            'worst_trade': round(worst_trade, 2),
            'sharpe_ratio': round(sharpe_ratio, 2),
            'max_drawdown': round(max_drawdown, 2),
            'profit_factor': round(profit_factor, 2)
        }

    def _validate_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate backtest results against thresholds

        Returns:
            Dict with validation decision
        """
        concerns = []
        score = 100

        # Check win rate (CRITICAL)
        if results['win_rate'] < self.min_win_rate:
            concerns.append(f"Win rate {results['win_rate']}% < {self.min_win_rate}%")
            score -= 40

        # Check minimum trades
        if results['total_trades'] < self.min_trades:
            concerns.append(f"Only {results['total_trades']} trades (need {self.min_trades})")
            score -= 20

        # Check Sharpe ratio (if available)
        if 'sharpe_ratio' in results and results['sharpe_ratio'] < self.min_sharpe:
            concerns.append(f"Sharpe {results['sharpe_ratio']:.2f} < {self.min_sharpe}")
            score -= 20

        # Check max drawdown (if available)
        if 'max_drawdown' in results and results['max_drawdown'] < self.max_drawdown:
            concerns.append(f"Max drawdown {results['max_drawdown']:.1f}% exceeds {self.max_drawdown}%")
            score -= 20

        validated = len(concerns) == 0 or (results['win_rate'] >= self.min_win_rate and results['total_trades'] >= self.min_trades)

        return {
            'validated': validated,
            'score': max(0, score),
            'concerns': concerns,
            'recommendation': 'VALIDATED' if validated else 'NOT_VALIDATED'
        }

    def _empty_backtest_result(self, ticker: str, pattern: str, reason: str) -> Dict[str, Any]:
        """Return empty backtest result"""
        return {
            'ticker': ticker,
            'strategy': pattern,
            'pattern': pattern,
            'start_date': None,
            'end_date': None,
            'win_rate': 0,
            'total_trades': 0,
            'validated': False,
            'error': reason,
            'details': {}
        }

    def _format_cached_result(self, cached: Dict[str, Any]) -> Dict[str, Any]:
        """Format cached result for response"""
        validation = self._validate_results(cached)

        return {
            'agent': self.name,
            'ticker': cached['ticker'],
            'strategy': cached['strategy'],
            'validated': validation['validated'],
            'score': validation['score'],
            'win_rate': cached['win_rate'],
            'total_trades': cached['total_trades'],
            'avg_return': cached.get('avg_return', 0),
            'sharpe_ratio': cached.get('sharpe_ratio', 0),
            'max_drawdown': cached.get('max_drawdown', 0),
            'recommendation': validation['recommendation'],
            'concerns': validation['concerns'],
            'details': cached,
            'cached': True,
            'timestamp': datetime.now().isoformat()
        }

    def _error_response(self, ticker: str, error: str) -> Dict[str, Any]:
        """Return error response"""
        return {
            'agent': self.name,
            'ticker': ticker,
            'validated': False,
            'score': 0,
            'error': error,
            'recommendation': 'ERROR',
            'timestamp': datetime.now().isoformat()
        }


# Example usage
async def main():
    """Example backtest validation"""

    config = {
        'historical_years': 5,
        'min_win_rate': 70.0,
        'min_trades': 10,
        'use_market_regime_filter': True,
        'market_index': '^NSEI'
    }

    validator = BacktestValidator(config)

    # Test RHS pattern on Reliance
    context = {
        'pattern': 'RHS',
        'strategy': 'rhs_breakout',
        'formation_days': 60
    }

    result = await validator.analyze('RELIANCE.NS', context)

    print("\n" + "="*80)
    print("BACKTEST VALIDATION RESULT")
    print("="*80)
    print(f"Ticker: {result['ticker']}")
    print(f"Strategy: {result['strategy']}")
    print(f"Validated: {'✅ YES' if result['validated'] else '❌ NO'}")
    print(f"Win Rate: {result['win_rate']}%")
    print(f"Total Trades: {result['total_trades']}")
    print(f"Avg Return: {result['avg_return']}%")
    print(f"Sharpe Ratio: {result['sharpe_ratio']}")
    print(f"Score: {result['score']}/100")

    if result['concerns']:
        print("\nConcerns:")
        for concern in result['concerns']:
            print(f"  ⚠️  {concern}")


if __name__ == '__main__':
    asyncio.run(main())
