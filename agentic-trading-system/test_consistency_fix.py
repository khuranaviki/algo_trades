#!/usr/bin/env python3
"""
Quick test to verify consistency fix works
"""
import sys
import asyncio
import logging
from datetime import datetime, timedelta

# Force reload of modules
if 'agents.orchestrator' in sys.modules:
    del sys.modules['agents.orchestrator']

from agents.orchestrator import Orchestrator
from config.paper_trading_config import PAPER_TRADING_CONFIG

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    print("\n" + "="*80)
    print("  TESTING CONSISTENCY FIX")
    print("  Pattern validator passes (72.2%) but backtest fails (<70%)")
    print("  Fix should skip backtest veto and allow trade")
    print("="*80 + "\n")

    # Initialize orchestrator
    config = PAPER_TRADING_CONFIG['orchestrator']
    orchestrator = Orchestrator(config)

    # Test AXISBANK (known to have validated pattern with 72.2% success)
    ticker = 'AXISBANK.NS'
    current_date = datetime.now()

    print(f"🔍 Analyzing {ticker}...")
    print(f"Expected: Pattern validator passes (72.2%), backtest fails (<70%)")
    print(f"Expected: Backtest veto should be SKIPPED (warning only)\n")

    decision = await orchestrator.analyze(ticker, {'current_date': current_date})

    print("\n" + "="*80)
    print("RESULTS:")
    print("="*80)
    print(f"Decision: {decision['action']}")
    print(f"Score: {decision['composite_score']:.1f}/100")
    print(f"\nVetoes: {decision.get('vetoes', [])}")
    print(f"Warnings: {decision.get('warnings', [])}")

    # Check if fix worked
    pattern_validated = decision.get('technical', {}).get('primary_pattern', {}).get('validated', False)
    backtest_validated = decision.get('backtest', {}).get('validated', False)
    has_backtest_veto = any('Backtest validation failed' in v for v in decision.get('vetoes', []))
    has_backtest_warning = any('Backtest validation' in w for w in decision.get('warnings', []))

    print(f"\nPattern Validated: {pattern_validated}")
    print(f"Backtest Validated: {backtest_validated}")
    print(f"Has Backtest Veto: {has_backtest_veto}")
    print(f"Has Backtest Warning: {has_backtest_warning}")

    print("\n" + "="*80)
    if pattern_validated and not backtest_validated and has_backtest_warning and not has_backtest_veto:
        print("✅ FIX WORKING!")
        print("   - Pattern validator passed")
        print("   - Backtest failed but only showed WARNING")
        print("   - No veto applied")
        print("   - Trade can proceed based on pattern validation")
    elif pattern_validated and not backtest_validated and has_backtest_veto:
        print("❌ FIX NOT WORKING")
        print("   - Pattern validator passed")
        print("   - Backtest veto still applied")
        print("   - Need to check code")
    else:
        print("⚠️  Unexpected state - check results above")
    print("="*80 + "\n")

if __name__ == '__main__':
    asyncio.run(main())
