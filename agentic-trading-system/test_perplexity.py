#!/usr/bin/env python3
"""
Test Perplexity API Integration

Usage: python test_perplexity.py
"""

import asyncio
import sys
import logging
import json
from pprint import pprint

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from tools.data_fetchers.perplexity_search import PerplexitySearchClient

async def test_fundamental_metrics():
    """Test Perplexity fundamental metrics search"""

    print("="*80)
    print("  TESTING PERPLEXITY FUNDAMENTAL METRICS SEARCH")
    print("="*80)

    client = PerplexitySearchClient()

    # Test stocks
    test_stocks = [
        ('RELIANCE.NS', 'Reliance Industries'),
        ('TCS.NS', 'TCS'),
    ]

    for ticker, company_name in test_stocks:
        print(f"\n{'='*80}")
        print(f"  Testing: {company_name} ({ticker})")
        print(f"{'='*80}")

        try:
            # Search for fundamental metrics
            result = await client.search_fundamental_metrics(ticker, company_name)

            print(f"\nSource: {result.get('source', 'Unknown')}")
            print(f"Company: {result.get('company_name', 'N/A')}")

            if 'error' in result:
                print(f"❌ ERROR: {result['error']}")
                continue

            # Display metrics found
            print(f"\nFundamental Metrics Found:")
            print("-" * 60)

            metrics_to_check = [
                'market_cap_cr',
                'book_value',
                'dividend_yield',
                'promoter_holding',
                'debt_to_equity',
                'current_ratio',
                'pb_ratio',
                '52_week_high',
                '52_week_low',
                'face_value'
            ]

            found_count = 0
            for key in metrics_to_check:
                value = result.get(key)
                if value is not None:
                    print(f"  ✅ {key:<25} : {value}")
                    found_count += 1
                else:
                    print(f"  ❌ {key:<25} : Not found")

            print(f"\nSummary: Found {found_count}/{len(metrics_to_check)} metrics")

        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()

async def test_conference_calls():
    """Test Perplexity conference calls search"""

    print("\n\n" + "="*80)
    print("  TESTING PERPLEXITY CONFERENCE CALLS SEARCH")
    print("="*80)

    client = PerplexitySearchClient()

    ticker = 'RELIANCE.NS'
    company_name = 'Reliance Industries'

    print(f"\n{'='*80}")
    print(f"  Testing: {company_name} ({ticker})")
    print(f"{'='*80}")

    try:
        # Search for conference calls
        result = await client.search_conference_calls(ticker, company_name, quarters=2)

        print(f"\nSource: {result.get('source', 'Unknown')}")
        print(f"Quarters Requested: {result.get('quarters_requested', 0)}")

        if 'error' in result:
            print(f"❌ ERROR: {result['error']}")
            return

        print(f"\nRaw Response Preview (first 500 chars):")
        print("-" * 60)
        raw_response = result.get('raw_response', '')
        print(raw_response[:500] + "..." if len(raw_response) > 500 else raw_response)

        # Try to parse JSON from response
        try:
            import re
            json_match = re.search(r'\{[^{}]*"conference_calls"[^{}]*\[.*?\]\s*\}', raw_response, re.DOTALL)
            if json_match:
                parsed_data = json.loads(json_match.group())
                print(f"\n✅ Successfully parsed conference call data:")
                print(json.dumps(parsed_data, indent=2))
            else:
                print(f"\n⚠️  Could not parse structured JSON from response")
        except Exception as parse_error:
            print(f"\n⚠️  JSON parsing failed: {parse_error}")

        print(f"\n✅ Conference call search completed")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

async def test_news_search():
    """Test Perplexity news search"""

    print("\n\n" + "="*80)
    print("  TESTING PERPLEXITY NEWS SEARCH")
    print("="*80)

    client = PerplexitySearchClient()

    ticker = 'RELIANCE.NS'

    print(f"\n{'='*80}")
    print(f"  Testing: {ticker}")
    print(f"{'='*80}")

    try:
        # Search for news
        result = await client.search_stock_news(ticker, days=7)

        print(f"\nSource: {result.get('source', 'Unknown')}")
        print(f"Lookback Days: {result.get('lookback_days', 0)}")

        if 'error' in result:
            print(f"❌ ERROR: {result['error']}")
            return

        print(f"\nRaw Response Preview (first 500 chars):")
        print("-" * 60)
        raw_response = result.get('raw_response', '')
        print(raw_response[:500] + "..." if len(raw_response) > 500 else raw_response)

        print(f"\n✅ News search completed")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Run all tests"""

    # Test 1: Fundamental metrics
    await test_fundamental_metrics()

    # Test 2: Conference calls
    await test_conference_calls()

    # Test 3: News search
    await test_news_search()

    print(f"\n{'='*80}")
    print("  ALL PERPLEXITY TESTS COMPLETE")
    print(f"{'='*80}\n")

if __name__ == '__main__':
    asyncio.run(main())
