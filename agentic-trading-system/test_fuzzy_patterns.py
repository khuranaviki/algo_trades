#!/usr/bin/env python3
"""Test fuzzy pattern detection"""

import asyncio
from agents.technical_analyst import TechnicalAnalyst
from datetime import datetime

async def test_patterns():
    """Test fuzzy cup with handle and RHS detection"""
    
    config = {
        'lookback_days': 365,
        'detect_patterns': True,
        'min_pattern_confidence': 60.0
    }
    
    analyst = TechnicalAnalyst(config)
    
    test_stocks = ['TCS.NS', 'RELIANCE.NS', 'SBIN.NS', 'INFY.NS']
    
    print("="*80)
    print("FUZZY PATTERN DETECTION TEST")
    print("="*80)
    print("\nCup with Handle: Handle can go 35-100% of cup (85% tolerance)")
    print("RHS: Shoulders 15-60% above head (85% tolerance)\n")
    
    for ticker in test_stocks:
        print(f"\n{'='*80}")
        print(f"📊 {ticker}")
        print('='*80)
        
        result = await analyst.analyze(ticker, {})
        
        if 'error' in result:
            print(f"   ❌ Error: {result['error']}")
            continue
        
        # Show all patterns detected
        patterns = result.get('patterns', [])
        
        if patterns:
            print(f"\n✅ {len(patterns)} Pattern(s) Detected:\n")
            for i, pattern in enumerate(patterns, 1):
                print(f"{i}. {pattern['name']} (Confidence: {pattern['confidence']}%)")
                
                if pattern['type'] == 'CWH':
                    print(f"   - Cup Depth: {pattern['cup_depth_pct']:.1f}%")
                    print(f"   - Handle Position: {pattern.get('handle_position', 'N/A')}")
                    print(f"   - Entry Type: {pattern.get('entry_type', 'N/A')}")
                    if pattern.get('entry_ready'):
                        print(f"   - 🎯 ENTRY READY!")
                    print(f"   - Target: ₹{pattern.get('target_conservative', 0):.2f}")
                    
                elif pattern['type'] == 'RHS':
                    print(f"   - Head Depth: {pattern['head_depth_pct']:.1f}%")
                    print(f"   - Shoulder Symmetry: {pattern['shoulder_symmetry_pct']:.1f}%")
                    print(f"   - Entry Type: {pattern.get('entry_type', 'N/A')}")
                    print(f"   - Neckline: ₹{pattern['neckline']:.2f}")
                    print(f"   - Target: ₹{pattern['target']:.2f}")
                    if pattern.get('entry_ready'):
                        print(f"   - 🎯 ENTRY READY!")
        else:
            print("\n❌ No patterns detected")
        
        # Show technical score
        print(f"\nTechnical Score: {result['score']}/100")
        print(f"Trend Score: {result['trend']['score']}/100")

if __name__ == '__main__':
    asyncio.run(test_patterns())
