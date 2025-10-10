#!/usr/bin/env python3
"""
Test Screener.in scraping implementation

Usage: python test_screener.py
"""

import sys
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from tools.data_fetchers.fundamental_data import FundamentalDataFetcher

def test_screener_scraping():
    """Test Screener.in data extraction"""

    print("="*80)
    print("  TESTING SCREENER.IN SCRAPING")
    print("="*80)

    fetcher = FundamentalDataFetcher()

    # Test stocks
    test_stocks = [
        ('RELIANCE.NS', 'Reliance Industries'),
        ('TCS.NS', 'TCS'),
        ('HDFCBANK.NS', 'HDFC Bank'),
    ]

    for ticker, name in test_stocks:
        print(f"\n{'='*80}")
        print(f"  Testing: {name} ({ticker})")
        print(f"{'='*80}")

        # Get data
        data = fetcher.get_fundamental_data(ticker, use_screener=True)

        print(f"\nSource: {data.get('source', 'Unknown')}")
        print(f"Company: {data.get('company_name', 'N/A')}")

        # Check what we got from Screener
        screener_metrics = {}
        yfinance_metrics = {}

        # Key metrics to check
        metrics_to_check = {
            'pe_ratio': 'PE Ratio',
            'roe': 'ROE (%)',
            'roce': 'ROCE (%)',
            'market_cap_cr': 'Market Cap (Cr)',
            'book_value': 'Book Value',
            'dividend_yield': 'Dividend Yield (%)',
            'promoter_holding': 'Promoter Holding (%)',
            'sales': 'Sales',
            'net_profit': 'Net Profit',
            'eps': 'EPS',
        }

        print(f"\nMetrics Found:")
        print("-" * 60)

        found_count = 0
        for key, label in metrics_to_check.items():
            value = data.get(key)
            if value is not None:
                print(f"  ✅ {label:<25} : {value}")
                found_count += 1
            else:
                print(f"  ❌ {label:<25} : Not found")

        print(f"\nSummary: Found {found_count}/{len(metrics_to_check)} metrics")

        if data.get('source') == 'screener.in':
            print("✅ SUCCESS: Using Screener.in data!")
        elif data.get('source') == 'yfinance':
            print("⚠️  FALLBACK: Using yfinance (Screener.in parsing failed)")
        else:
            print("❌ ERROR: No data source worked")

    print(f"\n{'='*80}")
    print("  TEST COMPLETE")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    test_screener_scraping()
