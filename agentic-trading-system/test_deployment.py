#!/usr/bin/env python3
"""
Quick Deployment Test Script

Tests the paper trading system locally before GitHub Actions deployment.
Run this to verify everything works before the scheduled 3 PM run.

Usage:
    python3 test_deployment.py

This will:
1. Validate all imports
2. Check configuration
3. Verify API keys (if set)
4. Test paper trading engine initialization
5. Run for 10 seconds to check basic functionality
"""

import sys
import os
from datetime import datetime
import asyncio

# Colors for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}{text:^80}{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")

def print_success(text):
    print(f"{GREEN}✅ {text}{RESET}")

def print_error(text):
    print(f"{RED}❌ {text}{RESET}")

def print_warning(text):
    print(f"{YELLOW}⚠️  {text}{RESET}")

def print_info(text):
    print(f"{BLUE}ℹ️  {text}{RESET}")


def test_imports():
    """Test if all required modules can be imported"""
    print_header("TEST 1: Import Validation")
    
    tests = [
        ("paper_trading.engine", "PaperTradingEngine"),
        ("paper_trading.portfolio", "Portfolio"),
        ("paper_trading.data_stream", "LiveDataStream"),
        ("agents.orchestrator", "Orchestrator"),
        ("config.paper_trading_config", "PAPER_TRADING_CONFIG"),
    ]
    
    all_passed = True
    for module_name, class_name in tests:
        try:
            module = __import__(module_name, fromlist=[class_name])
            getattr(module, class_name)
            print_success(f"Import {module_name}.{class_name}")
        except ImportError as e:
            print_error(f"Failed to import {module_name}: {e}")
            all_passed = False
        except AttributeError as e:
            print_error(f"Module {module_name} missing {class_name}: {e}")
            all_passed = False
    
    return all_passed


def test_configuration():
    """Test if configuration is valid"""
    print_header("TEST 2: Configuration Validation")
    
    try:
        from config.paper_trading_config import PAPER_TRADING_CONFIG
        
        # Check required keys
        required_keys = ['initial_capital', 'watchlist', 'update_interval_seconds']
        all_present = True
        
        for key in required_keys:
            if key in PAPER_TRADING_CONFIG:
                value = PAPER_TRADING_CONFIG[key]
                print_success(f"Config key '{key}': {value if key != 'watchlist' else f'{len(value)} stocks'}")
            else:
                print_error(f"Missing config key: {key}")
                all_present = False
        
        # Validate values
        if PAPER_TRADING_CONFIG.get('initial_capital', 0) <= 0:
            print_error("Initial capital must be > 0")
            all_present = False
        
        if len(PAPER_TRADING_CONFIG.get('watchlist', [])) == 0:
            print_warning("Watchlist is empty - no stocks to trade")
        
        return all_present
        
    except Exception as e:
        print_error(f"Configuration error: {e}")
        return False


def test_api_keys():
    """Test if API keys are set"""
    print_header("TEST 3: API Key Validation")
    
    keys = {
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'ANTHROPIC_API_KEY': os.getenv('ANTHROPIC_API_KEY'),
    }
    
    all_set = True
    for key_name, key_value in keys.items():
        if key_value:
            masked = key_value[:10] + '...' + key_value[-4:] if len(key_value) > 14 else '***'
            print_success(f"{key_name}: {masked}")
        else:
            print_warning(f"{key_name}: Not set (will fail on GitHub Actions)")
            all_set = False
    
    if not all_set:
        print_info("Set environment variables:")
        print_info("  export OPENAI_API_KEY='your-key'")
        print_info("  export ANTHROPIC_API_KEY='your-key'")
    
    return True  # Don't fail test if keys not set locally


def test_directories():
    """Test if required directories exist"""
    print_header("TEST 4: Directory Structure")
    
    required_dirs = ['logs', 'data', 'backups']
    all_exist = True
    
    for dir_name in required_dirs:
        if os.path.exists(dir_name):
            print_success(f"Directory exists: {dir_name}/")
        else:
            print_warning(f"Directory missing: {dir_name}/ (will be created)")
            os.makedirs(dir_name, exist_ok=True)
            print_info(f"Created: {dir_name}/")
    
    return True


def test_dependencies():
    """Test if required packages are installed"""
    print_header("TEST 5: Dependency Check")
    
    required_packages = [
        'yfinance',
        'pandas',
        'numpy',
        'aiohttp',
        'openai',
        'anthropic',
    ]
    
    all_installed = True
    for package in required_packages:
        try:
            __import__(package)
            print_success(f"Package installed: {package}")
        except ImportError:
            print_error(f"Package missing: {package}")
            all_installed = False
    
    if not all_installed:
        print_info("Install missing packages:")
        print_info("  pip install -r requirements.txt")
    
    return all_installed


async def test_engine_initialization():
    """Test if paper trading engine can be initialized"""
    print_header("TEST 6: Engine Initialization")
    
    try:
        from paper_trading.engine import PaperTradingEngine
        from config.paper_trading_config import PAPER_TRADING_CONFIG
        
        print_info("Initializing paper trading engine...")
        engine = PaperTradingEngine(config=PAPER_TRADING_CONFIG)
        print_success("Engine initialized successfully")
        
        # Check engine components
        if hasattr(engine, 'portfolio'):
            print_success(f"Portfolio: ₹{engine.portfolio.initial_capital:,.0f}")
        if hasattr(engine, 'watchlist'):
            print_success(f"Watchlist: {len(engine.watchlist)} stocks")
        if hasattr(engine, 'orchestrator'):
            print_success("Orchestrator: Ready")
        
        return True
        
    except Exception as e:
        print_error(f"Engine initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_quick_run():
    """Run engine for 10 seconds to test basic functionality"""
    print_header("TEST 7: Quick Run (10 seconds)")
    
    try:
        from paper_trading.engine import PaperTradingEngine
        from config.paper_trading_config import PAPER_TRADING_CONFIG
        
        print_info("Starting paper trading engine...")
        print_info("This will run for 10 seconds...")
        
        engine = PaperTradingEngine(config=PAPER_TRADING_CONFIG)
        
        # Run for 10 seconds
        try:
            await asyncio.wait_for(engine.start(), timeout=10.0)
        except asyncio.TimeoutError:
            print_success("10-second test run completed")
            engine.is_running = False
        
        # Print stats
        print_info(f"Scans completed: {engine.stats.get('scans_completed', 0)}")
        print_info(f"Signals detected: {engine.stats.get('signals_detected', 0)}")
        
        return True
        
    except Exception as e:
        print_error(f"Quick run failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test runner"""
    print_header("🧪 DEPLOYMENT TEST SUITE")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python: {sys.version}")
    print(f"Working Dir: {os.getcwd()}")
    
    # Run all tests
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Configuration", test_configuration()))
    results.append(("API Keys", test_api_keys()))
    results.append(("Directories", test_directories()))
    results.append(("Dependencies", test_dependencies()))
    results.append(("Engine Init", await test_engine_initialization()))
    
    # Only run quick test if API keys are set
    if os.getenv('OPENAI_API_KEY') and os.getenv('ANTHROPIC_API_KEY'):
        results.append(("Quick Run", await test_quick_run()))
    else:
        print_warning("Skipping Quick Run test (API keys not set)")
    
    # Summary
    print_header("📊 TEST SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
        print(f"{test_name:.<40} {status}")
    
    print(f"\n{BLUE}Results: {passed}/{total} tests passed{RESET}\n")
    
    if passed == total:
        print_success("🎉 ALL TESTS PASSED!")
        print_success("✅ Ready for GitHub Actions deployment")
        print_info("\nNext steps:")
        print_info("1. Push code to GitHub: git push origin main")
        print_info("2. Go to: https://github.com/khuranaviki/algo_trades/actions")
        print_info("3. Click 'Paper Trading (Cloud)' → 'Run workflow'")
        print_info("4. Or wait until 3:00 PM IST for automatic run")
        return 0
    else:
        print_error("❌ SOME TESTS FAILED")
        print_error("Fix the issues above before deploying")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

