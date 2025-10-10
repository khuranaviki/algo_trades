#!/usr/bin/env python3
"""
Check raw data fetched for HDFC Bank
"""

import asyncio
import logging
from pprint import pprint

logging.basicConfig(level=logging.INFO)

from tools.data_fetchers.fundamental_data import FundamentalDataFetcher

async def check_hdfc_data():
    """Check what data is actually fetched for HDFC"""

    fetcher = FundamentalDataFetcher()

    ticker = 'HDFCBANK.NS'

    print("="*100)
    print("  CHECKING RAW DATA FOR HDFCBANK.NS")
    print("="*100)

    # Fetch from Screener.in
    print("\n1. SCREENER.IN DATA:")
    print("-"*100)
    screener_data = fetcher._fetch_from_screener(ticker)
    print("\nScreener.in results:")
    pprint(screener_data, width=100)

    # Fetch from yfinance
    print("\n\n2. YFINANCE DATA:")
    print("-"*100)
    yfinance_data = fetcher._fetch_from_yfinance(ticker)
    print("\nyfinance results:")
    pprint(yfinance_data, width=100)

    # Check specific financial health metrics
    print("\n\n3. FINANCIAL HEALTH METRICS:")
    print("-"*100)
    print(f"Total Debt: {yfinance_data.get('total_debt', 'MISSING')}")
    print(f"Cash: {yfinance_data.get('cash', 'MISSING')}")
    print(f"Current Assets: {yfinance_data.get('current_assets', 'MISSING')}")
    print(f"Current Liabilities: {yfinance_data.get('current_liabilities', 'MISSING')}")
    print(f"Interest Expense: {yfinance_data.get('interest_expense', 'MISSING')}")
    print(f"EBIT: {yfinance_data.get('ebit', 'MISSING')}")
    print(f"Operating Cash Flow: {yfinance_data.get('operating_cash_flow', 'MISSING')}")

    # Check growth metrics
    print("\n\n4. GROWTH METRICS:")
    print("-"*100)
    print(f"Revenue: {yfinance_data.get('revenue', 'MISSING')}")
    print(f"Net Income: {yfinance_data.get('net_income', 'MISSING')}")
    print(f"Sales Growth 3Y: {screener_data.get('sales_growth_3y', 'MISSING')}")
    print(f"Profit Growth 3Y: {screener_data.get('profit_growth_3y', 'MISSING')}")

    # Check quality metrics
    print("\n\n5. QUALITY METRICS:")
    print("-"*100)
    print(f"ROE: {screener_data.get('roe', 'MISSING')}")
    print(f"ROCE: {screener_data.get('roce', 'MISSING')}")
    print(f"Operating Margin: {yfinance_data.get('operating_margin', 'MISSING')}")
    print(f"Net Margin: {yfinance_data.get('net_margin', 'MISSING')}")

    print("\n" + "="*100)
    print("  DATA CHECK COMPLETE")
    print("="*100)


if __name__ == '__main__':
    asyncio.run(check_hdfc_data())
