#!/usr/bin/env python3
"""
Configuration file for algorithmic trading system
"""

from datetime import datetime, timedelta

# ==============================================================================
# BACKTEST CONFIGURATION
# ==============================================================================

# Default backtest period
DEFAULT_START_DATE = (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')  # 2 years ago
DEFAULT_END_DATE = datetime.now().strftime('%Y-%m-%d')

# Portfolio settings
INITIAL_CASH = 100000  # Starting capital in INR
COMMISSION_RATE = 0.001  # 0.1% commission per trade

# ==============================================================================
# STRATEGY PARAMETERS
# ==============================================================================

# RHS Strategy Parameters
RHS_PARAMS = {
    'min_pattern_days': 100,
    'lookback_period': 200,
    'volume_threshold': 1.5,
    'pattern_symmetry_tolerance': 0.15,
    'min_depth_ratio': 0.10,
    'max_depth_ratio': 0.35,
    'risk_reward_ratio': 2.0,
    'stop_loss_pct': 0.08,
    'position_size_pct': 0.04,
}

# CWH Strategy Parameters
CWH_PARAMS = {
    'min_pattern_days': 100,
    'lookback_period': 200,
    'volume_threshold': 1.5,
    'min_cup_depth_pct': 0.12,
    'max_cup_depth_pct': 0.33,
    'max_handle_depth_ratio': 0.15,
    'min_handle_duration': 5,
    'max_handle_duration_ratio': 0.30,
    'risk_reward_ratio': 2.0,
    'position_size_pct': 0.04,
}

# Fundamental Screen Strategy Parameters
FUNDAMENTAL_PARAMS = {
    'min_revenue_growth': 20.0,
    'min_roce': 20.0,
    'min_roe': 15.0,
    'max_debt_equity': 1.0,
    'max_market_cap': 50000,
    'target_pct': 0.20,
    'stop_loss_pct': 0.10,
    'position_size_pct': 0.03,
    'max_positions': 5,
}

# Multibagger Strategy Parameters
MULTIBAGGER_PARAMS = {
    'min_revenue_growth': 25.0,
    'min_roce': 25.0,
    'min_roe': 20.0,
    'max_debt_equity': 0.5,
    'max_market_cap': 10000,
    'target_pct': 0.30,
    'stop_loss_pct': 0.12,
    'position_size_pct': 0.05,
    'max_positions': 3,
}

# ==============================================================================
# STOCK UNIVERSES
# ==============================================================================

# Nifty 50 stocks
NIFTY_50 = [
    'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS',
    'HINDUNILVR.NS', 'ITC.NS', 'SBIN.NS', 'BHARTIARTL.NS', 'KOTAKBANK.NS',
    'LT.NS', 'AXISBANK.NS', 'ASIANPAINT.NS', 'MARUTI.NS', 'SUNPHARMA.NS',
    'TITAN.NS', 'BAJFINANCE.NS', 'ULTRACEMCO.NS', 'NESTLEIND.NS', 'WIPRO.NS',
    'HCLTECH.NS', 'POWERGRID.NS', 'NTPC.NS', 'TATAMOTORS.NS', 'BAJAJFINSV.NS',
    'ONGC.NS', 'M&M.NS', 'TATASTEEL.NS', 'TECHM.NS', 'ADANIPORTS.NS',
]

# Mid-cap stocks (potential multibaggers)
MID_CAP_STOCKS = [
    'DELHIVERY.NS', 'ZOMATO.NS', 'PAYTM.NS', 'POLICYBZR.NS',
    'LALPATHLAB.NS', 'DIXON.NS', 'PERSISTENT.NS', 'COFORGE.NS',
    'MPHASIS.NS', 'IIFL.NS', 'SAIL.NS', 'BEL.NS',
]

# Sector-wise stock lists
SECTORS = {
    'PHARMA': [
        'SUNPHARMA.NS', 'DRREDDY.NS', 'CIPLA.NS', 'DIVISLAB.NS',
        'AUROPHARMA.NS', 'BIOCON.NS', 'TORNTPHARM.NS', 'LALPATHLAB.NS'
    ],
    'LOGISTICS': [
        'DELHIVERY.NS', 'BLUEDART.NS', 'VRL.NS', 'GATI.NS', 'TCI.NS'
    ],
    'IT': [
        'TCS.NS', 'INFY.NS', 'WIPRO.NS', 'HCLTECH.NS', 'TECHM.NS',
        'PERSISTENT.NS', 'COFORGE.NS', 'MPHASIS.NS'
    ],
    'BANKING': [
        'HDFCBANK.NS', 'ICICIBANK.NS', 'SBIN.NS', 'AXISBANK.NS',
        'KOTAKBANK.NS', 'INDUSINDBK.NS', 'BANDHANBNK.NS'
    ],
    'AUTO': [
        'MARUTI.NS', 'TATAMOTORS.NS', 'M&M.NS', 'BAJAJ-AUTO.NS',
        'HEROMOTOCO.NS', 'EICHERMOT.NS', 'TVSMOTOR.NS'
    ],
}

# Default stock list for testing
DEFAULT_STOCKS = ['RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS', 'DELHIVERY.NS']

# ==============================================================================
# DATA CONFIGURATION
# ==============================================================================

# Data directories
DATA_DIR = 'data'
RESULTS_DIR = 'backtest_results'
LOGS_DIR = 'logs'

# Data intervals
INTERVALS = {
    'DAILY': '1d',
    'WEEKLY': '1wk',
    'MONTHLY': '1mo',
}

# ==============================================================================
# RISK MANAGEMENT
# ==============================================================================

# Portfolio risk limits
MAX_PORTFOLIO_RISK = 0.20  # Maximum 20% of portfolio at risk
MAX_POSITION_SIZE = 0.05   # Maximum 5% per position
MAX_CONCURRENT_POSITIONS = 10

# Drawdown limits
MAX_DRAWDOWN_LIMIT = 0.25  # Stop trading if 25% drawdown

# ==============================================================================
# LOGGING CONFIGURATION
# ==============================================================================

LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def get_stock_universe(universe_name: str):
    """Get stock list by universe name"""
    universes = {
        'NIFTY50': NIFTY_50,
        'MIDCAP': MID_CAP_STOCKS,
        'DEFAULT': DEFAULT_STOCKS,
    }

    # Add sector universes
    for sector, stocks in SECTORS.items():
        universes[sector] = stocks

    return universes.get(universe_name.upper(), DEFAULT_STOCKS)


def get_strategy_params(strategy_name: str):
    """Get strategy parameters by strategy name"""
    params_map = {
        'RHS': RHS_PARAMS,
        'CWH': CWH_PARAMS,
        'FUNDAMENTAL': FUNDAMENTAL_PARAMS,
        'MULTIBAGGER': MULTIBAGGER_PARAMS,
    }

    return params_map.get(strategy_name.upper(), {})
