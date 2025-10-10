#!/usr/bin/env python3
"""
Test Technical Analyst Agent

Usage: python test_technical_analyst.py
"""

import asyncio
import sys
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from agents.technical_analyst import TechnicalAnalyst

async def test_technical_analyst():
    """Test Technical Analyst with real stocks"""

    print("="*80)
    print("  TESTING TECHNICAL ANALYST AGENT")
    print("="*80)

    # Configure agent
    config = {
        'lookback_days': 200,
        'detect_patterns': True,
        'min_pattern_confidence': 70.0,
        'rsi_period': 14,
        'macd_fast': 12,
        'macd_slow': 26,
        'macd_signal': 9
    }

    analyst = TechnicalAnalyst(config)

    # Test stocks
    test_stocks = [
        'RELIANCE.NS',
        'TCS.NS',
        'HDFCBANK.NS'
    ]

    for ticker in test_stocks:
        print(f"\n{'='*80}")
        print(f"  Analyzing: {ticker}")
        print(f"{'='*80}")

        try:
            result = await analyst.analyze(ticker, {})

            if 'error' in result:
                print(f"❌ ERROR: {result['error']}")
                continue

            # Display results
            print(f"\n📊 Technical Score: {result['score']}/100")
            print(f"📝 Summary: {result['summary']}")

            # Category scores
            print(f"\n📈 Category Scores:")
            print(f"  Trend:       {result['trend']['score']}/100")
            print(f"  Momentum:    {result['momentum']['score']}/100")
            print(f"  Volume:      {result['volume']['score']}/100")
            print(f"  Volatility:  {result['volatility']['score']}/100")

            # Indicators
            print(f"\n📉 Key Indicators:")
            indicators = result['indicators']
            print(f"  Current Price: ₹{indicators['price']['current']:.2f}")
            print(f"  SMA-20:        ₹{indicators['price']['sma_20']:.2f}")
            if indicators['price']['sma_50']:
                print(f"  SMA-50:        ₹{indicators['price']['sma_50']:.2f}")
            if indicators['price']['sma_200']:
                print(f"  SMA-200:       ₹{indicators['price']['sma_200']:.2f}")
            print(f"  RSI:           {indicators['momentum']['rsi']:.2f}")
            print(f"  MACD:          {indicators['momentum']['macd']:.4f}")
            print(f"  Volume Ratio:  {indicators['volume']['current']:.2f}x")

            # Patterns detected
            if result.get('patterns'):
                print(f"\n🔍 Patterns Detected:")
                for pattern in result['patterns']:
                    print(f"  ✅ {pattern['name']} (Confidence: {pattern['confidence']}%)")

                if result.get('primary_pattern'):
                    print(f"\n⭐ Primary Pattern: {result['primary_pattern']['name']}")
                    print(f"   Confidence: {result['primary_pattern']['confidence']}%")
                    print(f"   Entry Price: ₹{result['primary_pattern']['entry_price']:.2f}")
            else:
                print(f"\n🔍 Patterns: None detected")

            # Signals
            signals = result['signals']
            signal_emoji = "🟢" if signals['action'] == 'BUY' else "🔴" if signals['action'] == 'SELL' else "🟡"
            print(f"\n{signal_emoji} Signal: {signals['action']} ({signals['strength']})")
            if signals['reasons']:
                print(f"   Reasons:")
                for reason in signals['reasons']:
                    print(f"     • {reason}")

            # Backtest context
            if result.get('backtest_context'):
                context = result['backtest_context']
                print(f"\n🎯 Backtest Context:")
                if context.get('pattern'):
                    print(f"  Pattern for validation: {context['pattern']}")
                print(f"  Support:    ₹{context['support']:.2f}")
                print(f"  Resistance: ₹{context['resistance']:.2f}")
                if context.get('atr'):
                    print(f"  ATR:        ₹{context['atr']:.2f}")

            # Overall assessment
            print(f"\n{'='*80}")
            if result['score'] >= 75:
                print(f"  ✅ STRONG BUY - Excellent technical setup")
            elif result['score'] >= 60:
                print(f"  ✅ BUY - Good technical setup")
            elif result['score'] >= 40:
                print(f"  ⚠️  HOLD - Neutral technicals")
            else:
                print(f"  ❌ AVOID - Weak technicals")
            print(f"{'='*80}")

        except Exception as e:
            print(f"❌ Exception: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'='*80}")
    print("  TECHNICAL ANALYST TEST COMPLETE")
    print(f"{'='*80}\n")


async def test_pattern_detection():
    """Test specific pattern detection"""

    print("\n" + "="*80)
    print("  TESTING PATTERN DETECTION")
    print("="*80)

    config = {
        'lookback_days': 200,
        'detect_patterns': True,
        'min_pattern_confidence': 60.0  # Lower threshold for testing
    }

    analyst = TechnicalAnalyst(config)

    # Test with stocks known for patterns
    test_stocks = [
        ('RELIANCE.NS', 'Reliance'),
        ('TCS.NS', 'TCS')
    ]

    pattern_summary = {
        'RHS': 0,
        'CWH': 0,
        'Golden Cross': 0,
        'Breakout': 0,
        'Total': 0
    }

    for ticker, name in test_stocks:
        print(f"\n{name} ({ticker}):")

        result = await analyst.analyze(ticker, {})

        if 'error' not in result and result.get('patterns'):
            for pattern in result['patterns']:
                pattern_type = pattern['type']
                print(f"  ✅ {pattern['name']} - {pattern['confidence']}%")
                pattern_summary[pattern_type] = pattern_summary.get(pattern_type, 0) + 1
                pattern_summary['Total'] += 1
        else:
            print(f"  No patterns detected")

    print(f"\n{'='*80}")
    print(f"  Pattern Summary:")
    for pattern_type, count in pattern_summary.items():
        if pattern_type != 'Total':
            print(f"    {pattern_type}: {count}")
    print(f"  Total: {pattern_summary['Total']}")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    asyncio.run(test_technical_analyst())
    asyncio.run(test_pattern_detection())
