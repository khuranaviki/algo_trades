"""
Portfolio management module

Handles:
- Position tracking
- Trade history
- P&L calculation
- Performance metrics
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import uuid4
import pandas as pd
import numpy as np


@dataclass
class Position:
    """Single stock position"""
    ticker: str
    quantity: int
    avg_entry_price: float
    current_price: float
    stop_loss: Optional[float] = None
    target_price: Optional[float] = None
    entry_date: datetime = field(default_factory=datetime.now)
    entry_reasoning: str = ""

    @property
    def market_value(self) -> float:
        """Current market value"""
        return self.quantity * self.current_price

    @property
    def cost_basis(self) -> float:
        """Total cost"""
        return self.quantity * self.avg_entry_price

    @property
    def unrealized_pnl(self) -> float:
        """Unrealized profit/loss in rupees"""
        return self.market_value - self.cost_basis

    @property
    def unrealized_pnl_pct(self) -> float:
        """Unrealized profit/loss as percentage"""
        if self.cost_basis == 0:
            return 0.0
        return (self.unrealized_pnl / self.cost_basis) * 100

    @property
    def days_held(self) -> int:
        """Days since entry"""
        return (datetime.now() - self.entry_date).days

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'ticker': self.ticker,
            'quantity': self.quantity,
            'avg_entry_price': self.avg_entry_price,
            'current_price': self.current_price,
            'market_value': self.market_value,
            'cost_basis': self.cost_basis,
            'unrealized_pnl': self.unrealized_pnl,
            'unrealized_pnl_pct': self.unrealized_pnl_pct,
            'stop_loss': self.stop_loss,
            'target_price': self.target_price,
            'entry_date': self.entry_date,
            'days_held': self.days_held
        }


@dataclass
class Trade:
    """Executed trade record"""
    trade_id: str = field(default_factory=lambda: str(uuid4()))
    ticker: str = ""
    action: str = ""  # BUY, SELL
    quantity: int = 0
    price: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    reason: str = ""
    transaction_cost: float = 0.0
    realized_pnl: Optional[float] = None
    realized_pnl_pct: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'trade_id': self.trade_id,
            'ticker': self.ticker,
            'action': self.action,
            'quantity': self.quantity,
            'price': self.price,
            'timestamp': self.timestamp,
            'reason': self.reason,
            'transaction_cost': self.transaction_cost,
            'realized_pnl': self.realized_pnl,
            'realized_pnl_pct': self.realized_pnl_pct
        }


class Portfolio:
    """Manage virtual portfolio state"""

    def __init__(self, initial_capital: float = 1000000):
        """
        Args:
            initial_capital: Starting cash in rupees
        """
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: Dict[str, Position] = {}
        self.trade_history: List[Trade] = []
        self.daily_snapshots: List[Dict[str, Any]] = []

        self.logger = logging.getLogger(__name__)

    def get_total_value(self, current_prices: Optional[Dict[str, float]] = None) -> float:
        """
        Calculate total portfolio value

        Args:
            current_prices: Optional dict of ticker -> price (if None, uses position.current_price)

        Returns:
            Total value in rupees
        """
        if current_prices:
            # Update position prices first
            self.update_prices(current_prices)

        positions_value = sum(pos.market_value for pos in self.positions.values())
        return self.cash + positions_value

    def get_total_return_pct(self) -> float:
        """Total return as percentage"""
        total_value = self.get_total_value()
        if self.initial_capital == 0:
            return 0.0
        return ((total_value - self.initial_capital) / self.initial_capital) * 100

    def get_unrealized_pnl(self) -> float:
        """Total unrealized P&L across all positions"""
        return sum(pos.unrealized_pnl for pos in self.positions.values())

    def get_realized_pnl(self) -> float:
        """Total realized P&L from closed trades"""
        return sum(
            trade.realized_pnl for trade in self.trade_history
            if trade.realized_pnl is not None
        )

    def get_position_size(
        self,
        ticker: str,
        score: float,
        risk_level: str,
        current_price: float,
        stop_loss: Optional[float] = None
    ) -> int:
        """
        Calculate safe position size

        Uses simplified Kelly Criterion or fixed-fractional based on score

        Args:
            ticker: Stock ticker
            score: Composite score (0-100)
            risk_level: 'low', 'medium', 'high'
            current_price: Current stock price
            stop_loss: Stop loss price (for risk-based sizing)

        Returns:
            Number of shares to buy
        """
        # Base position size as % of portfolio
        if risk_level == 'low':
            base_pct = 0.02  # 2%
        elif risk_level == 'medium':
            base_pct = 0.03  # 3%
        else:
            base_pct = 0.05  # 5%

        # Adjust by score (score of 100 = full position, 70 = 70% of base)
        score_multiplier = min(score / 100, 1.0)
        position_pct = base_pct * score_multiplier

        # Calculate position value
        total_value = self.get_total_value()
        position_value = total_value * position_pct

        # If stop loss provided, use risk-based sizing
        if stop_loss and stop_loss < current_price:
            risk_per_share = current_price - stop_loss
            risk_pct = 0.01  # Risk 1% of portfolio per trade
            max_loss = total_value * risk_pct
            quantity = int(max_loss / risk_per_share)
        else:
            # Simple value-based sizing
            quantity = int(position_value / current_price)

        # Ensure we have enough cash
        cost = quantity * current_price
        if cost > self.cash * 0.95:  # Use max 95% of cash per trade
            quantity = int((self.cash * 0.95) / current_price)

        return max(1, quantity)  # Minimum 1 share

    def can_open_position(self, ticker: str, estimated_cost: float) -> bool:
        """Check if we have enough cash"""
        if ticker in self.positions:
            self.logger.warning(f"⚠️ Already have position in {ticker}")
            return False

        if estimated_cost > self.cash:
            self.logger.warning(
                f"⚠️ Insufficient cash: need ₹{estimated_cost:,.0f}, have ₹{self.cash:,.0f}"
            )
            return False

        return True

    def open_position(
        self,
        ticker: str,
        quantity: int,
        price: float,
        stop_loss: Optional[float],
        target: Optional[float],
        reason: str,
        transaction_cost: float = 0.0
    ) -> Trade:
        """
        Execute BUY and open position

        Args:
            ticker: Stock ticker
            quantity: Number of shares
            price: Fill price
            stop_loss: Stop loss price
            target: Target price
            reason: Entry reasoning
            transaction_cost: Total transaction costs

        Returns:
            Trade object
        """
        if ticker in self.positions:
            raise ValueError(f"Position already exists for {ticker}")

        # Calculate total cost
        total_cost = (quantity * price) + transaction_cost

        if total_cost > self.cash:
            raise ValueError(f"Insufficient cash: need ₹{total_cost:,.0f}, have ₹{self.cash:,.0f}")

        # Deduct cash
        self.cash -= total_cost

        # Create position
        position = Position(
            ticker=ticker,
            quantity=quantity,
            avg_entry_price=price,
            current_price=price,
            stop_loss=stop_loss,
            target_price=target,
            entry_date=datetime.now(),
            entry_reasoning=reason
        )

        self.positions[ticker] = position

        # Record trade
        trade = Trade(
            ticker=ticker,
            action='BUY',
            quantity=quantity,
            price=price,
            timestamp=datetime.now(),
            reason=reason,
            transaction_cost=transaction_cost
        )

        self.trade_history.append(trade)

        self.logger.info(
            f"✅ OPENED {ticker}: {quantity} shares @ ₹{price:.2f} "
            f"(Total: ₹{quantity * price:,.0f}, Cost: ₹{transaction_cost:.2f})"
        )

        return trade

    def close_position(
        self,
        ticker: str,
        price: float,
        reason: str,
        transaction_cost: float = 0.0
    ) -> Trade:
        """
        Execute SELL and close position

        Args:
            ticker: Stock ticker
            price: Fill price
            reason: Exit reasoning
            transaction_cost: Total transaction costs

        Returns:
            Trade object with realized P&L
        """
        if ticker not in self.positions:
            raise ValueError(f"No position exists for {ticker}")

        position = self.positions[ticker]

        # Calculate proceeds
        proceeds = (position.quantity * price) - transaction_cost

        # Add to cash
        self.cash += proceeds

        # Calculate realized P&L
        realized_pnl = proceeds - position.cost_basis
        realized_pnl_pct = (realized_pnl / position.cost_basis) * 100

        # Record trade
        trade = Trade(
            ticker=ticker,
            action='SELL',
            quantity=position.quantity,
            price=price,
            timestamp=datetime.now(),
            reason=reason,
            transaction_cost=transaction_cost,
            realized_pnl=realized_pnl,
            realized_pnl_pct=realized_pnl_pct
        )

        self.trade_history.append(trade)

        # Remove position
        del self.positions[ticker]

        pnl_emoji = "🟢" if realized_pnl > 0 else "🔴"
        self.logger.info(
            f"{pnl_emoji} CLOSED {ticker}: {trade.quantity} shares @ ₹{price:.2f} | "
            f"P&L: ₹{realized_pnl:,.2f} ({realized_pnl_pct:+.2f}%) | Reason: {reason}"
        )

        return trade

    def update_prices(self, current_prices: Dict[str, float]):
        """Update current prices for all positions"""
        for ticker, position in self.positions.items():
            if ticker in current_prices:
                position.current_price = current_prices[ticker]

    def take_snapshot(self):
        """Take daily portfolio snapshot for performance tracking"""
        snapshot = {
            'timestamp': datetime.now(),
            'total_value': self.get_total_value(),
            'cash': self.cash,
            'positions_value': sum(pos.market_value for pos in self.positions.values()),
            'num_positions': len(self.positions),
            'unrealized_pnl': self.get_unrealized_pnl(),
            'realized_pnl': self.get_realized_pnl()
        }

        self.daily_snapshots.append(snapshot)

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics"""

        total_value = self.get_total_value()
        total_return_pct = self.get_total_return_pct()

        # Trade statistics
        closed_trades = [t for t in self.trade_history if t.action == 'SELL']
        winning_trades = [t for t in closed_trades if t.realized_pnl and t.realized_pnl > 0]
        losing_trades = [t for t in closed_trades if t.realized_pnl and t.realized_pnl < 0]

        win_rate = (len(winning_trades) / len(closed_trades) * 100) if closed_trades else 0

        avg_win = np.mean([t.realized_pnl_pct for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t.realized_pnl_pct for t in losing_trades]) if losing_trades else 0

        # Sharpe ratio (if we have daily snapshots)
        sharpe_ratio = 0.0
        if len(self.daily_snapshots) > 1:
            values = [s['total_value'] for s in self.daily_snapshots]
            returns = np.diff(values) / values[:-1]
            if len(returns) > 0 and np.std(returns) > 0:
                sharpe_ratio = (np.mean(returns) * 252) / (np.std(returns) * np.sqrt(252))

        # Max drawdown
        max_drawdown = 0.0
        if len(self.daily_snapshots) > 1:
            values = [s['total_value'] for s in self.daily_snapshots]
            peak = values[0]
            for value in values:
                if value > peak:
                    peak = value
                drawdown = ((peak - value) / peak) * 100
                if drawdown > max_drawdown:
                    max_drawdown = drawdown

        return {
            'total_value': total_value,
            'cash': self.cash,
            'total_return_pct': total_return_pct,
            'unrealized_pnl': self.get_unrealized_pnl(),
            'realized_pnl': self.get_realized_pnl(),
            'num_positions': len(self.positions),
            'total_trades': len(self.trade_history),
            'closed_trades': len(closed_trades),
            'win_rate': win_rate,
            'avg_win_pct': avg_win,
            'avg_loss_pct': avg_loss,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown_pct': max_drawdown
        }

    def get_positions_df(self) -> pd.DataFrame:
        """Get positions as DataFrame"""
        if not self.positions:
            return pd.DataFrame()

        data = [pos.to_dict() for pos in self.positions.values()]
        return pd.DataFrame(data)

    def get_trades_df(self) -> pd.DataFrame:
        """Get trade history as DataFrame"""
        if not self.trade_history:
            return pd.DataFrame()

        data = [trade.to_dict() for trade in self.trade_history]
        return pd.DataFrame(data)

    def get_equity_curve(self) -> pd.DataFrame:
        """Get equity curve from snapshots"""
        if not self.daily_snapshots:
            return pd.DataFrame()

        df = pd.DataFrame(self.daily_snapshots)
        df.set_index('timestamp', inplace=True)
        return df

    def get_current_drawdown_pct(self) -> float:
        """Get current drawdown from peak"""
        if not self.daily_snapshots:
            return 0.0

        values = [s['total_value'] for s in self.daily_snapshots]
        peak = max(values)
        current = self.get_total_value()

        if peak == 0:
            return 0.0

        return ((peak - current) / peak) * 100
