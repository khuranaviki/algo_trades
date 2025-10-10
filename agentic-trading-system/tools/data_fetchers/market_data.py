"""
Market Data Fetcher using yfinance

Provides:
- Historical OHLCV data (5+ years)
- Real-time quotes
- Index data (NIFTY, sector indices)
- Technical indicators data
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import logging


class MarketDataFetcher:
    """
    Fetch market data using yfinance for Indian stocks

    Supports NSE and BSE listings with .NS and .BO suffixes
    """

    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize market data fetcher

        Args:
            cache_dir: Optional directory for caching data
        """
        self.logger = logging.getLogger(__name__)
        self.cache_dir = cache_dir

    def get_historical_data(
        self,
        ticker: str,
        period: str = "5y",
        interval: str = "1d"
    ) -> pd.DataFrame:
        """
        Get historical OHLCV data

        Args:
            ticker: Stock ticker (e.g., 'RELIANCE.NS')
            period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)

        Returns:
            DataFrame with OHLCV data
        """
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period=period, interval=interval)

            if df.empty:
                self.logger.warning(f"No data returned for {ticker}")
                return pd.DataFrame()

            # Clean data
            df = df.dropna()

            self.logger.info(f"Fetched {len(df)} rows for {ticker} ({period})")

            return df

        except Exception as e:
            self.logger.error(f"Error fetching data for {ticker}: {e}")
            return pd.DataFrame()

    def get_historical_data_range(
        self,
        ticker: str,
        start_date: str,
        end_date: str,
        interval: str = "1d"
    ) -> pd.DataFrame:
        """
        Get historical data for specific date range

        Args:
            ticker: Stock ticker
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            interval: Data interval

        Returns:
            DataFrame with OHLCV data
        """
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(start=start_date, end=end_date, interval=interval)

            if df.empty:
                self.logger.warning(f"No data for {ticker} between {start_date} and {end_date}")
                return pd.DataFrame()

            df = df.dropna()

            self.logger.info(f"Fetched {len(df)} rows for {ticker} ({start_date} to {end_date})")

            return df

        except Exception as e:
            self.logger.error(f"Error fetching data for {ticker}: {e}")
            return pd.DataFrame()

    def get_current_price(self, ticker: str) -> Optional[float]:
        """
        Get current market price

        Args:
            ticker: Stock ticker

        Returns:
            Current price or None
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            # Try different price fields
            price = info.get('currentPrice') or info.get('regularMarketPrice')

            if price:
                self.logger.info(f"Current price for {ticker}: {price}")
                return float(price)

            # Fallback to last close
            hist = stock.history(period="1d")
            if not hist.empty:
                price = hist['Close'].iloc[-1]
                self.logger.info(f"Last close for {ticker}: {price}")
                return float(price)

            return None

        except Exception as e:
            self.logger.error(f"Error fetching price for {ticker}: {e}")
            return None

    def get_stock_info(self, ticker: str) -> Dict[str, Any]:
        """
        Get comprehensive stock information

        Args:
            ticker: Stock ticker

        Returns:
            Dict with stock info
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            # Extract key fields
            result = {
                'ticker': ticker,
                'company_name': info.get('longName', info.get('shortName', 'Unknown')),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'market_cap': info.get('marketCap'),
                'current_price': info.get('currentPrice', info.get('regularMarketPrice')),
                'previous_close': info.get('previousClose'),
                'open': info.get('open'),
                'day_high': info.get('dayHigh'),
                'day_low': info.get('dayLow'),
                '52_week_high': info.get('fiftyTwoWeekHigh'),
                '52_week_low': info.get('fiftyTwoWeekLow'),
                'volume': info.get('volume'),
                'avg_volume': info.get('averageVolume'),
                'beta': info.get('beta'),
                'pe_ratio': info.get('trailingPE'),
                'forward_pe': info.get('forwardPE'),
                'dividend_yield': info.get('dividendYield'),
                'book_value': info.get('bookValue'),
                'price_to_book': info.get('priceToBook'),
                'eps': info.get('trailingEps'),
                'profit_margin': info.get('profitMargins'),
                'operating_margin': info.get('operatingMargins'),
                'roe': info.get('returnOnEquity'),
                'revenue': info.get('totalRevenue'),
                'debt_to_equity': info.get('debtToEquity'),
                'current_ratio': info.get('currentRatio'),
                'quick_ratio': info.get('quickRatio')
            }

            self.logger.info(f"Fetched info for {ticker}: {result['company_name']}")

            return result

        except Exception as e:
            self.logger.error(f"Error fetching info for {ticker}: {e}")
            return {'ticker': ticker, 'error': str(e)}

    def get_index_data(
        self,
        index_symbol: str = "^NSEI",  # NIFTY 50
        period: str = "1y"
    ) -> pd.DataFrame:
        """
        Get index historical data

        Args:
            index_symbol: Index symbol (^NSEI for NIFTY, ^NSEBANK for BANKNIFTY)
            period: Time period

        Returns:
            DataFrame with index data
        """
        return self.get_historical_data(index_symbol, period=period)

    def get_multiple_tickers(
        self,
        tickers: List[str],
        period: str = "1y",
        data_column: str = "Close"
    ) -> pd.DataFrame:
        """
        Get data for multiple tickers at once

        Args:
            tickers: List of ticker symbols
            period: Time period
            data_column: Column to extract (Close, Open, High, Low, Volume)

        Returns:
            DataFrame with tickers as columns
        """
        try:
            data = yf.download(
                tickers,
                period=period,
                group_by='ticker',
                auto_adjust=True,
                threads=True
            )

            if len(tickers) == 1:
                # Single ticker - return as is
                return data[[data_column]] if data_column in data.columns else pd.DataFrame()

            # Multiple tickers - extract specified column
            result = pd.DataFrame()
            for ticker in tickers:
                if ticker in data.columns.get_level_values(0):
                    result[ticker] = data[ticker][data_column]

            self.logger.info(f"Fetched data for {len(tickers)} tickers")

            return result

        except Exception as e:
            self.logger.error(f"Error fetching multiple tickers: {e}")
            return pd.DataFrame()

    def calculate_returns(
        self,
        ticker: str,
        period: str = "1y"
    ) -> Dict[str, float]:
        """
        Calculate various return metrics

        Args:
            ticker: Stock ticker
            period: Time period

        Returns:
            Dict with return metrics
        """
        try:
            df = self.get_historical_data(ticker, period=period)

            if df.empty:
                return {}

            # Calculate returns
            total_return = ((df['Close'].iloc[-1] / df['Close'].iloc[0]) - 1) * 100

            # Daily returns
            daily_returns = df['Close'].pct_change().dropna()

            # Volatility (annualized)
            volatility = daily_returns.std() * np.sqrt(252) * 100

            # Sharpe ratio (assuming 6% risk-free rate)
            risk_free_rate = 0.06
            excess_returns = daily_returns - (risk_free_rate / 252)
            sharpe_ratio = (excess_returns.mean() / excess_returns.std()) * np.sqrt(252)

            # Max drawdown
            cumulative = (1 + daily_returns).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            max_drawdown = drawdown.min() * 100

            result = {
                'ticker': ticker,
                'period': period,
                'total_return_pct': round(total_return, 2),
                'annualized_volatility_pct': round(volatility, 2),
                'sharpe_ratio': round(sharpe_ratio, 2),
                'max_drawdown_pct': round(max_drawdown, 2),
                'start_price': round(df['Close'].iloc[0], 2),
                'end_price': round(df['Close'].iloc[-1], 2),
                'data_points': len(df)
            }

            self.logger.info(f"Calculated returns for {ticker}: {result['total_return_pct']}%")

            return result

        except Exception as e:
            self.logger.error(f"Error calculating returns for {ticker}: {e}")
            return {}

    def check_market_regime(
        self,
        index_symbol: str = "^NSEI",
        lookback_days: int = 50
    ) -> Dict[str, Any]:
        """
        Check current market regime (bullish/bearish/sideways)

        Args:
            index_symbol: Index to check (default NIFTY)
            lookback_days: Days to look back

        Returns:
            Dict with regime analysis
        """
        try:
            # Get index data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=lookback_days + 50)  # Extra for SMA

            df = self.get_historical_data_range(
                index_symbol,
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d")
            )

            if df.empty:
                return {'regime': 'UNKNOWN', 'error': 'No data'}

            # Calculate moving averages
            df['SMA_20'] = df['Close'].rolling(window=20).mean()
            df['SMA_50'] = df['Close'].rolling(window=50).mean()

            current_price = df['Close'].iloc[-1]
            sma_20 = df['SMA_20'].iloc[-1]
            sma_50 = df['SMA_50'].iloc[-1]

            # Determine regime
            if current_price > sma_20 > sma_50:
                regime = 'BULLISH'
            elif current_price < sma_20 < sma_50:
                regime = 'BEARISH'
            else:
                regime = 'SIDEWAYS'

            # Calculate trend strength
            returns_20d = ((current_price / df['Close'].iloc[-20]) - 1) * 100

            result = {
                'index': index_symbol,
                'regime': regime,
                'current_price': round(current_price, 2),
                'sma_20': round(sma_20, 2),
                'sma_50': round(sma_50, 2),
                'returns_20d_pct': round(returns_20d, 2),
                'above_sma_20': current_price > sma_20,
                'above_sma_50': current_price > sma_50,
                'checked_at': datetime.now().isoformat()
            }

            self.logger.info(f"Market regime for {index_symbol}: {regime}")

            return result

        except Exception as e:
            self.logger.error(f"Error checking market regime: {e}")
            return {'regime': 'UNKNOWN', 'error': str(e)}


# Example usage
def example_usage():
    """Example usage of MarketDataFetcher"""

    fetcher = MarketDataFetcher()

    # Get historical data
    df = fetcher.get_historical_data('RELIANCE.NS', period='1y')
    print(f"Historical data shape: {df.shape}")
    print(df.head())

    # Get current price
    price = fetcher.get_current_price('RELIANCE.NS')
    print(f"\nCurrent price: {price}")

    # Get stock info
    info = fetcher.get_stock_info('RELIANCE.NS')
    print(f"\nStock info: {info['company_name']}, Sector: {info['sector']}")

    # Calculate returns
    returns = fetcher.calculate_returns('RELIANCE.NS', period='1y')
    print(f"\nReturns: {returns}")

    # Check market regime
    regime = fetcher.check_market_regime()
    print(f"\nMarket regime: {regime}")


if __name__ == '__main__':
    example_usage()
