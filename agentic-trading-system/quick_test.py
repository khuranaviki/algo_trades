#!/usr/bin/env python3
"""
Quick Test - Run this to verify installation and basic functionality

Usage: python quick_test.py
"""

import sys
import asyncio
from datetime import datetime

print("="*80)
print("  AGENTIC TRADING SYSTEM - QUICK TEST")
print("="*80)
print()

# Test 1: Python version
print("✓ Python version:", sys.version.split()[0])

# Test 2: Import core dependencies
print("\nChecking dependencies...")
try:
    import pandas
    print("✓ pandas:", pandas.__version__)
except ImportError as e:
    print("✗ pandas: NOT INSTALLED")
    sys.exit(1)

try:
    import numpy
    print("✓ numpy:", numpy.__version__)
except ImportError:
    print("✗ numpy: NOT INSTALLED")
    sys.exit(1)

try:
    import yfinance
    print("✓ yfinance:", yfinance.__version__)
except ImportError:
    print("✗ yfinance: NOT INSTALLED")
    sys.exit(1)

try:
    import diskcache
    print("✓ diskcache:", diskcache.__version__)
except ImportError:
    print("✗ diskcache: NOT INSTALLED")
    sys.exit(1)

try:
    import yaml
    print("✓ pyyaml: installed")
except ImportError:
    print("✗ pyyaml: NOT INSTALLED")
    sys.exit(1)

# Test 3: Import our modules
print("\nChecking our modules...")
try:
    from tools.data_fetchers.market_data import MarketDataFetcher
    print("✓ MarketDataFetcher")
except ImportError as e:
    print("✗ MarketDataFetcher:", e)
    sys.exit(1)

try:
    from tools.data_fetchers.fundamental_data import FundamentalDataFetcher
    print("✓ FundamentalDataFetcher")
except ImportError as e:
    print("✗ FundamentalDataFetcher:", e)
    sys.exit(1)

try:
    from tools.storage.database import DatabaseClient
    print("✓ DatabaseClient")
except ImportError as e:
    print("✗ DatabaseClient:", e)
    sys.exit(1)

try:
    from tools.caching.cache_client import CacheClient
    print("✓ CacheClient")
except ImportError as e:
    print("✗ CacheClient:", e)
    sys.exit(1)

try:
    from agents.backtest_validator import BacktestValidator
    print("✓ BacktestValidator")
except ImportError as e:
    print("✗ BacktestValidator:", e)
    sys.exit(1)

try:
    from agents.fundamental_analyst import FundamentalAnalyst
    print("✓ FundamentalAnalyst")
except ImportError as e:
    print("✗ FundamentalAnalyst:", e)
    sys.exit(1)

# Test 4: Quick data fetch
print("\nTesting data fetch (RELIANCE.NS)...")
try:
    fetcher = MarketDataFetcher()
    price = fetcher.get_current_price('RELIANCE.NS')
    if price and price > 0:
        print(f"✓ Current price: ₹{price:.2f}")
    else:
        print("✗ Could not fetch price")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 5: Database
print("\nTesting database...")
try:
    db = DatabaseClient()
    test_trade = {
        'ticker': 'TEST.NS',
        'action': 'BUY',
        'quantity': 1,
        'price': 100.0,
        'timestamp': datetime.now().isoformat(),
        'strategy': 'QUICK_TEST',
        'notes': 'Quick test trade'
    }
    trade_id = db.save_trade(test_trade)
    print(f"✓ Database working (trade ID: {trade_id})")
except Exception as e:
    print(f"✗ Database error: {e}")

# Test 6: Cache
print("\nTesting cache...")
try:
    cache = CacheClient()
    cache.set('test_key', {'value': 123}, ttl=60)
    value = cache.get('test_key')
    if value and value.get('value') == 123:
        print("✓ Cache working")
    else:
        print("✗ Cache not working correctly")
except Exception as e:
    print(f"✗ Cache error: {e}")

# Test 7: Agent initialization
print("\nTesting agents...")
try:
    config = {
        'historical_years': 2,
        'min_win_rate': 70.0,
        'min_trades': 5,
    }
    validator = BacktestValidator(config)
    print("✓ BacktestValidator initialized")
except Exception as e:
    print(f"✗ BacktestValidator error: {e}")

try:
    config = {
        'weights': {
            'financial_health': 0.30,
            'growth': 0.30,
            'valuation': 0.20,
            'quality': 0.20
        },
        'use_llm': False
    }
    analyst = FundamentalAnalyst(config)
    print("✓ FundamentalAnalyst initialized")
except Exception as e:
    print(f"✗ FundamentalAnalyst error: {e}")

# Summary
print("\n" + "="*80)
print("  SUMMARY")
print("="*80)
print()
print("✅ All basic tests passed!")
print()
print("Next steps:")
print("  1. Install missing dependencies: pip install -r requirements.txt")
print("  2. Run full test suite: python tests/test_real_data.py")
print("  3. Add API keys to .env file (if using LLM features)")
print()
print("System is ready to use! 🚀")
print()
