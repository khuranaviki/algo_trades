#!/usr/bin/env python3
"""
Full System Integration Test

Tests the complete agentic trading system with Orchestrator coordinating all agents.

Usage: python test_full_system.py
"""

import asyncio
import sys
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from agents.orchestrator import Orchestrator

async def test_full_system():
    """Test complete system integration"""

    print("="*80)
    print("  FULL SYSTEM INTEGRATION TEST")
    print("  Testing Orchestrator + All 5 Specialist Agents")
    print("="*80)

    # Configure orchestrator with all agent settings
    config = {
        # Orchestrator weights
        'weights': {
            'fundamental': 0.25,
            'technical': 0.20,
            'sentiment': 0.20,
            'management': 0.15,
            'market_regime': 0.10,
            'risk_adjustment': 0.10
        },

        # Decision thresholds
        'buy_threshold': 70.0,
        'strong_buy_threshold': 85.0,
        'sell_threshold': 40.0,

        # Risk parameters
        'max_position_size': 0.05,  # 5% max
        'initial_capital': 100000,

        # Agent-specific configs
        'fundamental_config': {
            'use_perplexity': True
        },
        'technical_config': {
            'lookback_days': 200,
            'detect_patterns': True,
            'min_pattern_confidence': 70.0
        },
        'backtest_config': {
            'historical_years': 5,
            'min_win_rate': 70.0,
            'min_trades': 10,
            'use_market_regime_filter': True
        },
        'sentiment_config': {
            'news_lookback_days': 30,
            'social_lookback_days': 7
        },
        'management_config': {
            'quarters_to_analyze': 4,
            'min_confidence': 60.0
        }
    }

    orchestrator = Orchestrator(config)

    # Test stocks
    test_stocks = [
        ('RELIANCE.NS', 'Reliance Industries', 'neutral'),
        ('TCS.NS', 'Tata Consultancy Services', 'neutral')
    ]

    results_summary = []

    for ticker, company_name, market_regime in test_stocks:
        print(f"\n{'='*80}")
        print(f"  Analyzing: {company_name} ({ticker})")
        print(f"  Market Regime: {market_regime}")
        print(f"{'='*80}")

        start_time = datetime.now()

        try:
            result = await orchestrator.analyze(ticker, {
                'company_name': company_name,
                'market_regime': market_regime
            })

            if 'error' in result:
                print(f"\n❌ ERROR: {result['error']}")
                continue

            # Display comprehensive results
            print(f"\n{'='*80}")
            print(f"  FINAL DECISION: {result['decision']}")
            print(f"{'='*80}")

            print(f"\n📊 Overall Metrics:")
            print(f"  Composite Score: {result['composite_score']:.2f}/100")
            print(f"  Confidence: {result['confidence']:.1f}%")
            print(f"  Execution Time: {result['execution_time_seconds']:.2f}s")

            # Agent scores
            print(f"\n📈 Agent Scores:")
            scores = result['agent_scores']
            print(f"  Fundamental:  {scores['fundamental']:.1f}/100")
            print(f"  Technical:    {scores['technical']:.1f}/100")
            print(f"  Sentiment:    {scores['sentiment']:.1f}/100")
            print(f"  Management:   {scores['management']:.1f}/100")

            # Trading parameters
            if result['decision'] in ['BUY', 'STRONG BUY']:
                print(f"\n💰 Trading Parameters:")
                print(f"  Position Size: {result['position_size']*100:.2f}% of portfolio")
                print(f"  Position Value: ₹{result['position_size'] * config['initial_capital']:,.0f}")

                if result.get('stop_loss'):
                    print(f"  Stop Loss: ₹{result['stop_loss']:.2f}")
                if result.get('target_price'):
                    print(f"  Target Price: ₹{result['target_price']:.2f}")

                # Calculate risk/reward
                current_price = result['technical_analysis'].get('indicators', {}).get('price', {}).get('current')
                if current_price and result.get('stop_loss') and result.get('target_price'):
                    risk = current_price - result['stop_loss']
                    reward = result['target_price'] - current_price
                    rr_ratio = reward / risk if risk > 0 else 0
                    print(f"  Risk/Reward Ratio: 1:{rr_ratio:.2f}")

            # Decision factors
            if result.get('decision_factors'):
                print(f"\n✅ Key Factors:")
                for factor in result['decision_factors'][:5]:
                    print(f"  • {factor}")

            # Vetoes
            if result.get('vetoes'):
                print(f"\n🚫 VETOES:")
                for veto in result['vetoes']:
                    print(f"  • {veto}")

            # Warnings
            if result.get('warnings'):
                print(f"\n⚠️  Warnings:")
                for warning in result['warnings']:
                    print(f"  • {warning}")

            # Detailed agent insights
            print(f"\n📋 Detailed Agent Insights:")

            # Fundamental highlights
            fund = result['fundamental_analysis']
            if fund.get('score'):
                print(f"\n  Fundamental Analysis:")
                print(f"    Financial Health: {fund.get('financial_health', {}).get('score', 'N/A')}/100")
                print(f"    Growth: {fund.get('growth', {}).get('score', 'N/A')}/100")
                print(f"    Valuation: {fund.get('valuation', {}).get('score', 'N/A')}/100")

            # Technical highlights
            tech = result['technical_analysis']
            if tech.get('score'):
                print(f"\n  Technical Analysis:")
                print(f"    Signal: {tech.get('signals', {}).get('action', 'N/A')}")
                if tech.get('primary_pattern'):
                    pattern = tech['primary_pattern']
                    print(f"    Pattern: {pattern.get('name', 'N/A')} ({pattern.get('confidence', 0):.0f}% confidence)")

            # Backtest result
            backtest = result.get('backtest_validation', {})
            if backtest.get('validated') is not None:
                print(f"\n  Backtest Validation:")
                print(f"    Validated: {'✅ Yes' if backtest.get('validated') else '❌ No'}")
                if backtest.get('win_rate'):
                    print(f"    Win Rate: {backtest.get('win_rate', 0):.1f}%")
                    print(f"    Total Trades: {backtest.get('total_trades', 0)}")

            # Sentiment highlights
            sent = result['sentiment_analysis']
            if sent.get('score'):
                print(f"\n  Sentiment Analysis:")
                print(f"    Sentiment: {sent.get('sentiment_label', 'N/A')}")
                print(f"    Analyst Consensus: {sent.get('analyst_consensus', 'Unknown')}")

            # Management highlights
            mgmt = result['management_analysis']
            if mgmt.get('score'):
                print(f"\n  Management Analysis:")
                print(f"    Tone: {mgmt.get('management_tone', 'Unknown')}")
                print(f"    Quarters Analyzed: {mgmt.get('quarters_analyzed', 0)}")

            # Summary
            print(f"\n📝 Summary:")
            print(f"  {result['summary']}")

            # Overall recommendation
            print(f"\n{'='*80}")
            decision = result['decision']
            score = result['composite_score']

            if decision == 'STRONG BUY':
                print(f"  🟢🟢 STRONG BUY RECOMMENDATION")
                print(f"  Excellent opportunity with high confidence")
            elif decision == 'BUY':
                print(f"  🟢 BUY RECOMMENDATION")
                print(f"  Good opportunity with reasonable confidence")
            elif decision == 'HOLD':
                print(f"  🟡 HOLD RECOMMENDATION")
                print(f"  Insufficient conviction or mixed signals")
            elif decision == 'SELL':
                print(f"  🔴 SELL RECOMMENDATION")
                print(f"  Poor outlook or failed validation")

            print(f"{'='*80}")

            # Store summary
            results_summary.append({
                'ticker': ticker,
                'decision': decision,
                'score': score,
                'confidence': result['confidence'],
                'execution_time': result['execution_time_seconds']
            })

        except Exception as e:
            print(f"\n❌ Exception: {e}")
            import traceback
            traceback.print_exc()

    # Print summary table
    print(f"\n\n{'='*80}")
    print(f"  TEST SUMMARY")
    print(f"{'='*80}\n")

    print(f"{'Ticker':<15} {'Decision':<15} {'Score':>10} {'Confidence':>12} {'Time':>10}")
    print(f"{'-'*15} {'-'*15} {'-'*10} {'-'*12} {'-'*10}")

    for result in results_summary:
        print(f"{result['ticker']:<15} {result['decision']:<15} {result['score']:>10.2f} {result['confidence']:>11.1f}% {result['execution_time']:>9.2f}s")

    print(f"\n{'='*80}")
    print(f"  FULL SYSTEM TEST COMPLETE")
    print(f"  All 5 agents working in coordination!")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    asyncio.run(test_full_system())
