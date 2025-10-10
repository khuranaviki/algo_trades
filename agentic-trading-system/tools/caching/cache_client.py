"""
File-based Cache Client using diskcache

Replacement for Redis - much simpler!

Features:
- Redis-like API
- No server setup
- File-based storage
- TTL support
- Thread-safe
- Fast enough for our use case
"""

import diskcache
from typing import Any, Optional
from pathlib import Path
import logging
import json


class CacheClient:
    """
    File-based cache client (Redis replacement)

    Much simpler than Redis:
    - No server setup
    - No configuration
    - Just works!

    API is similar to Redis for easy transition if needed later.
    """

    def __init__(self, cache_dir: str = "storage/cache"):
        """
        Initialize cache client

        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = cache_dir
        self.logger = logging.getLogger(__name__)

        # Ensure directory exists
        Path(cache_dir).mkdir(parents=True, exist_ok=True)

        # Initialize diskcache
        self.cache = diskcache.Cache(cache_dir)

        self.logger.info(f"Cache initialized at {cache_dir}")

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        try:
            value = self.cache.get(key)
            if value is not None:
                self.logger.debug(f"Cache HIT: {key}")
            else:
                self.logger.debug(f"Cache MISS: {key}")
            return value
        except Exception as e:
            self.logger.error(f"Error getting from cache: {e}")
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache (must be pickleable)
            ttl: Time to live in seconds (None = forever)

        Returns:
            True if successful
        """
        try:
            if ttl:
                self.cache.set(key, value, expire=ttl)
            else:
                self.cache.set(key, value)

            self.logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
            return True

        except Exception as e:
            self.logger.error(f"Error setting cache: {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        Delete key from cache

        Args:
            key: Cache key

        Returns:
            True if key existed
        """
        try:
            result = self.cache.delete(key)
            self.logger.debug(f"Cache DELETE: {key}")
            return result
        except Exception as e:
            self.logger.error(f"Error deleting from cache: {e}")
            return False

    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache

        Args:
            key: Cache key

        Returns:
            True if key exists and not expired
        """
        return key in self.cache

    def clear(self) -> bool:
        """
        Clear all cache entries

        Returns:
            True if successful
        """
        try:
            self.cache.clear()
            self.logger.info("Cache cleared")
            return True
        except Exception as e:
            self.logger.error(f"Error clearing cache: {e}")
            return False

    def get_stats(self) -> dict:
        """
        Get cache statistics

        Returns:
            Dict with cache stats
        """
        try:
            return {
                'size': len(self.cache),
                'volume': self.cache.volume(),
                'hits': getattr(self.cache, 'hits', 0),
                'misses': getattr(self.cache, 'misses', 0)
            }
        except Exception as e:
            self.logger.error(f"Error getting stats: {e}")
            return {}

    def keys(self, pattern: Optional[str] = None) -> list:
        """
        Get all keys matching pattern

        Args:
            pattern: Optional pattern to match (simple string contains)

        Returns:
            List of matching keys
        """
        try:
            all_keys = list(self.cache.iterkeys())

            if pattern:
                # Simple pattern matching (contains)
                return [k for k in all_keys if pattern in k]

            return all_keys

        except Exception as e:
            self.logger.error(f"Error getting keys: {e}")
            return []

    # Convenience methods for common cache patterns

    def get_or_set(
        self,
        key: str,
        default_func: callable,
        ttl: Optional[int] = None
    ) -> Any:
        """
        Get from cache, or set if not exists

        Args:
            key: Cache key
            default_func: Function to call if cache miss
            ttl: Time to live in seconds

        Returns:
            Cached or computed value
        """
        value = self.get(key)

        if value is None:
            value = default_func()
            self.set(key, value, ttl=ttl)

        return value

    def cache_backtest_result(
        self,
        ticker: str,
        strategy: str,
        result: dict,
        ttl: int = 7776000  # 90 days
    ):
        """
        Cache backtest result

        Args:
            ticker: Stock ticker
            strategy: Strategy name
            result: Backtest result dict
            ttl: Cache TTL (default 90 days)
        """
        key = f"backtest:{ticker}:{strategy}"
        self.set(key, result, ttl=ttl)
        self.logger.info(f"Cached backtest: {key}")

    def get_backtest_result(
        self,
        ticker: str,
        strategy: str
    ) -> Optional[dict]:
        """
        Get cached backtest result

        Args:
            ticker: Stock ticker
            strategy: Strategy name

        Returns:
            Cached backtest result or None
        """
        key = f"backtest:{ticker}:{strategy}"
        return self.get(key)

    def cache_management_analysis(
        self,
        ticker: str,
        quarter: str,
        analysis: dict,
        ttl: int = 7776000  # 90 days
    ):
        """
        Cache management quality analysis

        Args:
            ticker: Stock ticker
            quarter: Quarter (e.g., "Q1-2025")
            analysis: Analysis result dict
            ttl: Cache TTL (default 90 days)
        """
        key = f"management:{ticker}:{quarter}"
        self.set(key, analysis, ttl=ttl)
        self.logger.info(f"Cached management analysis: {key}")

    def get_management_analysis(
        self,
        ticker: str,
        quarter: str
    ) -> Optional[dict]:
        """
        Get cached management analysis

        Args:
            ticker: Stock ticker
            quarter: Quarter identifier

        Returns:
            Cached analysis or None
        """
        key = f"management:{ticker}:{quarter}"
        return self.get(key)

    def cache_fundamental_data(
        self,
        ticker: str,
        data: dict,
        ttl: int = 604800  # 7 days
    ):
        """
        Cache fundamental data

        Args:
            ticker: Stock ticker
            data: Fundamental data dict
            ttl: Cache TTL (default 7 days)
        """
        key = f"fundamental:{ticker}"
        self.set(key, data, ttl=ttl)
        self.logger.info(f"Cached fundamental data: {key}")

    def get_fundamental_data(self, ticker: str) -> Optional[dict]:
        """Get cached fundamental data"""
        key = f"fundamental:{ticker}"
        return self.get(key)

    def cache_sentiment_data(
        self,
        ticker: str,
        data: dict,
        ttl: int = 86400  # 1 day
    ):
        """
        Cache sentiment analysis

        Args:
            ticker: Stock ticker
            data: Sentiment data dict
            ttl: Cache TTL (default 1 day)
        """
        key = f"sentiment:{ticker}"
        self.set(key, data, ttl=ttl)
        self.logger.info(f"Cached sentiment data: {key}")

    def get_sentiment_data(self, ticker: str) -> Optional[dict]:
        """Get cached sentiment data"""
        key = f"sentiment:{ticker}"
        return self.get(key)


# Example usage
if __name__ == '__main__':
    # Initialize cache
    cache = CacheClient()

    # Basic operations
    cache.set('test_key', {'data': 'value'}, ttl=300)
    value = cache.get('test_key')
    print(f"Cached value: {value}")

    # Backtest caching
    backtest_result = {
        'win_rate': 75.5,
        'total_trades': 42,
        'sharpe_ratio': 1.8
    }
    cache.cache_backtest_result('RELIANCE.NS', 'RHS_BREAKOUT', backtest_result)

    # Retrieve
    cached = cache.get_backtest_result('RELIANCE.NS', 'RHS_BREAKOUT')
    print(f"\nCached backtest: {cached}")

    # Stats
    stats = cache.get_stats()
    print(f"\nCache stats: {stats}")

    # List keys
    keys = cache.keys()
    print(f"\nCache keys: {keys}")
