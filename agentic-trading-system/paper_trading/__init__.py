"""
Paper Trading System

Simulates live trading with realistic constraints:
- Real-time data streaming
- Order execution with slippage and transaction costs
- Portfolio management
- Risk controls
"""

from .engine import PaperTradingEngine
from .portfolio import Portfolio, Position, Trade
from .order_executor import OrderExecutor
from .data_stream import LiveDataStream, PriceCache
from .risk_manager import RiskManager
from .transaction_costs import TransactionCostModel

__all__ = [
    'PaperTradingEngine',
    'Portfolio',
    'Position',
    'Trade',
    'OrderExecutor',
    'LiveDataStream',
    'PriceCache',
    'RiskManager',
    'TransactionCostModel'
]

__version__ = '1.0.0'
