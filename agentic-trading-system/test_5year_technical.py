#!/usr/bin/env python3
"""
5-Year Technical Analysis Test

Tests with full 5-year lookback for technical indicators and patterns.
This provides sufficient history for:
- Proper 200-day MA calculation
- Full pattern formation visibility
- Seasonal trend analysis
- Multi-quarter pattern detection
"""

import asyncio
import sys
import logging
from datetime import datetime
import json
from typing import Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from agents.orchestrator import Orchestrator

# Test on 5 high-quality stocks to verify improvements
TEST_STOCKS = [
    ('RELIANCE.NS', 'Reliance Industries'),
    ('TCS.NS', 'Tata Consultancy Services'),
    ('HDFCBANK.NS', 'HDFC Bank'),
    ('INFY.NS', 'Infosys'),
    ('BAJFINANCE.NS', 'Bajaj Finance'),
]


async def analyze_with_5year_data(
    orchestrator: Orchestrator,
    ticker: str,
    company_name: str,
    index: int,
    total: int
) -> Dict[str, Any]:
    """Analyze single stock with detailed output"""

    print(f"\n{'='*80}")
    print(f"[{index}/{total}] {ticker} - {company_name}")
    print(f"{'='*80}")

    try:
        result = await orchestrator.analyze(ticker, {
            'company_name': company_name,
            'market_regime': 'neutral'
        })

        # Print comprehensive breakdown
        print(f"\n📊 AGENT SCORES:")
        agent_scores = result.get('agent_scores', {})
        print(f"  Fundamental:  {agent_scores.get('fundamental', 0):.1f}/100")
        print(f"  Technical:    {agent_scores.get('technical', 0):.1f}/100")
        print(f"  Sentiment:    {agent_scores.get('sentiment', 0):.1f}/100")
        print(f"  Management:   {agent_scores.get('management', 0):.1f}/100")

        # Technical signal details
        tech_signal = result.get('technical_signal', {})
        print(f"\n🎯 TECHNICAL SIGNAL:")
        print(f"  Has Signal: {'✅ YES' if tech_signal.get('has_signal') else '❌ NO'}")
        print(f"  Type: {tech_signal.get('signal_type', 'none')}")
        print(f"  Strength: {tech_signal.get('signal_strength', 'none')}")

        if tech_signal.get('details'):
            details = tech_signal['details']

            if details.get('pattern'):
                pat = details['pattern']
                print(f"\n  📈 Pattern:")
                print(f"    Name: {pat.get('name', 'N/A')}")
                print(f"    Type: {pat.get('type', 'N/A')}")
                print(f"    Confidence: {pat.get('confidence', 0):.1f}%")
                if pat.get('target_price'):
                    print(f"    Target: ₹{pat.get('target_price'):.2f}")

            if details.get('indicators'):
                ind = details['indicators']
                print(f"\n  📊 Indicators:")
                print(f"    Trend: {ind.get('trend', 'N/A')}")
                print(f"    MA Signal: {ind.get('ma_signal', 'N/A')}")
                print(f"    MACD: {ind.get('macd_signal', 'N/A')}")
                print(f"    RSI: {ind.get('rsi', 0):.1f}")
                print(f"    Bullish Indicators: {ind.get('bullish_count', 0)}/4")

        # Backtest results
        if result.get('backtest'):
            bt = result['backtest']
            print(f"\n  🔬 Backtest:")
            print(f"    Validated: {'✅' if bt.get('validated') else '❌'}")
            print(f"    Win Rate: {bt.get('win_rate', 0):.1f}%")
            print(f"    Avg Return: {bt.get('avg_return_pct', 0):.1f}%")
            if bt.get('total_signals'):
                print(f"    Signals Found: {bt.get('total_signals')}")

        # Conflict analysis
        conflict = result.get('conflict_analysis', {})
        print(f"\n⚔️  CONFLICT:")
        print(f"  Level: {conflict.get('conflict_level', 'none').upper()}")
        print(f"  Variance: {conflict.get('variance', 0):.3f}")
        if conflict.get('disagreements'):
            print(f"  Disagreements: {len(conflict['disagreements'])}")

        # LLM synthesis
        used_llm = result.get('used_llm_synthesis', False)
        if used_llm:
            llm_synth = result.get('llm_synthesis', {})
            print(f"\n🤖 LLM SYNTHESIS:")
            print(f"  Recommendation: {llm_synth.get('final_recommendation', 'N/A')}")
            print(f"  Confidence: {llm_synth.get('confidence', 0)}%")
            if llm_synth.get('key_insights'):
                print(f"  Key Insights:")
                for insight in llm_synth['key_insights'][:2]:
                    print(f"    • {insight}")

        # Final decision
        decision = result.get('decision', 'UNKNOWN')
        score = result.get('composite_score', 0)
        confidence = result.get('confidence', 0)

        print(f"\n⚖️  FINAL DECISION:")
        print(f"  Action: {decision}")
        print(f"  Score: {score:.1f}/100")
        print(f"  Confidence: {confidence:.1f}%")

        vetoes = result.get('vetoes', [])
        if vetoes:
            print(f"\n  ⚠️  Vetoes ({len(vetoes)}):")
            for v in vetoes:
                print(f"    • {v}")

        # Position details if BUY
        if decision in ['BUY', 'STRONG BUY']:
            print(f"\n  💰 Position Details:")
            if result.get('target_price'):
                print(f"    Target: ₹{result['target_price']:.2f}")
            if result.get('stop_loss'):
                print(f"    Stop Loss: ₹{result['stop_loss']:.2f}")
            if result.get('position_size'):
                print(f"    Position Size: {result['position_size']*100:.1f}% of capital")

        print(f"\n{'='*80}\n")

        return result

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


async def test_5year_technical():
    """Test with 5-year technical lookback"""

    print("\n" + "="*80)
    print("  5-YEAR TECHNICAL ANALYSIS TEST")
    print("  Full historical lookback for accurate pattern detection")
    print("="*80)

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

        # 5-YEAR technical lookback
        'technical_config': {
            'detect_patterns': True,
            'lookback_days': 1825,  # 5 years = ~1250 trading days
            'min_pattern_confidence': 70.0,
            'rsi_period': 14,
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9,
            'bb_period': 20,
            'bb_std': 2
        },

        # 5-year backtest
        'backtest_config': {
            'historical_years': 5,
            'min_win_rate': 70.0
        },

        # Other agents
        'fundamental_config': {
            'use_perplexity': True,
            'use_llm': True,
            'llm_provider': 'openai',
            'llm_model': 'gpt-4-turbo'
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

    print(f"\n⚙️  Configuration:")
    print(f"  Technical Lookback: 5 years (1,825 days)")
    print(f"  Expected Data: ~1,250 trading days")
    print(f"  Pattern Confidence Threshold: 70%")
    print(f"  Backtest Win Rate Threshold: 70%")
    print(f"\n📊 Testing {len(TEST_STOCKS)} high-quality stocks...\n")

    results = []

    # Analyze stocks
    for i, (ticker, company) in enumerate(TEST_STOCKS, 1):
        result = await analyze_with_5year_data(orchestrator, ticker, company, i, len(TEST_STOCKS))
        results.append(result)

        if i < len(TEST_STOCKS):
            await asyncio.sleep(1)

    # Summary
    print("\n" + "="*80)
    print("  SUMMARY - 5 YEAR TECHNICAL ANALYSIS")
    print("="*80)

    successful = [r for r in results if 'error' not in r]
    total = len(successful)

    if total == 0:
        print("\n❌ No successful analyses")
        return

    # Decisions
    decisions = {}
    for r in successful:
        dec = r.get('decision', 'UNKNOWN')
        decisions[dec] = decisions.get(dec, 0) + 1

    print(f"\n📊 DECISIONS ({total} stocks):")
    for decision, count in sorted(decisions.items()):
        pct = count / total * 100
        print(f"  {decision:12s}: {count} ({pct:.1f}%)")

    # Technical signals
    tech_signals = sum(1 for r in successful if r.get('technical_signal', {}).get('has_signal'))
    print(f"\n🎯 TECHNICAL SIGNALS:")
    print(f"  Found: {tech_signals}/{total} ({tech_signals/total*100:.1f}%)")

    if tech_signals > 0:
        print(f"  🎉 IMPROVEMENT! Signals detected with 5-year data")
    else:
        print(f"  ⚠️  Still no signals - may indicate market conditions")

    # LLM usage
    llm_used = sum(1 for r in successful if r.get('used_llm_synthesis'))
    print(f"\n🤖 LLM SYNTHESIS:")
    print(f"  Used: {llm_used}/{total} ({llm_used/total*100:.1f}%)")

    # BUY recommendations
    buy_stocks = [r for r in successful if r.get('decision') in ['BUY', 'STRONG BUY']]
    if buy_stocks:
        print(f"\n✅ BUY RECOMMENDATIONS ({len(buy_stocks)}):")
        for r in buy_stocks:
            ticker = r.get('ticker', 'UNKNOWN')
            score = r.get('composite_score', 0)
            target = r.get('target_price')
            print(f"  • {ticker}: Score {score:.1f}/100")
            if target:
                print(f"    Target: ₹{target:.2f}")
    else:
        print(f"\n❌ NO BUY RECOMMENDATIONS")

    # Save results
    output_file = f"5year_technical_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump({
            'config': config,
            'results': results,
            'summary': {
                'total': total,
                'decisions': decisions,
                'technical_signals': tech_signals,
                'llm_used': llm_used
            },
            'timestamp': datetime.now().isoformat()
        }, f, indent=2, default=str)

    print(f"\n💾 Results saved to: {output_file}")
    print("\n" + "="*80 + "\n")


if __name__ == '__main__':
    try:
        asyncio.run(test_5year_technical())
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
