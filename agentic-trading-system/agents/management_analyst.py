"""
Management Analyst Agent

Analyzes management quality and corporate governance using:
- Conference call transcripts and summaries
- Management guidance and tone
- Strategic initiatives and execution
- Risk disclosure and transparency
- Capital allocation decisions

Uses Perplexity AI to fetch and analyze earnings calls and management commentary.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging
import json
import re

from agents.base_agent import BaseAgent
from tools.data_fetchers.perplexity_search import PerplexitySearchClient
from tools.llm.llm_client import LLMClient


class ManagementAnalyst(BaseAgent):
    """
    Analyzes management quality through conference calls and guidance

    Core responsibilities:
    1. Analyze conference call transcripts
    2. Assess management tone (optimistic/cautious/neutral)
    3. Evaluate guidance quality and accuracy
    4. Track strategic initiatives
    5. Assess risk disclosure and transparency
    6. Generate management quality score (0-100)

    Management Score Breakdown:
    - Guidance Quality (30%): Accuracy, clarity, transparency
    - Strategic Vision (25%): Long-term plans, innovation, execution
    - Communication (20%): Tone, transparency, investor relations
    - Risk Management (15%): Risk disclosure, mitigation plans
    - Capital Allocation (10%): Dividend policy, buybacks, investments
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Management Analyst

        Args:
            config: Configuration dict with management analysis settings
        """
        super().__init__("Management Analyst", config)

        # Initialize Perplexity client for data fetching
        self.perplexity = PerplexitySearchClient()

        # Initialize LLM client for deep analysis
        self.llm = LLMClient()
        self.use_llm = config.get('use_llm', True)

        # Analysis settings
        self.quarters_to_analyze = config.get('quarters_to_analyze', 4)
        self.min_confidence = config.get('min_confidence', 60.0)

        # Scoring weights
        self.weights = {
            'guidance': 0.30,
            'strategy': 0.25,
            'communication': 0.20,
            'risk_management': 0.15,
            'capital_allocation': 0.10
        }

        # Tone keywords
        self.positive_tone = [
            'optimistic', 'confident', 'strong', 'growth', 'opportunity',
            'excited', 'positive', 'bullish', 'momentum', 'accelerating'
        ]
        self.cautious_tone = [
            'cautious', 'uncertain', 'challenging', 'headwinds', 'concerns',
            'risks', 'difficult', 'pressure', 'volatility', 'weakness'
        ]

        # Strategic keywords
        self.strategic_keywords = {
            'innovation': ['innovation', 'r&d', 'technology', 'digital', 'ai', 'automation'],
            'expansion': ['expansion', 'growth', 'market share', 'new markets', 'scaling'],
            'efficiency': ['efficiency', 'optimization', 'margin', 'cost reduction', 'productivity'],
            'sustainability': ['sustainability', 'esg', 'green', 'carbon', 'renewable']
        }

    async def analyze(self, ticker: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform management quality analysis

        Args:
            ticker: Stock ticker
            context: Additional context (company name, etc.)

        Returns:
            Dict with management analysis results
        """
        if not self.validate_input(ticker):
            return self._error_response(ticker, "Invalid ticker")

        self.logger.info(f"Analyzing management for {ticker}")

        try:
            # Get company name from context or fetch it
            company_name = context.get('company_name')
            if not company_name:
                company_name = self.perplexity._ticker_to_company(ticker)

            # Fetch conference call data
            conf_calls = await self.perplexity.search_conference_calls(
                ticker, company_name, quarters=self.quarters_to_analyze
            )

            if 'error' in conf_calls:
                self.logger.warning(f"Conference call search failed: {conf_calls['error']}")
                return self._error_response(ticker, f"Could not fetch conference calls: {conf_calls['error']}")

            # Parse conference call data
            calls_data = self._parse_conference_calls(conf_calls)

            if not calls_data or len(calls_data) == 0:
                return self._error_response(ticker, "No conference call data available")

            # Score each category
            guidance_score = self._score_guidance_quality(calls_data)
            strategy_score = self._score_strategic_vision(calls_data)
            communication_score = self._score_communication(calls_data)
            risk_score = self._score_risk_management(calls_data)
            capital_score = self._score_capital_allocation(calls_data)

            # Calculate composite management score
            composite_score = (
                guidance_score['score'] * self.weights['guidance'] +
                strategy_score['score'] * self.weights['strategy'] +
                communication_score['score'] * self.weights['communication'] +
                risk_score['score'] * self.weights['risk_management'] +
                capital_score['score'] * self.weights['capital_allocation']
            )

            # Extract key insights
            management_tone = self._determine_tone(calls_data)
            key_initiatives = self._extract_initiatives(calls_data)
            risks_disclosed = self._extract_risks(calls_data)

            # Get LLM deep analysis using Claude (long context)
            llm_analysis = None
            if self.use_llm and calls_data:
                llm_analysis = await self._get_llm_analysis(
                    ticker, company_name, conf_calls, calls_data
                )

            # Build result
            result = {
                'score': round(composite_score, 2),
                'ticker': ticker,
                'company_name': company_name,
                'timestamp': datetime.now().isoformat(),
                'quarters_analyzed': len(calls_data),

                # Category scores
                'guidance': guidance_score,
                'strategy': strategy_score,
                'communication': communication_score,
                'risk_management': risk_score,
                'capital_allocation': capital_score,

                # Key insights
                'management_tone': management_tone,
                'key_initiatives': key_initiatives,
                'risks_disclosed': risks_disclosed,
                'conference_calls': calls_data,

                # Raw data for audit
                'raw_data': conf_calls,

                # LLM deep analysis
                'llm_analysis': llm_analysis,

                # Summary
                'summary': self._generate_summary(
                    composite_score, management_tone, key_initiatives, llm_analysis
                )
            }

            self.log_analysis(ticker, result)
            return result

        except Exception as e:
            self.logger.error(f"Error analyzing management for {ticker}: {e}")
            import traceback
            traceback.print_exc()
            return self._error_response(ticker, str(e))

    def _parse_conference_calls(self, conf_calls_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse conference call data from Perplexity response"""
        calls = []

        try:
            raw_response = conf_calls_data.get('raw_response', '')

            # Try to parse JSON structure
            json_match = re.search(r'\{[^{}]*"conference_calls"[^{}]*\[.*?\]\s*\}', raw_response, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group())
                    conference_calls = data.get('conference_calls', [])

                    for call in conference_calls:
                        calls.append({
                            'quarter': call.get('quarter', 'Unknown'),
                            'date': call.get('date', 'Unknown'),
                            'revenue_guidance': call.get('revenue_guidance', ''),
                            'margin_guidance': call.get('margin_guidance', ''),
                            'key_initiatives': call.get('key_initiatives', []),
                            'risks_mentioned': call.get('risks_mentioned', []),
                            'management_tone': call.get('management_tone', 'Neutral'),
                            'key_quotes': call.get('key_quotes', [])
                        })

                    return calls
                except json.JSONDecodeError:
                    self.logger.debug("Could not parse JSON, falling back to text analysis")

            # Fallback: Extract information from raw text
            # Look for quarters mentioned
            quarters = re.findall(r'Q[1-4]\s+(?:FY)?20\d{2}', raw_response)

            if quarters:
                # Create a call entry for the most recent quarter
                calls.append({
                    'quarter': quarters[0] if quarters else 'Recent',
                    'date': 'Unknown',
                    'revenue_guidance': self._extract_guidance(raw_response, 'revenue'),
                    'margin_guidance': self._extract_guidance(raw_response, 'margin'),
                    'key_initiatives': self._extract_text_initiatives(raw_response),
                    'risks_mentioned': self._extract_text_risks(raw_response),
                    'management_tone': self._extract_tone(raw_response),
                    'key_quotes': []
                })

        except Exception as e:
            self.logger.warning(f"Error parsing conference calls: {e}")

        return calls

    def _extract_guidance(self, text: str, guidance_type: str) -> str:
        """Extract guidance information from text"""
        # Look for sentences containing guidance keywords
        guidance_keywords = {
            'revenue': ['revenue', 'sales', 'topline'],
            'margin': ['margin', 'ebitda', 'profit']
        }

        keywords = guidance_keywords.get(guidance_type, [])
        sentences = text.split('.')

        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in keywords):
                if any(word in sentence.lower() for word in ['expect', 'guidance', 'forecast', 'target']):
                    return sentence.strip()

        return "Not found"

    def _extract_text_initiatives(self, text: str) -> List[str]:
        """Extract strategic initiatives from text"""
        initiatives = []
        text_lower = text.lower()

        for category, keywords in self.strategic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                initiatives.append(category.title())

        return initiatives[:5]  # Top 5

    def _extract_text_risks(self, text: str) -> List[str]:
        """Extract risks mentioned from text"""
        risks = []
        risk_keywords = ['risk', 'challenge', 'headwind', 'concern', 'uncertainty']

        sentences = text.split('.')
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in risk_keywords):
                # Extract the risk (simplified)
                if len(sentence.strip()) < 200:  # Keep it short
                    risks.append(sentence.strip())
                    if len(risks) >= 3:  # Max 3 risks
                        break

        return risks

    def _extract_tone(self, text: str) -> str:
        """Extract management tone from text"""
        text_lower = text.lower()

        pos_count = sum(1 for word in self.positive_tone if word in text_lower)
        caut_count = sum(1 for word in self.cautious_tone if word in text_lower)

        if pos_count > caut_count * 1.5:
            return "Optimistic"
        elif caut_count > pos_count * 1.5:
            return "Cautious"
        else:
            return "Neutral"

    def _score_guidance_quality(self, calls_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Score guidance quality (0-100)"""
        score = 50  # Neutral default
        signals = []

        if not calls_data:
            return {
                'score': 50,
                'signals': ['No guidance data available'],
                'clarity': 'unknown'
            }

        # Check if guidance is provided
        guidance_provided = 0
        total_calls = len(calls_data)

        for call in calls_data:
            if call.get('revenue_guidance') and call['revenue_guidance'] != 'Not found':
                guidance_provided += 1
                score += 10
                signals.append(f"Revenue guidance provided in {call['quarter']}")

            if call.get('margin_guidance') and call['margin_guidance'] != 'Not found':
                guidance_provided += 1
                score += 5
                signals.append(f"Margin guidance provided in {call['quarter']}")

        # Consistency bonus
        if guidance_provided >= total_calls:
            score += 15
            signals.append("Consistent guidance across quarters")

        score = max(0, min(100, score))

        return {
            'score': score,
            'signals': signals[:5],  # Top 5 signals
            'clarity': 'high' if guidance_provided >= total_calls else 'medium' if guidance_provided > 0 else 'low',
            'guidance_frequency': f"{guidance_provided}/{total_calls * 2} metrics"
        }

    def _score_strategic_vision(self, calls_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Score strategic vision (0-100)"""
        score = 50
        signals = []

        if not calls_data:
            return {'score': 50, 'signals': ['No strategy data'], 'vision_clarity': 'unknown'}

        # Count strategic initiatives mentioned
        all_initiatives = []
        for call in calls_data:
            initiatives = call.get('key_initiatives', [])
            all_initiatives.extend(initiatives)

        unique_initiatives = set(all_initiatives)

        # Score based on number and diversity of initiatives
        if len(unique_initiatives) >= 4:
            score += 20
            signals.append(f"Diverse strategic initiatives ({len(unique_initiatives)} categories)")
        elif len(unique_initiatives) >= 2:
            score += 10
            signals.append(f"Multiple strategic initiatives ({len(unique_initiatives)} categories)")

        # Check for innovation focus
        if 'Innovation' in all_initiatives:
            score += 15
            signals.append("Strong innovation focus")

        # Check for expansion/growth
        if 'Expansion' in all_initiatives:
            score += 10
            signals.append("Growth and expansion focus")

        score = max(0, min(100, score))

        return {
            'score': score,
            'signals': signals,
            'vision_clarity': 'high' if len(unique_initiatives) >= 3 else 'medium',
            'initiatives_count': len(unique_initiatives)
        }

    def _score_communication(self, calls_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Score communication quality (0-100)"""
        score = 50
        signals = []

        if not calls_data:
            return {'score': 50, 'signals': ['No communication data'], 'tone': 'unknown'}

        # Analyze tone consistency
        tones = [call.get('management_tone', 'Neutral') for call in calls_data]
        optimistic_count = tones.count('Optimistic')
        cautious_count = tones.count('Cautious')

        if optimistic_count > cautious_count:
            score += 15
            signals.append(f"Generally optimistic tone ({optimistic_count}/{len(tones)} calls)")
        elif cautious_count > optimistic_count:
            score -= 10
            signals.append(f"Cautious tone ({cautious_count}/{len(tones)} calls)")

        # Check for key quotes (transparency indicator)
        quotes_count = sum(len(call.get('key_quotes', [])) for call in calls_data)
        if quotes_count >= len(calls_data):
            score += 10
            signals.append("Good transparency with detailed quotes")

        score = max(0, min(100, score))

        dominant_tone = 'Optimistic' if optimistic_count > len(tones) / 2 else 'Cautious' if cautious_count > len(tones) / 2 else 'Neutral'

        return {
            'score': score,
            'signals': signals,
            'tone': dominant_tone,
            'transparency': 'high' if quotes_count >= len(calls_data) else 'medium'
        }

    def _score_risk_management(self, calls_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Score risk management (0-100)"""
        score = 50
        signals = []

        if not calls_data:
            return {'score': 50, 'signals': ['No risk data'], 'disclosure': 'unknown'}

        # Count risks disclosed
        total_risks = sum(len(call.get('risks_mentioned', [])) for call in calls_data)

        if total_risks >= len(calls_data) * 2:  # At least 2 risks per call
            score += 20
            signals.append(f"Comprehensive risk disclosure ({total_risks} risks across {len(calls_data)} calls)")
        elif total_risks >= len(calls_data):
            score += 10
            signals.append(f"Adequate risk disclosure ({total_risks} risks)")
        else:
            score -= 10
            signals.append(f"Limited risk disclosure ({total_risks} risks)")

        score = max(0, min(100, score))

        return {
            'score': score,
            'signals': signals,
            'disclosure': 'high' if total_risks >= len(calls_data) * 2 else 'medium' if total_risks > 0 else 'low',
            'risks_disclosed': total_risks
        }

    def _score_capital_allocation(self, calls_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Score capital allocation (0-100)"""
        score = 50
        signals = []

        if not calls_data:
            return {'score': 50, 'signals': ['No capital allocation data'], 'focus': 'unknown'}

        # Look for mentions of dividends, buybacks, capex in guidance
        all_guidance = ' '.join([
            call.get('revenue_guidance', '') + ' ' +
            call.get('margin_guidance', '')
            for call in calls_data
        ]).lower()

        capital_keywords = {
            'dividend': ['dividend', 'payout'],
            'buyback': ['buyback', 'share repurchase'],
            'investment': ['capex', 'investment', 'r&d'],
            'debt': ['debt reduction', 'deleveraging']
        }

        focus_areas = []
        for category, keywords in capital_keywords.items():
            if any(keyword in all_guidance for keyword in keywords):
                focus_areas.append(category)
                score += 10
                signals.append(f"{category.title()} mentioned in guidance")

        score = max(0, min(100, score))

        return {
            'score': score,
            'signals': signals,
            'focus': ', '.join(focus_areas) if focus_areas else 'unclear',
            'areas_covered': len(focus_areas)
        }

    def _determine_tone(self, calls_data: List[Dict[str, Any]]) -> str:
        """Determine overall management tone"""
        if not calls_data:
            return "Unknown"

        tones = [call.get('management_tone', 'Neutral') for call in calls_data]

        optimistic = tones.count('Optimistic')
        cautious = tones.count('Cautious')

        if optimistic > cautious:
            return "Optimistic"
        elif cautious > optimistic:
            return "Cautious"
        else:
            return "Neutral"

    def _extract_initiatives(self, calls_data: List[Dict[str, Any]]) -> List[str]:
        """Extract key strategic initiatives"""
        all_initiatives = []

        for call in calls_data:
            initiatives = call.get('key_initiatives', [])
            all_initiatives.extend(initiatives)

        # Get unique initiatives, preserving order
        seen = set()
        unique_initiatives = []
        for initiative in all_initiatives:
            if initiative not in seen:
                seen.add(initiative)
                unique_initiatives.append(initiative)

        return unique_initiatives[:5]  # Top 5

    def _extract_risks(self, calls_data: List[Dict[str, Any]]) -> List[str]:
        """Extract key risks disclosed"""
        all_risks = []

        for call in calls_data:
            risks = call.get('risks_mentioned', [])
            all_risks.extend(risks)

        return all_risks[:5]  # Top 5 risks

    async def _get_llm_analysis(
        self,
        ticker: str,
        company_name: str,
        raw_conf_calls: Dict[str, Any],
        parsed_calls: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Get deep LLM analysis using Claude-3.5-Sonnet (200k context)

        Analyzes:
        - Promise vs performance tracking
        - Management credibility
        - Strategic execution
        - Risk assessment
        """
        try:
            from tools.llm.prompts import PromptTemplates

            # Extract transcripts/excerpts
            transcripts = []
            for call in parsed_calls[:3]:  # Last 3 quarters
                transcript_text = f"""
Quarter: {call.get('quarter', 'Unknown')}
Date: {call.get('date', 'Unknown')}
Revenue Guidance: {call.get('revenue_guidance', 'Not specified')}
Margin Guidance: {call.get('margin_guidance', 'Not specified')}
Key Initiatives: {', '.join(call.get('key_initiatives', []))}
Risks Mentioned: {', '.join(call.get('risks_mentioned', []))}
Management Tone: {call.get('management_tone', 'Neutral')}
"""
                transcripts.append(transcript_text)

            # Use management quality analysis prompt
            messages = PromptTemplates.management_quality_analysis(
                ticker=ticker,
                company_name=company_name,
                concall_transcripts=transcripts,
                annual_report_excerpts=[],  # Not available yet
                actual_performance={}  # Not available yet
            )

            # Call GPT-4-Turbo for management analysis
            # Note: Switched from Claude-3.5-Sonnet due to API access issues
            # GPT-4 still provides excellent analysis with 128k context window
            response = await self.llm.chat(
                messages=messages,
                provider="openai",
                model="gpt-4-turbo",
                temperature=0.2,
                json_mode=True  # Request structured JSON response
            )

            # Parse response
            try:
                analysis = json.loads(response.content)
            except json.JSONDecodeError:
                # If not JSON, wrap as text
                analysis = {'summary': response.content[:1000]}

            self.logger.info(f"Claude-3.5 management analysis complete for {ticker}")
            return analysis

        except Exception as e:
            self.logger.error(f"LLM analysis failed: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _generate_summary(self, score: float, tone: str, initiatives: List[str], llm_analysis: Optional[Dict] = None) -> str:
        """Generate human-readable summary"""
        summary_parts = []

        # If LLM analysis available, use it
        if llm_analysis and llm_analysis.get('recommendation'):
            return f"{llm_analysis.get('recommendation', '')} | Management Score: {score:.1f}/100"

        # Otherwise use rule-based summary
        # Score assessment
        if score >= 75:
            summary_parts.append("Excellent management quality")
        elif score >= 60:
            summary_parts.append("Good management quality")
        elif score >= 40:
            summary_parts.append("Average management quality")
        else:
            summary_parts.append("Below average management quality")

        # Tone
        summary_parts.append(f"{tone} management tone")

        # Initiatives
        if initiatives:
            summary_parts.append(f"Focus on: {', '.join(initiatives[:3])}")

        return " | ".join(summary_parts)

    def _error_response(self, ticker: str, error: str) -> Dict[str, Any]:
        """Return error response"""
        return {
            'score': 50,
            'ticker': ticker,
            'error': error,
            'management_tone': 'Unknown',
            'timestamp': datetime.now().isoformat()
        }


# Example usage
async def main():
    """Example usage of Management Analyst"""

    config = {
        'quarters_to_analyze': 4,
        'min_confidence': 60.0
    }

    analyst = ManagementAnalyst(config)

    # Analyze a stock
    result = await analyst.analyze('RELIANCE.NS', {'company_name': 'Reliance Industries'})

    if 'error' not in result or result.get('score') != 50:
        print(f"Management Score: {result['score']}")
        print(f"Management Tone: {result['management_tone']}")
        print(f"Quarters Analyzed: {result['quarters_analyzed']}")
        print(f"Summary: {result['summary']}")

        print(f"\nCategory Scores:")
        print(f"  Guidance:           {result['guidance']['score']}")
        print(f"  Strategic Vision:   {result['strategy']['score']}")
        print(f"  Communication:      {result['communication']['score']}")
        print(f"  Risk Management:    {result['risk_management']['score']}")
        print(f"  Capital Allocation: {result['capital_allocation']['score']}")

        if result.get('key_initiatives'):
            print(f"\nKey Initiatives: {', '.join(result['key_initiatives'])}")
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
