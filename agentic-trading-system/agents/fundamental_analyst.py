"""
Fundamental Analyst Agent

Analyzes financial health, growth, valuation, and quality metrics.
Provides a composite fundamental score (0-100).

VETO POWER: Score < 50 = trade rejection
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
import logging

from agents.base_agent import BaseAgent
from tools.data_fetchers.fundamental_data import FundamentalDataFetcher
from tools.llm.llm_client import LLMClient
from tools.llm.prompts import PromptTemplates
from tools.caching.cache_client import CacheClient


class FundamentalAnalyst(BaseAgent):
    """
    Analyzes fundamental metrics and provides buy/hold/sell recommendation

    Scoring breakdown:
    - Financial Health: 30% (debt, liquidity, coverage)
    - Growth: 30% (revenue, profit, CAGR)
    - Valuation: 20% (PE, PB, fair value)
    - Quality: 20% (ROE, ROCE, margins)
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Fundamental Analyst

        Args:
            config: Configuration dict with weights and thresholds
        """
        super().__init__("Fundamental Analyst", config)

        self.fundamental_data = FundamentalDataFetcher()
        self.llm = LLMClient()
        self.cache = CacheClient()

        # Scoring weights
        self.weights = config.get('weights', {
            'financial_health': 0.30,
            'growth': 0.30,
            'valuation': 0.20,
            'quality': 0.20
        })

        # Thresholds
        self.scoring_criteria = config.get('scoring_criteria', {})

        # LLM settings
        self.use_llm = config.get('use_llm', True)
        self.llm_provider = config.get('llm_provider', 'openai')
        self.llm_model = config.get('llm_model', 'gpt-4-turbo')

    async def analyze(self, ticker: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze fundamental metrics for a stock

        Args:
            ticker: Stock ticker
            context: Additional context

        Returns:
            Dict with fundamental analysis
        """
        if not self.validate_input(ticker):
            return self._error_response(ticker, "Invalid ticker")

        self.logger.info(f"Analyzing fundamentals for {ticker}")

        # Check cache first (7-day TTL for fundamentals)
        cached = self.cache.get_fundamental_data(ticker)
        if cached and not context.get('force_refresh', False):
            self.logger.info(f"Cache HIT: Fundamental data for {ticker}")
            return self._format_analysis(ticker, cached, from_cache=True)

        # Fetch fundamental data
        fundamental_data = self.fundamental_data.get_fundamental_data(ticker)

        if fundamental_data.get('error'):
            return self._error_response(ticker, fundamental_data['error'])

        # Detect sector for specialized scoring
        sector = fundamental_data.get('sector', '')
        industry = fundamental_data.get('industry', '')
        is_bank = self._is_bank(sector, industry)

        # Calculate component scores (sector-specific)
        if is_bank:
            self.logger.info(f"Using bank-specific scoring for {ticker}")
            financial_health = self._score_bank_financial_health(fundamental_data)
        else:
            financial_health = self._score_financial_health(fundamental_data)

        growth = self._score_growth(fundamental_data)
        valuation = self._score_valuation(fundamental_data)
        quality = self._score_quality(fundamental_data)

        # Calculate composite score
        composite_score = (
            financial_health['score'] * self.weights['financial_health'] +
            growth['score'] * self.weights['growth'] +
            valuation['score'] * self.weights['valuation'] +
            quality['score'] * self.weights['quality']
        )

        # Detect red flags
        red_flags = self._detect_red_flags(fundamental_data)

        # Get LLM analysis if enabled
        llm_analysis = None
        if self.use_llm:
            llm_analysis = await self._get_llm_analysis(ticker, fundamental_data)

        # Determine recommendation
        recommendation = self._get_recommendation(composite_score, red_flags)

        result = {
            'fundamental_score': round(composite_score, 2),
            'financial_health': financial_health,
            'growth': growth,
            'valuation': valuation,
            'quality': quality,
            'red_flags': red_flags,
            'recommendation': recommendation,
            'llm_analysis': llm_analysis,
            'raw_data': fundamental_data
        }

        # Cache for 7 days
        self.cache.cache_fundamental_data(ticker, result, ttl=604800)

        self.analysis_count += 1

        return self._format_analysis(ticker, result, from_cache=False)

    def _is_bank(self, sector: str, industry: str) -> bool:
        """
        Detect if the company is a bank/financial institution

        Args:
            sector: Company sector
            industry: Company industry

        Returns:
            True if bank, False otherwise
        """
        bank_keywords = [
            'bank', 'banking', 'financial services', 'nbfc',
            'finance', 'credit', 'lending'
        ]

        sector_lower = sector.lower()
        industry_lower = industry.lower()

        return any(keyword in sector_lower or keyword in industry_lower
                   for keyword in bank_keywords)

    def _score_bank_financial_health(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score financial health for banks (0-100)

        Bank-specific metrics:
        - Capital Adequacy Ratio (CAR)
        - Gross/Net NPA
        - CASA Ratio
        - Return on Assets (ROA)

        Falls back to available metrics if bank-specific data not available
        """
        score = 0
        max_score = 100
        breakdown = {}
        signals = []

        # For now, use alternative metrics that ARE available for banks
        # ROA (25 points) - banks report this
        roa = data.get('roa')
        if roa is not None and roa > 0:
            if roa >= 2.0:
                roa_score = 25
                signals.append(f"Excellent ROA: {roa:.2f}%")
            elif roa >= 1.5:
                roa_score = 20
                signals.append(f"Good ROA: {roa:.2f}%")
            elif roa >= 1.0:
                roa_score = 15
                signals.append(f"Average ROA: {roa:.2f}%")
            elif roa >= 0.5:
                roa_score = 10
            else:
                roa_score = 5
                signals.append(f"Low ROA: {roa:.2f}%")
            score += roa_score
            breakdown['roa_score'] = roa_score

        # Book Value (25 points) - indicates capital strength
        book_value = data.get('book_value')
        pb_ratio = data.get('pb_ratio')
        if book_value and book_value > 0:
            # Higher book value = stronger capital base
            if book_value >= 300:
                bv_score = 25
                signals.append(f"Strong capital base (BV: ₹{book_value:.0f})")
            elif book_value >= 200:
                bv_score = 20
            elif book_value >= 100:
                bv_score = 15
            else:
                bv_score = 10
            score += bv_score
            breakdown['book_value_score'] = bv_score

        # ROE for banks (25 points) - profitability measure
        roe = data.get('roe')
        if roe is not None and roe > 0:
            if roe >= 15.0:
                roe_score = 25
                signals.append(f"Strong ROE: {roe:.2f}%")
            elif roe >= 12.0:
                roe_score = 20
                signals.append(f"Good ROE: {roe:.2f}%")
            elif roe >= 10.0:
                roe_score = 15
            elif roe >= 8.0:
                roe_score = 10
            else:
                roe_score = 5
                signals.append(f"Low ROE: {roe:.2f}%")
            score += roe_score
            breakdown['roe_score'] = roe_score

        # Payout Ratio (25 points) - sustainable dividends
        payout_ratio = data.get('payout_ratio')
        if payout_ratio is not None and payout_ratio > 0:
            if 20 <= payout_ratio <= 40:
                payout_score = 25
                signals.append(f"Healthy payout ratio: {payout_ratio:.1f}%")
            elif 15 <= payout_ratio <= 50:
                payout_score = 20
            elif 10 <= payout_ratio <= 60:
                payout_score = 15
            elif payout_ratio < 70:
                payout_score = 10
            else:
                payout_score = 5
                signals.append(f"High payout ratio: {payout_ratio:.1f}%")
            score += payout_score
            breakdown['payout_score'] = payout_score

        # If no metrics available, give neutral score
        if score == 0:
            score = 50
            signals.append("Limited financial health data - neutral score")

        return {
            'score': score,
            'max_score': max_score,
            'percentage': round((score / max_score) * 100, 2),
            'breakdown': breakdown,
            'signals': signals,
            'rating': self._get_rating(score / max_score * 100)
        }

    def _score_financial_health(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score financial health (0-100)

        Metrics: Debt/Equity, Current Ratio, Interest Coverage
        """
        score = 0
        max_score = 100
        breakdown = {}

        criteria = self.scoring_criteria.get('financial_health', {})

        # Debt to Equity (40 points)
        debt_to_equity = data.get('debt_to_equity')
        if debt_to_equity is not None and debt_to_equity >= 0:
            de_criteria = criteria.get('debt_to_equity', {'excellent': 0.5, 'good': 1.0, 'average': 2.0})
            if debt_to_equity <= de_criteria['excellent']:
                debt_score = 40
            elif debt_to_equity <= de_criteria['good']:
                debt_score = 30
            elif debt_to_equity <= de_criteria['average']:
                debt_score = 15
            else:
                debt_score = 0
            score += debt_score
            breakdown['debt_score'] = debt_score

        # Current Ratio (30 points)
        current_ratio = data.get('current_ratio')
        if current_ratio is not None and current_ratio > 0:
            cr_criteria = criteria.get('current_ratio', {'excellent': 2.0, 'good': 1.5, 'average': 1.0})
            if current_ratio >= cr_criteria['excellent']:
                current_score = 30
            elif current_ratio >= cr_criteria['good']:
                current_score = 22
            elif current_ratio >= cr_criteria['average']:
                current_score = 10
            else:
                current_score = 0
            score += current_score
            breakdown['current_ratio_score'] = current_score

        # Interest Coverage (30 points)
        interest_coverage = data.get('interest_coverage')
        if interest_coverage is not None and interest_coverage > 0:
            ic_criteria = criteria.get('interest_coverage', {'excellent': 5.0, 'good': 3.0, 'average': 2.0})
            if interest_coverage >= ic_criteria['excellent']:
                interest_score = 30
            elif interest_coverage >= ic_criteria['good']:
                interest_score = 22
            elif interest_coverage >= ic_criteria['average']:
                interest_score = 10
            else:
                interest_score = 0
            score += interest_score
            breakdown['interest_coverage_score'] = interest_score

        return {
            'score': score,
            'max_score': max_score,
            'percentage': round((score / max_score) * 100, 2),
            'breakdown': breakdown,
            'rating': self._get_rating(score / max_score * 100)
        }

    def _score_growth(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score growth metrics (0-100)

        Metrics: Revenue growth, Profit growth, CAGR
        """
        score = 0
        max_score = 100
        breakdown = {}

        criteria = self.scoring_criteria.get('growth', {})

        # Revenue Growth (35 points) - Prioritize YoY from quarterly data
        revenue_growth = data.get('revenue_growth_yoy') or data.get('revenue_growth')
        revenue_trend = data.get('revenue_trend')  # New: 6-quarter trendline

        if revenue_growth is not None and isinstance(revenue_growth, (int, float)):
            rg_criteria = criteria.get('revenue_growth_yoy', {'excellent': 20.0, 'good': 15.0, 'average': 10.0})
            if revenue_growth >= rg_criteria['excellent']:
                rev_score = 35
            elif revenue_growth >= rg_criteria['good']:
                rev_score = 25
            elif revenue_growth >= rg_criteria['average']:
                rev_score = 15
            elif revenue_growth >= 0:  # Positive growth but below average
                rev_score = 10
            else:
                rev_score = 0  # Negative growth

            # Bonus/penalty based on 6-quarter trendline
            if revenue_trend == 'growing':
                rev_score = min(35, rev_score + 5)  # +5 bonus for growing trend
            elif revenue_trend == 'declining':
                rev_score = max(0, rev_score - 10)  # -10 penalty for declining trend

            score += rev_score
            breakdown['revenue_growth_score'] = rev_score
            breakdown['revenue_trend'] = revenue_trend

        # Earnings Growth (35 points)
        earnings_growth = data.get('earnings_growth')
        if earnings_growth is not None and isinstance(earnings_growth, (int, float)):
            eg_criteria = criteria.get('profit_growth_yoy', {'excellent': 25.0, 'good': 20.0, 'average': 15.0})
            if earnings_growth >= eg_criteria['excellent']:
                earn_score = 35
            elif earnings_growth >= eg_criteria['good']:
                earn_score = 25
            elif earnings_growth >= eg_criteria['average']:
                earn_score = 15
            else:
                earn_score = 0
            score += earn_score
            breakdown['earnings_growth_score'] = earn_score

        # Consistency (30 points) - based on margins
        profit_margin = data.get('profit_margin')
        if profit_margin is not None and isinstance(profit_margin, (int, float)) and profit_margin > 10:
            score += 30
            breakdown['consistency_score'] = 30

        return {
            'score': score,
            'max_score': max_score,
            'percentage': round((score / max_score) * 100, 2),
            'breakdown': breakdown,
            'rating': self._get_rating(score / max_score * 100)
        }

    def _score_valuation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score valuation metrics (0-100)

        Metrics: PE ratio, PB ratio, relative valuation
        """
        score = 0
        max_score = 100
        breakdown = {}

        criteria = self.scoring_criteria.get('valuation', {})

        # PE Ratio (50 points)
        pe_ratio = data.get('pe_ratio')
        if pe_ratio is not None and isinstance(pe_ratio, (int, float)) and pe_ratio > 0:
            pe_criteria = criteria.get('pe_ratio', {'undervalued': 15.0, 'fair': 25.0, 'overvalued': 35.0})
            if pe_ratio <= pe_criteria['undervalued']:
                pe_score = 50  # Undervalued
            elif pe_ratio <= pe_criteria['fair']:
                pe_score = 35  # Fair value
            elif pe_ratio <= pe_criteria['overvalued']:
                pe_score = 20  # Slightly overvalued
            else:
                pe_score = 0   # Overvalued
            score += pe_score
            breakdown['pe_score'] = pe_score

        # PB Ratio (50 points)
        pb_ratio = data.get('pb_ratio')
        if pb_ratio is not None and isinstance(pb_ratio, (int, float)) and pb_ratio > 0:
            pb_criteria = criteria.get('pb_ratio', {'undervalued': 2.0, 'fair': 4.0, 'overvalued': 6.0})
            if pb_ratio <= pb_criteria['undervalued']:
                pb_score = 50
            elif pb_ratio <= pb_criteria['fair']:
                pb_score = 35
            elif pb_ratio <= pb_criteria['overvalued']:
                pb_score = 20
            else:
                pb_score = 0
            score += pb_score
            breakdown['pb_score'] = pb_score

        return {
            'score': score,
            'max_score': max_score,
            'percentage': round((score / max_score) * 100, 2),
            'breakdown': breakdown,
            'rating': self._get_rating(score / max_score * 100)
        }

    def _score_quality(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score quality metrics (0-100)

        Metrics: ROE, ROCE, Operating margins
        """
        score = 0
        max_score = 100
        breakdown = {}

        criteria = self.scoring_criteria.get('quality', {})

        # ROE (35 points)
        roe = data.get('roe')
        if roe is not None and isinstance(roe, (int, float)):
            roe_criteria = criteria.get('roe', {'excellent': 20.0, 'good': 15.0, 'average': 10.0})
            if roe >= roe_criteria['excellent']:
                roe_score = 35
            elif roe >= roe_criteria['good']:
                roe_score = 25
            elif roe >= roe_criteria['average']:
                roe_score = 15
            else:
                roe_score = 0
            score += roe_score
            breakdown['roe_score'] = roe_score

        # ROCE (35 points)
        roce = data.get('roce')
        if roce is not None and isinstance(roce, (int, float)):
            roce_criteria = criteria.get('roce', {'excellent': 18.0, 'good': 15.0, 'average': 12.0})
            if roce >= roce_criteria['excellent']:
                roce_score = 35
            elif roce >= roce_criteria['good']:
                roce_score = 25
            elif roce >= roce_criteria['average']:
                roce_score = 15
            else:
                roce_score = 0
            score += roce_score
            breakdown['roce_score'] = roce_score

        # Operating Margin (30 points)
        op_margin = data.get('operating_margin')
        if op_margin is not None and isinstance(op_margin, (int, float)):
            om_criteria = criteria.get('operating_margin', {'excellent': 20.0, 'good': 15.0, 'average': 10.0})
            if op_margin >= om_criteria['excellent']:
                margin_score = 30
            elif op_margin >= om_criteria['good']:
                margin_score = 22
            elif op_margin >= om_criteria['average']:
                margin_score = 15
            else:
                margin_score = 0
            score += margin_score
            breakdown['margin_score'] = margin_score

        return {
            'score': score,
            'max_score': max_score,
            'percentage': round((score / max_score) * 100, 2),
            'breakdown': breakdown,
            'rating': self._get_rating(score / max_score * 100)
        }

    def _detect_red_flags(self, data: Dict[str, Any]) -> list:
        """Detect critical red flags"""
        red_flags = []

        # High debt
        debt_to_equity = data.get('debt_to_equity')
        if debt_to_equity is not None and debt_to_equity > 3.0:
            red_flags.append("Excessive debt (D/E > 3.0)")

        # Liquidity issues
        current_ratio = data.get('current_ratio')
        if current_ratio is not None and current_ratio < 1.0:
            red_flags.append("Liquidity concern (Current Ratio < 1.0)")

        # Negative ROE
        roe = data.get('roe')
        if roe is not None and roe < 0:
            red_flags.append("Negative ROE")

        # Declining margins
        operating_margin = data.get('operating_margin')
        if operating_margin is not None and operating_margin < 5:
            red_flags.append("Low operating margins (< 5%)")

        return red_flags

    async def _get_llm_analysis(self, ticker: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get LLM-powered qualitative analysis using GPT-4

        Uses GPT-4 for deep reasoning on:
        - Valuation context (is high PE justified?)
        - Red flag detection (accounting irregularities)
        - Qualitative assessment

        Only called for borderline scores (40-60) to save costs
        """
        try:
            from tools.llm.prompts import PromptTemplates

            company_name = data.get('company_name', ticker)

            # Get messages from prompt template
            messages = PromptTemplates.fundamental_analysis(
                ticker=ticker,
                company_name=company_name,
                financial_data=data
            )

            # Call GPT-4 for reasoning
            response = await self.llm.chat(
                messages=messages,
                provider=self.llm_provider,  # "openai"
                model=self.llm_model,  # "gpt-4-turbo"
                temperature=0.2,
                json_mode=True
            )

            # Parse JSON response
            import json
            analysis = json.loads(response.content)

            self.logger.info(f"GPT-4 analysis complete for {ticker}")
            return analysis

        except Exception as e:
            self.logger.error(f"LLM analysis failed: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _get_recommendation(self, score: float, red_flags: list) -> str:
        """Determine recommendation based on score and red flags"""
        if red_flags:
            return "HOLD"  # Red flags prevent BUY

        if score >= 70:
            return "BUY"
        elif score >= 50:
            return "HOLD"
        else:
            return "SELL"

    def _get_rating(self, score: float) -> str:
        """Convert score to rating"""
        if score >= 80:
            return "EXCELLENT"
        elif score >= 60:
            return "GOOD"
        elif score >= 40:
            return "AVERAGE"
        else:
            return "POOR"

    def _format_analysis(self, ticker: str, result: Dict[str, Any], from_cache: bool) -> Dict[str, Any]:
        """Format analysis result"""
        return {
            'agent': self.name,
            'ticker': ticker,
            'score': result['fundamental_score'],
            'recommendation': result['recommendation'],
            'financial_health': result['financial_health'],
            'growth': result['growth'],
            'valuation': result['valuation'],
            'quality': result['quality'],
            'red_flags': result['red_flags'],
            'llm_analysis': result.get('llm_analysis'),
            'cached': from_cache,
            'timestamp': datetime.now().isoformat()
        }

    def _error_response(self, ticker: str, error: str) -> Dict[str, Any]:
        """Return error response"""
        return {
            'agent': self.name,
            'ticker': ticker,
            'score': 0,
            'recommendation': 'ERROR',
            'error': error,
            'timestamp': datetime.now().isoformat()
        }


# Example usage
async def main():
    """Example fundamental analysis"""

    config = {
        'weights': {
            'financial_health': 0.30,
            'growth': 0.30,
            'valuation': 0.20,
            'quality': 0.20
        },
        'use_llm': True,
        'llm_provider': 'openai',
        'llm_model': 'gpt-4-turbo'
    }

    analyst = FundamentalAnalyst(config)

    result = await analyst.analyze('RELIANCE.NS', {})

    print("\n" + "="*80)
    print("FUNDAMENTAL ANALYSIS")
    print("="*80)
    print(f"Ticker: {result['ticker']}")
    print(f"Overall Score: {result['score']}/100")
    print(f"Recommendation: {result['recommendation']}")
    print(f"\nComponent Scores:")
    print(f"  Financial Health: {result['financial_health']['percentage']}% ({result['financial_health']['rating']})")
    print(f"  Growth: {result['growth']['percentage']}% ({result['growth']['rating']})")
    print(f"  Valuation: {result['valuation']['percentage']}% ({result['valuation']['rating']})")
    print(f"  Quality: {result['quality']['percentage']}% ({result['quality']['rating']})")

    if result['red_flags']:
        print(f"\n⚠️  Red Flags:")
        for flag in result['red_flags']:
            print(f"  - {flag}")


if __name__ == '__main__':
    asyncio.run(main())
