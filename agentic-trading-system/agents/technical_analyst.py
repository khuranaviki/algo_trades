"""
Technical Analyst Agent

Analyzes technical indicators and chart patterns to identify trading opportunities.
Focuses on momentum, trend, volume, and volatility indicators.

All detected patterns are then sent to Backtest Validator for >70% win rate verification.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
import logging

from agents.base_agent import BaseAgent
from tools.data_fetchers.market_data import MarketDataFetcher
from agents.pattern_validator import PatternValidator


class TechnicalAnalyst(BaseAgent):
    """
    Analyzes technical indicators and patterns

    Core responsibilities:
    1. Calculate technical indicators (RSI, MACD, Bollinger Bands, etc.)
    2. Detect chart patterns (RHS, CWH, Golden Cross, etc.)
    3. Analyze volume and momentum
    4. Generate technical score (0-100)
    5. Provide context for Backtest Validator

    Technical Score Breakdown:
    - Trend Indicators (30%): SMA crossovers, MACD, ADX
    - Momentum (25%): RSI, Stochastic, ROC
    - Volume (25%): OBV, Volume trend, Money Flow
    - Volatility (20%): Bollinger Bands, ATR, Keltner Channels
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Technical Analyst

        Args:
            config: Configuration dict with indicator settings
        """
        super().__init__("Technical Analyst", config)

        self.market_data = MarketDataFetcher()

        # Indicator settings
        self.lookback_days = config.get('lookback_days', 1825)  # 5 years default
        self.rsi_period = config.get('rsi_period', 14)
        self.macd_fast = config.get('macd_fast', 12)
        self.macd_slow = config.get('macd_slow', 26)
        self.macd_signal = config.get('macd_signal', 9)
        self.bb_period = config.get('bb_period', 20)
        self.bb_std = config.get('bb_std', 2)

        # Scoring weights
        self.weights = {
            'trend': 0.30,
            'momentum': 0.25,
            'volume': 0.25,
            'volatility': 0.20
        }

        # Pattern detection settings
        self.detect_patterns = config.get('detect_patterns', True)
        self.min_pattern_confidence = config.get('min_pattern_confidence', 60.0)  # Fuzzy logic threshold

        # Pattern validator for historical backtesting
        self.validate_patterns = config.get('validate_patterns', True)
        self.pattern_validator = PatternValidator(config) if self.validate_patterns else None

    async def analyze(self, ticker: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform technical analysis on a stock

        Args:
            ticker: Stock ticker
            context: Additional context (market regime, etc.)

        Returns:
            Dict with technical analysis results
        """
        if not self.validate_input(ticker):
            return self._error_response(ticker, "Invalid ticker")

        self.logger.info(f"Analyzing technicals for {ticker}")

        try:
            # Get historical data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.lookback_days)

            hist_data = self.market_data.get_historical_data_range(
                ticker, start_date, end_date
            )

            if hist_data is None or hist_data.empty:
                return self._error_response(ticker, "No historical data available")

            if len(hist_data) < 50:
                return self._error_response(ticker, f"Insufficient data: {len(hist_data)} days")

            # Calculate all indicators
            indicators = self._calculate_indicators(hist_data)

            # Score each category
            trend_score = self._score_trend(indicators, hist_data)
            momentum_score = self._score_momentum(indicators, hist_data)
            volume_score = self._score_volume(indicators, hist_data)
            volatility_score = self._score_volatility(indicators, hist_data)

            # Calculate composite technical score
            composite_score = (
                trend_score['score'] * self.weights['trend'] +
                momentum_score['score'] * self.weights['momentum'] +
                volume_score['score'] * self.weights['volume'] +
                volatility_score['score'] * self.weights['volatility']
            )

            # Detect patterns
            patterns = []
            if self.detect_patterns:
                patterns = self._detect_all_patterns(hist_data, indicators)

                # Validate patterns against historical performance
                if self.pattern_validator and patterns:
                    validated_patterns = []
                    for pattern in patterns:
                        if pattern['type'] in ['CWH', 'RHS']:  # Only validate actionable patterns
                            validation = self.pattern_validator.validate_pattern_history(
                                hist_data, pattern['type'], pattern
                            )

                            if validation['validation_passed']:
                                # Update pattern with validation results
                                pattern['validation'] = validation
                                pattern['recommended_target'] = validation['recommended_target']
                                pattern['target_type'] = validation['target_type']
                                pattern['risk_reward_ratio'] = validation['risk_reward_ratio']
                                validated_patterns.append(pattern)

                                target_type = validation['target_type']
                                success_rate_key = f"{target_type}_success_rate"
                                success_rate = validation[success_rate_key] * 100
                                self.logger.info(f"✅ {pattern['name']} validated: {target_type} target "
                                               f"(success rate: {success_rate:.1f}%)")
                            else:
                                self.logger.warning(f"❌ {pattern['name']} failed validation: {validation.get('reason', 'Unknown')}")
                        else:
                            # Keep non-validated patterns (like Golden Cross)
                            validated_patterns.append(pattern)

                    patterns = validated_patterns

            # Find strongest pattern for backtesting
            primary_pattern = self._select_primary_pattern(patterns)

            # Generate signals
            signals = self._generate_signals(indicators, hist_data, primary_pattern)

            # Build result
            result = {
                'score': round(composite_score, 2),
                'ticker': ticker,
                'timestamp': datetime.now().isoformat(),

                # Category scores
                'trend': trend_score,
                'momentum': momentum_score,
                'volume': volume_score,
                'volatility': volatility_score,

                # Indicators
                'indicators': self._format_indicators(indicators),

                # Patterns
                'patterns': patterns,
                'primary_pattern': primary_pattern,

                # Signals
                'signals': signals,

                # Context for Backtest Validator
                'backtest_context': {
                    'pattern': primary_pattern.get('type') if primary_pattern else None,
                    'entry_price': hist_data['Close'].iloc[-1],
                    'support': self._find_support(hist_data),
                    'resistance': self._find_resistance(hist_data),
                    'atr': indicators.get('atr'),
                    'volume_trend': volume_score.get('trend')
                },

                # Summary
                'summary': self._generate_summary(composite_score, patterns, signals)
            }

            self.log_analysis(ticker, result)
            return result

        except Exception as e:
            self.logger.error(f"Error analyzing {ticker}: {e}")
            return self._error_response(ticker, str(e))

    def _calculate_indicators(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate all technical indicators"""
        indicators = {}

        # Close prices
        close = data['Close']
        high = data['High']
        low = data['Low']
        volume = data['Volume']

        # Trend Indicators
        indicators['sma_20'] = close.rolling(window=20).mean().iloc[-1]
        indicators['sma_50'] = close.rolling(window=50).mean().iloc[-1] if len(data) >= 50 else None
        indicators['sma_200'] = close.rolling(window=200).mean().iloc[-1] if len(data) >= 200 else None
        indicators['ema_12'] = close.ewm(span=12).mean().iloc[-1]
        indicators['ema_26'] = close.ewm(span=26).mean().iloc[-1]

        # MACD
        ema_12 = close.ewm(span=self.macd_fast).mean()
        ema_26 = close.ewm(span=self.macd_slow).mean()
        macd_line = ema_12 - ema_26
        signal_line = macd_line.ewm(span=self.macd_signal).mean()
        indicators['macd'] = macd_line.iloc[-1]
        indicators['macd_signal'] = signal_line.iloc[-1]
        indicators['macd_histogram'] = (macd_line - signal_line).iloc[-1]

        # RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        indicators['rsi'] = (100 - (100 / (1 + rs))).iloc[-1]

        # Bollinger Bands
        bb_middle = close.rolling(window=self.bb_period).mean()
        bb_std = close.rolling(window=self.bb_period).std()
        indicators['bb_upper'] = (bb_middle + (bb_std * self.bb_std)).iloc[-1]
        indicators['bb_middle'] = bb_middle.iloc[-1]
        indicators['bb_lower'] = (bb_middle - (bb_std * self.bb_std)).iloc[-1]
        indicators['bb_width'] = ((indicators['bb_upper'] - indicators['bb_lower']) / indicators['bb_middle']) * 100

        # ATR (Average True Range)
        high_low = high - low
        high_close = np.abs(high - close.shift())
        low_close = np.abs(low - close.shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        indicators['atr'] = tr.rolling(window=14).mean().iloc[-1]

        # ADX (Average Directional Index)
        indicators['adx'] = self._calculate_adx(data)

        # Stochastic Oscillator
        stoch = self._calculate_stochastic(data, period=14)
        indicators['stoch_k'] = stoch['%K']
        indicators['stoch_d'] = stoch['%D']

        # Volume indicators
        indicators['volume_sma_20'] = volume.rolling(window=20).mean().iloc[-1]
        indicators['volume_ratio'] = volume.iloc[-1] / indicators['volume_sma_20']

        # OBV (On-Balance Volume)
        obv = (np.sign(close.diff()) * volume).fillna(0).cumsum()
        indicators['obv'] = obv.iloc[-1]
        indicators['obv_trend'] = 'up' if obv.iloc[-1] > obv.iloc[-20] else 'down'

        # Current price
        indicators['current_price'] = close.iloc[-1]

        return indicators

    def _calculate_adx(self, data: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average Directional Index"""
        try:
            high = data['High']
            low = data['Low']
            close = data['Close']

            plus_dm = high.diff()
            minus_dm = -low.diff()

            plus_dm[plus_dm < 0] = 0
            minus_dm[minus_dm < 0] = 0

            tr = pd.concat([
                high - low,
                np.abs(high - close.shift()),
                np.abs(low - close.shift())
            ], axis=1).max(axis=1)

            atr = tr.rolling(window=period).mean()

            plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
            minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)

            dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
            adx = dx.rolling(window=period).mean()

            return adx.iloc[-1]
        except:
            return None

    def _calculate_stochastic(self, data: pd.DataFrame, period: int = 14) -> Dict[str, float]:
        """Calculate Stochastic Oscillator"""
        try:
            high = data['High']
            low = data['Low']
            close = data['Close']

            low_min = low.rolling(window=period).min()
            high_max = high.rolling(window=period).max()

            k = 100 * ((close - low_min) / (high_max - low_min))
            d = k.rolling(window=3).mean()

            return {
                '%K': k.iloc[-1],
                '%D': d.iloc[-1]
            }
        except:
            return {'%K': None, '%D': None}

    def _score_trend(self, indicators: Dict[str, Any], data: pd.DataFrame) -> Dict[str, Any]:
        """
        Score trend indicators (0-100)

        MEAN REVERSION STRATEGY:
        - BUY when price is BELOW moving averages (stock is oversold/undervalued)
        - Best setup: 200 > 50 > 20 > Price (bearish alignment ready to reverse)
        """
        score = 50  # Neutral
        signals = []

        current_price = indicators['current_price']

        # MEAN REVERSION: Price below MAs is BULLISH (buying opportunity)
        if indicators['sma_20'] and current_price < indicators['sma_20']:
            score += 10
            signals.append("Below SMA-20 (oversold)")

        if indicators['sma_50'] and current_price < indicators['sma_50']:
            score += 10
            signals.append("Below SMA-50 (oversold)")

        if indicators['sma_200'] and current_price < indicators['sma_200']:
            score += 15
            signals.append("Below SMA-200 (oversold)")

        # Perfect mean reversion setup: 200 > 50 > 20 (bearish alignment)
        if indicators['sma_50'] and indicators['sma_200'] and indicators['sma_20']:
            if indicators['sma_200'] > indicators['sma_50'] > indicators['sma_20']:
                score += 15
                signals.append("Perfect mean reversion setup (200>50>20)")
            elif indicators['sma_50'] < indicators['sma_200']:
                # Death Cross is actually BULLISH for mean reversion
                score += 5
                signals.append("Death Cross zone (mean reversion opportunity)")

        # MACD
        if indicators['macd_histogram'] > 0:
            score += 10
            signals.append("MACD bullish")
        else:
            score -= 5

        # ADX strength
        if indicators['adx']:
            if indicators['adx'] > 25:
                score += 5
                signals.append(f"Strong trend (ADX: {indicators['adx']:.1f})")

        score = max(0, min(100, score))

        return {
            'score': score,
            'signals': signals,
            'macd_histogram': indicators['macd_histogram'],
            'adx': indicators['adx'],
            'position': 'above' if current_price > indicators.get('sma_50', 0) else 'below'
        }

    def _score_momentum(self, indicators: Dict[str, Any], data: pd.DataFrame) -> Dict[str, Any]:
        """Score momentum indicators (0-100)"""
        score = 50
        signals = []

        rsi = indicators['rsi']

        # RSI scoring
        if rsi < 30:
            score += 20
            signals.append(f"RSI oversold ({rsi:.1f})")
        elif rsi < 40:
            score += 10
            signals.append(f"RSI bullish ({rsi:.1f})")
        elif rsi > 70:
            score -= 20
            signals.append(f"RSI overbought ({rsi:.1f})")
        elif rsi > 60:
            score -= 5
            signals.append(f"RSI elevated ({rsi:.1f})")
        else:
            signals.append(f"RSI neutral ({rsi:.1f})")

        # Stochastic
        if indicators['stoch_k'] and indicators['stoch_d']:
            if indicators['stoch_k'] < 20:
                score += 10
                signals.append("Stochastic oversold")
            elif indicators['stoch_k'] > 80:
                score -= 10
                signals.append("Stochastic overbought")

            # Bullish crossover
            if indicators['stoch_k'] > indicators['stoch_d'] and indicators['stoch_k'] < 50:
                score += 10
                signals.append("Stochastic bullish crossover")

        score = max(0, min(100, score))

        return {
            'score': score,
            'signals': signals,
            'rsi': rsi,
            'stochastic_k': indicators.get('stoch_k'),
            'stochastic_d': indicators.get('stoch_d')
        }

    def _score_volume(self, indicators: Dict[str, Any], data: pd.DataFrame) -> Dict[str, Any]:
        """Score volume indicators (0-100)"""
        score = 50
        signals = []

        volume_ratio = indicators['volume_ratio']
        obv_trend = indicators['obv_trend']

        # Volume surge
        if volume_ratio > 2.0:
            score += 20
            signals.append(f"Strong volume surge ({volume_ratio:.1f}x)")
        elif volume_ratio > 1.5:
            score += 15
            signals.append(f"Volume surge ({volume_ratio:.1f}x)")
        elif volume_ratio > 1.2:
            score += 5
            signals.append(f"Above average volume ({volume_ratio:.1f}x)")
        elif volume_ratio < 0.5:
            score -= 10
            signals.append(f"Low volume ({volume_ratio:.1f}x)")

        # OBV trend
        if obv_trend == 'up':
            score += 15
            signals.append("OBV trending up")
        else:
            score -= 10
            signals.append("OBV trending down")

        score = max(0, min(100, score))

        return {
            'score': score,
            'signals': signals,
            'volume_ratio': volume_ratio,
            'trend': obv_trend
        }

    def _score_volatility(self, indicators: Dict[str, Any], data: pd.DataFrame) -> Dict[str, Any]:
        """Score volatility indicators (0-100)"""
        score = 50
        signals = []

        current_price = indicators['current_price']
        bb_upper = indicators['bb_upper']
        bb_middle = indicators['bb_middle']
        bb_lower = indicators['bb_lower']
        bb_width = indicators['bb_width']

        # Bollinger Band position
        if current_price < bb_lower:
            score += 20
            signals.append("Below lower Bollinger Band")
        elif current_price < bb_middle:
            score += 10
            signals.append("Below middle Bollinger Band")
        elif current_price > bb_upper:
            score -= 20
            signals.append("Above upper Bollinger Band")
        elif current_price > bb_middle:
            score -= 5
            signals.append("Above middle Bollinger Band")

        # Bollinger Band width (squeeze detection)
        if bb_width < 5:
            score += 10
            signals.append(f"Bollinger Band squeeze (width: {bb_width:.1f}%)")

        # ATR
        atr = indicators['atr']
        if atr:
            atr_pct = (atr / current_price) * 100
            if atr_pct < 2:
                signals.append(f"Low volatility (ATR: {atr_pct:.1f}%)")
            elif atr_pct > 5:
                signals.append(f"High volatility (ATR: {atr_pct:.1f}%)")
                score -= 5  # High volatility is risky

        score = max(0, min(100, score))

        return {
            'score': score,
            'signals': signals,
            'bb_position': 'lower' if current_price < bb_middle else 'upper',
            'bb_width': bb_width,
            'atr_pct': (atr / current_price) * 100 if atr else None
        }

    def _detect_all_patterns(self, data: pd.DataFrame, indicators: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect all chart patterns"""
        patterns = []

        # Rounding Bottom (RHS)
        rhs = self._detect_rhs_pattern(data, indicators)
        if rhs:
            patterns.append(rhs)

        # Cup with Handle
        cwh = self._detect_cwh_pattern(data, indicators)
        if cwh:
            patterns.append(cwh)

        # Golden Cross
        golden_cross = self._detect_golden_cross_pattern(data, indicators)
        if golden_cross:
            patterns.append(golden_cross)

        # Support/Resistance Breakout
        breakout = self._detect_breakout_pattern(data, indicators)
        if breakout:
            patterns.append(breakout)

        return patterns

    def _detect_rhs_pattern(self, data: pd.DataFrame, indicators: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Detect Reverse Head and Shoulders (RHS) pattern

        CORRECT PATTERN DEFINITION:
        1. Structure: Three consecutive troughs - left shoulder, head (lowest), right shoulder
        2. Shoulders: Similar depth to each other, but ABOVE the head
        3. Neckline: Connect highs after left shoulder and head
        4. Entry: Either in right shoulder recovery OR after neckline breakout with strong candle
        5. Target: Head depth extrapolated above neckline
        """
        if len(data) < 60:
            return None

        recent_60 = data.tail(60)
        confidence_score = 0

        # 1. IDENTIFY THREE TROUGHS
        # Divide into sections to find left shoulder, head, right shoulder
        left_section = recent_60.iloc[0:20]
        mid_section = recent_60.iloc[15:35]  # Overlap to catch head
        right_section = recent_60.iloc[30:60]  # Overlap to catch right shoulder

        left_low = left_section['Low'].min()
        left_low_idx = left_section['Low'].idxmin()

        head_low = mid_section['Low'].min()
        head_low_idx = mid_section['Low'].idxmin()

        right_low = right_section['Low'].min()
        right_low_idx = right_section['Low'].idxmin()

        current_price = data['Close'].iloc[-1]

        # 2. VALIDATE STRUCTURE: head must be lowest, chronologically ordered
        if not (left_low_idx < head_low_idx < right_low_idx):
            return None  # Not chronologically ordered

        # Head must be the lowest point
        if not (head_low < left_low and head_low < right_low):
            return None  # Head is not lowest

        # 3. SHOULDER SYMMETRY & VALIDATION (fuzzy with 85% tolerance)
        # Calculate how deep shoulders are relative to head
        left_to_head_depth = (left_low - head_low) / head_low
        right_to_head_depth = (right_low - head_low) / head_low

        # REJECT if either shoulder is too close to head depth (within 15%)
        # This means shoulder went 85%+ down towards the head
        if left_to_head_depth < 0.15 or right_to_head_depth < 0.15:
            return None  # Shoulder too close to head = invalid pattern

        # Check shoulder symmetry (fuzzy)
        shoulder_diff = abs(left_low - right_low) / head_low

        if shoulder_diff < 0.05:  # Very similar shoulders
            confidence_score += 25
        elif shoulder_diff < 0.10:  # Reasonably similar
            confidence_score += 20
        elif shoulder_diff < 0.15:  # Acceptable asymmetry
            confidence_score += 15
        else:
            confidence_score += 10  # Significant asymmetry but ok

        # FUZZY BONUS: Shoulders can be slightly above or below ideal
        # but should generally be between 15-60% above head
        avg_shoulder_height = (left_to_head_depth + right_to_head_depth) / 2
        if 0.20 <= avg_shoulder_height <= 0.40:  # Ideal range
            confidence_score += 15
        elif 0.15 <= avg_shoulder_height <= 0.60:  # Acceptable fuzzy range
            confidence_score += 10
        else:
            confidence_score += 5  # Outside ideal but still valid

        # 4. CALCULATE NECKLINE
        # Find peaks after left shoulder and after head
        left_to_head = recent_60.loc[left_low_idx:head_low_idx]
        head_to_right = recent_60.loc[head_low_idx:right_low_idx]

        if len(left_to_head) > 1:
            peak_after_left = left_to_head['High'].max()
        else:
            peak_after_left = left_low * 1.05

        if len(head_to_right) > 1:
            peak_after_head = head_to_right['High'].max()
        else:
            peak_after_head = head_low * 1.05

        neckline = (peak_after_left + peak_after_head) / 2  # Average of two peaks

        # 5. HEAD DEPTH (from neckline to head)
        head_depth = (neckline - head_low) / neckline

        if 0.10 <= head_depth <= 0.30:  # Ideal depth
            confidence_score += 25
        elif 0.05 <= head_depth <= 0.40:  # Acceptable
            confidence_score += 20
        else:
            confidence_score += 10

        # 6. RIGHT SHOULDER RECOVERY (is it recovering?)
        right_shoulder_data = recent_60.loc[right_low_idx:]
        if len(right_shoulder_data) < 3:
            return None  # Not enough data in right shoulder

        right_recovery = (current_price - right_low) / right_low
        right_trend = (right_shoulder_data['Close'].iloc[-1] - right_shoulder_data['Close'].iloc[0]) / right_shoulder_data['Close'].iloc[0]

        entry_ready = False
        entry_type = None

        # Entry Type 1: Recovering in right shoulder (IDEAL - before breakout)
        if current_price > right_low * 1.03 and right_trend > 0.02:  # Recovering 3%+
            if current_price < neckline * 0.98:  # Still below neckline
                confidence_score += 25
                entry_ready = True
                entry_type = "Right Shoulder Recovery"
            else:
                confidence_score += 15
                entry_type = "Near Neckline"

        # Entry Type 2: Neckline breakout
        elif current_price > neckline * 1.01:  # Broke above neckline
            # Check for strong breakout candle
            recent_3_candles = data.tail(3)
            breakout_strength = (recent_3_candles['Close'].iloc[-1] - recent_3_candles['Open'].iloc[-3]) / recent_3_candles['Open'].iloc[-3]

            if breakout_strength > 0.03:  # Strong 3%+ move
                confidence_score += 25
                entry_ready = True
                entry_type = "Neckline Breakout"
            else:
                confidence_score += 15
                entry_ready = True
                entry_type = "Weak Breakout"
        else:
            confidence_score += 5
            entry_type = "Pattern Forming"

        # 7. VOLUME PATTERN (decline through formation, rise at breakout)
        left_volume = left_section['Volume'].mean()
        mid_volume = mid_section['Volume'].mean()
        right_volume = right_shoulder_data['Volume'].mean()

        volume_declining = left_volume > mid_volume
        volume_rising = right_volume > mid_volume

        if volume_declining and volume_rising:  # Ideal pattern
            confidence_score += 15
        elif volume_rising:  # At least volume rising
            confidence_score += 10
        else:
            confidence_score += 5

        # 8. CALCULATE TARGET
        target = neckline + (neckline - head_low)  # Head depth projected above neckline

        # Return pattern if confidence >= 60%
        if confidence_score >= 60:
            return {
                'type': 'RHS',
                'name': 'Reverse Head & Shoulders',
                'confidence': min(95, confidence_score),
                'head_depth_pct': head_depth * 100,
                'shoulder_symmetry_pct': (1 - shoulder_diff) * 100,
                'neckline': neckline,
                'target': target,
                'entry_type': entry_type,
                'entry_ready': entry_ready,
                'current_price': current_price,
                'distance_to_neckline_pct': ((current_price / neckline - 1) * 100),
                'potential_gain_pct': ((target / current_price - 1) * 100),
                'detected_at': data.index[-1],
                'entry_price': current_price
            }

        return None

    def _detect_cwh_pattern(self, data: pd.DataFrame, indicators: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Detect Cup with Handle pattern

        CORRECT PATTERN DEFINITION:
        1. Cup: U-shaped bottom (not V-shape), price declines then gradually recovers to former high
        2. Handle: Slight dip after cup, stays in UPPER HALF of cup
        3. Entry: When in handle and recovering (ideally >= 50% of cup height)
        4. Target: Resistance (cup top), aggressive = cup depth added to resistance
        """
        if len(data) < 90:
            return None

        recent_90 = data.tail(90)
        confidence_score = 0

        # 1. IDENTIFY CUP (first ~70 days, excluding potential handle)
        cup_section = recent_90.iloc[:-20]

        cup_high_idx = cup_section['High'].idxmax()
        cup_high = cup_section['High'].max()
        cup_low_idx = cup_section['Low'].idxmin()
        cup_low = cup_section['Low'].min()

        # Cup must have formed (high at beginning, low in middle, recovery)
        if cup_high_idx > cup_low_idx:  # High after low = not a valid cup
            return None

        cup_depth = (cup_high - cup_low) / cup_high

        # Reasonable cup depth (8-40%)
        if not (0.08 <= cup_depth <= 0.40):
            return None

        # Score cup depth
        if 0.12 <= cup_depth <= 0.30:
            confidence_score += 25
        else:
            confidence_score += 15

        # 2. CHECK U-SHAPE (not V-shape)
        # Price should spend time at bottom, not sharp reversal
        bottom_section = cup_section.iloc[int(len(cup_section)*0.3):int(len(cup_section)*0.7)]
        bottom_volatility = bottom_section['Close'].std() / bottom_section['Close'].mean()

        if bottom_volatility < 0.05:  # Low volatility at bottom = U-shape
            confidence_score += 20
        elif bottom_volatility < 0.08:
            confidence_score += 15
        else:
            confidence_score += 10  # Might be V-shape but accept

        # Check recovery to near former high
        cup_end_price = cup_section['Close'].iloc[-1]
        recovery_to_high = cup_end_price / cup_high

        if recovery_to_high > 0.90:  # Recovered to 90%+ of high
            confidence_score += 20
        elif recovery_to_high > 0.80:  # Recovered to 80%+
            confidence_score += 15
        else:
            confidence_score += 10

        # 3. HANDLE FORMATION (last 20 days)
        handle_section = recent_90.tail(20)
        handle_high = handle_section['High'].max()
        handle_low = handle_section['Low'].min()
        current_price = data['Close'].iloc[-1]

        # FUZZY HANDLE POSITION: Allow handle to dip below 50% but not too close to cup bottom
        handle_position = (handle_low - cup_low) / (cup_high - cup_low)

        # Reject if handle is too close to cup depth (within 15% of bottom)
        if handle_position < 0.15:  # Handle too deep (85%+ of cup depth)
            return None  # Invalid - handle essentially retests cup bottom

        # FUZZY ACCEPTANCE: Allow 35-100% range (was strict 50%)
        # This means handle can go to 65% of cup depth (35% from bottom)
        if handle_position < 0.35:  # Handle between 35-65% depth
            confidence_score += 10  # Accept but low confidence
        elif handle_position < 0.50:  # Handle between 50-50% depth
            confidence_score += 15  # Acceptable
        elif handle_position > 0.65:  # Handle in upper 35%
            confidence_score += 20  # Ideal
        else:  # Handle in upper 50%
            confidence_score += 18  # Good

        # Handle depth (should be shallow)
        handle_depth = (handle_high - handle_low) / handle_high

        if handle_depth < 0.12:  # Shallow handle
            confidence_score += 15
        elif handle_depth < 0.20:  # Moderate
            confidence_score += 10
        else:
            confidence_score += 5

        # 4. ENTRY SIGNAL: Are we in handle and recovering?
        # Check if price is recovering from handle low
        recent_5 = handle_section.tail(5)
        price_trend = (recent_5['Close'].iloc[-1] - recent_5['Close'].iloc[0]) / recent_5['Close'].iloc[0]

        entry_ready = False
        entry_type = None

        # Entry Type 1: Recovering in handle (IDEAL)
        if current_price > handle_low * 1.02 and price_trend > 0:  # Recovering
            confidence_score += 20
            entry_ready = True
            entry_type = "Handle Recovery"

        # Entry Type 2: Near breakout (handle high)
        elif current_price > handle_high * 0.98:
            confidence_score += 15
            entry_ready = True
            entry_type = "Near Breakout"

        else:
            confidence_score += 5
            entry_type = "Pattern Forming"

        # 5. VOLUME PATTERN (decrease in cup, increase near breakout)
        cup_volume = cup_section['Volume'].mean()
        handle_volume = handle_section['Volume'].mean()
        recent_volume = recent_5['Volume'].mean()

        volume_trend = recent_volume / cup_volume

        if volume_trend > 1.2:  # Volume surging
            confidence_score += 15
        elif volume_trend > 1.0:
            confidence_score += 10
        else:
            confidence_score += 5

        # 6. CALCULATE TARGETS
        resistance = cup_high  # Conservative target
        aggressive_target = cup_high + (cup_high - cup_low)  # Cup depth projected up

        # Return pattern if valid and confidence >= 60%
        if confidence_score >= 60:
            return {
                'type': 'CWH',
                'name': 'Cup with Handle',
                'confidence': min(95, confidence_score),
                'cup_depth_pct': cup_depth * 100,
                'handle_position': f"Upper {(1-handle_position)*100:.0f}%",
                'handle_depth_pct': handle_depth * 100,
                'entry_type': entry_type,
                'entry_ready': entry_ready,
                'current_price': current_price,
                'resistance': resistance,
                'target_conservative': resistance,
                'target_aggressive': aggressive_target,
                'volume_trend': 'increasing' if volume_trend > 1.1 else 'stable',
                'detected_at': data.index[-1],
                'entry_price': current_price
            }

        return None

    def _detect_golden_cross_pattern(self, data: pd.DataFrame, indicators: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Detect Golden Cross (SMA50 crosses above SMA200)"""
        if indicators['sma_50'] is None or indicators['sma_200'] is None:
            return None

        if indicators['sma_50'] > indicators['sma_200']:
            # Check if crossover happened recently (within 10 days)
            if len(data) >= 210:
                sma_50_series = data['Close'].rolling(window=50).mean()
                sma_200_series = data['Close'].rolling(window=200).mean()

                # Check last 10 days for crossover
                recent_10 = pd.DataFrame({
                    'sma_50': sma_50_series.tail(10),
                    'sma_200': sma_200_series.tail(10)
                })

                # Find where SMA50 crossed above SMA200
                crossover_detected = False
                for i in range(1, len(recent_10)):
                    if (recent_10['sma_50'].iloc[i] > recent_10['sma_200'].iloc[i] and
                        recent_10['sma_50'].iloc[i-1] <= recent_10['sma_200'].iloc[i-1]):
                        crossover_detected = True
                        break

                if crossover_detected or indicators['sma_50'] > indicators['sma_200']:
                    return {
                        'type': 'Golden Cross',
                        'name': 'Golden Cross',
                        'confidence': 80,
                        'sma_50': indicators['sma_50'],
                        'sma_200': indicators['sma_200'],
                        'detected_at': data.index[-1],
                        'entry_price': data['Close'].iloc[-1]
                    }

        return None

    def _detect_breakout_pattern(self, data: pd.DataFrame, indicators: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Detect resistance breakout with volume"""
        if len(data) < 50:
            return None

        recent_50 = data.tail(50)
        resistance = recent_50['High'].iloc[:-5].max()  # Resistance from days 1-45
        current_price = data['Close'].iloc[-1]

        # Breakout above resistance with volume
        if current_price > resistance * 1.02:  # 2% above resistance
            if indicators['volume_ratio'] > 1.5:
                return {
                    'type': 'Breakout',
                    'name': 'Resistance Breakout',
                    'confidence': 70,
                    'resistance': resistance,
                    'breakout_pct': ((current_price - resistance) / resistance) * 100,
                    'volume_surge': indicators['volume_ratio'],
                    'detected_at': data.index[-1],
                    'entry_price': current_price
                }

        return None

    def _select_primary_pattern(self, patterns: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Select the strongest pattern for backtesting"""
        if not patterns:
            return None

        # Sort by confidence
        sorted_patterns = sorted(patterns, key=lambda p: p.get('confidence', 0), reverse=True)

        # Return highest confidence pattern above threshold
        best_pattern = sorted_patterns[0]
        if best_pattern.get('confidence', 0) >= self.min_pattern_confidence:
            return best_pattern

        return None

    def _find_support(self, data: pd.DataFrame) -> float:
        """Find nearest support level"""
        recent_50 = data.tail(50)
        return recent_50['Low'].min()

    def _find_resistance(self, data: pd.DataFrame) -> float:
        """Find nearest resistance level"""
        recent_50 = data.tail(50)
        return recent_50['High'].max()

    def _generate_signals(self, indicators: Dict[str, Any], data: pd.DataFrame, primary_pattern: Optional[Dict[str, Any]]) -> Dict[str, str]:
        """Generate buy/sell/hold signals"""
        signals = {
            'action': 'HOLD',
            'strength': 'NEUTRAL',
            'reasons': []
        }

        buy_signals = 0
        sell_signals = 0

        # RSI
        if indicators['rsi'] < 30:
            buy_signals += 2
            signals['reasons'].append("RSI oversold")
        elif indicators['rsi'] > 70:
            sell_signals += 2
            signals['reasons'].append("RSI overbought")

        # MACD
        if indicators['macd_histogram'] > 0:
            buy_signals += 1
            signals['reasons'].append("MACD bullish")
        else:
            sell_signals += 1

        # Pattern
        if primary_pattern:
            buy_signals += 2
            signals['reasons'].append(f"Pattern detected: {primary_pattern['name']}")

        # Volume
        if indicators['volume_ratio'] > 1.5 and indicators['obv_trend'] == 'up':
            buy_signals += 1
            signals['reasons'].append("Strong volume confirmation")

        # Determine action
        if buy_signals >= 3:
            signals['action'] = 'BUY'
            signals['strength'] = 'STRONG' if buy_signals >= 5 else 'MODERATE'
        elif sell_signals >= 3:
            signals['action'] = 'SELL'
            signals['strength'] = 'STRONG' if sell_signals >= 5 else 'MODERATE'

        return signals

    def _format_indicators(self, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Format indicators for output"""
        return {
            'price': {
                'current': indicators['current_price'],
                'sma_20': indicators.get('sma_20'),
                'sma_50': indicators.get('sma_50'),
                'sma_200': indicators.get('sma_200')
            },
            'momentum': {
                'rsi': indicators.get('rsi'),
                'macd': indicators.get('macd'),
                'macd_signal': indicators.get('macd_signal'),
                'macd_histogram': indicators.get('macd_histogram')
            },
            'volatility': {
                'bb_upper': indicators.get('bb_upper'),
                'bb_middle': indicators.get('bb_middle'),
                'bb_lower': indicators.get('bb_lower'),
                'atr': indicators.get('atr')
            },
            'volume': {
                'current': indicators.get('volume_ratio'),
                'obv_trend': indicators.get('obv_trend')
            }
        }

    def _generate_summary(self, score: float, patterns: List[Dict[str, Any]], signals: Dict[str, str]) -> str:
        """Generate human-readable summary"""
        summary_parts = []

        # Overall assessment (Mean Reversion Strategy)
        if score >= 75:
            summary_parts.append("Strong mean reversion opportunity")
        elif score >= 60:
            summary_parts.append("Moderate mean reversion setup")
        elif score >= 40:
            summary_parts.append("Neutral technicals")
        else:
            summary_parts.append("Weak setup")

        # Pattern
        if patterns:
            pattern_names = ", ".join([p['name'] for p in patterns])
            summary_parts.append(f"Patterns: {pattern_names}")

        # Signal
        if signals['action'] != 'HOLD':
            summary_parts.append(f"{signals['action']} signal ({signals['strength']})")

        return " | ".join(summary_parts)

    def _error_response(self, ticker: str, error: str) -> Dict[str, Any]:
        """Return error response"""
        return {
            'score': 0,
            'ticker': ticker,
            'error': error,
            'timestamp': datetime.now().isoformat()
        }


# Example usage
async def main():
    """Example usage of Technical Analyst"""

    config = {
        'lookback_days': 200,
        'detect_patterns': True,
        'min_pattern_confidence': 70.0
    }

    analyst = TechnicalAnalyst(config)

    # Analyze a stock
    result = await analyst.analyze('RELIANCE.NS', {})

    print(f"Technical Score: {result['score']}")
    print(f"Summary: {result['summary']}")
    print(f"\nSignals: {result['signals']['action']} ({result['signals']['strength']})")

    if result.get('primary_pattern'):
        print(f"\nPrimary Pattern: {result['primary_pattern']['name']}")
        print(f"Confidence: {result['primary_pattern']['confidence']}%")

    print(f"\nCategory Scores:")
    print(f"  Trend: {result['trend']['score']}")
    print(f"  Momentum: {result['momentum']['score']}")
    print(f"  Volume: {result['volume']['score']}")
    print(f"  Volatility: {result['volatility']['score']}")


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
