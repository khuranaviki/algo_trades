#!/usr/bin/env python3
"""Test Mean Reversion Strategy"""

import asyncio
from agents.technical_analyst import TechnicalAnalyst

async def test_mean_reversion():
    """Test the updated mean reversion strategy"""
    
    config = {
        'lookback_days': 365,
        'detect_patterns': True,
        'min_pattern_confidence': 70.0
    }
    
    analyst = TechnicalAnalyst(config)
    
    # Test on a few stocks
    test_stocks = ['RELIANCE.NS', 'TCS.NS', 'SBIN.NS']
    
    print("="*80)
    print("MEAN REVERSION STRATEGY TEST")
    print("="*80)
    
    for ticker in test_stocks:
        print(f"\n📊 Testing {ticker}...")
        result = await analyst.analyze(ticker, {})
        
        if 'error' in result:
            print(f"   ❌ Error: {result['error']}")
            continue
        
        print(f"   Technical Score: {result['score']}/100")
        print(f"   Trend Score: {result['trend']['score']}/100")
        print(f"   Summary: {result['summary']}")
        print(f"   Signals: {', '.join(result['trend']['signals'][:3])}")
        
        if result.get('primary_pattern'):
            print(f"   Pattern: {result['primary_pattern']['name']} ({result['primary_pattern']['confidence']}%)")

if __name__ == '__main__':
    asyncio.run(test_mean_reversion())
