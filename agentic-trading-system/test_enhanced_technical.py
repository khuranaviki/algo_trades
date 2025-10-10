#!/usr/bin/env python3
"""
Enhanced Technical Analysis Test

Tests with more comprehensive technical analysis:
- Lower pattern confidence threshold (65% instead of 70%)
- More indicators analyzed
- Detailed technical signal breakdown
- Focus on 10 stocks to verify improvements
"""

import asyncio
import sys
import logging
from datetime import datetime
import json
from typing import List, Dict, Any
import traceback

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from agents.orchestrator import Orchestrator

# Test on 10 representative stocks
TEST_STOCKS = [
    ('RELIANCE.NS', 'Reliance Industries'),
    ('TCS.NS', 'Tata Consultancy Services'),
    ('HDFCBANK.NS', 'HDFC Bank'),
    ('INFY.NS', 'Infosys'),
    ('ICICIBANK.NS', 'ICICI Bank'),
    ('BHARTIARTL.NS', 'Bharti Airtel'),
    ('BAJFINANCE.NS', 'Bajaj Finance'),
    ('TITAN.NS', 'Titan Company'),
    ('MARUTI.NS', 'Maruti Suzuki'),
    ('TATAMOTORS.NS', 'Tata Motors'),
]


async def analyze_stock_detailed(
    orchestrator: Orchestrator,
    ticker: str,
    company_name: str,
    index: int,
    total: int
) -> Dict[str, Any]:
    """Analyze single stock with detailed technical breakdown"""

    print(f"\n{'='*80}")
    print(f"[{index}/{total}] Analyzing {ticker} - {company_name}")
    print(f"{'='*80}")

    try:
        result = await orchestrator.analyze(ticker, {
            'company_name': company_name,
            'market_regime': 'neutral'
        })

        # Print detailed breakdown
        print(f"\n📊 AGENT SCORES:")
        agent_scores = result.get('agent_scores', {})
        print(f"  Fundamental:  {agent_scores.get('fundamental', 0):.1f}/100")
        print(f"  Technical:    {agent_scores.get('technical', 0):.1f}/100")
        print(f"  Sentiment:    {agent_scores.get('sentiment', 0):.1f}/100")
        print(f"  Management:   {agent_scores.get('management', 0):.1f}/100")

        # Technical signal details
        tech_signal = result.get('technical_signal', {})
        print(f"\n🎯 TECHNICAL SIGNAL:")
        print(f"  Has Signal: {tech_signal.get('has_signal', False)}")
        print(f"  Type: {tech_signal.get('signal_type', 'none')}")
        print(f"  Strength: {tech_signal.get('signal_strength', 'none')}")

        if tech_signal.get('details'):
            details = tech_signal['details']
            print(f"\n  📈 Pattern Details:")
            if details.get('pattern'):
                pat = details['pattern']
                print(f"    Name: {pat.get('name', 'N/A')}")
                print(f"    Type: {pat.get('type', 'N/A')}")
                print(f"    Confidence: {pat.get('confidence', 0):.1f}%")

            print(f"\n  📊 Indicator Details:")
            if details.get('indicators'):
                ind = details['indicators']
                print(f"    Trend: {ind.get('trend', 'N/A')}")
                print(f"    MA Signal: {ind.get('ma_signal', 'N/A')}")
                print(f"    MACD: {ind.get('macd_signal', 'N/A')}")
                print(f"    RSI: {ind.get('rsi', 0):.1f}")
                print(f"    Bullish Indicators: {ind.get('bullish_count', 0)}")

        # Conflict analysis
        conflict = result.get('conflict_analysis', {})
        print(f"\n⚔️  CONFLICT:")
        print(f"  Level: {conflict.get('conflict_level', 'none')}")
        print(f"  Variance: {conflict.get('variance', 0):.3f}")

        # LLM synthesis
        used_llm = result.get('used_llm_synthesis', False)
        print(f"\n🤖 LLM SYNTHESIS: {'✅ Used' if used_llm else '❌ Not used'}")

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
            print(f"  Vetoes: {len(vetoes)}")
            for v in vetoes:
                print(f"    - {v}")

        print(f"\n{'='*80}\n")

        return result

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        traceback.print_exc()
        return {'error': str(e)}


async def test_enhanced_technical():
    """Test with enhanced technical analysis"""

    print("\n" + "="*80)
    print("  ENHANCED TECHNICAL ANALYSIS TEST")
    print("  Testing 10 stocks with detailed technical breakdown")
    print("="*80)

    # Enhanced configuration
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

        # Enhanced technical config with 5-year lookback
        'technical_config': {
            'detect_patterns': True,
            'lookback_days': 1825,  # 5 years of data for comprehensive analysis
            'min_pattern_confidence': 65.0,  # Lower threshold (was 70)
            'rsi_period': 14,
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9,
            'bb_period': 20,
            'bb_std': 2
        },

        # Backtest config
        'backtest_config': {
            'historical_years': 5,
            'min_win_rate': 65.0  # Slightly lower (was 70)
        },

        # Other agent configs
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
    print(f"  Pattern confidence threshold: {config['technical_config']['min_pattern_confidence']}%")
    print(f"  Backtest win rate threshold: {config['backtest_config']['min_win_rate']}%")
    print(f"  Lookback period: {config['technical_config']['lookback_days']} days")
    print(f"\n📊 Testing {len(TEST_STOCKS)} stocks...\n")

    results = []

    # Analyze all stocks
    for i, (ticker, company) in enumerate(TEST_STOCKS, 1):
        result = await analyze_stock_detailed(orchestrator, ticker, company, i, len(TEST_STOCKS))
        results.append(result)

        # Small delay
        if i < len(TEST_STOCKS):
            await asyncio.sleep(1)

    # Summary
    print("\n" + "="*80)
    print("  SUMMARY")
    print("="*80)

    decisions = {}
    tech_signals = 0
    llm_used = 0
    conflicts = {'none': 0, 'low': 0, 'medium': 0, 'high': 0}

    for r in results:
        if 'error' in r:
            continue

        decision = r.get('decision', 'UNKNOWN')
        decisions[decision] = decisions.get(decision, 0) + 1

        if r.get('technical_signal', {}).get('has_signal'):
            tech_signals += 1

        if r.get('used_llm_synthesis'):
            llm_used += 1

        conflict_level = r.get('conflict_analysis', {}).get('conflict_level', 'none')
        conflicts[conflict_level] = conflicts.get(conflict_level, 0) + 1

    total = len([r for r in results if 'error' not in r])

    print(f"\n📊 DECISION BREAKDOWN ({total} stocks):")
    for decision, count in sorted(decisions.items()):
        pct = count / total * 100 if total > 0 else 0
        print(f"  {decision:12s}: {count:2d} ({pct:5.1f}%)")

    print(f"\n🎯 TECHNICAL SIGNALS:")
    print(f"  Found: {tech_signals}/{total} ({tech_signals/total*100 if total > 0 else 0:.1f}%)")

    print(f"\n🤖 LLM SYNTHESIS:")
    print(f"  Used: {llm_used}/{total} ({llm_used/total*100 if total > 0 else 0:.1f}%)")

    print(f"\n⚔️  CONFLICTS:")
    for level, count in sorted(conflicts.items()):
        pct = count / total * 100 if total > 0 else 0
        print(f"  {level.capitalize():12s}: {count:2d} ({pct:5.1f}%)")

    # Save results
    output_file = f"enhanced_technical_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump({
            'config': config,
            'results': results,
            'summary': {
                'total': total,
                'decisions': decisions,
                'technical_signals': tech_signals,
                'llm_used': llm_used,
                'conflicts': conflicts
            },
            'timestamp': datetime.now().isoformat()
        }, f, indent=2, default=str)

    print(f"\n💾 Results saved to: {output_file}")
    print("\n" + "="*80 + "\n")


if __name__ == '__main__':
    try:
        asyncio.run(test_enhanced_technical())
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        traceback.print_exc()
        sys.exit(1)
