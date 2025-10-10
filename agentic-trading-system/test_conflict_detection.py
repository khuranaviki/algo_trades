#!/usr/bin/env python3
"""
Test Conflict Detection and Technical Signal Requirements

Tests:
1. Conflict detection between agents
2. Technical signal validation (pattern or indicator)
3. Pattern-based target price calculation
4. Strict BUY rule: Only with clear technical signal
"""

import asyncio
import logging
import json

logging.basicConfig(level=logging.INFO)

from agents.orchestrator import Orchestrator

async def test_conflict_detection():
    print("="*80)
    print("  TESTING CONFLICT DETECTION & TECHNICAL SIGNAL REQUIREMENTS")
    print("="*80)

    # Configuration with hybrid LLMs
    config = {
        'weights': {
            'fundamental': 0.25,
            'technical': 0.20,
            'sentiment': 0.20,
            'management': 0.15,
            'market_regime': 0.10,
            'risk_adjustment': 0.10
        },
        'buy_threshold': 70.0,
        'strong_buy_threshold': 85.0,
        'sell_threshold': 40.0,
        'max_position_size': 0.05,
        'initial_capital': 100000,

        # Agent configs with LLMs enabled
        'fundamental_config': {
            'use_perplexity': True,
            'use_llm': True,
            'llm_provider': 'openai',
            'llm_model': 'gpt-4-turbo'
        },
        'technical_config': {
            'detect_patterns': True
        },
        'backtest_config': {
            'historical_years': 5,
            'min_win_rate': 70.0
        },
        'sentiment_config': {
            'news_lookback_days': 30,
            'use_perplexity': True
        },
        'management_config': {
            'quarters_to_analyze': 4,
            'use_llm': True
        }
    }

    orchestrator = Orchestrator(config)

    # Test with HDFC Bank (likely has fundamental-technical conflict)
    ticker = 'HDFCBANK.NS'
    company_name = 'HDFC Bank'

    print(f"\n🎯 Analyzing: {ticker} ({company_name})")
    print("="*80)

    result = await orchestrator.analyze(ticker, {
        'company_name': company_name,
        'market_regime': 'neutral'
    })

    # Display results
    print(f"\n{'='*80}")
    print(f"  FINAL DECISION: {result['decision']}")
    print(f"{'='*80}")

    print(f"\n📊 COMPOSITE SCORE: {result['composite_score']:.2f}/100")
    print(f"🎯 CONFIDENCE: {result['confidence']:.1f}%")

    # Agent scores
    print(f"\n📈 AGENT SCORES:")
    for agent, score in result['agent_scores'].items():
        print(f"  • {agent.capitalize()}: {score:.1f}/100")

    # Conflict analysis
    conflict = result.get('conflict_analysis', {})
    print(f"\n⚠️  CONFLICT ANALYSIS:")
    print(f"  • Has Conflict: {conflict.get('has_conflict', False)}")
    print(f"  • Conflict Level: {conflict.get('conflict_level', 'none')}")
    print(f"  • Score Variance: {conflict.get('variance', 0):.3f}")
    print(f"  • Std Deviation: {conflict.get('std_dev', 0):.2f}")
    print(f"  • Mean Score: {conflict.get('mean_score', 0):.2f}")

    if conflict.get('disagreements'):
        print(f"\n  🔥 DISAGREEMENTS:")
        for d in conflict['disagreements']:
            agents = d['agents']
            diff = d['difference']
            scores = d['scores']
            print(f"    • {agents[0]} ({scores[agents[0]]:.1f}) vs "
                  f"{agents[1]} ({scores[agents[1]]:.1f}) = {diff:.1f} point gap")

    # Technical signal analysis
    tech_signal = result.get('technical_signal', {})
    print(f"\n🎯 TECHNICAL SIGNAL ANALYSIS:")
    print(f"  • Has Signal: {tech_signal.get('has_signal', False)}")
    print(f"  • Signal Type: {tech_signal.get('signal_type', 'None')}")
    print(f"  • Signal Strength: {tech_signal.get('signal_strength', 'N/A')}")

    if tech_signal.get('details'):
        details = tech_signal['details']

        if 'pattern' in details:
            pattern = details['pattern']
            print(f"\n  📊 PATTERN DETECTED:")
            print(f"    • Name: {pattern.get('name', 'N/A')}")
            print(f"    • Confidence: {pattern.get('confidence', 0):.1f}%")
            if pattern.get('target'):
                print(f"    • Pattern Target: ₹{pattern['target']:.2f}")

        if 'indicators' in details:
            print(f"\n  📈 BULLISH INDICATORS:")
            for indicator in details['indicators']:
                print(f"    • {indicator}")

    # Vetoes and warnings
    if result.get('vetoes'):
        print(f"\n🚫 VETOES:")
        for veto in result['vetoes']:
            print(f"  • {veto}")

    if result.get('warnings'):
        print(f"\n⚠️  WARNINGS:")
        for warning in result['warnings']:
            print(f"  • {warning}")

    # Position details (if BUY)
    if result['decision'] in ['BUY', 'STRONG BUY']:
        print(f"\n💰 POSITION DETAILS:")
        print(f"  • Position Size: {result['position_size']*100:.2f}% of portfolio")
        if result.get('stop_loss'):
            print(f"  • Stop Loss: ₹{result['stop_loss']:.2f}")
        if result.get('target_price'):
            print(f"  • Target Price: ₹{result['target_price']:.2f}")

            # Calculate R:R ratio
            current_price = result['technical_analysis'].get('indicators', {}).get('price', {}).get('current', 0)
            if current_price and result.get('stop_loss'):
                risk = current_price - result['stop_loss']
                reward = result['target_price'] - current_price
                rr_ratio = reward / risk if risk > 0 else 0
                print(f"  • Risk-Reward Ratio: {rr_ratio:.2f}:1")

    # Decision factors
    print(f"\n📝 KEY FACTORS:")
    for factor in result.get('factors', []):
        print(f"  • {factor}")

    print(f"\n💡 SUMMARY:")
    print(f"  {result['summary']}")

    # Execution time
    print(f"\n⏱️  Execution Time: {result['execution_time_seconds']:.2f}s")

    print(f"\n{'='*80}")
    print("  TEST COMPLETE")
    print(f"{'='*80}\n")

    return result


if __name__ == '__main__':
    result = asyncio.run(test_conflict_detection())

    # Pretty print full result to JSON file
    with open('conflict_detection_result.json', 'w') as f:
        json.dump(result, f, indent=2, default=str)
    print("\n✅ Full result saved to: conflict_detection_result.json")
