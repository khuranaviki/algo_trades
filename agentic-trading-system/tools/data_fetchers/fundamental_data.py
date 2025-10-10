"""
Fundamental Data Fetcher using Screener.in and yfinance

Provides:
- Financial ratios (PE, PB, ROE, ROCE, etc.)
- Growth metrics (revenue, profit, CAGR)
- Financial health (debt, interest coverage, current ratio)
- Quarterly results
- Peer comparison
"""

import requests
from bs4 import BeautifulSoup
import yfinance as yf
import pandas as pd
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
import time
import asyncio


class FundamentalDataFetcher:
    """
    Fetch fundamental data from multiple sources

    Primary: Screener.in (Indian stocks)
    Secondary: yfinance
    Tertiary: Perplexity grounded search (fills gaps)
    """

    def __init__(self, use_perplexity: bool = True):
        """Initialize fundamental data fetcher"""
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://www.screener.in/company"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        # Initialize Perplexity client if enabled
        self.use_perplexity = use_perplexity
        self.perplexity_client = None
        if use_perplexity:
            try:
                from tools.data_fetchers.perplexity_search import PerplexitySearchClient
                self.perplexity_client = PerplexitySearchClient()
            except Exception as e:
                self.logger.warning(f"Could not initialize Perplexity client: {e}")
                self.use_perplexity = False

    def get_fundamental_data(
        self,
        ticker: str,
        use_screener: bool = True,
        use_hybrid: bool = True
    ) -> Dict[str, Any]:
        """
        Get comprehensive fundamental data using hybrid approach

        Hybrid strategy:
        1. Fetch from Screener.in (PE, ROE, ROCE, Sales, Profit)
        2. Fetch from yfinance (Market Cap, Debt, Cash Flow)
        3. Fill gaps with Perplexity (Book Value, Dividend Yield, Promoter Holding)

        Args:
            ticker: Stock ticker (e.g., 'RELIANCE.NS')
            use_screener: Try Screener.in first (for Indian stocks)
            use_hybrid: Merge data from multiple sources

        Returns:
            Dict with fundamental metrics
        """
        result = {
            'ticker': ticker,
            'fetched_at': datetime.now().isoformat(),
            'sources': []
        }

        # Strategy 1: Single source (legacy mode)
        if not use_hybrid:
            # Try Screener.in for Indian stocks (NSE)
            if use_screener and '.NS' in ticker:
                screener_data = self._fetch_from_screener(ticker)
                if screener_data:
                    result.update(screener_data)
                    result['source'] = 'screener.in'
                    return result

            # Fallback to yfinance
            yf_data = self._fetch_from_yfinance(ticker)
            if yf_data:
                result.update(yf_data)
                result['source'] = 'yfinance'
                return result

            result['error'] = 'No data available'
            return result

        # Strategy 2: Hybrid mode - merge from all sources
        data_collected = {}

        # Source 1: Screener.in (best for PE, ROE, ROCE, Sales, Profit)
        if use_screener and '.NS' in ticker:
            screener_data = self._fetch_from_screener(ticker)
            if screener_data:
                data_collected.update(screener_data)
                result['sources'].append('screener.in')
                self.logger.info(f"Screener.in provided {len(screener_data)} metrics")

        # Source 2: yfinance (good for Market Cap, Debt, Cash Flow)
        yf_data = self._fetch_from_yfinance(ticker)
        if yf_data:
            # Only add metrics not already present
            for key, value in yf_data.items():
                if key not in data_collected or data_collected.get(key) is None:
                    data_collected[key] = value
            result['sources'].append('yfinance')
            self.logger.info(f"yfinance added/updated metrics")

        # Source 3: Perplexity (fills remaining gaps)
        if self.use_perplexity and self.perplexity_client:
            missing_metrics = self._identify_missing_metrics(data_collected)
            if missing_metrics:
                self.logger.info(f"Filling {len(missing_metrics)} missing metrics with Perplexity")

                # Use company name from already collected data, or fetch it
                company_name = data_collected.get('company_name')
                if not company_name:
                    # Fetch company name from yfinance as fallback
                    company_name = self._get_company_name(ticker)

                perplexity_data = self._fetch_from_perplexity_sync(ticker, company_name)
                if perplexity_data:
                    for key, value in perplexity_data.items():
                        if key not in data_collected or data_collected.get(key) is None:
                            data_collected[key] = value
                    result['sources'].append('perplexity')
                    self.logger.info(f"Perplexity filled gaps")

        # Merge all collected data
        result.update(data_collected)
        result['source'] = '+'.join(result['sources']) if result['sources'] else 'none'

        if not data_collected:
            result['error'] = 'No data available from any source'

        return result

    def _fetch_from_screener(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Fetch data from Screener.in using consolidated view

        Args:
            ticker: Stock ticker (e.g., 'RELIANCE.NS')

        Returns:
            Dict with fundamental data or None
        """
        try:
            # Convert ticker to Screener.in format
            clean_ticker = ticker.replace('.NS', '').replace('.BO', '')

            # Use consolidated URL format
            url = f"{self.base_url}/{clean_ticker}/consolidated/"

            self.logger.info(f"Fetching from Screener.in: {url}")

            response = self.session.get(url, timeout=15)

            if response.status_code != 200:
                self.logger.warning(f"Screener.in returned {response.status_code}")
                return None

            soup = BeautifulSoup(response.content, 'html.parser')

            data = {}

            # Method 1: Extract from top ratios list
            data.update(self._parse_top_ratios(soup))

            # Method 2: Extract from financial tables
            data.update(self._parse_financial_tables(soup))

            # Method 3: Extract quarterly revenue/profit data with trendline analysis
            quarterly_data = self._extract_quarterly_data(soup, num_quarters=6)
            data.update(quarterly_data)

            # Method 4: Extract from company info
            data.update(self._parse_company_info(soup))

            # If we got some data, return it
            if len(data) > 0:
                self.logger.info(f"Screener.in: Extracted {len(data)} metrics")
                return data
            else:
                self.logger.warning("Screener.in: No data extracted (likely JS-rendered)")
                return None

        except Exception as e:
            self.logger.error(f"Error fetching from Screener.in: {e}")
            return None

    def _parse_top_ratios(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Parse top ratios section"""
        data = {}

        try:
            # Find all ratio list items
            ratio_items = soup.find_all('li', class_='flex-space-between') or soup.find_all('li')

            for item in ratio_items:
                name_elem = item.find('span', class_='name')
                value_elem = item.find('span', class_='value') or item.find('span', class_='nowrap')

                if name_elem and value_elem:
                    name = name_elem.get_text(strip=True)
                    value = value_elem.get_text(strip=True)

                    # Skip if value is placeholder
                    if value == '--' or not value:
                        continue

                    # Map to our field names
                    if 'Market Cap' in name:
                        data['market_cap_cr'] = self._parse_number(value)
                    elif 'Stock P/E' in name or 'P/E' in name:
                        data['pe_ratio'] = self._parse_number(value)
                    elif 'Book Value' in name:
                        data['book_value'] = self._parse_number(value)
                    elif 'Dividend Yield' in name:
                        data['dividend_yield'] = self._parse_number(value)
                    elif name == 'ROCE':
                        data['roce'] = self._parse_number(value.replace('%', ''))
                    elif name == 'ROE':
                        data['roe'] = self._parse_number(value.replace('%', ''))
                    elif 'Current Price' in name or 'Price' in name:
                        data['current_price'] = self._parse_number(value)
                    elif 'Face Value' in name:
                        data['face_value'] = self._parse_number(value)

        except Exception as e:
            self.logger.debug(f"Error parsing top ratios: {e}")

        return data

    def _parse_financial_tables(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Parse quarterly/annual result tables"""
        data = {}

        try:
            # Find tables
            tables = soup.find_all('table')

            for table in tables:
                rows = table.find_all('tr')

                for row in rows:
                    cells = row.find_all(['th', 'td'])
                    if len(cells) < 2:
                        continue

                    label = cells[0].get_text(strip=True)

                    # Get latest value (usually in 2nd column)
                    value = cells[1].get_text(strip=True) if len(cells) > 1 else None

                    if not value or value == '--':
                        continue

                    # Map common financial metrics
                    if 'Sales' in label and 'Growth' not in label:
                        data['sales'] = self._parse_number(value)
                    elif 'Operating Profit' in label or 'EBIT' in label:
                        data['operating_profit'] = self._parse_number(value)
                    elif 'Net Profit' in label:
                        data['net_profit'] = self._parse_number(value)
                    elif 'EPS' in label:
                        data['eps'] = self._parse_number(value)
                    elif 'Debt' in label and 'Equity' not in label:
                        data['total_debt'] = self._parse_number(value)
                    elif 'Promoter' in label and 'Holding' in label:
                        data['promoter_holding'] = self._parse_number(value.replace('%', ''))

        except Exception as e:
            self.logger.debug(f"Error parsing financial tables: {e}")

        return data

    def _extract_quarterly_data(self, soup: BeautifulSoup, num_quarters: int = 6) -> Dict[str, Any]:
        """
        Extract quarterly revenue and profit data with trendline analysis

        Args:
            soup: BeautifulSoup object
            num_quarters: Number of recent quarters to extract

        Returns:
            Dict with quarterly data and growth analysis
        """
        data = {
            'quarterly_data': [],
            'revenue_trend': None,
            'profit_trend': None,
            'revenue_growth_qoq': None,  # Quarter-over-quarter
            'profit_growth_qoq': None,
            'revenue_growth_yoy': None,  # Year-over-year
            'profit_growth_yoy': None
        }

        try:
            # Find the quarterly results table
            tables = soup.find_all('table', class_='data-table')

            for table in tables:
                # Check if this is the quarterly results table
                thead = table.find('thead')
                if not thead:
                    continue

                # Extract quarter periods from header (all quarters, then we'll take last N)
                headers = thead.find_all('th')
                all_quarters = []
                for header in headers[1:]:  # Skip first column (labels)
                    period_text = header.get_text(strip=True)
                    if period_text and ('202' in period_text or '201' in period_text):
                        all_quarters.append(period_text)

                # Take the LAST (most recent) num_quarters
                quarters = all_quarters[-num_quarters:] if len(all_quarters) > num_quarters else all_quarters

                if not quarters:
                    continue

                # Extract data rows
                tbody = table.find('tbody')
                if not tbody:
                    continue

                rows = tbody.find_all('tr')

                all_sales_values = []
                all_profit_values = []

                for row in rows:
                    cells = row.find_all(['th', 'td'])
                    if len(cells) < 2:
                        continue

                    label = cells[0].get_text(strip=True)

                    # Look for Sales/Revenue/Income row (banks use "Income", companies use "Sales")
                    if (('Sales' in label or 'Income' in label or 'Revenue' in label)
                        and 'Growth' not in label
                        and 'Interest' not in label
                        and 'Other' not in label):
                        # Only capture if we haven't already captured sales
                        if not all_sales_values:
                            for i in range(1, len(cells)):  # Get all columns
                                value = cells[i].get_text(strip=True)
                                all_sales_values.append(self._parse_number(value))

                    # Look for Net Profit row
                    elif 'Net Profit' in label and 'Margin' not in label and 'Growth' not in label:
                        # Only capture if we haven't already captured profit
                        if not all_profit_values:
                            for i in range(1, len(cells)):  # Get all columns
                                value = cells[i].get_text(strip=True)
                                all_profit_values.append(self._parse_number(value))

                # Take only the last (most recent) num_quarters values
                sales_values = all_sales_values[-num_quarters:] if len(all_sales_values) > num_quarters else all_sales_values
                profit_values = all_profit_values[-num_quarters:] if len(all_profit_values) > num_quarters else all_profit_values

                # Build quarterly data structure (reverse so newest is first)
                if len(quarters) > 0:
                    # Reverse to show newest first
                    for i in range(len(quarters) - 1, -1, -1):
                        quarter_data = {
                            'period': quarters[i],
                            'revenue': sales_values[i] if i < len(sales_values) else None,
                            'profit': profit_values[i] if i < len(profit_values) else None
                        }
                        data['quarterly_data'].append(quarter_data)

                    # Reverse arrays for growth calculation (newest first)
                    sales_values_reversed = list(reversed(sales_values))
                    profit_values_reversed = list(reversed(profit_values))

                    # Calculate growth trends (expects newest first)
                    data.update(self._calculate_growth_trends(sales_values_reversed, profit_values_reversed))

                    self.logger.info(f"Extracted {len(quarters)} quarters of data")
                    return data

        except Exception as e:
            self.logger.error(f"Error extracting quarterly data: {e}")

        return data

    def _calculate_growth_trends(self, revenue_values: List[float], profit_values: List[float]) -> Dict[str, Any]:
        """
        Calculate growth trends from quarterly data

        Args:
            revenue_values: List of revenue values (newest first)
            profit_values: List of profit values (newest first)

        Returns:
            Dict with growth metrics and trend analysis
        """
        result = {}

        try:
            # Filter out None values
            revenue_values = [v for v in revenue_values if v is not None]
            profit_values = [p for p in profit_values if p is not None]

            # Quarter-over-quarter growth (Q1 vs Q2)
            if len(revenue_values) >= 2:
                result['revenue_growth_qoq'] = ((revenue_values[0] - revenue_values[1]) / revenue_values[1]) * 100

            if len(profit_values) >= 2:
                result['profit_growth_qoq'] = ((profit_values[0] - profit_values[1]) / profit_values[1]) * 100

            # Year-over-year growth (Q1 2024 vs Q1 2023 - 4 quarters ago)
            if len(revenue_values) >= 5:
                result['revenue_growth_yoy'] = ((revenue_values[0] - revenue_values[4]) / revenue_values[4]) * 100

            if len(profit_values) >= 5:
                result['profit_growth_yoy'] = ((profit_values[0] - profit_values[4]) / profit_values[4]) * 100

            # Trendline analysis (linear regression over 6 quarters)
            if len(revenue_values) >= 4:
                result['revenue_trend'] = self._calculate_trendline(revenue_values)

            if len(profit_values) >= 4:
                result['profit_trend'] = self._calculate_trendline(profit_values)

        except Exception as e:
            self.logger.error(f"Error calculating growth trends: {e}")

        return result

    def _calculate_trendline(self, values: List[float]) -> str:
        """
        Calculate trendline direction using linear regression

        Args:
            values: List of values (newest first, so we reverse for time series)

        Returns:
            'growing', 'declining', or 'stable'
        """
        try:
            if len(values) < 4:
                return 'insufficient_data'

            # Reverse so oldest is first (time series order)
            values = list(reversed(values))

            # Simple linear regression
            n = len(values)
            x = list(range(n))

            # Calculate slope
            x_mean = sum(x) / n
            y_mean = sum(values) / n

            numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
            denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

            if denominator == 0:
                return 'stable'

            slope = numerator / denominator

            # Calculate percentage change over period
            avg_value = y_mean
            slope_percentage = (slope / avg_value) * 100 if avg_value != 0 else 0

            # Classify trend
            if slope_percentage > 2:  # Growing >2% per quarter on average
                return 'growing'
            elif slope_percentage < -2:  # Declining >2% per quarter on average
                return 'declining'
            else:
                return 'stable'

        except Exception as e:
            self.logger.error(f"Error calculating trendline: {e}")
            return 'error'

    def _parse_company_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Parse company name and basic info"""
        data = {}

        try:
            # Company name from title or h1
            title = soup.find('title')
            if title:
                title_text = title.get_text()
                # Extract company name before " share price"
                if 'share price' in title_text:
                    company_name = title_text.split('share price')[0].strip()
                    data['company_name'] = company_name

            # Try h1 as fallback
            if 'company_name' not in data:
                h1 = soup.find('h1')
                if h1:
                    data['company_name'] = h1.get_text(strip=True)

        except Exception as e:
            self.logger.debug(f"Error parsing company info: {e}")

        return data

    def _fetch_from_yfinance(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Fetch fundamental data from yfinance

        Args:
            ticker: Stock ticker

        Returns:
            Dict with fundamental data
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            # Extract fundamental metrics
            data = {
                'company_name': info.get('longName', info.get('shortName')),
                'sector': info.get('sector'),
                'industry': info.get('industry'),
                'market_cap': info.get('marketCap'),

                # Valuation metrics
                'pe_ratio': info.get('trailingPE'),
                'forward_pe': info.get('forwardPE'),
                'pb_ratio': info.get('priceToBook'),
                'ps_ratio': info.get('priceToSalesTrailing12Months'),
                'peg_ratio': info.get('pegRatio'),
                'enterprise_value': info.get('enterpriseValue'),
                'ev_to_revenue': info.get('enterpriseToRevenue'),
                'ev_to_ebitda': info.get('enterpriseToEbitda'),

                # Profitability metrics
                'profit_margin': self._to_percentage(info.get('profitMargins')),
                'operating_margin': self._to_percentage(info.get('operatingMargins')),
                'gross_margin': self._to_percentage(info.get('grossMargins')),
                'roe': self._to_percentage(info.get('returnOnEquity')),
                'roa': self._to_percentage(info.get('returnOnAssets')),
                'roce': None,  # Not directly available in yfinance

                # Financial health
                'debt_to_equity': info.get('debtToEquity'),
                'current_ratio': info.get('currentRatio'),
                'quick_ratio': info.get('quickRatio'),
                'interest_coverage': None,  # Calculate if data available

                # Growth metrics
                'revenue_growth': self._to_percentage(info.get('revenueGrowth')),
                'earnings_growth': self._to_percentage(info.get('earningsGrowth')),
                'revenue_per_share': info.get('revenuePerShare'),
                'eps': info.get('trailingEps'),
                'forward_eps': info.get('forwardEps'),

                # Dividends
                'dividend_yield': self._to_percentage(info.get('dividendYield')),
                'dividend_rate': info.get('dividendRate'),
                'payout_ratio': self._to_percentage(info.get('payoutRatio')),

                # Cash flow
                'free_cash_flow': info.get('freeCashflow'),
                'operating_cash_flow': info.get('operatingCashflow'),

                # Other
                'beta': info.get('beta'),
                'book_value': info.get('bookValue'),
                'shares_outstanding': info.get('sharesOutstanding'),
                'float_shares': info.get('floatShares'),
                '52_week_high': info.get('fiftyTwoWeekHigh'),
                '52_week_low': info.get('fiftyTwoWeekLow')
            }

            # Calculate additional metrics if possible
            data = self._calculate_additional_metrics(stock, data)

            self.logger.info(f"Fetched fundamentals from yfinance for {ticker}")

            return data

        except Exception as e:
            self.logger.error(f"Error fetching from yfinance: {e}")
            return None

    def _calculate_additional_metrics(
        self,
        stock: yf.Ticker,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate additional derived metrics"""

        try:
            # Get financials
            financials = stock.financials
            balance_sheet = stock.balance_sheet

            if not financials.empty and not balance_sheet.empty:
                # Calculate ROCE if possible
                # ROCE = EBIT / (Total Assets - Current Liabilities)
                if 'EBIT' in financials.index and 'Total Assets' in balance_sheet.index:
                    ebit = financials.loc['EBIT'].iloc[0] if len(financials.loc['EBIT']) > 0 else None
                    total_assets = balance_sheet.loc['Total Assets'].iloc[0] if len(balance_sheet.loc['Total Assets']) > 0 else None
                    current_liabilities = balance_sheet.loc['Current Liabilities'].iloc[0] if 'Current Liabilities' in balance_sheet.index else 0

                    if ebit and total_assets:
                        capital_employed = total_assets - current_liabilities
                        if capital_employed > 0:
                            data['roce'] = round((ebit / capital_employed) * 100, 2)

                # Calculate Interest Coverage if possible
                # Interest Coverage = EBIT / Interest Expense
                if 'EBIT' in financials.index and 'Interest Expense' in financials.index:
                    ebit = financials.loc['EBIT'].iloc[0] if len(financials.loc['EBIT']) > 0 else None
                    interest = financials.loc['Interest Expense'].iloc[0] if len(financials.loc['Interest Expense']) > 0 else None

                    if ebit and interest and interest != 0:
                        data['interest_coverage'] = round(abs(ebit / interest), 2)

            # Get quarterly data for growth calculations
            quarterly = stock.quarterly_financials
            if not quarterly.empty and 'Total Revenue' in quarterly.index:
                revenues = quarterly.loc['Total Revenue']
                if len(revenues) >= 4:
                    # YoY growth (Q1 vs Q1 last year)
                    latest_revenue = revenues.iloc[0]
                    year_ago_revenue = revenues.iloc[3] if len(revenues) > 3 else revenues.iloc[-1]

                    if year_ago_revenue > 0:
                        yoy_growth = ((latest_revenue / year_ago_revenue) - 1) * 100
                        data['revenue_growth_yoy'] = round(yoy_growth, 2)

        except Exception as e:
            self.logger.warning(f"Error calculating additional metrics: {e}")

        return data

    def get_quarterly_results(
        self,
        ticker: str,
        num_quarters: int = 8
    ) -> pd.DataFrame:
        """
        Get quarterly financial results

        Args:
            ticker: Stock ticker
            num_quarters: Number of quarters to fetch

        Returns:
            DataFrame with quarterly data
        """
        try:
            stock = yf.Ticker(ticker)
            quarterly = stock.quarterly_financials

            if quarterly.empty:
                self.logger.warning(f"No quarterly data for {ticker}")
                return pd.DataFrame()

            # Limit to requested quarters
            quarterly = quarterly.iloc[:, :num_quarters]

            self.logger.info(f"Fetched {len(quarterly.columns)} quarters for {ticker}")

            return quarterly.T  # Transpose for easier reading

        except Exception as e:
            self.logger.error(f"Error fetching quarterly results: {e}")
            return pd.DataFrame()

    def calculate_financial_health_score(
        self,
        fundamental_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate financial health score based on fundamentals

        Args:
            fundamental_data: Dict with fundamental metrics

        Returns:
            Dict with health score and breakdown
        """
        score = 0
        max_score = 100
        breakdown = {}

        # Debt to Equity (25 points)
        debt_to_equity = fundamental_data.get('debt_to_equity', 999)
        if debt_to_equity is not None:
            if debt_to_equity < 0.5:
                debt_score = 25
            elif debt_to_equity < 1.0:
                debt_score = 20
            elif debt_to_equity < 2.0:
                debt_score = 10
            else:
                debt_score = 0
            score += debt_score
            breakdown['debt_score'] = debt_score

        # Current Ratio (25 points)
        current_ratio = fundamental_data.get('current_ratio')
        if current_ratio is not None:
            if current_ratio >= 2.0:
                current_score = 25
            elif current_ratio >= 1.5:
                current_score = 20
            elif current_ratio >= 1.0:
                current_score = 10
            else:
                current_score = 0
            score += current_score
            breakdown['current_ratio_score'] = current_score

        # Interest Coverage (25 points)
        interest_coverage = fundamental_data.get('interest_coverage')
        if interest_coverage is not None:
            if interest_coverage >= 5:
                interest_score = 25
            elif interest_coverage >= 3:
                interest_score = 20
            elif interest_coverage >= 2:
                interest_score = 10
            else:
                interest_score = 0
            score += interest_score
            breakdown['interest_coverage_score'] = interest_score

        # ROE (25 points)
        roe = fundamental_data.get('roe')
        if roe is not None:
            if roe >= 20:
                roe_score = 25
            elif roe >= 15:
                roe_score = 20
            elif roe >= 10:
                roe_score = 10
            else:
                roe_score = 0
            score += roe_score
            breakdown['roe_score'] = roe_score

        return {
            'financial_health_score': score,
            'max_score': max_score,
            'percentage': round((score / max_score) * 100, 2),
            'breakdown': breakdown,
            'rating': self._get_health_rating(score)
        }

    def _get_health_rating(self, score: float) -> str:
        """Convert score to rating"""
        if score >= 80:
            return 'EXCELLENT'
        elif score >= 60:
            return 'GOOD'
        elif score >= 40:
            return 'AVERAGE'
        elif score >= 20:
            return 'POOR'
        else:
            return 'WEAK'

    def _parse_number(self, text: str) -> Optional[float]:
        """Parse number from text"""
        try:
            # Remove commas and convert to float
            clean_text = text.replace(',', '').strip()
            return float(clean_text)
        except:
            return None

    def _to_percentage(self, value: Optional[float]) -> Optional[float]:
        """Convert decimal to percentage"""
        if value is None:
            return None
        return round(value * 100, 2)

    def _identify_missing_metrics(self, data: Dict[str, Any]) -> List[str]:
        """
        Identify which key metrics are missing

        Args:
            data: Currently collected data

        Returns:
            List of missing metric keys
        """
        essential_metrics = [
            'market_cap_cr',
            'book_value',
            'dividend_yield',
            'promoter_holding',
            'debt_to_equity',
            'current_ratio',
            'pb_ratio',
            'pe_ratio',
            'roe',
            'roce'
        ]

        missing = []
        for metric in essential_metrics:
            if metric not in data or data.get(metric) is None:
                missing.append(metric)

        return missing

    def _get_company_name(self, ticker: str) -> str:
        """
        Get company name from yfinance

        Args:
            ticker: Stock ticker

        Returns:
            Company name or cleaned ticker as fallback
        """
        try:
            import yfinance as yf
            stock = yf.Ticker(ticker)
            info = stock.info
            company_name = info.get('longName') or info.get('shortName')

            if company_name:
                return company_name
            else:
                # Fallback to cleaned ticker
                return ticker.replace('.NS', '').replace('.BO', '')

        except Exception as e:
            self.logger.warning(f"Error fetching company name for {ticker}: {e}")
            return ticker.replace('.NS', '').replace('.BO', '')

    def _fetch_from_perplexity_sync(self, ticker: str, company_name: str) -> Optional[Dict[str, Any]]:
        """
        Synchronous wrapper for Perplexity async search

        Args:
            ticker: Stock ticker
            company_name: Company name (required)

        Returns:
            Dict with fundamental data or None
        """
        if not self.perplexity_client:
            return None

        try:
            # Get or create event loop
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # Run async search with actual company name
            result = loop.run_until_complete(
                self.perplexity_client.search_fundamental_metrics(ticker, company_name)
            )

            if 'error' in result:
                self.logger.warning(f"Perplexity search failed: {result['error']}")
                return None

            return result

        except Exception as e:
            self.logger.error(f"Error fetching from Perplexity: {e}")
            return None


# Example usage
def example_usage():
    """Example usage of FundamentalDataFetcher"""

    fetcher = FundamentalDataFetcher()

    # Get fundamental data
    data = fetcher.get_fundamental_data('RELIANCE.NS')
    print("Fundamental Data:")
    print(f"Company: {data.get('company_name')}")
    print(f"PE Ratio: {data.get('pe_ratio')}")
    print(f"ROE: {data.get('roe')}%")
    print(f"Debt/Equity: {data.get('debt_to_equity')}")
    print(f"Source: {data.get('source')}")

    # Calculate health score
    health = fetcher.calculate_financial_health_score(data)
    print(f"\nFinancial Health Score: {health['percentage']}%")
    print(f"Rating: {health['rating']}")
    print(f"Breakdown: {health['breakdown']}")

    # Get quarterly results
    quarterly = fetcher.get_quarterly_results('RELIANCE.NS', num_quarters=4)
    print(f"\nQuarterly Results shape: {quarterly.shape}")
    if not quarterly.empty:
        print(quarterly.head())


if __name__ == '__main__':
    example_usage()
