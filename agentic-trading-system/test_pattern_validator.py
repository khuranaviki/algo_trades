#!/usr/bin/env python3
"""
Test Pattern Validator on V40 Stocks

Tests the historical pattern validation system to see:
1. Which patterns pass >70% success rate for aggressive targets
2. Which patterns pass >55% success rate for conservative targets
3. Risk/reward ratios for validated patterns
"""

import asyncio
import sys
from datetime import datetime
from agents.technical_analyst import TechnicalAnalyst

# Test stocks (diverse selection from V40)
TEST_STOCKS = [
    'TATAMOTORS.NS',  # Has Cup with Handle (+26.4% aggressive potential)
    'DRREDDY.NS',     # Has Cup with Handle (+25.1% aggressive potential)
    'AXISBANK.NS',    # Has Cup with Handle (+24.2% aggressive potential)
    'NESTLEIND.NS',   # Has Cup with Handle (+18.3% aggressive potential) - Entry Ready
    'BAJAJFINSV.NS',  # Has Cup with Handle (+11.5% aggressive potential) - Entry Ready
    'RELIANCE.NS',    # Golden Cross only
    'TCS.NS',         # Previously rejected pattern
    'ITC.NS',         # Strong mean reversion (75.25 score)
]

async def test_pattern_validation():
    """Test pattern validator on stocks with known patterns"""

    print("="*100)
    print(" "*30 + "PATTERN VALIDATOR TEST")
    print(" "*20 + "Historical Pattern Success Rate Validation")
    print("="*100)
    print(f"\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Stocks: {len(TEST_STOCKS)}")
    print(f"Lookback: 5 years")
    print(f"\nCriteria:")
    print(f"  - Aggressive targets: >70% success rate required")
    print(f"  - Conservative targets: >55% success rate required")
    print(f"  - Risk/Reward: Minimum 2:1 ratio")
    print("\n" + "="*100)

    # Initialize analyzer WITH pattern validation enabled
    config = {
        'lookback_days': 1825,  # 5 years
        'detect_patterns': True,
        'validate_patterns': True,  # Enable validation
        'min_pattern_confidence': 60.0,
        'aggressive_success_threshold': 0.70,  # 70%
        'conservative_success_threshold': 0.55,  # 55%
        'min_risk_reward': 2.0,
        'max_holding_days': 60
    }

    analyst = TechnicalAnalyst(config)

    validated_patterns = []
    rejected_patterns = []

    for i, ticker in enumerate(TEST_STOCKS, 1):
        print(f"\n{'='*100}")
        print(f"[{i}/{len(TEST_STOCKS)}] 📊 {ticker}")
        print('='*100)

        try:
            # Run analysis with validation
            result = await analyst.analyze(ticker, {})

            if 'error' in result:
                print(f"❌ Error: {result['error']}")
                continue

            current_price = result['indicators']['price']['current']

            print(f"\n💰 Current Price: ₹{current_price:,.2f}")
            print(f"📊 Technical Score: {result['score']}/100")

            # Check for patterns
            patterns = result.get('patterns', [])

            if patterns:
                print(f"\n🎯 {len(patterns)} PATTERN(S) AFTER VALIDATION:")
                print("="*100)

                for pattern in patterns:
                    pattern_type = pattern['type']

                    print(f"\n📐 Pattern: {pattern['name']}")
                    print(f"   Confidence: {pattern['confidence']}%")

                    # Check if pattern was validated
                    if 'validation' in pattern:
                        validation = pattern['validation']

                        print(f"\n   ✅ VALIDATION PASSED:")
                        print(f"      - Historical patterns found: {validation['historical_patterns']}")
                        print(f"      - Aggressive success rate: {validation['aggressive_success_rate']*100:.1f}%")
                        print(f"      - Conservative success rate: {validation['conservative_success_rate']*100:.1f}%")
                        print(f"      - Avg gain (aggressive): {validation['avg_gain_aggressive']:+.1f}%")
                        print(f"      - Avg gain (conservative): {validation['avg_gain_conservative']:+.1f}%")
                        print(f"\n   🎯 RECOMMENDED TARGET:")
                        print(f"      - Type: {validation['target_type'].upper()}")
                        print(f"      - Target Price: ₹{pattern['recommended_target']:,.2f}")
                        print(f"      - Potential Gain: {validation['potential_gain_pct']:+.1f}%")
                        print(f"      - Risk/Reward Ratio: {validation['risk_reward_ratio']:.2f}:1")

                        if pattern.get('entry_ready'):
                            print(f"\n   🚀 ENTRY READY: {pattern.get('entry_type')}")

                        validated_patterns.append({
                            'ticker': ticker,
                            'pattern': pattern['name'],
                            'target_type': validation['target_type'],
                            'recommended_target': pattern['recommended_target'],
                            'potential_gain': validation['potential_gain_pct'],
                            'risk_reward': validation['risk_reward_ratio'],
                            'success_rate': validation[f"{validation['target_type']}_success_rate"],
                            'entry_ready': pattern.get('entry_ready', False)
                        })

                    elif pattern_type in ['CWH', 'RHS']:
                        # Pattern was detected but failed validation
                        print(f"\n   ❌ VALIDATION FAILED:")
                        print(f"      - Pattern did not meet success rate threshold")
                        print(f"      - Conservative target: ₹{pattern.get('target_conservative', 0):,.2f}")
                        print(f"      - Aggressive target: ₹{pattern.get('target_aggressive', 0):,.2f}")

                        rejected_patterns.append({
                            'ticker': ticker,
                            'pattern': pattern['name'],
                            'reason': 'Failed historical validation'
                        })

                    else:
                        # Non-validated pattern (like Golden Cross)
                        print(f"\n   ℹ️  Pattern detected (no validation required)")
                        for key, value in pattern.items():
                            if key not in ['type', 'name', 'confidence', 'detected_at']:
                                print(f"      - {key}: {value}")

            else:
                print(f"\n❌ No patterns detected")

        except Exception as e:
            print(f"❌ Error analyzing {ticker}: {e}")
            import traceback
            traceback.print_exc()

    # Summary
    print(f"\n\n{'='*100}")
    print(" "*35 + "VALIDATION SUMMARY")
    print('='*100)

    if validated_patterns:
        print(f"\n✅ VALIDATED PATTERNS ({len(validated_patterns)} stocks):")
        print("="*100)

        # Sort by potential gain
        validated_patterns.sort(key=lambda x: x['potential_gain'], reverse=True)

        for p in validated_patterns:
            entry_status = "🚀 ENTRY READY" if p['entry_ready'] else "⏳ Wait"
            print(f"\n{entry_status} | {p['ticker']} - {p['pattern']}")
            print(f"   Target Type: {p['target_type'].upper()}")
            print(f"   Target: ₹{p['recommended_target']:,.2f}")
            print(f"   Potential: {p['potential_gain']:+.1f}%")
            print(f"   Risk/Reward: {p['risk_reward']:.2f}:1")
            print(f"   Success Rate: {p['success_rate']*100:.1f}%")
    else:
        print(f"\n❌ No patterns passed validation")
        print(f"   All detected patterns failed historical success rate requirements")

    if rejected_patterns:
        print(f"\n\n❌ REJECTED PATTERNS ({len(rejected_patterns)}):")
        print("="*100)
        for p in rejected_patterns:
            print(f"   {p['ticker']} - {p['pattern']}: {p['reason']}")

    print("\n" + "="*100)
    print("Validation test complete!")
    print("="*100 + "\n")

if __name__ == '__main__':
    try:
        asyncio.run(test_pattern_validation())
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
