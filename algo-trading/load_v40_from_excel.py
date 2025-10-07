#!/usr/bin/env python3
"""
Load V40 and V40 Next stocks from Excel file
Converts NSE: format to .NS format for yfinance
"""

import pandas as pd

EXCEL_FILE = '/Users/delhivery/Documents/To_Backup/Codes/streamlit-market-analysis/algo-trading/v_stocks.xlsx'

def load_v40_stocks():
    """Load V40 stocks from Excel"""
    df = pd.read_excel(EXCEL_FILE, sheet_name='V40')
    # Convert NSE:TICKER to TICKER.NS format
    tickers = df['V40'].apply(lambda x: x.replace('NSE:', '') + '.NS').tolist()
    return tickers

def load_v40_next_stocks():
    """Load V40 Next stocks from Excel"""
    df = pd.read_excel(EXCEL_FILE, sheet_name='V40 Next')
    # Convert NSE:TICKER to TICKER.NS format
    tickers = df['V40 Next'].apply(lambda x: x.replace('NSE:', '') + '.NS').tolist()
    return tickers

def load_all_v40_stocks():
    """Load both V40 and V40 Next stocks"""
    v40 = load_v40_stocks()
    v40_next = load_v40_next_stocks()
    return v40 + v40_next

def is_v40_stock(ticker):
    """Check if ticker is in V40 list"""
    v40_stocks = load_v40_stocks()
    return ticker in v40_stocks

def is_v40_next_stock(ticker):
    """Check if ticker is in V40 Next list"""
    v40_next_stocks = load_v40_next_stocks()
    return ticker in v40_next_stocks

if __name__ == '__main__':
    print("\n" + "="*80)
    print("V40 STOCKS FROM EXCEL")
    print("="*80)

    v40 = load_v40_stocks()
    print(f"\nTotal V40 stocks: {len(v40)}")
    print("\nV40 Stocks:")
    for i, ticker in enumerate(v40, 1):
        print(f"{i:2d}. {ticker}")

    print("\n" + "="*80)
    print("V40 NEXT STOCKS FROM EXCEL")
    print("="*80)

    v40_next = load_v40_next_stocks()
    print(f"\nTotal V40 Next stocks: {len(v40_next)}")
    print("\nV40 Next Stocks:")
    for i, ticker in enumerate(v40_next, 1):
        print(f"{i:2d}. {ticker}")

    print("\n" + "="*80)
    print(f"TOTAL: {len(v40) + len(v40_next)} stocks")
    print("="*80 + "\n")
