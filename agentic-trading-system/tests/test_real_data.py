"""
Real Data Integration Test

Tests all implemented components with actual market data:
- Data fetchers (market + fundamental)
- Backtest Validator agent
- Fundamental Analyst agent
- Database + Cache
- LLM client (if API keys present)

Run: python tests/test_real_data.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import components
from tools.data_fetchers.market_data import MarketDataFetcher
from tools.data_fetchers.fundamental_data import FundamentalDataFetcher
from tools.storage.database import DatabaseClient
from tools.caching.cache_client import CacheClient
from agents.backtest_validator import BacktestValidator
from agents.fundamental_analyst import FundamentalAnalyst

# Test stocks from V40 universe
TEST_STOCKS = [
    'RELIANCE.NS',
    'TCS.NS',
    'HDFCBANK.NS',
    'INFY.NS',
]


class RealDataTester:
    """Comprehensive integration tester"""

    def __init__(self):
        self.results = {}
        self.passed = 0
        self.failed = 0

    def print_header(self, title: str):
        """Print formatted header"""
        print("\n" + "="*80)
        print(f"  {title}")
        print("="*80)

    def print_test(self, name: str, passed: bool, details: str = ""):
        """Print test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} | {name}")
        if details:
            print(f"       {details}")

        if passed:
            self.passed += 1
        else:
            self.failed += 1

    def print_summary(self):
        """Print test summary"""
        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0

        self.print_header("TEST SUMMARY")
        print(f"Total Tests:  {total}")
        print(f"Passed:       {self.passed} ✅")
        print(f"Failed:       {self.failed} ❌")
        print(f"Pass Rate:    {pass_rate:.1f}%")
        print()

        if self.failed == 0:
            print("🎉 ALL TESTS PASSED! System is working correctly.")
        else:
            print("⚠️  Some tests failed. Check the logs above.")

    async def test_market_data_fetcher(self):
        """Test 1: Market Data Fetcher"""
        self.print_header("TEST 1: Market Data Fetcher")

        fetcher = MarketDataFetcher()

        # Test 1.1: Get historical data
        try:
            df = fetcher.get_historical_data('RELIANCE.NS', period='1y')
            self.print_test(
                "Fetch 1-year historical data",
                not df.empty,
                f"Got {len(df)} rows"
            )
        except Exception as e:
            self.print_test("Fetch 1-year historical data", False, str(e))

        # Test 1.2: Get current price
        try:
            price = fetcher.get_current_price('RELIANCE.NS')
            self.print_test(
                "Get current price",
                price is not None and price > 0,
                f"₹{price}"
            )
        except Exception as e:
            self.print_test("Get current price", False, str(e))

        # Test 1.3: Get stock info
        try:
            info = fetcher.get_stock_info('RELIANCE.NS')
            self.print_test(
                "Get stock info",
                'company_name' in info,
                f"{info.get('company_name', 'N/A')}"
            )
        except Exception as e:
            self.print_test("Get stock info", False, str(e))

        # Test 1.4: Check market regime
        try:
            regime = fetcher.check_market_regime('^NSEI')
            self.print_test(
                "Check market regime (NIFTY)",
                'regime' in regime,
                f"Regime: {regime.get('regime', 'UNKNOWN')}"
            )
        except Exception as e:
            self.print_test("Check market regime", False, str(e))

    async def test_fundamental_data_fetcher(self):
        """Test 2: Fundamental Data Fetcher"""
        self.print_header("TEST 2: Fundamental Data Fetcher")

        fetcher = FundamentalDataFetcher()

        # Test 2.1: Get fundamental data
        try:
            data = fetcher.get_fundamental_data('RELIANCE.NS')
            self.print_test(
                "Fetch fundamental data",
                'company_name' in data and not data.get('error'),
                f"{data.get('company_name', 'N/A')} - PE: {data.get('pe_ratio', 'N/A')}"
            )

            # Test 2.2: Calculate financial health
            if not data.get('error'):
                health = fetcher.calculate_financial_health_score(data)
                self.print_test(
                    "Calculate financial health score",
                    'financial_health_score' in health,
                    f"Score: {health.get('percentage', 0)}% - {health.get('rating', 'N/A')}"
                )
        except Exception as e:
            self.print_test("Fetch fundamental data", False, str(e))

    async def test_database(self):
        """Test 3: Database Operations"""
        self.print_header("TEST 3: Database (SQLite)")

        db = DatabaseClient()

        # Test 3.1: Save trade
        try:
            trade_data = {
                'ticker': 'TEST.NS',
                'action': 'BUY',
                'quantity': 10,
                'price': 1000.50,
                'timestamp': datetime.now().isoformat(),
                'strategy': 'TEST_STRATEGY',
                'fundamental_score': 75.0,
                'technical_score': 80.0,
                'sentiment_score': 70.0,
                'management_score': 65.0,
                'backtest_validated': True,
                'notes': 'Integration test trade'
            }
            trade_id = db.save_trade(trade_data)
            self.print_test(
                "Save trade to database",
                trade_id > 0,
                f"Trade ID: {trade_id}"
            )

            # Test 3.2: Retrieve trade
            trades = db.get_trades(ticker='TEST.NS', limit=1)
            self.print_test(
                "Retrieve trade from database",
                len(trades) > 0,
                f"Found {len(trades)} trade(s)"
            )

        except Exception as e:
            self.print_test("Database operations", False, str(e))

        # Test 3.3: Save analysis
        try:
            analysis_data = {
                'ticker': 'TEST.NS',
                'agent_name': 'fundamental_analyst',
                'analysis_date': datetime.now().date().isoformat(),
                'score': 75.5,
                'recommendation': 'BUY',
                'details': {'test': 'data'}
            }
            analysis_id = db.save_analysis(analysis_data)
            self.print_test(
                "Save analysis to database",
                analysis_id > 0,
                f"Analysis ID: {analysis_id}"
            )
        except Exception as e:
            self.print_test("Save analysis", False, str(e))

    async def test_cache(self):
        """Test 4: Cache Operations"""
        self.print_header("TEST 4: Cache (diskcache)")

        cache = CacheClient()

        # Test 4.1: Set and get
        try:
            test_data = {'key': 'value', 'timestamp': datetime.now().isoformat()}
            cache.set('test_key', test_data, ttl=300)
            retrieved = cache.get('test_key')

            self.print_test(
                "Cache set and get",
                retrieved is not None and retrieved['key'] == 'value',
                f"Data cached and retrieved successfully"
            )

            # Test 4.2: Check exists
            exists = cache.exists('test_key')
            self.print_test(
                "Cache key exists check",
                exists,
                "Key exists in cache"
            )

            # Test 4.3: Delete
            deleted = cache.delete('test_key')
            not_exists = not cache.exists('test_key')
            self.print_test(
                "Cache delete",
                deleted and not_exists,
                "Key deleted successfully"
            )

        except Exception as e:
            self.print_test("Cache operations", False, str(e))

        # Test 4.4: Cache stats
        try:
            stats = cache.get_stats()
            self.print_test(
                "Cache statistics",
                'size' in stats,
                f"Cache size: {stats.get('size', 0)} items"
            )
        except Exception as e:
            self.print_test("Cache statistics", False, str(e))

    async def test_backtest_validator(self):
        """Test 5: Backtest Validator Agent"""
        self.print_header("TEST 5: Backtest Validator Agent")

        config = {
            'historical_years': 2,  # Use 2 years for faster testing
            'min_win_rate': 70.0,
            'min_trades': 5,  # Lower threshold for testing
            'use_market_regime_filter': True,
            'market_index': '^NSEI'
        }

        validator = BacktestValidator(config)

        # Test 5.1: Validate RHS pattern
        try:
            context = {
                'pattern': 'RHS',
                'strategy': 'rhs_breakout'
            }

            print("\n⏳ Running backtest (this may take 30-60 seconds)...")
            result = await validator.analyze('RELIANCE.NS', context)

            self.print_test(
                "RHS pattern backtest",
                'win_rate' in result,
                f"Win Rate: {result.get('win_rate', 0)}%, Trades: {result.get('total_trades', 0)}"
            )

            self.print_test(
                "Backtest validation logic",
                'validated' in result,
                f"Validated: {result.get('validated', False)}"
            )

        except Exception as e:
            self.print_test("Backtest validator", False, str(e))

        # Test 5.2: Cache check (second run should be instant)
        try:
            print("\n⏳ Testing cache (should be instant)...")
            start_time = datetime.now()
            result2 = await validator.analyze('RELIANCE.NS', context)
            duration = (datetime.now() - start_time).total_seconds()

            self.print_test(
                "Backtest cache hit",
                result2.get('cached', False) or duration < 2,
                f"Retrieved in {duration:.2f}s"
            )
        except Exception as e:
            self.print_test("Backtest cache", False, str(e))

    async def test_fundamental_analyst(self):
        """Test 6: Fundamental Analyst Agent"""
        self.print_header("TEST 6: Fundamental Analyst Agent")

        config = {
            'weights': {
                'financial_health': 0.30,
                'growth': 0.30,
                'valuation': 0.20,
                'quality': 0.20
            },
            'use_llm': False,  # Disable LLM for testing (requires API key)
            'scoring_criteria': {
                'financial_health': {
                    'debt_to_equity': {'excellent': 0.5, 'good': 1.0, 'average': 2.0},
                    'current_ratio': {'excellent': 2.0, 'good': 1.5, 'average': 1.0},
                    'interest_coverage': {'excellent': 5.0, 'good': 3.0, 'average': 2.0}
                },
                'growth': {
                    'revenue_growth_yoy': {'excellent': 20.0, 'good': 15.0, 'average': 10.0},
                    'profit_growth_yoy': {'excellent': 25.0, 'good': 20.0, 'average': 15.0}
                },
                'valuation': {
                    'pe_ratio': {'undervalued': 15.0, 'fair': 25.0, 'overvalued': 35.0},
                    'pb_ratio': {'undervalued': 2.0, 'fair': 4.0, 'overvalued': 6.0}
                },
                'quality': {
                    'roe': {'excellent': 20.0, 'good': 15.0, 'average': 10.0},
                    'roce': {'excellent': 18.0, 'good': 15.0, 'average': 12.0},
                    'operating_margin': {'excellent': 20.0, 'good': 15.0, 'average': 10.0}
                }
            }
        }

        analyst = FundamentalAnalyst(config)

        # Test 6.1: Analyze fundamentals
        try:
            print("\n⏳ Analyzing fundamentals...")
            result = await analyst.analyze('RELIANCE.NS', {})

            self.print_test(
                "Fundamental analysis",
                'score' in result and result['score'] >= 0,
                f"Score: {result.get('score', 0)}/100 - {result.get('recommendation', 'N/A')}"
            )

            # Test 6.2: Component scores
            components_exist = all([
                'financial_health' in result,
                'growth' in result,
                'valuation' in result,
                'quality' in result
            ])
            self.print_test(
                "Component scoring",
                components_exist,
                f"All 4 components scored"
            )

            # Test 6.3: Red flag detection
            self.print_test(
                "Red flag detection",
                'red_flags' in result,
                f"Found {len(result.get('red_flags', []))} red flag(s)"
            )

        except Exception as e:
            self.print_test("Fundamental analyst", False, str(e))

    async def test_full_pipeline(self):
        """Test 7: Full Pipeline (Multiple Stocks)"""
        self.print_header("TEST 7: Full Analysis Pipeline")

        # Initialize agents
        backtest_config = {
            'historical_years': 2,
            'min_win_rate': 70.0,
            'min_trades': 5,
            'use_market_regime_filter': True
        }

        fundamental_config = {
            'weights': {
                'financial_health': 0.30,
                'growth': 0.30,
                'valuation': 0.20,
                'quality': 0.20
            },
            'use_llm': False,
            'scoring_criteria': {
                'financial_health': {
                    'debt_to_equity': {'excellent': 0.5, 'good': 1.0, 'average': 2.0},
                    'current_ratio': {'excellent': 2.0, 'good': 1.5, 'average': 1.0}
                }
            }
        }

        validator = BacktestValidator(backtest_config)
        analyst = FundamentalAnalyst(fundamental_config)

        print(f"\n⏳ Analyzing {len(TEST_STOCKS)} stocks...")

        for ticker in TEST_STOCKS:
            try:
                print(f"\n--- {ticker} ---")

                # Get fundamental analysis
                fund_result = await analyst.analyze(ticker, {})
                print(f"  Fundamental Score: {fund_result.get('score', 0)}/100")

                # Get backtest validation
                backtest_context = {
                    'pattern': 'BREAKOUT',
                    'strategy': 'generic_breakout'
                }
                backtest_result = await validator.analyze(ticker, backtest_context)
                print(f"  Backtest Win Rate: {backtest_result.get('win_rate', 0)}%")
                print(f"  Backtest Validated: {backtest_result.get('validated', False)}")

                # Check if would pass both filters
                passes_fundamental = fund_result.get('score', 0) >= 50
                passes_backtest = backtest_result.get('validated', False)
                passes_both = passes_fundamental and passes_backtest

                status = "✅ WOULD TRADE" if passes_both else "❌ WOULD SKIP"
                print(f"  Decision: {status}")

            except Exception as e:
                print(f"  ❌ Error: {e}")

    async def run_all_tests(self):
        """Run all tests"""
        print("\n" + "="*80)
        print("  AGENTIC TRADING SYSTEM - REAL DATA INTEGRATION TEST")
        print("="*80)
        print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Run tests sequentially
        await self.test_market_data_fetcher()
        await self.test_fundamental_data_fetcher()
        await self.test_database()
        await self.test_cache()
        await self.test_backtest_validator()
        await self.test_fundamental_analyst()
        await self.test_full_pipeline()

        # Print summary
        self.print_summary()


async def main():
    """Main test runner"""
    tester = RealDataTester()
    await tester.run_all_tests()


if __name__ == '__main__':
    asyncio.run(main())
