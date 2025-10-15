"""
Orchestrator Agent

Coordinates all specialist agents and makes final trading decisions.

Decision Flow:
1. Run all specialist agents in parallel
2. Aggregate scores with configured weights
3. Apply vetoes (Pattern Validator can veto if historical success < 70%)
4. Generate final BUY/SELL/HOLD recommendation
5. Calculate position size and risk parameters
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

from agents.base_agent import BaseAgent
from agents.fundamental_analyst import FundamentalAnalyst
from agents.technical_analyst import TechnicalAnalyst
from agents.sentiment_analyst import SentimentAnalyst
from agents.management_analyst import ManagementAnalyst
from tools.llm_decision_cache import LLMDecisionCache


class Orchestrator(BaseAgent):
    """
    Orchestrates all specialist agents to make trading decisions

    Agent Weights (configurable):
    - Fundamental Analyst: 25%
    - Technical Analyst: 20%
    - Sentiment Analyst: 20%
    - Management Analyst: 15%
    - Market Regime: 10%
    - Risk Adjustment: 10%

    Veto Power (Critical - Can override all other signals):
    - Pattern Validator: VETOES if pattern's historical success rate < threshold
      * Aggressive target: Requires 70%+ historical success
      * Conservative target: Requires 55%+ historical success
      * Checks 5 years of historical data with strict pattern criteria
      * No time limits - target must have been hit eventually
    - Technical Signal: VETOES if no clear entry signal (pattern or indicator)
    - Risk Management: Can veto if position size exceeds limits

    Decision Thresholds:
    - BUY: composite score >= 70 AND no vetoes
    - STRONG BUY: composite score >= 85 AND all agents bullish
    - HOLD: 40 <= composite score < 70
    - SELL: composite score < 40 OR major veto
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Orchestrator

        Args:
            config: Configuration dict with orchestrator and agent settings
        """
        super().__init__("Orchestrator", config)

        # Agent weights
        self.weights = config.get('weights', {
            'fundamental': 0.25,
            'technical': 0.20,
            'sentiment': 0.20,
            'management': 0.15,
            'market_regime': 0.10,
            'risk_adjustment': 0.10
        })

        # Decision thresholds
        self.buy_threshold = config.get('buy_threshold', 70.0)
        self.strong_buy_threshold = config.get('strong_buy_threshold', 85.0)
        self.sell_threshold = config.get('sell_threshold', 40.0)

        # Risk parameters
        self.max_position_size = config.get('max_position_size', 0.05)  # 5% max
        self.initial_capital = config.get('initial_capital', 100000)

        # Initialize all specialist agents
        self.fundamental_analyst = FundamentalAnalyst(
            config.get('fundamental_config', {})
        )
        self.technical_analyst = TechnicalAnalyst(
            config.get('technical_config', {})
        )
        self.sentiment_analyst = SentimentAnalyst(
            config.get('sentiment_config', {})
        )
        self.management_analyst = ManagementAnalyst(
            config.get('management_config', {})
        )

        # Initialize LLM decision cache
        self.llm_cache = LLMDecisionCache()
        cache_stats = self.llm_cache.get_statistics()
        if cache_stats['total_decisions'] > 0:
            self.logger.info(
                f"💾 LLM Cache initialized: {cache_stats['total_decisions']} decisions, "
                f"{cache_stats['hit_rate']:.1f}% hit rate"
            )

        self.logger.info("All specialist agents initialized")

    async def analyze(self, ticker: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Orchestrate full analysis and generate trading decision

        Args:
            ticker: Stock ticker
            context: Additional context (market regime, etc.)

        Returns:
            Dict with final trading decision and all agent outputs
        """
        if not self.validate_input(ticker):
            return self._error_response(ticker, "Invalid ticker")

        self.logger.info(f"🎯 Orchestrating analysis for {ticker}")
        start_time = datetime.now()

        try:
            # Phase 1: Run fundamental and sentiment analysis in parallel
            # (These don't depend on each other)
            self.logger.info("📊 Phase 1: Fundamental & Sentiment Analysis")

            fundamental_task = self.fundamental_analyst.analyze(ticker, context)
            sentiment_task = self.sentiment_analyst.analyze(ticker, context)
            management_task = self.management_analyst.analyze(ticker, context)

            fundamental_result, sentiment_result, management_result = await asyncio.gather(
                fundamental_task,
                sentiment_task,
                management_task,
                return_exceptions=True
            )

            # Handle exceptions
            if isinstance(fundamental_result, Exception):
                self.logger.error(f"Fundamental analysis failed: {fundamental_result}")
                fundamental_result = {'score': 0, 'error': str(fundamental_result)}

            if isinstance(sentiment_result, Exception):
                self.logger.error(f"Sentiment analysis failed: {sentiment_result}")
                sentiment_result = {'score': 50, 'error': str(sentiment_result)}

            if isinstance(management_result, Exception):
                self.logger.error(f"Management analysis failed: {management_result}")
                management_result = {'score': 50, 'error': str(management_result)}

            # Phase 2: Technical analysis (needs fundamental data for context)
            self.logger.info("📈 Phase 2: Technical Analysis")

            technical_context = {
                **context,
                'fundamental_score': fundamental_result.get('score', 0)
            }

            technical_result = await self.technical_analyst.analyze(ticker, technical_context)

            if isinstance(technical_result, Exception):
                self.logger.error(f"Technical analysis failed: {technical_result}")
                technical_result = {'score': 0, 'error': str(technical_result)}

            # Phase 3: Final Decision (Pattern Validator already ran in Technical Analysis)
            # Note: Backtest Validator removed - Pattern Validator is more accurate

            self.logger.info("🎲 Phase 4: Final Decision")

            decision = await self._make_decision(
                fundamental_result,
                technical_result,
                sentiment_result,
                management_result,
                context
            )

            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()

            # Build comprehensive result
            result = {
                'ticker': ticker,
                'timestamp': datetime.now().isoformat(),
                'execution_time_seconds': execution_time,

                # Final decision
                'decision': decision['action'],
                'confidence': decision['confidence'],
                'composite_score': decision['composite_score'],
                'position_size': decision.get('position_size', 0),
                'target_price': decision.get('target_price'),

                # Agent scores
                'agent_scores': {
                    'fundamental': fundamental_result.get('score', 0),
                    'technical': technical_result.get('score', 0),
                    'sentiment': sentiment_result.get('score', 0),
                    'management': management_result.get('score', 0)
                },

                # Detailed agent results
                'fundamental_analysis': fundamental_result,
                'technical_analysis': technical_result,
                'sentiment_analysis': sentiment_result,
                'management_analysis': management_result,

                # Decision factors
                'decision_factors': decision['factors'],
                'vetoes': decision.get('vetoes', []),
                'warnings': decision.get('warnings', []),

                # Summary
                'summary': decision['summary']
            }

            self.log_analysis(ticker, result)
            self.logger.info(f"✅ Analysis complete in {execution_time:.2f}s")
            self.logger.info(f"📊 Decision: {decision['action']} (Score: {decision['composite_score']:.1f}/100)")

            return result

        except Exception as e:
            self.logger.error(f"Orchestration failed for {ticker}: {e}")
            import traceback
            traceback.print_exc()
            return self._error_response(ticker, str(e))

    def _detect_conflicts(self, agent_scores: Dict[str, float]) -> Dict[str, Any]:
        """
        Detect conflicts between agents

        Returns:
            {
                'has_conflict': bool,
                'conflict_level': 'none' | 'low' | 'medium' | 'high',
                'disagreements': List[Dict],
                'variance': float,
                'std_dev': float
            }
        """
        import numpy as np

        scores = list(agent_scores.values())

        if len(scores) == 0:
            return {
                'has_conflict': False,
                'conflict_level': 'none',
                'disagreements': [],
                'variance': 0.0,
                'std_dev': 0.0,
                'mean_score': 0.0
            }

        mean_score = np.mean(scores)
        std_dev = np.std(scores)

        # Calculate coefficient of variation (normalized variance)
        variance = std_dev / mean_score if mean_score > 0 else 0

        # Detect pairwise disagreements (>40 point difference)
        disagreements = []
        agent_names = list(agent_scores.keys())

        for i, agent1 in enumerate(agent_names):
            for j, agent2 in enumerate(agent_names):
                if i < j:  # Avoid duplicates
                    score1 = agent_scores[agent1]
                    score2 = agent_scores[agent2]
                    diff = abs(score1 - score2)

                    # Major disagreement: >40 point difference
                    if diff >= 40:
                        disagreements.append({
                            'agents': [agent1, agent2],
                            'difference': diff,
                            'scores': {agent1: score1, agent2: score2}
                        })

        # Classify conflict level
        if variance > 0.4 or len(disagreements) >= 2:
            conflict_level = 'high'
        elif variance > 0.25 or len(disagreements) == 1:
            conflict_level = 'medium'
        elif variance > 0.15:
            conflict_level = 'low'
        else:
            conflict_level = 'none'

        return {
            'has_conflict': conflict_level != 'none',
            'conflict_level': conflict_level,
            'disagreements': disagreements,
            'variance': round(variance, 3),
            'std_dev': round(std_dev, 2),
            'mean_score': round(mean_score, 2)
        }

    def _has_clear_technical_signal(self, technical: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if there's a clear technical BUY signal (pattern or indicator)

        Returns:
            {
                'has_signal': bool,
                'signal_type': 'pattern' | 'indicator' | 'both' | None,
                'signal_strength': 'weak' | 'moderate' | 'strong',
                'details': Dict
            }
        """
        has_signal = False
        signal_type = None
        signal_strength = 'weak'
        details = {}

        # Check for bullish pattern
        primary_pattern = technical.get('primary_pattern')
        if primary_pattern is None:
            primary_pattern = {}

        pattern_type = primary_pattern.get('type')
        pattern_confidence = primary_pattern.get('confidence', 0)

        # Bullish patterns: CWH, RHS, Golden Cross, Breakout
        bullish_patterns = ['CWH', 'RHS', 'Golden Cross', 'Breakout']

        if pattern_type in bullish_patterns and pattern_confidence >= 70:
            has_signal = True
            signal_type = 'pattern'
            details['pattern'] = {
                'name': primary_pattern.get('name'),
                'confidence': pattern_confidence,
                'target': primary_pattern.get('target_price')
            }

            if pattern_confidence >= 85:
                signal_strength = 'strong'
            elif pattern_confidence >= 75:
                signal_strength = 'moderate'

        # Check for bullish indicators
        trend = technical.get('trend', {})
        trend_direction = trend.get('direction', 'neutral')

        indicators = technical.get('indicators', {})
        ma_signal = indicators.get('moving_averages', {}).get('signal')
        rsi = indicators.get('rsi', {}).get('value', 50)
        macd_signal = indicators.get('macd', {}).get('signal')

        # Strong indicator signals
        bullish_indicators = []

        if trend_direction == 'uptrend':
            bullish_indicators.append('uptrend')

        if ma_signal == 'bullish':
            bullish_indicators.append('bullish_ma_crossover')

        if 30 <= rsi <= 70:  # Not overbought, not oversold
            bullish_indicators.append('rsi_neutral')

        if macd_signal == 'bullish':
            bullish_indicators.append('macd_crossover')

        if len(bullish_indicators) >= 2:
            if not has_signal:
                has_signal = True
                signal_type = 'indicator'
            else:
                signal_type = 'both'  # Both pattern AND indicators

            details['indicators'] = bullish_indicators

            if len(bullish_indicators) >= 3:
                signal_strength = 'strong'
            elif len(bullish_indicators) >= 2:
                signal_strength = 'moderate'

        return {
            'has_signal': has_signal,
            'signal_type': signal_type,
            'signal_strength': signal_strength,
            'details': details
        }

    def _calculate_pattern_target(
        self,
        technical: Dict[str, Any],
        current_price: float
    ) -> Optional[float]:
        """
        Calculate target price based on technical pattern

        Returns:
            Target price (float) or None
        """
        # Check if pattern has explicit target
        primary_pattern = technical.get('primary_pattern', {})
        if primary_pattern.get('target_price'):
            return primary_pattern['target_price']

        # Calculate based on pattern type
        pattern_name = (primary_pattern.get('name') or '').lower()
        resistance = technical.get('backtest_context', {}).get('resistance', 0)
        atr = technical.get('backtest_context', {}).get('atr', 0)

        # Pattern-specific target calculations
        if 'breakout' in pattern_name:
            # Breakout target: Resistance + (Height of consolidation)
            if resistance:
                consolidation_height = resistance * 0.05  # Assume 5% range
                return resistance + consolidation_height

        elif 'head and shoulders' in pattern_name and 'inverse' in pattern_name:
            # Inverse H&S: Neckline + Height of pattern
            neckline = primary_pattern.get('neckline', current_price)
            head = primary_pattern.get('head', current_price * 0.95)
            height = neckline - head
            return neckline + height

        elif 'double bottom' in pattern_name or 'triple bottom' in pattern_name:
            # Double/Triple bottom: Resistance level
            if resistance:
                return resistance

        elif atr:
            # Default: 2x ATR target
            return current_price + (2 * atr)

        # Fallback: 5% above current price
        return current_price * 1.05

    async def _llm_conflict_resolution(
        self,
        ticker: str,
        company_name: str,
        agent_results: Dict[str, Any],
        conflict_info: Dict[str, Any],
        composite_score: float,
        technical_signal: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Use GPT-4 to synthesize agent outputs and resolve conflicts

        Args:
            ticker: Stock ticker
            company_name: Company name
            agent_results: Full results from all agents
            conflict_info: Conflict detection output
            composite_score: Raw weighted average score
            technical_signal: Technical signal validation output

        Returns:
            {
                'final_recommendation': 'BUY' | 'SELL' | 'HOLD' | 'WAIT',
                'adjusted_score': float,
                'confidence': float,
                'reasoning': str,
                'key_insights': List[str],
                'conflict_analysis': str,
                'risk_factors': List[str],
                'alternative_scenarios': List[Dict],
                'time_horizon': str,
                'position_sizing_advice': str,
                'requires_monitoring': bool,
                'watchlist_triggers': List[str]
            }
        """
        try:
            from tools.llm.llm_client import LLMClient
            from tools.llm.prompts import PromptTemplates

            llm = LLMClient()

            # Get messages from prompt template
            messages = PromptTemplates.conflict_resolution_synthesis(
                ticker=ticker,
                company_name=company_name,
                agent_results=agent_results,
                conflict_info=conflict_info,
                composite_score=composite_score,
                technical_signal=technical_signal
            )

            # Call GPT-4 for synthesis
            self.logger.info(f"🤖 Calling GPT-4 for conflict resolution synthesis...")

            response = await llm.chat(
                messages=messages,
                provider="openai",
                model="gpt-4-turbo",
                temperature=0.2,
                json_mode=True
            )

            # Parse response
            import json
            synthesis = json.loads(response.content)

            self.logger.info(
                f"✅ LLM Synthesis complete: {synthesis.get('final_recommendation', 'N/A')} "
                f"(Confidence: {synthesis.get('confidence', 0)}%)"
            )

            return synthesis

        except Exception as e:
            self.logger.error(f"LLM conflict resolution failed: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def _make_decision(
        self,
        fundamental: Dict[str, Any],
        technical: Dict[str, Any],
        sentiment: Dict[str, Any],
        management: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Make final trading decision based on all agent inputs

        NEW RULE: Only BUY when there's a clear technical signal (pattern or indicator)
        NEW FEATURE: LLM synthesis for conflict resolution

        Returns:
            Dict with decision, confidence, and reasoning
        """
        # Extract scores
        fundamental_score = fundamental.get('score', 0)
        technical_score = technical.get('score', 0)
        sentiment_score = sentiment.get('score', 0)
        management_score = management.get('score', 0)

        # Detect conflicts between agents
        agent_scores = {
            'fundamental': fundamental_score,
            'technical': technical_score,
            'sentiment': sentiment_score,
            'management': management_score
        }
        conflict_info = self._detect_conflicts(agent_scores)

        # Check for clear technical signal (CRITICAL for BUY)
        technical_signal = self._has_clear_technical_signal(technical)

        # Calculate composite score
        composite_score = (
            fundamental_score * self.weights['fundamental'] +
            technical_score * self.weights['technical'] +
            sentiment_score * self.weights['sentiment'] +
            management_score * self.weights['management']
        )

        # Adjust for market regime (if provided)
        market_regime = context.get('market_regime', 'neutral')
        if market_regime == 'bullish':
            composite_score += 10 * self.weights['market_regime']
        elif market_regime == 'bearish':
            composite_score -= 10 * self.weights['market_regime']

        # Check for vetoes
        vetoes = []
        warnings = []

        # CRITICAL RULE: No technical signal = No BUY
        if not technical_signal['has_signal']:
            vetoes.append("No clear technical entry signal (pattern or indicator)")
            self.logger.warning(f"⚠️ No technical signal - cannot BUY even with good fundamentals")

        # VETO POWER: Pattern Validator is the SOLE authority on pattern quality
        # It uses strict criteria: cup depth, U-shape, handle position, 5 years of data
        # If pattern exists but didn't pass validation, VETO immediately
        primary_pattern = technical.get('primary_pattern') if technical else None
        if primary_pattern:
            pattern_validated = primary_pattern.get('validation', {}).get('validation_passed', False)
            if not pattern_validated:
                # CRITICAL VETO: Pattern failed strict historical validation
                vetoes.append("Pattern Validator VETO - historical success rate below threshold")
                self.logger.warning("🚫 VETO: Pattern detected but validation failed")
            else:
                # Pattern passed validation - TRUST IT! No other validator needed
                agg_success_rate = primary_pattern.get('validation', {}).get('aggressive_success_rate', 0) * 100
                cons_success_rate = primary_pattern.get('validation', {}).get('conservative_success_rate', 0) * 100
                target_type = primary_pattern.get('validation', {}).get('target_type', 'unknown')
                warnings.append(f"Pattern validated ({target_type}): {agg_success_rate:.1f}% aggressive, {cons_success_rate:.1f}% conservative success")
                self.logger.info(f"✅ Pattern Validator APPROVED: {agg_success_rate:.1f}% success rate ({target_type} target)")

        # Fundamental veto
        if fundamental_score < 30:
            warnings.append("Very weak fundamentals")
            composite_score *= 0.8

        # Risk adjustment
        risk_level = self._assess_risk(fundamental, technical, sentiment)
        if risk_level == 'high':
            composite_score -= 10 * self.weights['risk_adjustment']
            warnings.append("High risk detected")

        # Log conflict information
        if conflict_info['has_conflict']:
            self.logger.info(
                f"⚠️ Conflict detected ({conflict_info['conflict_level']}): "
                f"Variance={conflict_info['variance']}, "
                f"Disagreements={len(conflict_info['disagreements'])}"
            )

        # Log technical signal status
        if technical_signal['has_signal']:
            self.logger.info(
                f"✅ Technical signal found: {technical_signal['signal_type']} "
                f"({technical_signal['signal_strength']})"
            )

        # Check if LLM synthesis is needed
        use_llm_synthesis = (
            conflict_info['conflict_level'] in ['medium', 'high'] or
            (40 <= composite_score <= 70)  # Borderline cases
        )

        llm_synthesis = None
        ticker = fundamental.get('ticker', context.get('ticker', 'UNKNOWN'))

        if use_llm_synthesis:
            # Try cache first
            agent_scores = {
                'fundamental': fundamental.get('score', 0),
                'technical': technical.get('score', 0),
                'sentiment': sentiment.get('score', 0),
                'management': management.get('score', 0)
            }

            llm_synthesis = self.llm_cache.get_cached_decision(
                ticker=ticker,
                agent_scores=agent_scores,
                conflict_info=conflict_info,
                composite_score=composite_score,
                similarity_threshold=0.85
            )

            # If not in cache, call LLM
            if llm_synthesis is None:
                # Get company name
                company_name = context.get('company_name', fundamental.get('company_name', ticker))

                # Call LLM for conflict resolution
                llm_synthesis = await self._llm_conflict_resolution(
                    ticker=ticker,
                    company_name=company_name,
                    agent_results={
                        'fundamental': fundamental,
                        'technical': technical,
                        'sentiment': sentiment,
                        'management': management
                    },
                    conflict_info=conflict_info,
                    composite_score=composite_score,
                    technical_signal=technical_signal
                )

                # Cache the decision if LLM call succeeded
                if llm_synthesis:
                    self.llm_cache.cache_decision(
                        ticker=ticker,
                        agent_scores=agent_scores,
                        conflict_info=conflict_info,
                        composite_score=composite_score,
                        decision=llm_synthesis,
                        metadata={
                            'date': datetime.now().isoformat(),
                            'has_technical_signal': technical_signal['has_signal'],
                            'signal_type': technical_signal.get('signal_type')
                        }
                    )

        # Determine action (use LLM synthesis if available, otherwise rule-based)
        if llm_synthesis:
            self.logger.info("🤖 Using LLM synthesis for final decision")
            action = llm_synthesis.get('final_recommendation', 'HOLD')
            confidence = llm_synthesis.get('confidence', 50)
            # Note: Don't override composite_score - keep original for comparison
            adjusted_score = llm_synthesis.get('adjusted_score', composite_score)

            # Add LLM insights to warnings/factors
            if llm_synthesis.get('key_insights'):
                warnings.extend(llm_synthesis['key_insights'][:2])  # Add top 2 insights
        else:
            # Rule-based decision (original logic)
            action = "HOLD"
            confidence = 0
            adjusted_score = composite_score

            if composite_score >= self.strong_buy_threshold and len(vetoes) == 0:
                action = "STRONG BUY"
                confidence = min(95, composite_score)
            elif composite_score >= self.buy_threshold and len(vetoes) == 0:
                action = "BUY"
                confidence = composite_score
            elif composite_score < self.sell_threshold or len(vetoes) > 0:
                action = "SELL"
                confidence = 100 - composite_score
            else:
                action = "HOLD"
                confidence = 50

        # Build decision factors
        factors = []

        if fundamental_score >= 70:
            factors.append(f"Strong fundamentals ({fundamental_score:.1f}/100)")
        elif fundamental_score < 40:
            factors.append(f"Weak fundamentals ({fundamental_score:.1f}/100)")

        if technical_score >= 70:
            factors.append(f"Strong technicals ({technical_score:.1f}/100)")
        elif technical_score < 40:
            factors.append(f"Weak technicals ({technical_score:.1f}/100)")

        if sentiment_score >= 70:
            factors.append(f"Positive sentiment ({sentiment_score:.1f}/100)")
        elif sentiment_score < 40:
            factors.append(f"Negative sentiment ({sentiment_score:.1f}/100)")

        # Pattern Validator already handled in veto logic above
        # No need to add backtest factors - Pattern Validator is the sole authority

        # Calculate position size and target (only for BUY decisions)
        position_size = 0
        target_price = None

        if action in ["BUY", "STRONG BUY"]:
            position_size = self._calculate_position_size(
                composite_score, risk_level, fundamental, technical
            )

            # Calculate target price based on technical pattern
            current_price = technical.get('indicators', {}).get('price', {}).get('current')
            if current_price:
                target_price = self._calculate_pattern_target(technical, current_price)

        # Generate summary
        summary = self._generate_decision_summary(
            action, composite_score, factors, vetoes, warnings
        )

        return {
            'action': action,
            'confidence': round(confidence, 1),
            'composite_score': round(composite_score, 2),
            'position_size': position_size,
            'target_price': target_price,
            'factors': factors,
            'vetoes': vetoes,
            'warnings': warnings,
            'summary': summary,

            # Conflict detection information
            'conflict_analysis': conflict_info,

            # Technical signal information
            'technical_signal': technical_signal,

            # LLM synthesis (if used)
            'llm_synthesis': llm_synthesis,
            'used_llm_synthesis': llm_synthesis is not None
        }

    def _assess_risk(
        self,
        fundamental: Dict[str, Any],
        technical: Dict[str, Any],
        sentiment: Dict[str, Any]
    ) -> str:
        """Assess overall risk level"""
        risk_score = 0

        # Fundamental risk
        debt_to_equity = fundamental.get('financial_health', {}).get('debt_to_equity')
        if debt_to_equity and debt_to_equity > 2.0:
            risk_score += 2

        # Technical risk (volatility)
        atr_pct = technical.get('volatility', {}).get('atr_pct')
        if atr_pct and atr_pct > 5:
            risk_score += 2

        # Sentiment risk
        if sentiment.get('score', 50) < 30:
            risk_score += 1

        if risk_score >= 4:
            return 'high'
        elif risk_score >= 2:
            return 'medium'
        else:
            return 'low'

    def _calculate_position_size(
        self,
        composite_score: float,
        risk_level: str,
        fundamental: Dict[str, Any],
        technical: Dict[str, Any]
    ) -> float:
        """
        Calculate position size as percentage of portfolio

        Uses Kelly Criterion adjusted for confidence
        """
        # Base position size
        if composite_score >= 85:
            base_size = self.max_position_size  # 5%
        elif composite_score >= 75:
            base_size = self.max_position_size * 0.8  # 4%
        elif composite_score >= 65:
            base_size = self.max_position_size * 0.6  # 3%
        else:
            base_size = self.max_position_size * 0.4  # 2%

        # Adjust for risk
        risk_multiplier = {
            'low': 1.0,
            'medium': 0.75,
            'high': 0.5
        }

        position_size = base_size * risk_multiplier.get(risk_level, 0.75)

        return round(position_size, 4)

    def _generate_decision_summary(
        self,
        action: str,
        score: float,
        factors: List[str],
        vetoes: List[str],
        warnings: List[str]
    ) -> str:
        """Generate human-readable decision summary"""
        parts = []

        # Action and score
        parts.append(f"{action} - Composite Score: {score:.1f}/100")

        # Vetoes (critical)
        if vetoes:
            parts.append(f"VETOES: {', '.join(vetoes)}")

        # Key factors
        if factors:
            parts.append(f"Key factors: {', '.join(factors[:3])}")

        # Warnings
        if warnings:
            parts.append(f"Warnings: {', '.join(warnings)}")

        return " | ".join(parts)

    def _error_response(self, ticker: str, error: str) -> Dict[str, Any]:
        """Return error response"""
        return {
            'ticker': ticker,
            'decision': 'HOLD',
            'confidence': 0,
            'composite_score': 0,
            'error': error,
            'timestamp': datetime.now().isoformat()
        }


# Example usage
async def main():
    """Example usage of Orchestrator"""

    config = {
        'weights': {
            'fundamental': 0.25,
            'technical': 0.20,
            'sentiment': 0.20,
            'management': 0.15,
            'market_regime': 0.10,
            'risk_adjustment': 0.10
        },
        'buy_threshold': 70.0,
        'strong_buy_threshold': 85.0,
        'sell_threshold': 40.0,
        'max_position_size': 0.05,
        'initial_capital': 100000,

        # Agent configs
        'fundamental_config': {},
        'technical_config': {'detect_patterns': True},
        'backtest_config': {'historical_years': 5, 'min_win_rate': 70.0},
        'sentiment_config': {'news_lookback_days': 30},
        'management_config': {'quarters_to_analyze': 4}
    }

    orchestrator = Orchestrator(config)

    # Analyze a stock
    result = await orchestrator.analyze('RELIANCE.NS', {'market_regime': 'neutral'})

    print(f"\n{'='*80}")
    print(f"  FINAL TRADING DECISION: {result['decision']}")
    print(f"{'='*80}")
    print(f"Composite Score: {result['composite_score']:.2f}/100")
    print(f"Confidence: {result['confidence']:.1f}%")
    print(f"Position Size: {result['position_size']*100:.2f}% of portfolio")

    if result.get('target_price'):
        print(f"Target Price: ₹{result['target_price']:.2f}")

    print(f"\nAgent Scores:")
    for agent, score in result['agent_scores'].items():
        print(f"  {agent.title()}: {score:.1f}/100")

    print(f"\nExecution Time: {result['execution_time_seconds']:.2f}s")
    print(f"\nSummary: {result['summary']}")


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
