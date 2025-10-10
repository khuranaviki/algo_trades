#!/usr/bin/env python3
"""
Debug HDFC Bank Fundamental Scoring

This script will show exactly what data was fetched and how the score was calculated.
"""

import asyncio
import sys
import logging
import json
from pprint import pprint

# Setup detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from agents.fundamental_analyst import FundamentalAnalyst

async def debug_hdfc():
    """Debug HDFC Bank fundamental analysis"""

    print("="*100)
    print("  DEBUG: HDFC BANK FUNDAMENTAL SCORING")
    print("="*100)

    # Configure agent (no LLM)
    config = {
        'use_perplexity': True,
        'use_llm': False
    }

    analyst = FundamentalAnalyst(config)

    ticker = 'HDFCBANK.NS'
    company_name = 'HDFC Bank'

    print(f"\n{'='*100}")
    print(f"  Analyzing: {company_name} ({ticker})")
    print(f"{'='*100}\n")

    try:
        result = await analyst.analyze(ticker, {'company_name': company_name})

        print("\n" + "="*100)
        print("  FINAL RESULT")
        print("="*100)
        print(f"\nFinal Score: {result.get('score', 'N/A')}/100")
        print(f"Recommendation: {result.get('recommendation', 'N/A')}")
        if result.get('summary'):
            print(f"Summary: {result['summary']}\n")

        # Category breakdown
        print("="*100)
        print("  CATEGORY SCORES")
        print("="*100)

        if result.get('financial_health'):
            fh = result['financial_health']
            print(f"\n1. Financial Health: {fh['score']}/100")
            print(f"   Weight: 30%")
            print(f"   Signals:")
            for signal in fh.get('signals', []):
                print(f"     • {signal}")
            print(f"   Metrics:")
            for key, value in fh.get('metrics', {}).items():
                print(f"     {key}: {value}")

        if result.get('growth'):
            growth = result['growth']
            print(f"\n2. Growth: {growth['score']}/100")
            print(f"   Weight: 30%")
            print(f"   Signals:")
            for signal in growth.get('signals', []):
                print(f"     • {signal}")
            print(f"   Metrics:")
            for key, value in growth.get('metrics', {}).items():
                print(f"     {key}: {value}")

        if result.get('valuation'):
            val = result['valuation']
            print(f"\n3. Valuation: {val['score']}/100")
            print(f"   Weight: 20%")
            print(f"   Signals:")
            for signal in val.get('signals', []):
                print(f"     • {signal}")
            print(f"   Metrics:")
            for key, value in val.get('metrics', {}).items():
                print(f"     {key}: {value}")

        if result.get('quality'):
            qual = result['quality']
            print(f"\n4. Quality: {qual['score']}/100")
            print(f"   Weight: 20%")
            print(f"   Signals:")
            for signal in qual.get('signals', []):
                print(f"     • {signal}")
            print(f"   Metrics:")
            for key, value in qual.get('metrics', {}).items():
                print(f"     {key}: {value}")

        # Raw data fetched
        print("\n" + "="*100)
        print("  RAW DATA FETCHED")
        print("="*100)

        if result.get('raw_data'):
            print("\nRaw fundamental data:")
            pprint(result['raw_data'], width=100, depth=3)

        # Red flags
        if result.get('red_flags'):
            print("\n" + "="*100)
            print("  RED FLAGS")
            print("="*100)
            for flag in result['red_flags']:
                print(f"  🚩 {flag}")

        # Calculation breakdown
        print("\n" + "="*100)
        print("  SCORE CALCULATION")
        print("="*100)

        fh_score = result.get('financial_health', {}).get('score', 0)
        growth_score = result.get('growth', {}).get('score', 0)
        val_score = result.get('valuation', {}).get('score', 0)
        qual_score = result.get('quality', {}).get('score', 0)

        print(f"\nFinancial Health: {fh_score}/100 × 0.30 = {fh_score * 0.30:.2f}")
        print(f"Growth:           {growth_score}/100 × 0.30 = {growth_score * 0.30:.2f}")
        print(f"Valuation:        {val_score}/100 × 0.20 = {val_score * 0.20:.2f}")
        print(f"Quality:          {qual_score}/100 × 0.20 = {qual_score * 0.20:.2f}")
        print(f"{'-'*50}")
        print(f"Composite Score:  {result['score']:.2f}/100")

        # Save detailed report
        output_file = f"hdfc_fundamental_debug_{ticker}.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)

        print(f"\n💾 Detailed report saved to: {output_file}")

    except Exception as e:
        print(f"\n❌ Exception: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*100)
    print("  DEBUG COMPLETE")
    print("="*100 + "\n")


if __name__ == '__main__':
    asyncio.run(debug_hdfc())
