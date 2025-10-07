#!/usr/bin/env python3
"""
Data fetching utilities for algorithmic trading
Integrates with existing fundamental scraper and Yahoo Finance
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sys
import os

# Add parent directory to path to import from main project
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

try:
    from fundamental_scraper import FundamentalDataCollector
    FUNDAMENTAL_SCRAPER_AVAILABLE = True
except ImportError:
    print("⚠️ Warning: fundamental_scraper not available")
    FUNDAMENTAL_SCRAPER_AVAILABLE = False


class DataFetcher:
    """
    Unified data fetcher for market data and fundamentals
    """

    def __init__(self):
        """Initialize data fetcher"""
        if FUNDAMENTAL_SCRAPER_AVAILABLE:
            self.fundamental_collector = FundamentalDataCollector()
        else:
            self.fundamental_collector = None

    def fetch_ohlcv_data(
        self,
        ticker: str,
        start_date: str,
        end_date: str,
        interval: str = '1d'
    ) -> Optional[pd.DataFrame]:
        """
        Fetch OHLCV data from Yahoo Finance

        Args:
            ticker: Stock ticker (e.g., 'RELIANCE.NS')
            start_date: Start date 'YYYY-MM-DD'
            end_date: End date 'YYYY-MM-DD'
            interval: Data interval ('1d', '1wk', '1mo')

        Returns:
            DataFrame with OHLCV data
        """
        try:
            print(f"📊 Fetching OHLCV data for {ticker}...")
            data = yf.download(
                ticker,
                start=start_date,
                end=end_date,
                interval=interval,
                progress=False
            )

            if data.empty:
                print(f"❌ No data found for {ticker}")
                return None

            # Handle MultiIndex columns
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)

            print(f"✅ Fetched {len(data)} bars for {ticker}")
            return data

        except Exception as e:
            print(f"❌ Error fetching OHLCV data: {e}")
            return None

    def fetch_fundamental_data(self, ticker: str) -> Optional[Dict]:
        """
        Fetch fundamental data for Indian stocks

        Args:
            ticker: Stock ticker (e.g., 'RELIANCE.NS')

        Returns:
            Dictionary with fundamental metrics
        """
        if not FUNDAMENTAL_SCRAPER_AVAILABLE or not self.fundamental_collector:
            print("⚠️ Fundamental scraper not available")
            return None

        try:
            print(f"📈 Fetching fundamental data for {ticker}...")

            # Remove .NS suffix for screener.in
            clean_ticker = ticker.replace('.NS', '').replace('.BO', '')

            # Fetch fundamental data
            fund_data = self.fundamental_collector.fetch_all_data(
                clean_ticker,
                company_name="",  # Will be auto-detected
                sector=""
            )

            if fund_data is None:
                print(f"❌ No fundamental data found for {ticker}")
                return None

            # Extract key metrics into dict
            metrics = {
                'ticker': ticker,
                'market_cap': self._parse_metric(fund_data.market_cap),
                'pe_ratio': self._parse_metric(fund_data.pe_ratio),
                'roce': self._parse_metric(fund_data.roce),
                'roe': self._parse_metric(fund_data.roe),
                'debt_to_equity': self._parse_metric(fund_data.debt_to_equity),
                'revenue_growth_yoy': self._parse_metric(fund_data.revenue_growth_1y),
                'profit_growth_yoy': self._parse_metric(fund_data.profit_growth_1y),
                'revenue_growth_3y': self._parse_metric(fund_data.revenue_growth_3y),
                'profit_growth_3y': self._parse_metric(fund_data.profit_growth_3y),
                'promoter_holding': self._parse_metric(fund_data.promoter_holding),
            }

            print(f"✅ Fundamental data fetched for {ticker}")
            return metrics

        except Exception as e:
            print(f"❌ Error fetching fundamental data: {e}")
            return None

    def _parse_metric(self, value: str) -> Optional[float]:
        """Parse metric string to float"""
        if value is None or value == "Not Available":
            return None

        try:
            # Remove common suffixes and commas
            clean_value = str(value).replace(',', '').replace('%', '').replace('Cr', '').strip()
            return float(clean_value)
        except (ValueError, AttributeError):
            return None

    def fetch_stock_info(self, ticker: str) -> Optional[Dict]:
        """
        Fetch stock info from Yahoo Finance

        Args:
            ticker: Stock ticker

        Returns:
            Dictionary with stock info
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            return {
                'ticker': ticker,
                'company_name': info.get('longName', ticker),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE', None),
                'dividend_yield': info.get('dividendYield', None),
            }

        except Exception as e:
            print(f"❌ Error fetching stock info: {e}")
            return None

    def get_stock_universe(
        self,
        index: str = 'NIFTY50',
        fundamental_filters: Dict = None
    ) -> List[Dict]:
        """
        Get a universe of stocks based on index or filters

        Args:
            index: Stock index ('NIFTY50', 'NIFTY500', etc.)
            fundamental_filters: Optional filters for screening

        Returns:
            List of stock dictionaries
        """
        # Predefined stock universes
        stock_universes = {
            'NIFTY50': [
                'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS',
                'HINDUNILVR.NS', 'ITC.NS', 'SBIN.NS', 'BHARTIARTL.NS', 'KOTAKBANK.NS',
                'LT.NS', 'AXISBANK.NS', 'ASIANPAINT.NS', 'MARUTI.NS', 'SUNPHARMA.NS',
                'TITAN.NS', 'BAJFINANCE.NS', 'ULTRACEMCO.NS', 'NESTLEIND.NS', 'WIPRO.NS',
            ],
            'LOGISTICS': [
                'DELHIVERY.NS', 'BLUEDART.NS', 'VRL.NS', 'GATI.NS', 'TCI.NS'
            ],
            'PHARMA': [
                'SUNPHARMA.NS', 'DRREDDY.NS', 'CIPLA.NS', 'DIVISLAB.NS', 'AUROPHARMA.NS',
                'BIOCON.NS', 'TORNTPHARM.NS', 'LALPATHLAB.NS'
            ],
        }

        universe = stock_universes.get(index, stock_universes['NIFTY50'])

        # Fetch info for each stock
        stocks = []
        for ticker in universe:
            info = self.fetch_stock_info(ticker)
            if info:
                stocks.append(info)

        # Apply fundamental filters if provided
        if fundamental_filters:
            stocks = self._apply_filters(stocks, fundamental_filters)

        return stocks

    def _apply_filters(self, stocks: List[Dict], filters: Dict) -> List[Dict]:
        """Apply fundamental filters to stock list"""
        filtered = []

        for stock in stocks:
            passes = True

            # Market cap filter
            if 'min_market_cap' in filters:
                if stock.get('market_cap', 0) < filters['min_market_cap']:
                    passes = False

            if 'max_market_cap' in filters:
                if stock.get('market_cap', float('inf')) > filters['max_market_cap']:
                    passes = False

            # PE ratio filter
            if 'max_pe' in filters and stock.get('pe_ratio'):
                if stock['pe_ratio'] > filters['max_pe']:
                    passes = False

            if passes:
                filtered.append(stock)

        return filtered


# Example usage
if __name__ == '__main__':
    fetcher = DataFetcher()

    # Example 1: Fetch OHLCV data
    print("\n" + "="*80)
    print("Example 1: Fetch OHLCV Data")
    print("="*80)

    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

    data = fetcher.fetch_ohlcv_data('RELIANCE.NS', start_date, end_date)
    if data is not None:
        print(f"\nFirst 5 rows:")
        print(data.head())
        print(f"\nLast 5 rows:")
        print(data.tail())

    # Example 2: Fetch fundamental data
    print("\n" + "="*80)
    print("Example 2: Fetch Fundamental Data")
    print("="*80)

    fund_data = fetcher.fetch_fundamental_data('RELIANCE.NS')
    if fund_data:
        print(f"\nFundamental Metrics:")
        for key, value in fund_data.items():
            print(f"  {key}: {value}")

    # Example 3: Get stock universe
    print("\n" + "="*80)
    print("Example 3: Get Stock Universe")
    print("="*80)

    universe = fetcher.get_stock_universe('NIFTY50')
    print(f"\nFound {len(universe)} stocks in NIFTY50")
    for stock in universe[:5]:
        print(f"  {stock['ticker']}: {stock['company_name']} - {stock['sector']}")
