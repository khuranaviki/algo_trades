#!/usr/bin/env python3
"""
Test Hybrid Data Pipeline

Tests the integration of Screener.in + yfinance + Perplexity

Usage: python test_hybrid_pipeline.py
"""

import sys
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from tools.data_fetchers.fundamental_data import FundamentalDataFetcher

def test_hybrid_pipeline():
    """Test hybrid data pipeline with all three sources"""

    print("="*80)
    print("  TESTING HYBRID DATA PIPELINE")
    print("  Screener.in + yfinance + Perplexity")
    print("="*80)

    # Initialize with Perplexity enabled
    fetcher = FundamentalDataFetcher(use_perplexity=True)

    # Test stocks
    test_stocks = [
        ('RELIANCE.NS', 'Reliance Industries'),
        ('TCS.NS', 'TCS'),
    ]

    for ticker, name in test_stocks:
        print(f"\n{'='*80}")
        print(f"  Testing: {name} ({ticker})")
        print(f"{'='*80}")

        # Test 1: Single source mode (legacy)
        print(f"\n--- Test 1: Single Source Mode (Screener.in only) ---")
        data_single = fetcher.get_fundamental_data(ticker, use_hybrid=False)
        print(f"Source: {data_single.get('source', 'Unknown')}")
        print(f"Metrics found: {len([k for k, v in data_single.items() if v is not None and k not in ['ticker', 'fetched_at', 'source', 'sources']])}")

        # Test 2: Hybrid mode (all sources)
        print(f"\n--- Test 2: Hybrid Mode (All Sources) ---")
        data_hybrid = fetcher.get_fundamental_data(ticker, use_hybrid=True)
        print(f"Sources: {data_hybrid.get('source', 'Unknown')}")
        print(f"Sources list: {data_hybrid.get('sources', [])}")

        # Key metrics to check
        metrics_to_check = {
            'company_name': 'Company Name',
            'pe_ratio': 'PE Ratio',
            'roe': 'ROE (%)',
            'roce': 'ROCE (%)',
            'market_cap_cr': 'Market Cap (Cr)',
            'book_value': 'Book Value',
            'dividend_yield': 'Dividend Yield (%)',
            'promoter_holding': 'Promoter Holding (%)',
            'debt_to_equity': 'Debt to Equity',
            'current_ratio': 'Current Ratio',
            'pb_ratio': 'P/B Ratio',
            'sales': 'Sales',
            'net_profit': 'Net Profit',
            'eps': 'EPS',
            '52_week_high': '52 Week High',
            '52_week_low': '52 Week Low',
        }

        print(f"\nDetailed Metrics:")
        print("-" * 60)

        single_count = 0
        hybrid_count = 0

        for key, label in metrics_to_check.items():
            value_single = data_single.get(key)
            value_hybrid = data_hybrid.get(key)

            if value_single is not None:
                single_count += 1
            if value_hybrid is not None:
                hybrid_count += 1

            # Show comparison
            status_single = "✅" if value_single is not None else "❌"
            status_hybrid = "✅" if value_hybrid is not None else "❌"

            print(f"{label:<25} | Single: {status_single:<5} | Hybrid: {status_hybrid:<5}")

        print(f"\n{'='*60}")
        print(f"SINGLE SOURCE: {single_count}/{len(metrics_to_check)} metrics")
        print(f"HYBRID MODE:   {hybrid_count}/{len(metrics_to_check)} metrics")
        print(f"IMPROVEMENT:   +{hybrid_count - single_count} metrics")
        print(f"{'='*60}")

        # Show specific values for key metrics
        print(f"\nKey Metrics Values (Hybrid Mode):")
        print("-" * 60)
        for key in ['pe_ratio', 'roe', 'roce', 'market_cap_cr', 'book_value', 'dividend_yield', 'promoter_holding']:
            label = metrics_to_check.get(key, key)
            value = data_hybrid.get(key)
            if value is not None:
                print(f"  {label:<25} : {value}")

    print(f"\n{'='*80}")
    print("  HYBRID PIPELINE TEST COMPLETE")
    print(f"{'='*80}\n")


def test_data_quality():
    """Test data quality and consistency"""

    print("\n" + "="*80)
    print("  TESTING DATA QUALITY & CONSISTENCY")
    print("="*80)

    fetcher = FundamentalDataFetcher(use_perplexity=True)

    ticker = 'RELIANCE.NS'

    # Get data multiple times to check consistency
    print(f"\nFetching data 3 times to check consistency...")

    results = []
    for i in range(3):
        data = fetcher.get_fundamental_data(ticker, use_hybrid=True)
        results.append(data)
        print(f"  Fetch {i+1}: {len([k for k, v in data.items() if v is not None])} metrics from {data.get('source')}")

    # Check consistency
    print(f"\nConsistency Check:")
    print("-" * 60)

    key_metrics = ['pe_ratio', 'roe', 'roce', 'market_cap_cr']
    all_consistent = True

    for metric in key_metrics:
        values = [r.get(metric) for r in results]
        is_consistent = len(set(str(v) for v in values)) == 1  # All same

        if is_consistent:
            print(f"  ✅ {metric:<20} : Consistent ({values[0]})")
        else:
            print(f"  ⚠️  {metric:<20} : Inconsistent {values}")
            all_consistent = False

    if all_consistent:
        print(f"\n✅ All metrics are consistent across fetches")
    else:
        print(f"\n⚠️  Some metrics show inconsistency (may be due to Perplexity variation)")

    print(f"\n{'='*80}")
    print("  DATA QUALITY TEST COMPLETE")
    print(f"{'='*80}\n")


def test_fallback_behavior():
    """Test fallback behavior when sources fail"""

    print("\n" + "="*80)
    print("  TESTING FALLBACK BEHAVIOR")
    print("="*80)

    # Test with Perplexity disabled
    print(f"\nTest 1: Without Perplexity")
    fetcher_no_pplx = FundamentalDataFetcher(use_perplexity=False)
    data_no_pplx = fetcher_no_pplx.get_fundamental_data('TCS.NS', use_hybrid=True)
    print(f"  Sources: {data_no_pplx.get('sources', [])}")
    print(f"  Metrics: {len([k for k, v in data_no_pplx.items() if v is not None])}")

    # Test with Perplexity enabled
    print(f"\nTest 2: With Perplexity")
    fetcher_with_pplx = FundamentalDataFetcher(use_perplexity=True)
    data_with_pplx = fetcher_with_pplx.get_fundamental_data('TCS.NS', use_hybrid=True)
    print(f"  Sources: {data_with_pplx.get('sources', [])}")
    print(f"  Metrics: {len([k for k, v in data_with_pplx.items() if v is not None])}")

    improvement = len([k for k, v in data_with_pplx.items() if v is not None]) - len([k for k, v in data_no_pplx.items() if v is not None])
    print(f"\n✅ Perplexity adds {improvement} additional metrics")

    print(f"\n{'='*80}")
    print("  FALLBACK TEST COMPLETE")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    # Run all tests
    test_hybrid_pipeline()
    test_data_quality()
    test_fallback_behavior()

    print("\n" + "="*80)
    print("  ALL HYBRID PIPELINE TESTS COMPLETE")
    print("="*80)
