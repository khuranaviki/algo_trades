#!/usr/bin/env python3
"""
Test HDFC Bank with improved scoring

Tests:
1. Bank-specific financial health scoring
2. Perplexity-based LLM analysis
"""

import asyncio
import logging
from pprint import pprint

logging.basicConfig(level=logging.INFO)

from agents.fundamental_analyst import FundamentalAnalyst

async def test_hdfc_improved():
    """Test HDFC with bank-specific scoring and LLM"""

    print("="*100)
    print("  TESTING HDFC BANK WITH IMPROVEMENTS")
    print("  1. Bank-specific financial health scoring")
    print("  2. Perplexity-based LLM analysis")
    print("="*100)

    # Configure with LLM enabled
    config = {
        'use_perplexity': True,
        'use_llm': True  # Enable Perplexity LLM analysis
    }

    analyst = FundamentalAnalyst(config)

    ticker = 'HDFCBANK.NS'
    company_name = 'HDFC Bank'

    print(f"\n{'='*100}")
    print(f"  Analyzing: {company_name} ({ticker})")
    print(f"{'='*100}\n")

    result = await analyst.analyze(ticker, {'company_name': company_name})

    print("\n" + "="*100)
    print("  RESULTS")
    print("="*100)

    print(f"\n⭐ Final Score: {result['score']}/100")
    print(f"📊 Recommendation: {result['recommendation']}")

    # Category scores
    print(f"\n📈 Category Breakdown:")

    if result.get('financial_health'):
        fh = result['financial_health']
        print(f"\n  1. Financial Health: {fh['score']}/100 (weight: 30%)")
        print(f"     Rating: {fh['rating']}")
        if fh.get('signals'):
            print(f"     Signals:")
            for signal in fh['signals']:
                print(f"       • {signal}")
        if fh.get('breakdown'):
            print(f"     Breakdown: {fh['breakdown']}")

    if result.get('growth'):
        growth = result['growth']
        print(f"\n  2. Growth: {growth['score']}/100 (weight: 30%)")
        print(f"     Rating: {growth['rating']}")

    if result.get('valuation'):
        val = result['valuation']
        print(f"\n  3. Valuation: {val['score']}/100 (weight: 20%)")
        print(f"     Rating: {val['rating']}")

    if result.get('quality'):
        qual = result['quality']
        print(f"\n  4. Quality: {qual['score']}/100 (weight: 20%)")
        print(f"     Rating: {qual['rating']}")

    # LLM Analysis
    if result.get('llm_analysis'):
        llm = result['llm_analysis']
        print(f"\n" + "="*100)
        print("  PERPLEXITY LLM ANALYSIS")
        print("="*100)
        print(f"\n{llm.get('summary', 'N/A')}")
        if llm.get('sources'):
            print(f"\n📚 Sources:")
            for i, source in enumerate(llm['sources'], 1):
                print(f"  {i}. {source}")

    # Score calculation
    print(f"\n" + "="*100)
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

    # Comparison
    print(f"\n" + "="*100)
    print("  BEFORE vs AFTER")
    print("="*100)
    print(f"\nBEFORE:")
    print(f"  Financial Health: 0/100")
    print(f"  Total Score:      32/100")
    print(f"  Recommendation:   SELL")
    print(f"\nAFTER:")
    print(f"  Financial Health: {fh_score}/100")
    print(f"  Total Score:      {result['score']:.2f}/100")
    print(f"  Recommendation:   {result['recommendation']}")
    print(f"\n✅ Improvement: +{fh_score} on Financial Health")
    print(f"✅ Improvement: +{result['score'] - 32:.2f} on Total Score")

    print("\n" + "="*100)
    print("  TEST COMPLETE")
    print("="*100 + "\n")


if __name__ == '__main__':
    asyncio.run(test_hdfc_improved())
