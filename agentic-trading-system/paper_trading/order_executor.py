"""
Order execution simulator

Handles:
- Market order simulation with slippage
- Stop-loss and target checking
- Transaction cost application
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from .portfolio import Position
from .transaction_costs import TransactionCostModel


class OrderExecutor:
    """Simulates realistic order execution"""

    def __init__(
        self,
        slippage_pct: float = 0.05,
        use_realistic_costs: bool = True
    ):
        """
        Args:
            slippage_pct: Slippage percentage (default 0.05%)
            use_realistic_costs: Use realistic NSE transaction costs
        """
        self.slippage_pct = slippage_pct
        self.use_realistic_costs = use_realistic_costs
        self.transaction_cost_model = TransactionCostModel()

        self.logger = logging.getLogger(__name__)

    def execute_market_order(
        self,
        ticker: str,
        action: str,
        quantity: int,
        current_price: float,
        bid: Optional[float] = None,
        ask: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Simulate market order execution

        Args:
            ticker: Stock ticker
            action: 'BUY' or 'SELL'
            quantity: Number of shares
            current_price: Current market price
            bid: Bid price (optional, for more realistic execution)
            ask: Ask price (optional, for more realistic execution)

        Returns:
            Dict with execution details
        """
        # Determine fill price with slippage
        if action == 'BUY':
            # BUY at ask price (if available) + slippage
            base_price = ask if ask else current_price
            fill_price = base_price * (1 + self.slippage_pct / 100)

        elif action == 'SELL':
            # SELL at bid price (if available) - slippage
            base_price = bid if bid else current_price
            fill_price = base_price * (1 - self.slippage_pct / 100)

        else:
            raise ValueError(f"Invalid action: {action}. Must be 'BUY' or 'SELL'")

        # Calculate order value
        order_value = fill_price * quantity

        # Calculate transaction costs
        if self.use_realistic_costs:
            costs = self.transaction_cost_model.calculate_total_cost(order_value, action)
            transaction_cost = costs['total']
        else:
            # Simple 0.1% flat cost
            transaction_cost = order_value * 0.001

        # Slippage cost
        if action == 'BUY':
            slippage_cost = (fill_price - base_price) * quantity
        else:
            slippage_cost = (base_price - fill_price) * quantity

        self.logger.info(
            f"💱 {action} {ticker}: {quantity} shares @ ₹{fill_price:.2f} "
            f"(Slippage: ₹{slippage_cost:.2f}, Costs: ₹{transaction_cost:.2f})"
        )

        return {
            'status': 'filled',
            'ticker': ticker,
            'action': action,
            'quantity': quantity,
            'requested_price': current_price,
            'fill_price': fill_price,
            'order_value': order_value,
            'slippage_cost': slippage_cost,
            'transaction_cost': transaction_cost,
            'total_cost': order_value + transaction_cost if action == 'BUY' else order_value - transaction_cost,
            'timestamp': datetime.now()
        }

    def check_stop_loss(
        self,
        position: Position,
        current_price: float,
        buffer_pct: float = 0.0
    ) -> bool:
        """
        Check if stop loss should trigger

        Args:
            position: Current position
            current_price: Current market price
            buffer_pct: Buffer percentage (e.g., 0.1 = trigger at 0.1% below stop)

        Returns:
            True if stop loss hit
        """
        if not position.stop_loss:
            return False

        # Calculate trigger price with buffer
        trigger_price = position.stop_loss * (1 - buffer_pct / 100)

        if current_price <= trigger_price:
            self.logger.warning(
                f"🛑 STOP LOSS HIT: {position.ticker} @ ₹{current_price:.2f} "
                f"(Stop: ₹{position.stop_loss:.2f}, Loss: {position.unrealized_pnl_pct:.2f}%)"
            )
            return True

        return False

    def check_target(
        self,
        position: Position,
        current_price: float,
        buffer_pct: float = 0.0
    ) -> bool:
        """
        Check if target price reached

        Args:
            position: Current position
            current_price: Current market price
            buffer_pct: Buffer percentage (e.g., 0.1 = trigger at 0.1% above target)

        Returns:
            True if target reached
        """
        if not position.target_price:
            return False

        # Calculate trigger price with buffer
        trigger_price = position.target_price * (1 + buffer_pct / 100)

        if current_price >= trigger_price:
            self.logger.info(
                f"🎯 TARGET REACHED: {position.ticker} @ ₹{current_price:.2f} "
                f"(Target: ₹{position.target_price:.2f}, Gain: {position.unrealized_pnl_pct:.2f}%)"
            )
            return True

        return False

    def check_trailing_stop(
        self,
        position: Position,
        current_price: float,
        trailing_pct: float = 5.0
    ) -> bool:
        """
        Check trailing stop loss

        Args:
            position: Current position
            current_price: Current market price
            trailing_pct: Trailing stop percentage (default 5%)

        Returns:
            True if trailing stop hit
        """
        # Calculate peak price since entry
        peak_price = max(position.avg_entry_price, current_price)

        # Calculate trailing stop level
        trailing_stop = peak_price * (1 - trailing_pct / 100)

        if current_price <= trailing_stop:
            self.logger.warning(
                f"🔻 TRAILING STOP HIT: {position.ticker} @ ₹{current_price:.2f} "
                f"(Peak: ₹{peak_price:.2f}, Trail: {trailing_pct}%)"
            )
            return True

        return False

    def simulate_partial_fill(
        self,
        ticker: str,
        action: str,
        requested_quantity: int,
        current_price: float,
        volume: int,
        max_order_size_pct: float = 5.0
    ) -> Dict[str, Any]:
        """
        Simulate partial fill for large orders

        Args:
            ticker: Stock ticker
            action: 'BUY' or 'SELL'
            requested_quantity: Requested shares
            current_price: Current price
            volume: Current trading volume
            max_order_size_pct: Max % of volume per order (default 5%)

        Returns:
            Dict with partial fill details
        """
        max_quantity = int(volume * max_order_size_pct / 100)

        if requested_quantity <= max_quantity:
            # Full fill possible
            return self.execute_market_order(ticker, action, requested_quantity, current_price)

        else:
            # Partial fill
            filled_quantity = max_quantity
            self.logger.warning(
                f"⚠️ PARTIAL FILL: {ticker} - requested {requested_quantity}, "
                f"filled {filled_quantity} ({filled_quantity/requested_quantity*100:.1f}%)"
            )

            result = self.execute_market_order(ticker, action, filled_quantity, current_price)
            result['status'] = 'partially_filled'
            result['requested_quantity'] = requested_quantity
            result['fill_percentage'] = (filled_quantity / requested_quantity) * 100

            return result
