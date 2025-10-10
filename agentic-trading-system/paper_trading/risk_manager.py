"""
Risk management module

Handles:
- Portfolio-level risk controls
- Position size validation
- Sector exposure limits
- Drawdown protection
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from .portfolio import Portfolio


class RiskManager:
    """Portfolio-level risk controls"""

    def __init__(self, config: Dict[str, Any]):
        """
        Args:
            config: Risk management configuration
        """
        # Position limits
        self.max_position_size_pct = config.get('max_position_size_pct', 5.0)
        self.max_open_positions = config.get('max_open_positions', 10)

        # Portfolio risk limits
        self.max_portfolio_risk_pct = config.get('max_portfolio_risk_pct', 2.0)
        self.max_sector_exposure_pct = config.get('max_sector_exposure_pct', 30.0)
        self.max_correlation_exposure = config.get('max_correlation_exposure', 0.7)

        # Drawdown protection
        self.max_drawdown_pct = config.get('max_drawdown_pct', 10.0)
        self.daily_loss_limit_pct = config.get('daily_loss_limit_pct', 3.0)

        # Dynamic risk adjustment
        self.reduce_size_on_losses = config.get('reduce_size_on_losses', True)
        self.loss_streak_threshold = config.get('loss_streak_threshold', 3)

        self.logger = logging.getLogger(__name__)

    def can_open_position(
        self,
        portfolio: Portfolio,
        ticker: str,
        analysis: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Check if position passes all risk checks

        Args:
            portfolio: Current portfolio
            ticker: Stock ticker
            analysis: Orchestrator analysis result

        Returns:
            (can_open, reasons) tuple
        """
        checks = []
        reasons = []

        # Check 1: Max open positions
        if len(portfolio.positions) >= self.max_open_positions:
            checks.append(False)
            reasons.append(
                f"Max positions limit: {len(portfolio.positions)}/{self.max_open_positions}"
            )
        else:
            checks.append(True)

        # Check 2: Position size limit
        current_price = analysis.get('current_price', 0)
        quantity = analysis.get('quantity', 0)
        estimated_cost = current_price * quantity

        total_value = portfolio.get_total_value()
        position_pct = (estimated_cost / total_value) * 100 if total_value > 0 else 0

        if position_pct > self.max_position_size_pct:
            checks.append(False)
            reasons.append(
                f"Position size {position_pct:.1f}% exceeds max {self.max_position_size_pct}%"
            )
        else:
            checks.append(True)

        # Check 3: Portfolio risk (stop-loss based)
        stop_loss = analysis.get('stop_loss')
        if stop_loss and current_price and stop_loss < current_price:
            risk_per_share = current_price - stop_loss
            total_risk = risk_per_share * quantity
            risk_pct = (total_risk / total_value) * 100 if total_value > 0 else 0

            if risk_pct > self.max_portfolio_risk_pct:
                checks.append(False)
                reasons.append(
                    f"Portfolio risk {risk_pct:.2f}% exceeds max {self.max_portfolio_risk_pct}%"
                )
            else:
                checks.append(True)
        else:
            # No valid stop loss
            checks.append(False)
            reasons.append("No valid stop loss provided")

        # Check 4: Drawdown limit
        current_drawdown = portfolio.get_current_drawdown_pct()
        if current_drawdown > self.max_drawdown_pct:
            checks.append(False)
            reasons.append(
                f"Drawdown {current_drawdown:.1f}% exceeds max {self.max_drawdown_pct}%"
            )
        else:
            checks.append(True)

        # Check 5: Daily loss limit
        if self._check_daily_loss_limit(portfolio):
            checks.append(False)
            reasons.append("Daily loss limit reached")
        else:
            checks.append(True)

        # Check 6: Cash availability
        if estimated_cost > portfolio.cash:
            checks.append(False)
            reasons.append(
                f"Insufficient cash: need ₹{estimated_cost:,.0f}, have ₹{portfolio.cash:,.0f}"
            )
        else:
            checks.append(True)

        # All checks must pass
        all_passed = all(checks)

        if not all_passed:
            self.logger.warning(f"❌ Risk checks failed for {ticker}:")
            for reason in reasons:
                self.logger.warning(f"   • {reason}")
        else:
            self.logger.info(f"✅ Risk checks passed for {ticker}")

        return all_passed, reasons

    def calculate_safe_position_size(
        self,
        portfolio: Portfolio,
        analysis: Dict[str, Any]
    ) -> int:
        """
        Calculate safe position size using Kelly Criterion with safety factor

        Args:
            portfolio: Current portfolio
            analysis: Orchestrator analysis with backtest data

        Returns:
            Number of shares to buy
        """
        current_price = analysis.get('current_price', 0)
        if current_price == 0:
            return 0

        # Extract backtest metrics
        backtest = analysis.get('backtest', {})
        win_rate = backtest.get('win_rate', 50) / 100
        avg_win_pct = backtest.get('avg_return_pct', 5) / 100
        avg_loss_pct = abs(backtest.get('avg_loss_pct', -3)) / 100

        # Kelly Criterion: f = (p * W - q * L) / W
        # where p = win probability, q = loss probability, W = avg win, L = avg loss
        if avg_win_pct == 0:
            kelly_fraction = 0.02  # Default 2%
        else:
            kelly_fraction = (win_rate * avg_win_pct - (1 - win_rate) * avg_loss_pct) / avg_win_pct
            kelly_fraction = max(0, min(kelly_fraction, 0.1))  # Cap at 10%

        # Use fraction of Kelly for safety (0.5x)
        safe_kelly = kelly_fraction * 0.5

        # Adjust based on composite score
        score = analysis.get('composite_score', 70)
        score_multiplier = min(score / 100, 1.0)

        # Adjust based on recent performance
        if self.reduce_size_on_losses:
            performance_multiplier = self._get_performance_multiplier(portfolio)
        else:
            performance_multiplier = 1.0

        # Final position fraction
        position_fraction = safe_kelly * score_multiplier * performance_multiplier

        # Calculate position value
        total_value = portfolio.get_total_value()
        position_value = total_value * position_fraction

        # Calculate quantity
        quantity = int(position_value / current_price)

        # Apply max position size limit
        max_position_value = total_value * (self.max_position_size_pct / 100)
        max_quantity = int(max_position_value / current_price)
        quantity = min(quantity, max_quantity)

        # Ensure we don't use more than 95% of available cash
        max_cash_quantity = int((portfolio.cash * 0.95) / current_price)
        quantity = min(quantity, max_cash_quantity)

        # Risk-based sizing (if stop loss available)
        stop_loss = analysis.get('stop_loss')
        if stop_loss and stop_loss < current_price:
            risk_per_share = current_price - stop_loss
            max_loss = total_value * (self.max_portfolio_risk_pct / 100)
            risk_based_quantity = int(max_loss / risk_per_share)

            # Use the more conservative of Kelly-based or risk-based
            quantity = min(quantity, risk_based_quantity)

        self.logger.info(
            f"📊 Position sizing for {analysis.get('ticker', 'UNKNOWN')}: "
            f"Kelly={kelly_fraction:.3f}, Safe Kelly={safe_kelly:.3f}, "
            f"Score mult={score_multiplier:.2f}, Perf mult={performance_multiplier:.2f}, "
            f"Final quantity={quantity}"
        )

        return max(1, quantity)  # Minimum 1 share

    def check_sector_exposure(
        self,
        portfolio: Portfolio,
        ticker: str,
        sector: str,
        estimated_cost: float
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if adding position would exceed sector exposure limit

        Args:
            portfolio: Current portfolio
            ticker: Stock ticker
            sector: Sector name
            estimated_cost: Cost of new position

        Returns:
            (within_limits, reason) tuple
        """
        # Calculate current sector exposure
        sector_exposure = self._calculate_sector_exposure(portfolio)

        current_sector_value = sector_exposure.get(sector, 0)
        total_value = portfolio.get_total_value()

        new_sector_value = current_sector_value + estimated_cost
        new_sector_pct = (new_sector_value / total_value) * 100 if total_value > 0 else 0

        if new_sector_pct > self.max_sector_exposure_pct:
            reason = (
                f"Sector exposure for {sector} would be {new_sector_pct:.1f}% "
                f"(max {self.max_sector_exposure_pct}%)"
            )
            self.logger.warning(f"⚠️ {reason}")
            return False, reason

        return True, None

    def should_reduce_position(
        self,
        portfolio: Portfolio,
        ticker: str,
        reason: str = "risk_management"
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if position should be reduced due to risk

        Args:
            portfolio: Current portfolio
            ticker: Stock ticker
            reason: Reason for check

        Returns:
            (should_reduce, reason) tuple
        """
        if ticker not in portfolio.positions:
            return False, None

        position = portfolio.positions[ticker]

        # Check 1: Large unrealized loss
        if position.unrealized_pnl_pct < -10:
            return True, f"Large unrealized loss: {position.unrealized_pnl_pct:.1f}%"

        # Check 2: Position exceeded time limit (e.g., 30 days)
        if position.days_held > 30:
            return True, f"Position held too long: {position.days_held} days"

        # Check 3: Portfolio drawdown excessive
        if portfolio.get_current_drawdown_pct() > self.max_drawdown_pct:
            return True, "Portfolio drawdown excessive"

        return False, None

    def _check_daily_loss_limit(self, portfolio: Portfolio) -> bool:
        """Check if daily loss limit reached"""
        if not portfolio.daily_snapshots:
            return False

        # Get today's start value
        today_start = portfolio.daily_snapshots[-1]['total_value'] if portfolio.daily_snapshots else portfolio.initial_capital
        current_value = portfolio.get_total_value()

        daily_return_pct = ((current_value - today_start) / today_start) * 100

        if daily_return_pct < -self.daily_loss_limit_pct:
            self.logger.error(
                f"🚨 DAILY LOSS LIMIT HIT: {daily_return_pct:.2f}% "
                f"(limit: -{self.daily_loss_limit_pct}%)"
            )
            return True

        return False

    def _get_performance_multiplier(self, portfolio: Portfolio) -> float:
        """
        Calculate performance multiplier based on recent trades

        Returns multiplier between 0.5 and 1.5:
        - Winning streak: increase size (up to 1.5x)
        - Losing streak: decrease size (down to 0.5x)
        """
        if not portfolio.trade_history:
            return 1.0

        # Look at last 5 trades
        recent_trades = [t for t in portfolio.trade_history if t.action == 'SELL'][-5:]

        if not recent_trades:
            return 1.0

        # Count consecutive wins/losses
        consecutive_wins = 0
        consecutive_losses = 0

        for trade in reversed(recent_trades):
            if trade.realized_pnl and trade.realized_pnl > 0:
                consecutive_wins += 1
                consecutive_losses = 0
            elif trade.realized_pnl and trade.realized_pnl < 0:
                consecutive_losses += 1
                consecutive_wins = 0
            else:
                break

        # Adjust multiplier
        if consecutive_wins >= 3:
            multiplier = min(1.0 + (consecutive_wins * 0.1), 1.5)
            self.logger.info(f"🔥 Win streak: {consecutive_wins} trades, size multiplier: {multiplier:.2f}x")
        elif consecutive_losses >= self.loss_streak_threshold:
            multiplier = max(1.0 - (consecutive_losses * 0.1), 0.5)
            self.logger.warning(f"📉 Loss streak: {consecutive_losses} trades, size multiplier: {multiplier:.2f}x")
        else:
            multiplier = 1.0

        return multiplier

    def _calculate_sector_exposure(self, portfolio: Portfolio) -> Dict[str, float]:
        """
        Calculate current exposure by sector

        Returns:
            Dict of sector -> total value
        """
        sector_exposure = {}

        for ticker, position in portfolio.positions.items():
            # In real implementation, fetch sector from metadata
            # For now, simplified
            sector = self._get_sector(ticker)
            sector_exposure[sector] = sector_exposure.get(sector, 0) + position.market_value

        return sector_exposure

    def _get_sector(self, ticker: str) -> str:
        """
        Get sector for ticker

        In real implementation, this would query a database or API
        For now, simplified mapping
        """
        # Simplified sector mapping (expand in production)
        sector_map = {
            'RELIANCE.NS': 'Energy',
            'TCS.NS': 'IT',
            'INFY.NS': 'IT',
            'HDFCBANK.NS': 'Financials',
            'ICICIBANK.NS': 'Financials',
            'BAJFINANCE.NS': 'Financials',
            'BHARTIARTL.NS': 'Telecom',
            'MARUTI.NS': 'Auto',
            'TATAMOTORS.NS': 'Auto',
            'TITAN.NS': 'Consumer'
        }

        return sector_map.get(ticker, 'Other')

    def get_risk_report(self, portfolio: Portfolio) -> Dict[str, Any]:
        """
        Generate comprehensive risk report

        Args:
            portfolio: Current portfolio

        Returns:
            Dict with risk metrics
        """
        total_value = portfolio.get_total_value()
        current_drawdown = portfolio.get_current_drawdown_pct()

        # Sector exposure
        sector_exposure = self._calculate_sector_exposure(portfolio)
        sector_pct = {
            sector: (value / total_value) * 100 if total_value > 0 else 0
            for sector, value in sector_exposure.items()
        }

        # Position concentration
        position_sizes = [
            (pos.market_value / total_value) * 100 if total_value > 0 else 0
            for pos in portfolio.positions.values()
        ]

        max_position_size = max(position_sizes) if position_sizes else 0

        # Risk utilization
        num_positions = len(portfolio.positions)
        position_utilization = (num_positions / self.max_open_positions) * 100

        drawdown_utilization = (current_drawdown / self.max_drawdown_pct) * 100

        return {
            'total_value': total_value,
            'current_drawdown_pct': current_drawdown,
            'num_positions': num_positions,
            'max_position_size_pct': max_position_size,
            'sector_exposure': sector_pct,
            'utilization': {
                'positions': position_utilization,
                'drawdown': drawdown_utilization
            },
            'limits': {
                'max_positions': self.max_open_positions,
                'max_position_size_pct': self.max_position_size_pct,
                'max_drawdown_pct': self.max_drawdown_pct,
                'max_sector_exposure_pct': self.max_sector_exposure_pct
            }
        }
