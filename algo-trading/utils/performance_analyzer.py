#!/usr/bin/env python3
"""
Performance analysis utilities for backtesting results
"""

import pandas as pd
import numpy as np
from typing import Dict, List
import json
import os


class PerformanceAnalyzer:
    """
    Analyze and compare backtest performance across strategies
    """

    def __init__(self):
        """Initialize performance analyzer"""
        self.results = []

    def load_results(self, filepath: str) -> Dict:
        """Load backtest results from JSON file"""
        try:
            with open(filepath, 'r') as f:
                results = json.load(f)
            self.results.append(results)
            return results
        except Exception as e:
            print(f"❌ Error loading results: {e}")
            return {}

    def load_all_results(self, directory: str = 'backtest_results') -> List[Dict]:
        """Load all backtest results from directory"""
        results = []

        if not os.path.exists(directory):
            print(f"❌ Directory not found: {directory}")
            return results

        for filename in os.listdir(directory):
            if filename.endswith('.json'):
                filepath = os.path.join(directory, filename)
                result = self.load_results(filepath)
                if result:
                    results.append(result)

        print(f"✅ Loaded {len(results)} backtest results")
        return results

    def calculate_metrics(self, results: Dict) -> Dict:
        """Calculate additional performance metrics"""
        metrics = {
            'profit_factor': 0,
            'avg_win': 0,
            'avg_loss': 0,
            'expectancy': 0,
        }

        # Calculate profit factor (gross profit / gross loss)
        if results.get('lost_trades', 0) > 0:
            won = results.get('won_trades', 0)
            lost = results.get('lost_trades', 0)
            total = results.get('total_trades', 1)

            # Simplified calculation (would need individual trade data for exact)
            avg_win = results.get('total_return', 0) / max(won, 1) if won > 0 else 0
            avg_loss = -avg_win * 0.5  # Assumed

            metrics['avg_win'] = avg_win
            metrics['avg_loss'] = avg_loss

            if avg_loss != 0:
                metrics['profit_factor'] = abs(avg_win / avg_loss)

            # Expectancy = (Win% * Avg Win) - (Loss% * Avg Loss)
            win_pct = won / total if total > 0 else 0
            loss_pct = lost / total if total > 0 else 0

            metrics['expectancy'] = (win_pct * avg_win) + (loss_pct * avg_loss)

        return metrics

    def compare_strategies(self, results_list: List[Dict]) -> pd.DataFrame:
        """
        Compare multiple strategy results

        Args:
            results_list: List of backtest result dictionaries

        Returns:
            DataFrame with comparison
        """
        comparison_data = []

        for result in results_list:
            metrics = self.calculate_metrics(result)

            comparison_data.append({
                'Strategy': result.get('strategy', 'Unknown'),
                'Tickers': ', '.join(result.get('tickers', [])),
                'Total Return (%)': result.get('total_return', 0),
                'Sharpe Ratio': result.get('sharpe_ratio', 0),
                'Max Drawdown (%)': result.get('max_drawdown', 0),
                'Win Rate (%)': result.get('win_rate', 0),
                'Total Trades': result.get('total_trades', 0),
                'Profit Factor': metrics.get('profit_factor', 0),
                'Expectancy': metrics.get('expectancy', 0),
            })

        df = pd.DataFrame(comparison_data)

        # Sort by total return
        df = df.sort_values('Total Return (%)', ascending=False)

        return df

    def print_comparison(self, df: pd.DataFrame):
        """Print formatted comparison table"""
        print("\n" + "="*100)
        print("STRATEGY COMPARISON")
        print("="*100)
        print(df.to_string(index=False))
        print("="*100 + "\n")

    def generate_report(self, results: Dict) -> str:
        """Generate detailed text report for single backtest"""
        metrics = self.calculate_metrics(results)

        report = f"""
{'='*80}
BACKTEST PERFORMANCE REPORT
{'='*80}

Strategy:           {results.get('strategy', 'Unknown')}
Tickers:            {', '.join(results.get('tickers', []))}
Period:             {results.get('start_date', 'N/A')} to {results.get('end_date', 'N/A')}

PORTFOLIO PERFORMANCE
{'─'*80}
Initial Cash:       ₹{results.get('initial_cash', 0):,.2f}
Final Value:        ₹{results.get('final_value', 0):,.2f}
Total Return:       {results.get('total_return', 0):.2f}%
Sharpe Ratio:       {results.get('sharpe_ratio', 0):.2f}
Max Drawdown:       {results.get('max_drawdown', 0):.2f}%

TRADING STATISTICS
{'─'*80}
Total Trades:       {results.get('total_trades', 0)}
Won Trades:         {results.get('won_trades', 0)}
Lost Trades:        {results.get('lost_trades', 0)}
Win Rate:           {results.get('win_rate', 0):.2f}%

CALCULATED METRICS
{'─'*80}
Profit Factor:      {metrics.get('profit_factor', 0):.2f}
Average Win:        {metrics.get('avg_win', 0):.2f}%
Average Loss:       {metrics.get('avg_loss', 0):.2f}%
Expectancy:         {metrics.get('expectancy', 0):.2f}%

{'='*80}
"""
        return report

    def save_report(self, report: str, filename: str):
        """Save report to file"""
        filepath = os.path.join('backtest_results', filename)
        os.makedirs('backtest_results', exist_ok=True)

        with open(filepath, 'w') as f:
            f.write(report)

        print(f"✅ Report saved to: {filepath}")


# Example usage
if __name__ == '__main__':
    analyzer = PerformanceAnalyzer()

    # Load all results
    results = analyzer.load_all_results('backtest_results')

    if results:
        # Generate comparison
        comparison_df = analyzer.compare_strategies(results)
        analyzer.print_comparison(comparison_df)

        # Generate individual report for best strategy
        best_result = max(results, key=lambda x: x.get('total_return', 0))
        report = analyzer.generate_report(best_result)
        print(report)

        # Save report
        analyzer.save_report(report, 'best_strategy_report.txt')
    else:
        print("No backtest results found. Run backtests first using backtest_engine.py")
