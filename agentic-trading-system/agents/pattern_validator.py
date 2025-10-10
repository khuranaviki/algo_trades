#!/usr/bin/env python3
"""
Pattern Backtest Validator

Tests historical pattern performance to validate if aggressive or conservative targets
should be used based on historical success rates.

Success Criteria:
- Aggressive targets: Require >70% historical success rate
- Conservative targets: Lower bar, focus on risk/reward ratio
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import logging


class PatternValidator:
    """Validates pattern performance through historical backtesting"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger('Agent.Pattern Validator')
        self.logger.setLevel(logging.INFO)

        # Success rate thresholds
        self.aggressive_target_threshold = config.get('aggressive_success_threshold', 0.70)  # 70%
        self.conservative_target_threshold = config.get('conservative_success_threshold', 0.55)  # 55%

        # Risk/Reward requirements
        self.min_risk_reward_ratio = config.get('min_risk_reward', 2.0)  # 2:1 minimum

        # Pattern detection windows
        self.cwh_lookback = 90  # Cup with Handle: last 90 days
        self.rhs_lookback = 60  # RHS: last 60 days

        # NO HOLDING PERIOD LIMIT for validation
        # Check if target was EVER hit in remaining historical data
        # This matches real trading behavior - hold until target or stop loss

        self.logger.info(f"Pattern Validator initialized")
        self.logger.info(f"  Aggressive target threshold: {self.aggressive_target_threshold*100}%")
        self.logger.info(f"  Conservative target threshold: {self.conservative_target_threshold*100}%")
        self.logger.info(f"  No holding period limit - check if target ever hit")

    def validate_pattern_history(
        self,
        data: pd.DataFrame,
        pattern_type: str,
        current_pattern: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate pattern by backtesting similar patterns in historical data

        Returns:
            {
                'aggressive_success_rate': float,  # Success rate for aggressive target
                'conservative_success_rate': float,  # Success rate for conservative target
                'use_aggressive': bool,  # Whether to use aggressive target
                'recommended_target': float,  # Which target to use
                'historical_patterns': int,  # Number of similar patterns found
                'avg_gain_aggressive': float,  # Average gain when aggressive target hit
                'avg_gain_conservative': float,  # Average gain for conservative
                'risk_reward_ratio': float,  # Risk/reward for recommended target
                'validation_passed': bool  # Overall validation result
            }
        """

        if pattern_type == 'CWH':
            return self._validate_cwh_pattern(data, current_pattern)
        elif pattern_type == 'RHS':
            return self._validate_rhs_pattern(data, current_pattern)
        else:
            return self._default_validation()

    def _validate_cwh_pattern(
        self,
        data: pd.DataFrame,
        current_pattern: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate Cup with Handle pattern through historical analysis"""

        self.logger.info("Validating Cup with Handle pattern...")

        # Extract current pattern characteristics
        current_entry = current_pattern['current_price']
        conservative_target = current_pattern['target_conservative']
        aggressive_target = current_pattern['target_aggressive']
        cup_depth_pct = current_pattern['cup_depth_pct']

        # Find all historical Cup with Handle patterns in the data
        historical_patterns = self._find_historical_cwh_patterns(data)

        if len(historical_patterns) < 3:
            self.logger.warning(f"Only {len(historical_patterns)} historical patterns found - insufficient data")
            return self._default_validation()

        self.logger.info(f"Found {len(historical_patterns)} historical Cup with Handle patterns")

        # Test each historical pattern
        aggressive_successes = 0
        conservative_successes = 0
        aggressive_gains = []
        conservative_gains = []

        for pattern in historical_patterns:
            entry_date = pattern['entry_date']
            entry_price = pattern['entry_price']
            pattern_conservative_target = pattern['conservative_target']
            pattern_aggressive_target = pattern['aggressive_target']

            # Get ALL future data after entry (no time limit)
            # Check if target was EVER hit in remaining data
            future_data = data.loc[entry_date:].iloc[1:]  # All future data, excluding entry day

            if len(future_data) == 0:
                continue

            # Check if conservative target was hit
            conservative_hit = (future_data['High'] >= pattern_conservative_target).any()
            if conservative_hit:
                conservative_successes += 1
                # Calculate gain
                hit_date = future_data[future_data['High'] >= pattern_conservative_target].index[0]
                gain_pct = ((pattern_conservative_target / entry_price) - 1) * 100
                conservative_gains.append(gain_pct)
            else:
                # Check final price if target not hit
                final_price = future_data['Close'].iloc[-1]
                gain_pct = ((final_price / entry_price) - 1) * 100
                conservative_gains.append(gain_pct)

            # Check if aggressive target was hit
            aggressive_hit = (future_data['High'] >= pattern_aggressive_target).any()
            if aggressive_hit:
                aggressive_successes += 1
                gain_pct = ((pattern_aggressive_target / entry_price) - 1) * 100
                aggressive_gains.append(gain_pct)
            else:
                final_price = future_data['Close'].iloc[-1]
                gain_pct = ((final_price / entry_price) - 1) * 100
                aggressive_gains.append(gain_pct)

        # Calculate success rates
        num_patterns = len(historical_patterns)
        aggressive_success_rate = aggressive_successes / num_patterns if num_patterns > 0 else 0
        conservative_success_rate = conservative_successes / num_patterns if num_patterns > 0 else 0

        avg_aggressive_gain = np.mean(aggressive_gains) if aggressive_gains else 0
        avg_conservative_gain = np.mean(conservative_gains) if conservative_gains else 0

        self.logger.info(f"Aggressive success rate: {aggressive_success_rate*100:.1f}% ({aggressive_successes}/{num_patterns})")
        self.logger.info(f"Conservative success rate: {conservative_success_rate*100:.1f}% ({conservative_successes}/{num_patterns})")
        self.logger.info(f"Avg aggressive gain: {avg_aggressive_gain:+.1f}%")
        self.logger.info(f"Avg conservative gain: {avg_conservative_gain:+.1f}%")

        # Decide which target to use
        use_aggressive = aggressive_success_rate >= self.aggressive_target_threshold
        use_conservative = conservative_success_rate >= self.conservative_target_threshold

        # Calculate risk/reward ratio
        if use_aggressive:
            recommended_target = aggressive_target
            potential_gain = ((aggressive_target / current_entry) - 1) * 100
        elif use_conservative:
            recommended_target = conservative_target
            potential_gain = ((conservative_target / current_entry) - 1) * 100
        else:
            # Neither meets threshold - reject pattern
            self.logger.warning("Pattern validation failed - neither target meets success threshold")
            return {
                'aggressive_success_rate': aggressive_success_rate,
                'conservative_success_rate': conservative_success_rate,
                'use_aggressive': False,
                'recommended_target': None,
                'historical_patterns': num_patterns,
                'avg_gain_aggressive': avg_aggressive_gain,
                'avg_gain_conservative': avg_conservative_gain,
                'risk_reward_ratio': 0,
                'validation_passed': False,
                'reason': f"Success rates too low (Agg: {aggressive_success_rate*100:.1f}%, Cons: {conservative_success_rate*100:.1f}%)"
            }

        # Calculate risk (stop loss at handle low)
        # Assume 2% stop loss below entry as standard
        stop_loss_pct = 2.0
        risk_reward_ratio = potential_gain / stop_loss_pct if stop_loss_pct > 0 else 0

        validation_passed = (
            (use_aggressive or use_conservative) and
            risk_reward_ratio >= self.min_risk_reward_ratio
        )

        if not validation_passed:
            self.logger.warning(f"Risk/reward ratio too low: {risk_reward_ratio:.2f} (need {self.min_risk_reward_ratio})")

        return {
            'aggressive_success_rate': aggressive_success_rate,
            'conservative_success_rate': conservative_success_rate,
            'use_aggressive': use_aggressive,
            'recommended_target': recommended_target,
            'historical_patterns': num_patterns,
            'avg_gain_aggressive': avg_aggressive_gain,
            'avg_gain_conservative': avg_conservative_gain,
            'risk_reward_ratio': risk_reward_ratio,
            'validation_passed': validation_passed,
            'potential_gain_pct': potential_gain,
            'target_type': 'aggressive' if use_aggressive else 'conservative'
        }

    def _find_historical_cwh_patterns(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Scan historical data for Cup with Handle patterns

        Returns list of historical patterns with entry dates and targets
        """
        patterns = []

        # Start from index 90 (need 90 days for pattern)
        # Scan up to current date - no need to reserve future days since we check ALL future data
        # Only stop at len(data)-1 to avoid checking the very last day (no future to validate)
        for i in range(self.cwh_lookback, len(data) - 1, 5):  # Check every 5 days
            window = data.iloc[i-self.cwh_lookback:i]

            if len(window) < self.cwh_lookback:
                continue

            # Check for Cup with Handle structure
            pattern = self._detect_cwh_in_window(window)

            if pattern:
                pattern['entry_date'] = data.index[i]
                patterns.append(pattern)

        return patterns

    def _detect_cwh_in_window(self, window: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """
        Detect if window contains a valid Cup with Handle pattern

        Simplified detection for historical validation
        """
        # Cup: first 70 days, Handle: last 20 days
        cup_section = window.iloc[:-20]
        handle_section = window.tail(20)

        if len(cup_section) < 50 or len(handle_section) < 15:
            return None

        # Find cup high and low
        cup_high = cup_section['High'].max()
        cup_low = cup_section['Low'].min()
        cup_depth = (cup_high - cup_low) / cup_high

        # Validate cup depth (8-40%)
        if not (0.08 <= cup_depth <= 0.40):
            return None

        # Check U-shape (low should be in middle section)
        cup_low_idx = cup_section['Low'].idxmin()
        cup_low_position = list(cup_section.index).index(cup_low_idx) / len(cup_section)

        if not (0.3 <= cup_low_position <= 0.7):
            return None  # Not a U-shape

        # Handle should be in upper portion
        handle_high = handle_section['High'].max()
        handle_low = handle_section['Low'].min()
        handle_depth = (handle_high - handle_low) / handle_high

        # Handle position relative to cup
        handle_position = (handle_low - cup_low) / (cup_high - cup_low)

        if handle_position < 0.35:  # Handle too low
            return None

        if handle_depth > 0.25:  # Handle too deep
            return None

        # Valid pattern found
        entry_price = window['Close'].iloc[-1]
        conservative_target = cup_high
        aggressive_target = cup_high + (cup_high - cup_low)

        return {
            'entry_price': entry_price,
            'conservative_target': conservative_target,
            'aggressive_target': aggressive_target,
            'cup_depth_pct': cup_depth * 100,
            'handle_position_pct': handle_position * 100
        }

    def _validate_rhs_pattern(
        self,
        data: pd.DataFrame,
        current_pattern: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate Reverse Head & Shoulders pattern"""

        self.logger.info("Validating Reverse Head & Shoulders pattern...")

        # Similar logic to CWH but for RHS
        # For now, return default validation
        # TODO: Implement RHS historical validation

        return self._default_validation()

    def _default_validation(self) -> Dict[str, Any]:
        """Return default validation when insufficient data"""
        return {
            'aggressive_success_rate': 0,
            'conservative_success_rate': 0,
            'use_aggressive': False,
            'recommended_target': None,
            'historical_patterns': 0,
            'avg_gain_aggressive': 0,
            'avg_gain_conservative': 0,
            'risk_reward_ratio': 0,
            'validation_passed': False,
            'reason': 'Insufficient historical data for validation'
        }

    def calculate_risk_reward(
        self,
        entry_price: float,
        target_price: float,
        stop_loss_price: float
    ) -> float:
        """
        Calculate risk/reward ratio

        Returns:
            Ratio of potential gain to potential loss
        """
        potential_gain = target_price - entry_price
        potential_loss = entry_price - stop_loss_price

        if potential_loss <= 0:
            return 0

        return potential_gain / potential_loss
