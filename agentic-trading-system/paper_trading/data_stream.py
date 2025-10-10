"""
Real-time data streaming module

Handles:
- Live price streaming (yfinance with 1-min intervals)
- Price caching for technical analysis
- Market hours detection (NSE)
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Callable, Optional, Any
import pandas as pd
import yfinance as yf
import pytz
from collections import deque


class LiveDataStream:
    """Real-time price streaming with configurable intervals"""

    def __init__(
        self,
        tickers: List[str],
        update_interval: int = 60,
        max_cache_days: int = 1825
    ):
        """
        Args:
            tickers: List of stock tickers to stream
            update_interval: Seconds between updates (default 60)
            max_cache_days: Max days of historical data to cache
        """
        self.tickers = tickers
        self.update_interval = update_interval
        self.max_cache_days = max_cache_days

        self.cache = PriceCache(max_history_days=max_cache_days)
        self.subscribers: List[Callable] = []
        self.is_running = False

        self.logger = logging.getLogger(__name__)

    async def start(self):
        """Start streaming prices"""
        self.is_running = True
        self.logger.info(f"📡 Starting data stream for {len(self.tickers)} tickers")

        # Load initial historical data for each ticker
        for ticker in self.tickers:
            await self._load_initial_history(ticker)

        # Start update loop
        while self.is_running:
            if self.is_market_open()['open']:
                await self._update_prices()

            await asyncio.sleep(self.update_interval)

    async def _load_initial_history(self, ticker: str):
        """Load historical data for technical analysis"""
        try:
            self.logger.info(f"📥 Loading {self.max_cache_days} days of history for {ticker}")

            # Download historical data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.max_cache_days)

            stock = yf.Ticker(ticker)
            df = stock.history(start=start_date, end=end_date, interval='1d')

            if df.empty:
                self.logger.warning(f"⚠️ No historical data for {ticker}")
                return

            # Add to cache
            for timestamp, row in df.iterrows():
                price_data = {
                    'ticker': ticker,
                    'timestamp': timestamp,
                    'open': row['Open'],
                    'high': row['High'],
                    'low': row['Low'],
                    'close': row['Close'],
                    'volume': row['Volume']
                }
                self.cache.update(ticker, price_data)

            self.logger.info(
                f"✅ Loaded {len(df)} days of history for {ticker} "
                f"({df.index[0].date()} to {df.index[-1].date()})"
            )

        except Exception as e:
            self.logger.error(f"❌ Failed to load history for {ticker}: {e}")

    async def _update_prices(self):
        """Fetch latest prices for all tickers"""
        try:
            for ticker in self.tickers:
                price_data = await self.get_latest_price(ticker)

                if price_data:
                    # Update cache
                    self.cache.update(ticker, price_data)

                    # Notify subscribers
                    for callback in self.subscribers:
                        try:
                            await callback(ticker, price_data)
                        except Exception as e:
                            self.logger.error(f"Subscriber callback failed: {e}")

        except Exception as e:
            self.logger.error(f"❌ Price update failed: {e}")

    async def get_latest_price(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get latest price with OHLCV"""
        try:
            stock = yf.Ticker(ticker)

            # Get latest data (1-day interval, last 2 days)
            df = stock.history(period='2d', interval='1d')

            if df.empty:
                self.logger.warning(f"⚠️ No price data for {ticker}")
                return None

            latest = df.iloc[-1]

            # Get current price (last trade)
            info = stock.info
            current_price = info.get('currentPrice') or info.get('regularMarketPrice') or latest['Close']

            price_data = {
                'ticker': ticker,
                'timestamp': datetime.now(pytz.timezone('Asia/Kolkata')),
                'price': current_price,
                'open': latest['Open'],
                'high': latest['High'],
                'low': latest['Low'],
                'close': latest['Close'],
                'volume': latest['Volume'],
                'bid': info.get('bid', current_price * 0.9995),
                'ask': info.get('ask', current_price * 1.0005)
            }

            return price_data

        except Exception as e:
            self.logger.error(f"❌ Failed to get price for {ticker}: {e}")
            return None

    def subscribe(self, callback: Callable):
        """Subscribe to price updates"""
        self.subscribers.append(callback)

    def stop(self):
        """Stop streaming"""
        self.is_running = False
        self.logger.info("🛑 Data stream stopped")

    @staticmethod
    def is_market_open() -> Dict[str, Any]:
        """Check if NSE is currently open"""
        ist = pytz.timezone('Asia/Kolkata')
        now = datetime.now(ist)

        # NSE hours: 9:15 AM - 3:30 PM IST, Mon-Fri
        weekday = now.weekday()

        if weekday >= 5:  # Saturday (5) or Sunday (6)
            next_monday = now + timedelta(days=(7 - weekday))
            next_open = next_monday.replace(hour=9, minute=15, second=0, microsecond=0)
            return {
                'open': False,
                'reason': 'weekend',
                'opens_at': next_open
            }

        # Check if market holiday (simplified - can be enhanced with holiday calendar)
        market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
        market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)

        if now < market_open:
            return {
                'open': False,
                'reason': 'before_market',
                'opens_at': market_open,
                'closes_at': market_close
            }
        elif now > market_close:
            next_open = (now + timedelta(days=1)).replace(hour=9, minute=15, second=0, microsecond=0)
            return {
                'open': False,
                'reason': 'after_market',
                'opens_at': next_open
            }
        else:
            return {
                'open': True,
                'closes_at': market_close,
                'time_remaining_minutes': int((market_close - now).total_seconds() / 60)
            }


class PriceCache:
    """Cache recent prices for technical analysis"""

    def __init__(self, max_history_days: int = 1825):
        """
        Args:
            max_history_days: Maximum days of history to keep (default 5 years)
        """
        self.max_history_days = max_history_days
        self.cache: Dict[str, deque] = {}
        self.logger = logging.getLogger(__name__)

    def update(self, ticker: str, price_data: Dict[str, Any]):
        """Add new price data"""
        if ticker not in self.cache:
            self.cache[ticker] = deque(maxlen=self.max_history_days * 2)  # Buffer for weekends

        self.cache[ticker].append(price_data)

        # Log every 10th update to avoid spam
        if len(self.cache[ticker]) % 10 == 0:
            self.logger.debug(f"💾 Cache updated: {ticker} has {len(self.cache[ticker])} data points")

    def get_history(self, ticker: str, days: Optional[int] = None) -> pd.DataFrame:
        """
        Get historical data as DataFrame

        Args:
            ticker: Stock ticker
            days: Number of days to return (None = all available)

        Returns:
            DataFrame with OHLCV data
        """
        if ticker not in self.cache or len(self.cache[ticker]) == 0:
            self.logger.warning(f"⚠️ No cached data for {ticker}")
            return pd.DataFrame()

        data = list(self.cache[ticker])

        if days:
            data = data[-days:]

        df = pd.DataFrame(data)

        # Set timestamp as index
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)

        # Ensure numeric columns
        numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'price']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        return df

    def has_sufficient_data(self, ticker: str, min_days: int) -> bool:
        """Check if we have enough data for analysis"""
        if ticker not in self.cache:
            return False

        return len(self.cache[ticker]) >= min_days

    def get_latest(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get most recent price data"""
        if ticker not in self.cache or len(self.cache[ticker]) == 0:
            return None

        return self.cache[ticker][-1]

    def clear(self, ticker: Optional[str] = None):
        """Clear cache for ticker or all"""
        if ticker:
            if ticker in self.cache:
                self.cache[ticker].clear()
                self.logger.info(f"🗑️ Cleared cache for {ticker}")
        else:
            self.cache.clear()
            self.logger.info("🗑️ Cleared all cache")
