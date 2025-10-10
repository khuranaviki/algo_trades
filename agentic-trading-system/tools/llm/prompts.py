"""
Standardized LLM Prompts for Trading System Agents

Contains prompt templates for:
- Fundamental Analysis
- Technical Analysis (pattern interpretation)
- Sentiment Analysis
- Management Quality Analysis
- Risk Assessment
"""

from typing import Dict, Any, List, Optional
from datetime import datetime


class PromptTemplates:
    """Centralized prompt templates for all agents"""

    @staticmethod
    def fundamental_analysis(
        ticker: str,
        company_name: str,
        financial_data: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """
        Generate prompt for fundamental analysis

        Args:
            ticker: Stock ticker
            company_name: Company name
            financial_data: Dict with PE, ROE, Debt/Equity, etc.

        Returns:
            List of messages for LLM
        """
        system_prompt = """You are a senior fundamental analyst with 15 years of experience in Indian stock markets.
Your task is to analyze financial metrics and provide a comprehensive fundamental score (0-100).

Focus on:
1. Financial Health (30%): Debt levels, interest coverage, current ratio
2. Growth (30%): Revenue growth, profit growth, consistency
3. Valuation (20%): PE ratio vs industry, PB ratio, fair value
4. Quality (20%): ROE, ROCE, operating margins

Return response in JSON format with:
{
    "fundamental_score": 0-100,
    "financial_health_score": 0-100,
    "growth_score": 0-100,
    "valuation_score": 0-100,
    "quality_score": 0-100,
    "strengths": ["list of key strengths"],
    "weaknesses": ["list of key concerns"],
    "red_flags": ["any critical issues"],
    "recommendation": "BUY/HOLD/SELL",
    "reasoning": "2-3 sentence explanation"
}"""

        user_prompt = f"""Analyze the fundamental metrics for {company_name} ({ticker}):

Financial Metrics:
- PE Ratio: {financial_data.get('pe_ratio', 'N/A')}
- PB Ratio: {financial_data.get('pb_ratio', 'N/A')}
- ROE: {financial_data.get('roe', 'N/A')}%
- ROCE: {financial_data.get('roce', 'N/A')}%
- Debt to Equity: {financial_data.get('debt_to_equity', 'N/A')}
- Current Ratio: {financial_data.get('current_ratio', 'N/A')}
- Interest Coverage: {financial_data.get('interest_coverage', 'N/A')}

Growth Metrics:
- Revenue Growth (YoY): {financial_data.get('revenue_growth', 'N/A')}%
- Profit Growth (YoY): {financial_data.get('profit_growth', 'N/A')}%
- 3-Year CAGR: {financial_data.get('cagr_3y', 'N/A')}%

Profitability:
- Operating Margin: {financial_data.get('operating_margin', 'N/A')}%
- Net Margin: {financial_data.get('net_margin', 'N/A')}%

Sector: {financial_data.get('sector', 'N/A')}
Industry PE (avg): {financial_data.get('industry_pe', 'N/A')}

Provide comprehensive analysis in JSON format."""

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

    @staticmethod
    def technical_pattern_interpretation(
        ticker: str,
        pattern_name: str,
        backtest_results: Dict[str, Any],
        market_context: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """
        Generate prompt for technical pattern interpretation

        Args:
            ticker: Stock ticker
            pattern_name: Detected pattern (RHS, CWH, etc.)
            backtest_results: Historical validation results
            market_context: Current market conditions

        Returns:
            List of messages for LLM
        """
        system_prompt = """You are a quantitative analyst specializing in technical patterns and backtesting.
Your task is to interpret backtest results and assess the reliability of a technical pattern.

Consider:
1. Historical Win Rate (must be >70%)
2. Risk/Reward ratio
3. Current market regime
4. Pattern quality and confluence
5. Sample size adequacy

Return JSON format with:
{
    "technical_score": 0-100,
    "pattern_reliability": 0-100,
    "entry_timing": "IMMEDIATE/WAIT/AVOID",
    "confidence_level": "HIGH/MEDIUM/LOW",
    "risk_reward_ratio": float,
    "key_observations": ["list of insights"],
    "concerns": ["list of concerns"],
    "recommendation": "VALIDATED/NOT_VALIDATED"
}"""

        user_prompt = f"""Analyze this technical setup for {ticker}:

Pattern Detected: {pattern_name}

Backtest Results (5-year historical):
- Win Rate: {backtest_results.get('win_rate', 0)}%
- Total Trades: {backtest_results.get('total_trades', 0)}
- Average Return: {backtest_results.get('avg_return', 0)}%
- Best Trade: {backtest_results.get('best_trade', 0)}%
- Worst Trade: {backtest_results.get('worst_trade', 0)}%
- Sharpe Ratio: {backtest_results.get('sharpe_ratio', 0)}
- Max Drawdown: {backtest_results.get('max_drawdown', 0)}%

Market Context:
- NIFTY Trend: {market_context.get('nifty_trend', 'N/A')}
- Sector Trend: {market_context.get('sector_trend', 'N/A')}
- Volatility: {market_context.get('volatility', 'N/A')}
- Market Regime: {market_context.get('regime', 'UNKNOWN')}

Pattern Formed: {backtest_results.get('formation_date', 'Recently')}

Assess if this pattern is reliable enough to trade."""

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

    @staticmethod
    def sentiment_analysis(
        ticker: str,
        company_name: str,
        news_summary: str,
        social_sentiment: str,
        analyst_ratings: str
    ) -> List[Dict[str, str]]:
        """
        Generate prompt for sentiment analysis

        Args:
            ticker: Stock ticker
            company_name: Company name
            news_summary: Recent news summary
            social_sentiment: Social media sentiment
            analyst_ratings: Analyst consensus

        Returns:
            List of messages for LLM
        """
        system_prompt = """You are a market sentiment analyst tracking news, social media, and analyst opinions.
Your task is to synthesize multiple sentiment sources into a unified sentiment score.

Weighting:
- News Sentiment: 40%
- Analyst Ratings: 40%
- Social/Retail Sentiment: 20%

Return JSON format with:
{
    "sentiment_score": 0-100,
    "news_sentiment": 0-100,
    "analyst_sentiment": 0-100,
    "social_sentiment": 0-100,
    "sentiment_trend": "IMPROVING/STABLE/DETERIORATING",
    "key_catalysts": ["positive drivers"],
    "key_concerns": ["negative factors"],
    "market_buzz": "HIGH/MEDIUM/LOW",
    "recommendation": "BULLISH/NEUTRAL/BEARISH"
}"""

        user_prompt = f"""Analyze market sentiment for {company_name} ({ticker}):

Recent News (Last 30 Days):
{news_summary}

Analyst Ratings:
{analyst_ratings}

Social Media Sentiment:
{social_sentiment}

Synthesize overall sentiment and identify key drivers."""

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

    @staticmethod
    def management_quality_analysis(
        ticker: str,
        company_name: str,
        concall_transcripts: List[str],
        annual_report_excerpts: List[str],
        actual_performance: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """
        Generate prompt for management quality analysis

        Args:
            ticker: Stock ticker
            company_name: Company name
            concall_transcripts: Last 3 years concall excerpts
            annual_report_excerpts: Key sections from reports
            actual_performance: Actual business metrics

        Returns:
            List of messages for LLM
        """
        system_prompt = """You are an expert in corporate governance and management assessment.
Your task is to evaluate management quality by comparing their promises to actual performance.

Analyze:
1. Credibility (40%): Do they deliver on promises?
2. Transparency (30%): Are they honest about challenges?
3. Vision (20%): Strategic clarity and execution
4. Risk Management (10%): How they handle adversity

Return JSON format with:
{
    "management_score": 0-100,
    "credibility_score": 0-100,
    "transparency_score": 0-100,
    "vision_score": 0-100,
    "risk_management_score": 0-100,
    "promises_kept": ["list of delivered promises"],
    "promises_broken": ["list of unmet commitments"],
    "red_flags": ["concerning patterns"],
    "management_changes": ["significant leadership changes"],
    "recommendation": "EXCELLENT/GOOD/AVERAGE/POOR",
    "conviction_level": "HIGH/MEDIUM/LOW"
}"""

        # Build consolidated view
        concalls_text = "\n\n".join([
            f"--- Conference Call {i+1} ---\n{text[:1000]}"
            for i, text in enumerate(concall_transcripts[:3])
        ])

        reports_text = "\n\n".join([
            f"--- Annual Report {i+1} ---\n{text[:1000]}"
            for i, text in enumerate(annual_report_excerpts[:3])
        ])

        user_prompt = f"""Assess management quality for {company_name} ({ticker}):

Conference Call Excerpts (Last 3 Years):
{concalls_text}

Annual Report Excerpts (Last 3 Years):
{reports_text}

Actual Performance vs Guidance:
- Revenue Target: {actual_performance.get('revenue_target', 'N/A')} | Actual: {actual_performance.get('revenue_actual', 'N/A')}
- Margin Target: {actual_performance.get('margin_target', 'N/A')}% | Actual: {actual_performance.get('margin_actual', 'N/A')}%
- Growth Target: {actual_performance.get('growth_target', 'N/A')}% | Actual: {actual_performance.get('growth_actual', 'N/A')}%

Key Challenges Mentioned:
{actual_performance.get('challenges_mentioned', 'N/A')}

Evaluate if management is credible, transparent, and executes well."""

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

    @staticmethod
    def risk_assessment(
        ticker: str,
        fundamental_score: float,
        technical_score: float,
        sentiment_score: float,
        management_score: float,
        market_context: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """
        Generate prompt for overall risk assessment

        Args:
            ticker: Stock ticker
            fundamental_score: Score from fundamental analyst
            technical_score: Score from technical analyst
            sentiment_score: Score from sentiment analyst
            management_score: Score from management analyst
            market_context: Current market conditions

        Returns:
            List of messages for LLM
        """
        system_prompt = """You are a risk management specialist evaluating trade setups.
Your task is to assess overall risk and determine if a trade should proceed.

Veto Rules:
- Fundamental Score < 50: High risk
- Management Score < 40: Critical risk
- Technical Win Rate < 70%: Not validated
- Any Red Flag: Requires explanation

Return JSON format with:
{
    "overall_risk": "LOW/MEDIUM/HIGH",
    "risk_score": 0-100,
    "proceed_with_trade": true/false,
    "risk_factors": ["list of identified risks"],
    "mitigating_factors": ["positive aspects"],
    "position_size_recommendation": "FULL/HALF/QUARTER/NONE",
    "stop_loss_recommendation": float,
    "time_horizon": "SHORT/MEDIUM/LONG",
    "final_recommendation": "BUY/HOLD/SELL/AVOID"
}"""

        user_prompt = f"""Assess overall risk for trading {ticker}:

Agent Scores:
- Fundamental: {fundamental_score}/100
- Technical: {technical_score}/100
- Sentiment: {sentiment_score}/100
- Management: {management_score}/100

Market Context:
- Market Trend: {market_context.get('market_trend', 'N/A')}
- Sector Performance: {market_context.get('sector_performance', 'N/A')}
- Volatility Index: {market_context.get('vix', 'N/A')}
- Market Regime: {market_context.get('regime', 'N/A')}

Current Position:
- Portfolio Exposure: {market_context.get('portfolio_exposure', 0)}%
- Available Capital: {market_context.get('available_capital', 'N/A')}

Determine if this is a good risk/reward setup."""

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

    @staticmethod
    def orchestrator_decision(
        ticker: str,
        all_agent_outputs: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """
        Generate prompt for orchestrator's final decision

        Args:
            ticker: Stock ticker
            all_agent_outputs: Combined outputs from all agents

        Returns:
            List of messages for LLM
        """
        system_prompt = """You are the lead portfolio manager making final trading decisions.
You have received analysis from 5 specialized agents. Your task is to synthesize their
insights and make a clear BUY/HOLD/SELL decision.

Decision Framework:
1. Check for veto conditions (any agent below threshold)
2. Evaluate consensus across agents
3. Assess risk/reward
4. Determine position sizing
5. Set exit conditions

Return JSON format with:
{
    "final_decision": "BUY/HOLD/SELL",
    "confidence": 0-100,
    "position_size": 0-100 (% of intended allocation),
    "entry_price": float,
    "target_price": float,
    "stop_loss": float,
    "time_horizon_days": int,
    "reasoning": "detailed explanation",
    "consensus_level": "STRONG/MODERATE/WEAK",
    "conflicting_signals": ["any contradictions"],
    "key_catalysts": ["reasons to buy"],
    "key_risks": ["reasons to avoid"]
}"""

        # Format agent outputs
        agents_summary = f"""
Fundamental Analyst:
- Score: {all_agent_outputs.get('fundamental', {}).get('score', 0)}/100
- Recommendation: {all_agent_outputs.get('fundamental', {}).get('recommendation', 'N/A')}
- Key Points: {all_agent_outputs.get('fundamental', {}).get('summary', 'N/A')}

Technical Analyst:
- Score: {all_agent_outputs.get('technical', {}).get('score', 0)}/100
- Win Rate: {all_agent_outputs.get('technical', {}).get('win_rate', 0)}%
- Recommendation: {all_agent_outputs.get('technical', {}).get('recommendation', 'N/A')}

Sentiment Analyst:
- Score: {all_agent_outputs.get('sentiment', {}).get('score', 0)}/100
- Trend: {all_agent_outputs.get('sentiment', {}).get('trend', 'N/A')}
- Recommendation: {all_agent_outputs.get('sentiment', {}).get('recommendation', 'N/A')}

Management Analyst:
- Score: {all_agent_outputs.get('management', {}).get('score', 0)}/100
- Conviction: {all_agent_outputs.get('management', {}).get('conviction', 'N/A')}
- Recommendation: {all_agent_outputs.get('management', {}).get('recommendation', 'N/A')}

Backtest Validator:
- Validated: {all_agent_outputs.get('backtest', {}).get('validated', False)}
- Historical Win Rate: {all_agent_outputs.get('backtest', {}).get('win_rate', 0)}%
- Risk/Reward: {all_agent_outputs.get('backtest', {}).get('risk_reward', 0)}
"""

        user_prompt = f"""Make final trading decision for {ticker}:

{agents_summary}

Synthesize all inputs and make a clear decision with position sizing and exit strategy."""

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

    @staticmethod
    def conflict_resolution_synthesis(
        ticker: str,
        company_name: str,
        agent_results: Dict[str, Any],
        conflict_info: Dict[str, Any],
        composite_score: float,
        technical_signal: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """LLM-based conflict resolution"""

        system_prompt = """You are an expert trading decision synthesizer.

CRITICAL RULES:
1. Only recommend BUY if technical signal exists
2. Distinguish "good company, bad timing" vs "bad company"
3. Provide alternative scenarios

Return JSON:
{
    "final_recommendation": "BUY|SELL|HOLD|WAIT",
    "adjusted_score": 0-100,
    "confidence": 0-100,
    "reasoning": "explanation",
    "key_insights": ["insight1", "insight2"],
    "conflict_analysis": "why agents disagree",
    "risk_factors": ["risk1"],
    "alternative_scenarios": [{"condition": "if X", "action": "then Y", "probability": "high"}],
    "time_horizon": "short-term|medium-term|long-term"
}"""

        fund = agent_results.get('fundamental', {})
        tech = agent_results.get('technical', {})
        sent = agent_results.get('sentiment', {})
        mgmt = agent_results.get('management', {})

        user_prompt = f"""Synthesize decision for {company_name} ({ticker}):

FUNDAMENTAL: {fund.get('score', 0)}/100 - {fund.get('llm_analysis', {}).get('reasoning', 'N/A')[:150]}
TECHNICAL: {tech.get('score', 0)}/100 - {tech.get('trend', {}).get('direction', 'N/A')}
SENTIMENT: {sent.get('score', 0)}/100 - {sent.get('sentiment', 'N/A')}
MANAGEMENT: {mgmt.get('score', 0)}/100 - Credibility: {mgmt.get('llm_analysis', {}).get('credibility_score', 'N/A')}

CONFLICT: {conflict_info.get('conflict_level', 'none')} (variance={conflict_info.get('variance', 0):.3f})
TECHNICAL SIGNAL: {technical_signal.get('has_signal', False)}
COMPOSITE: {composite_score:.1f}/100

Provide nuanced recommendation."""

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]


# Helper function to create messages
def create_chat_messages(
    system_prompt: str,
    user_prompt: str,
    context: Optional[Dict[str, Any]] = None
) -> List[Dict[str, str]]:
    """
    Helper to create chat messages with optional context injection

    Args:
        system_prompt: System message
        user_prompt: User message
        context: Optional context dict to inject into user prompt

    Returns:
        List of message dicts
    """
    messages = [
        {"role": "system", "content": system_prompt}
    ]

    if context:
        context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
        user_prompt = f"{user_prompt}\n\nAdditional Context:\n{context_str}"

    messages.append({"role": "user", "content": user_prompt})

    return messages

    @staticmethod
    def conflict_resolution_synthesis(
        ticker: str,
        company_name: str,
        agent_results: Dict[str, Any],
        conflict_info: Dict[str, Any],
        composite_score: float,
        technical_signal: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """LLM-based conflict resolution and decision synthesis"""

        system_prompt = """You are an expert trading decision synthesizer with 20 years of experience.

CRITICAL RULES:
1. Only recommend BUY if there's a clear technical entry signal
2. Distinguish between "good company, bad timing" vs "bad company"
3. Provide alternative scenarios
4. Specify time horizon

Return JSON:
{
    "final_recommendation": "BUY|SELL|HOLD|WAIT",
    "adjusted_score": 0-100,
    "confidence": 0-100,
    "reasoning": "2-3 sentence explanation",
    "key_insights": ["insight1", "insight2", "insight3"],
    "conflict_analysis": "Why agents disagree",
    "risk_factors": ["risk1", "risk2"],
    "alternative_scenarios": [{"condition": "if X", "action": "then Y", "probability": "high|medium|low"}],
    "time_horizon": "short-term|medium-term|long-term",
    "position_sizing_advice": "FULL|HALF|QUARTER|NONE",
    "requires_monitoring": true|false,
    "watchlist_triggers": ["trigger1", "trigger2"]
}"""

        fundamental = agent_results.get('fundamental', {})
        technical = agent_results.get('technical', {})
        sentiment = agent_results.get('sentiment', {})
        management = agent_results.get('management', {})

        disagreements_text = "None"
        if conflict_info.get('disagreements'):
            lines = []
            for d in conflict_info['disagreements']:
                agents = d.get('agents', [])
                diff = d.get('difference', 0)
                scores = d.get('scores', {})
                lines.append(f"- {agents[0]} ({scores.get(agents[0], 0):.1f}) vs {agents[1]} ({scores.get(agents[1], 0):.1f}) = {diff:.1f} gap")
            disagreements_text = "\n".join(lines)

        user_prompt = f"""Synthesize decision for {company_name} ({ticker}):

FUNDAMENTAL (Score: {fundamental.get('score', 0)}/100)
Recommendation: {fundamental.get('recommendation', 'N/A')}
LLM Reasoning: {fundamental.get('llm_analysis', {}).get('reasoning', 'N/A')[:200]}

TECHNICAL (Score: {technical.get('score', 0)}/100)
Trend: {technical.get('trend', {}).get('direction', 'N/A')}
Pattern: {technical.get('primary_pattern', {}).get('name', 'None')}

SENTIMENT (Score: {sentiment.get('score', 0)}/100)
Sentiment: {sentiment.get('sentiment', 'N/A')}

MANAGEMENT (Score: {management.get('score', 0)}/100)
Tone: {management.get('management_tone', 'N/A')}
Credibility: {management.get('llm_analysis', {}).get('credibility_score', 'N/A')}/100

CONFLICT: {conflict_info.get('conflict_level', 'none')} (variance={conflict_info.get('variance', 0):.3f})
Disagreements: {disagreements_text}

TECHNICAL SIGNAL: {technical_signal.get('has_signal', False)} ({technical_signal.get('signal_type', 'None')})

COMPOSITE SCORE: {composite_score:.2f}/100

IMPORTANT: Can only BUY if technical signal exists!

Provide nuanced recommendation."""

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

