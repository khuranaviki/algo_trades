#!/usr/bin/env python3
"""
V40 and V40 Next Stock Universe
Based on high-quality stocks with multibagger potential
"""

# V40 Stocks - Premium quality stocks with proven track record
V40_STOCKS = {
    # Large Cap Blue Chips
    'RELIANCE.NS': {'name': 'Reliance Industries', 'sector': 'Oil & Gas', 'mcap_category': 'Large'},
    'TCS.NS': {'name': 'Tata Consultancy Services', 'sector': 'IT', 'mcap_category': 'Large'},
    'HDFCBANK.NS': {'name': 'HDFC Bank', 'sector': 'Banking', 'mcap_category': 'Large'},
    'INFY.NS': {'name': 'Infosys', 'sector': 'IT', 'mcap_category': 'Large'},
    'ICICIBANK.NS': {'name': 'ICICI Bank', 'sector': 'Banking', 'mcap_category': 'Large'},
    'HINDUNILVR.NS': {'name': 'Hindustan Unilever', 'sector': 'FMCG', 'mcap_category': 'Large'},
    'ITC.NS': {'name': 'ITC Ltd', 'sector': 'FMCG', 'mcap_category': 'Large'},
    'LT.NS': {'name': 'Larsen & Toubro', 'sector': 'Infrastructure', 'mcap_category': 'Large'},
    'BAJFINANCE.NS': {'name': 'Bajaj Finance', 'sector': 'Finance', 'mcap_category': 'Large'},
    'ASIANPAINT.NS': {'name': 'Asian Paints', 'sector': 'Paints', 'mcap_category': 'Large'},
    'MARUTI.NS': {'name': 'Maruti Suzuki', 'sector': 'Auto', 'mcap_category': 'Large'},
    'SUNPHARMA.NS': {'name': 'Sun Pharma', 'sector': 'Pharma', 'mcap_category': 'Large'},
    'TITAN.NS': {'name': 'Titan Company', 'sector': 'Retail', 'mcap_category': 'Large'},
    'NESTLEIND.NS': {'name': 'Nestle India', 'sector': 'FMCG', 'mcap_category': 'Large'},
    'ULTRACEMCO.NS': {'name': 'UltraTech Cement', 'sector': 'Cement', 'mcap_category': 'Large'},

    # Mid Cap Quality
    'PIDILITIND.NS': {'name': 'Pidilite Industries', 'sector': 'Chemicals', 'mcap_category': 'Mid'},
    'DMART.NS': {'name': 'Avenue Supermarts (DMart)', 'sector': 'Retail', 'mcap_category': 'Mid'},
    'PAGEIND.NS': {'name': 'Page Industries', 'sector': 'Textile', 'mcap_category': 'Mid'},
    'BAJAJFINSV.NS': {'name': 'Bajaj Finserv', 'sector': 'Finance', 'mcap_category': 'Large'},
    'HCLTECH.NS': {'name': 'HCL Technologies', 'sector': 'IT', 'mcap_category': 'Large'},
    'WIPRO.NS': {'name': 'Wipro', 'sector': 'IT', 'mcap_category': 'Large'},
    'TECHM.NS': {'name': 'Tech Mahindra', 'sector': 'IT', 'mcap_category': 'Large'},
    'BRITANNIA.NS': {'name': 'Britannia Industries', 'sector': 'FMCG', 'mcap_category': 'Large'},
    'DIVISLAB.NS': {'name': 'Divis Laboratories', 'sector': 'Pharma', 'mcap_category': 'Mid'},
    'DRREDDY.NS': {'name': 'Dr Reddys Labs', 'sector': 'Pharma', 'mcap_category': 'Large'},
}

# V40 Next Stocks - High growth potential stocks
V40_NEXT_STOCKS = {
    # Emerging Leaders
    'DELHIVERY.NS': {'name': 'Delhivery', 'sector': 'Logistics', 'mcap_category': 'Mid'},
    'ZOMATO.NS': {'name': 'Zomato', 'sector': 'Food Tech', 'mcap_category': 'Mid'},
    'NYKAA.NS': {'name': 'Nykaa (FSN E-commerce)', 'sector': 'E-commerce', 'mcap_category': 'Mid'},
    'POLICYBZR.NS': {'name': 'PB Fintech (Policybazaar)', 'sector': 'FinTech', 'mcap_category': 'Mid'},

    # High Growth Mid Caps
    'LALPATHLAB.NS': {'name': 'Dr Lal PathLabs', 'sector': 'Healthcare', 'mcap_category': 'Mid'},
    'DIXON.NS': {'name': 'Dixon Technologies', 'sector': 'Electronics', 'mcap_category': 'Mid'},
    'PERSISTENT.NS': {'name': 'Persistent Systems', 'sector': 'IT', 'mcap_category': 'Mid'},
    'COFORGE.NS': {'name': 'Coforge', 'sector': 'IT', 'mcap_category': 'Mid'},
    'MPHASIS.NS': {'name': 'Mphasis', 'sector': 'IT', 'mcap_category': 'Mid'},
    'ALKYLAMINE.NS': {'name': 'Alkyl Amines', 'sector': 'Chemicals', 'mcap_category': 'Small'},
    'POLYMED.NS': {'name': 'Poly Medicure', 'sector': 'Healthcare', 'mcap_category': 'Small'},
    'CROMPTON.NS': {'name': 'Crompton Greaves', 'sector': 'Consumer Electricals', 'mcap_category': 'Mid'},
    'VOLTAS.NS': {'name': 'Voltas', 'sector': 'Consumer Durables', 'mcap_category': 'Mid'},
    'CAMS.NS': {'name': 'Computer Age Management', 'sector': 'Finance', 'mcap_category': 'Mid'},
    'ROUTE.NS': {'name': 'Route Mobile', 'sector': 'IT', 'mcap_category': 'Small'},

    # Quality Small Caps with Potential
    'CLEAN.NS': {'name': 'Clean Science', 'sector': 'Chemicals', 'mcap_category': 'Small'},
    'ASTRAL.NS': {'name': 'Astral Poly', 'sector': 'Building Materials', 'mcap_category': 'Mid'},
    'AEGISCHEM.NS': {'name': 'Aegis Logistics', 'sector': 'Logistics', 'mcap_category': 'Small'},
    'VBL.NS': {'name': 'Varun Beverages', 'sector': 'Beverages', 'mcap_category': 'Mid'},
    'TATAELXSI.NS': {'name': 'Tata Elxsi', 'sector': 'IT', 'mcap_category': 'Mid'},
}

# Combined universe
ALL_V40_STOCKS = {**V40_STOCKS, **V40_NEXT_STOCKS}


def get_v40_universe():
    """Get list of all V40 stock tickers"""
    return list(V40_STOCKS.keys())


def get_v40_next_universe():
    """Get list of all V40 Next stock tickers"""
    return list(V40_NEXT_STOCKS.keys())


def get_all_v40_universe():
    """Get combined V40 and V40 Next universe"""
    return list(ALL_V40_STOCKS.keys())


def get_stock_info(ticker):
    """Get stock information"""
    return ALL_V40_STOCKS.get(ticker, {
        'name': ticker,
        'sector': 'Unknown',
        'mcap_category': 'Unknown'
    })


def get_stocks_by_sector(sector):
    """Get stocks by sector"""
    return [ticker for ticker, info in ALL_V40_STOCKS.items()
            if info['sector'].lower() == sector.lower()]


def get_stocks_by_mcap(category):
    """Get stocks by market cap category (Large/Mid/Small)"""
    return [ticker for ticker, info in ALL_V40_STOCKS.items()
            if info['mcap_category'].lower() == category.lower()]


def is_v40_stock(ticker):
    """Check if ticker is in V40 universe"""
    return ticker in V40_STOCKS


def is_v40_next_stock(ticker):
    """Check if ticker is in V40 Next universe"""
    return ticker in V40_NEXT_STOCKS


# Fundamental screening criteria for V40 stocks
V40_FUNDAMENTAL_CRITERIA = {
    'min_revenue_growth': 15.0,    # 15% minimum revenue growth
    'min_roce': 18.0,              # 18% minimum ROCE
    'min_roe': 15.0,               # 15% minimum ROE
    'max_debt_equity': 1.5,        # Maximum 1.5 D/E ratio
    'min_promoter_holding': 40.0,  # Minimum 40% promoter holding
    'max_promoter_pledging': 10.0, # Maximum 10% pledging
}

# V40 Next has more aggressive criteria for high-growth stocks
V40_NEXT_FUNDAMENTAL_CRITERIA = {
    'min_revenue_growth': 20.0,    # 20% minimum revenue growth
    'min_roce': 15.0,              # 15% minimum ROCE (relaxed)
    'min_roe': 12.0,               # 12% minimum ROE (relaxed)
    'max_debt_equity': 2.0,        # More lenient for growth stocks
    'min_promoter_holding': 35.0,  # Minimum 35% promoter holding
    'max_promoter_pledging': 15.0, # Maximum 15% pledging
}


if __name__ == '__main__':
    print("\n" + "="*80)
    print("V40 STOCK UNIVERSE")
    print("="*80)

    print(f"\nTotal V40 Stocks: {len(V40_STOCKS)}")
    print(f"Total V40 Next Stocks: {len(V40_NEXT_STOCKS)}")
    print(f"Total Combined: {len(ALL_V40_STOCKS)}")

    print("\n" + "="*80)
    print("V40 STOCKS (Premium Quality)")
    print("="*80)
    for ticker, info in V40_STOCKS.items():
        print(f"{ticker:<20} {info['name']:<35} {info['sector']:<20} {info['mcap_category']}")

    print("\n" + "="*80)
    print("V40 NEXT STOCKS (High Growth Potential)")
    print("="*80)
    for ticker, info in V40_NEXT_STOCKS.items():
        print(f"{ticker:<20} {info['name']:<35} {info['sector']:<20} {info['mcap_category']}")

    print("\n" + "="*80)
    print("SECTOR BREAKDOWN")
    print("="*80)
    sectors = set(info['sector'] for info in ALL_V40_STOCKS.values())
    for sector in sorted(sectors):
        stocks = get_stocks_by_sector(sector)
        print(f"{sector:<20} {len(stocks)} stocks")

    print("\n")
