#!/usr/bin/env python3
"""
Example backtests demonstrating all strategies
Run this to quickly test the system
"""

from backtest_engine import BacktestEngine
from strategies.rhs_strategy import RHSPatternStrategy
from strategies.cwh_strategy import CWHPatternStrategy
from strategies.fundamental_screen_strategy import FundamentalScreenStrategy, MultibaggerScreenStrategy
from datetime import datetime, timedelta
import config


def run_all_examples():
    """Run example backtests for all strategies"""

    print("\n" + "="*100)
    print("🚀 RUNNING EXAMPLE BACKTESTS FOR ALL STRATEGIES")
    print("="*100)

    # Initialize engine
    engine = BacktestEngine(initial_cash=config.INITIAL_CASH, commission=config.COMMISSION_RATE)

    # Date range: Last 2 years
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')

    results_list = []

    # ========================================================================
    # Example 1: RHS Strategy on Blue Chip Stock
    # ========================================================================
    print("\n" + "="*100)
    print("Example 1: RHS Pattern Strategy on RELIANCE.NS")
    print("="*100)

    results = engine.run_backtest(
        strategy_class=RHSPatternStrategy,
        tickers=['RELIANCE.NS'],
        start_date=start_date,
        end_date=end_date,
        strategy_params={'print_log': False}
    )

    if results:
        results_list.append(results)
        engine.save_results(results, 'example_rhs_reliance.json')

    # ========================================================================
    # Example 2: CWH Strategy on IT Stock
    # ========================================================================
    print("\n" + "="*100)
    print("Example 2: CWH Pattern Strategy on TCS.NS")
    print("="*100)

    results = engine.run_backtest(
        strategy_class=CWHPatternStrategy,
        tickers=['TCS.NS'],
        start_date=start_date,
        end_date=end_date,
        strategy_params={'print_log': False}
    )

    if results:
        results_list.append(results)
        engine.save_results(results, 'example_cwh_tcs.json')

    # ========================================================================
    # Example 3: Fundamental Screening on Multiple Stocks
    # ========================================================================
    print("\n" + "="*100)
    print("Example 3: Fundamental Screening Strategy on Multiple Stocks")
    print("="*100)

    # Note: For fundamental strategy, we would ideally pass fundamental_data
    # For this example, we'll run without it (will default to technical-only)
    results = engine.run_backtest(
        strategy_class=FundamentalScreenStrategy,
        tickers=['INFY.NS', 'WIPRO.NS', 'HCLTECH.NS'],
        start_date=start_date,
        end_date=end_date,
        strategy_params={'print_log': False}
    )

    if results:
        results_list.append(results)
        engine.save_results(results, 'example_fundamental_it_stocks.json')

    # ========================================================================
    # Example 4: Multibagger Strategy on Small/Mid Cap
    # ========================================================================
    print("\n" + "="*100)
    print("Example 4: Multibagger Strategy on DELHIVERY.NS")
    print("="*100)

    results = engine.run_backtest(
        strategy_class=MultibaggerScreenStrategy,
        tickers=['DELHIVERY.NS'],
        start_date='2022-05-24',  # Delhivery IPO date
        end_date=end_date,
        strategy_params={'print_log': False}
    )

    if results:
        results_list.append(results)
        engine.save_results(results, 'example_multibagger_delhivery.json')

    # ========================================================================
    # Example 5: RHS Strategy on Multiple Stocks (Portfolio)
    # ========================================================================
    print("\n" + "="*100)
    print("Example 5: RHS Strategy Portfolio (Multiple Stocks)")
    print("="*100)

    results = engine.run_backtest(
        strategy_class=RHSPatternStrategy,
        tickers=['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS'],
        start_date=start_date,
        end_date=end_date,
        strategy_params={'print_log': False}
    )

    if results:
        results_list.append(results)
        engine.save_results(results, 'example_rhs_portfolio.json')

    # ========================================================================
    # Summary Comparison
    # ========================================================================
    if results_list:
        print("\n" + "="*100)
        print("📊 STRATEGY COMPARISON SUMMARY")
        print("="*100)

        from utils.performance_analyzer import PerformanceAnalyzer
        analyzer = PerformanceAnalyzer()

        comparison_df = analyzer.compare_strategies(results_list)
        analyzer.print_comparison(comparison_df)

        # Generate report for best strategy
        best_result = max(results_list, key=lambda x: x.get('total_return', 0))
        report = analyzer.generate_report(best_result)
        analyzer.save_report(report, 'best_strategy_report.txt')

    print("\n" + "="*100)
    print("✅ ALL EXAMPLE BACKTESTS COMPLETED")
    print("="*100)
    print("\n📁 Results saved in: backtest_results/")
    print("📊 View individual JSON files for detailed results")
    print("📈 Best strategy report: backtest_results/best_strategy_report.txt")
    print("\n🎯 Next steps:")
    print("   1. Review the results in backtest_results/ directory")
    print("   2. Adjust strategy parameters in config.py")
    print("   3. Run custom backtests using backtest_engine.py")
    print("   4. Test on your own stock picks\n")


if __name__ == '__main__':
    run_all_examples()
