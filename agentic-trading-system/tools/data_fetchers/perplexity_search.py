"""
Perplexity Search API Integration for Market Sentiment Analysis

Uses Perplexity AI's search capabilities to gather:
- Recent news and market sentiment
- Social media trends and discussions
- Analyst opinions and market chatter
- Company-specific news and events
"""

import os
from typing import Dict, Any, List, Optional
import aiohttp
from datetime import datetime, timedelta
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class PerplexitySearchClient:
    """
    Client for Perplexity AI Search API

    Uses Perplexity's Sonar models which have access to real-time web data
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Perplexity search client

        Args:
            api_key: Perplexity API key (defaults to env var)
        """
        self.api_key = api_key or os.getenv('PERPLEXITY_API_KEY')
        self.base_url = "https://api.perplexity.ai"
        self.logger = logging.getLogger(__name__)

        # Perplexity models with search capabilities
        # Options: sonar-pro (advanced), sonar (fast), sonar-deep-research, sonar-reasoning
        self.model = "sonar-pro"  # Real-time web access with grounding

    async def search(self, query: str, search_domain_filter: Optional[list] = None, return_citations: bool = True) -> Dict[str, Any]:
        """
        Generic search method for any query

        Args:
            query: Search query
            search_domain_filter: Optional list of domains to filter
            return_citations: Whether to return citations

        Returns:
            Dict with answer and optional citations
        """
        try:
            answer = await self._call_api(query)

            result = {
                'answer': answer,
                'provider': 'perplexity',
                'model': self.model
            }

            if return_citations:
                result['citations'] = []  # Perplexity API doesn't return separate citations

            return result

        except Exception as e:
            self.logger.error(f"Perplexity search failed: {e}")
            return {
                'answer': None,
                'error': str(e)
            }

    async def search_fundamental_metrics(self, ticker: str, company_name: str) -> Dict[str, Any]:
        """
        Search for fundamental metrics using Perplexity grounded search

        Args:
            ticker: Stock ticker
            company_name: Company name

        Returns:
            Dict with fundamental metrics
        """
        prompt = f"""
        Search for the latest fundamental metrics for {company_name} ({ticker}) stock.

        Find and return ONLY the following numerical data in JSON format:

        {{
            "market_cap_cr": <market cap in crores>,
            "book_value": <book value per share>,
            "dividend_yield": <dividend yield percentage>,
            "promoter_holding": <promoter holding percentage>,
            "debt_to_equity": <debt to equity ratio>,
            "current_ratio": <current ratio>,
            "pb_ratio": <price to book ratio>,
            "52_week_high": <52 week high price>,
            "52_week_low": <52 week low price>,
            "face_value": <face value per share>
        }}

        Search specifically for:
        - Latest market capitalization in crores
        - Book value per share
        - Current dividend yield percentage
        - Promoter holding percentage
        - Debt to equity ratio
        - Current ratio
        - Price to book ratio
        - 52 week high and low prices
        - Face value

        Return ONLY the JSON with numerical values. If a metric is not found, use null.
        Source: Use latest data from screener.in, moneycontrol.com, or BSE/NSE official websites.
        """

        try:
            response = await self._call_api(prompt, max_tokens=1000)

            # Parse JSON from response
            import json
            import re

            # Try to extract JSON from response
            json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                data['ticker'] = ticker
                data['company_name'] = company_name
                data['source'] = 'perplexity_grounded_search'
                return data
            else:
                self.logger.warning(f"Could not parse JSON from Perplexity response")
                return {'ticker': ticker, 'error': 'Failed to parse response'}

        except Exception as e:
            self.logger.error(f"Error fetching fundamental metrics for {ticker}: {e}")
            return {
                'ticker': ticker,
                'error': str(e)
            }

    async def search_stock_sentiment(self, ticker: str, days: int = 30) -> Dict[str, Any]:
        """
        Search for stock sentiment and recent discussions

        Args:
            ticker: Stock ticker symbol
            days: Number of days to look back

        Returns:
            Dict with sentiment analysis and key findings
        """
        company_name = self._ticker_to_company(ticker)

        prompt = f"""
        Analyze the market sentiment for {company_name} ({ticker}) over the last {days} days.

        Search for:
        1. Recent news headlines and articles
        2. Social media discussions (Reddit, Twitter/X, StockTwits)
        3. Analyst opinions and rating changes
        4. Institutional investor activity
        5. Overall market sentiment (bullish/bearish)

        Provide:
        - Sentiment Score (-100 to +100): Overall market sentiment
        - News Summary: Key news items from the last {days} days
        - Social Media Buzz: What retail investors are discussing
        - Analyst Activity: Recent upgrades, downgrades, or target price changes
        - Key Themes: Top 3-5 recurring themes in discussions
        - Bullish Factors: What's driving positive sentiment
        - Bearish Factors: What concerns are being raised

        Return as structured JSON.
        """

        try:
            response = await self._call_api(prompt)

            # Parse and structure response
            result = {
                'ticker': ticker,
                'search_date': datetime.now().isoformat(),
                'lookback_days': days,
                'raw_response': response,
                'source': 'perplexity_sonar'
            }

            return result

        except Exception as e:
            self.logger.error(f"Error searching sentiment for {ticker}: {e}")
            return {
                'ticker': ticker,
                'error': str(e),
                'sentiment_score': 50  # Neutral default
            }

    async def search_stock_news(self, ticker: str, days: int = 7) -> Dict[str, Any]:
        """
        Search for recent news about a stock

        Args:
            ticker: Stock ticker symbol
            days: Number of days to look back

        Returns:
            Dict with news summary and headlines
        """
        company_name = self._ticker_to_company(ticker)

        prompt = f"""
        Find recent news articles about {company_name} ({ticker}) from the last {days} days.

        Focus on:
        - Earnings announcements
        - Product launches
        - Regulatory developments
        - Management changes
        - Strategic partnerships or acquisitions
        - Industry trends affecting the company

        Provide:
        - Top 10 Headlines: Most important news items
        - News Sentiment: Positive, Neutral, or Negative for each
        - Impact Assessment: High, Medium, or Low impact on stock
        - Summary: 2-3 sentence overview of recent developments

        Return as structured JSON with headlines list.
        """

        try:
            response = await self._call_api(prompt)

            result = {
                'ticker': ticker,
                'news_date': datetime.now().isoformat(),
                'lookback_days': days,
                'headlines': [],  # Parse from response
                'raw_response': response,
                'source': 'perplexity_sonar'
            }

            return result

        except Exception as e:
            self.logger.error(f"Error fetching news for {ticker}: {e}")
            return {
                'ticker': ticker,
                'error': str(e),
                'headlines': []
            }

    async def search_analyst_opinions(self, ticker: str) -> Dict[str, Any]:
        """
        Search for analyst opinions and ratings

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dict with analyst consensus and recent changes
        """
        company_name = self._ticker_to_company(ticker)

        prompt = f"""
        Find the latest analyst opinions and ratings for {company_name} ({ticker}).

        Search for:
        - Current analyst consensus (Buy/Hold/Sell)
        - Recent rating changes (last 3 months)
        - Price targets from major firms
        - Number of analysts covering the stock
        - Institutional investor sentiment

        Provide:
        - Consensus Rating: Overall buy/hold/sell consensus
        - Average Target Price: If available
        - Recent Upgrades: List any recent upgrades
        - Recent Downgrades: List any recent downgrades
        - Top Bull Case: What bulls are saying
        - Top Bear Case: What bears are saying

        Return as structured JSON.
        """

        try:
            response = await self._call_api(prompt)

            result = {
                'ticker': ticker,
                'analyst_date': datetime.now().isoformat(),
                'consensus': 'Unknown',
                'raw_response': response,
                'source': 'perplexity_sonar'
            }

            return result

        except Exception as e:
            self.logger.error(f"Error fetching analyst opinions for {ticker}: {e}")
            return {
                'ticker': ticker,
                'error': str(e),
                'consensus': 'Unknown'
            }

    async def search_sector_trends(self, sector: str) -> Dict[str, Any]:
        """
        Search for sector-wide trends and sentiment

        Args:
            sector: Sector name (e.g., "Technology", "Pharmaceuticals")

        Returns:
            Dict with sector analysis
        """
        prompt = f"""
        Analyze recent trends and sentiment in the {sector} sector.

        Search for:
        - Overall sector performance trends
        - Key drivers affecting the sector
        - Regulatory or policy changes
        - Emerging themes or disruptions
        - Institutional investor flows

        Provide:
        - Sector Sentiment: Bullish/Neutral/Bearish
        - Key Trends: Top 3-5 trends
        - Growth Drivers: What's driving sector growth
        - Headwinds: What challenges the sector faces
        - Outlook: Short-term (3-6 months) outlook

        Return as structured JSON.
        """

        try:
            response = await self._call_api(prompt)

            result = {
                'sector': sector,
                'search_date': datetime.now().isoformat(),
                'raw_response': response,
                'source': 'perplexity_sonar'
            }

            return result

        except Exception as e:
            self.logger.error(f"Error searching sector trends for {sector}: {e}")
            return {
                'sector': sector,
                'error': str(e)
            }

    async def _call_api(self, prompt: str, max_tokens: int = 4000) -> str:
        """
        Call Perplexity API

        Args:
            prompt: Search query/prompt
            max_tokens: Maximum response tokens

        Returns:
            API response text
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a financial analyst searching for market information. Always return responses in valid JSON format."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": max_tokens,
            "temperature": 0.2,  # Low temperature for factual responses
            "return_citations": True,  # Get source citations
            "search_recency_filter": "month"  # Focus on recent information
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Perplexity API error: {error_text}")

                data = await response.json()

                # Extract response text and citations
                content = data['choices'][0]['message']['content']
                citations = data.get('citations', [])

                self.logger.info(f"Perplexity search completed with {len(citations)} citations")

                return content

    async def search_conference_calls(self, ticker: str, company_name: str, quarters: int = 4) -> Dict[str, Any]:
        """
        Search for recent conference call transcripts and key highlights

        Args:
            ticker: Stock ticker
            company_name: Company name
            quarters: Number of recent quarters to fetch

        Returns:
            Dict with conference call summaries
        """
        prompt = f"""
        Find the latest {quarters} earnings conference call transcripts or summaries for {company_name} ({ticker}).

        For each conference call, extract:
        1. Quarter and Year (e.g., "Q2 FY2024")
        2. Date of the call
        3. Key management commentary on:
           - Financial performance (revenue, profit, margins)
           - Business outlook and guidance
           - Strategic initiatives
           - Challenges and risks mentioned
           - Future growth plans
        4. Analyst questions and management responses (key themes)

        Return as a structured summary with:
        {{
            "conference_calls": [
                {{
                    "quarter": "Q2 FY2024",
                    "date": "2024-10-15",
                    "revenue_guidance": "...",
                    "margin_guidance": "...",
                    "key_initiatives": ["...", "..."],
                    "risks_mentioned": ["...", "..."],
                    "management_tone": "Optimistic/Cautious/Neutral",
                    "key_quotes": ["...", "..."]
                }}
            ]
        }}

        Search: earnings call transcript, investor presentation, earnings release
        """

        try:
            response = await self._call_api(prompt, max_tokens=4000)

            return {
                'ticker': ticker,
                'company_name': company_name,
                'raw_response': response,
                'source': 'perplexity_grounded_search',
                'quarters_requested': quarters
            }

        except Exception as e:
            self.logger.error(f"Error fetching conference calls for {ticker}: {e}")
            return {
                'ticker': ticker,
                'error': str(e)
            }

    def _ticker_to_company(self, ticker: str) -> str:
        """
        Convert ticker to company name by fetching from yfinance

        Args:
            ticker: Stock ticker (e.g., 'RELIANCE.NS')

        Returns:
            Company name or ticker if not found
        """
        try:
            import yfinance as yf

            # Fetch company info from yfinance
            stock = yf.Ticker(ticker)
            info = stock.info

            # Get company name
            company_name = info.get('longName') or info.get('shortName')

            if company_name:
                self.logger.info(f"Fetched company name for {ticker}: {company_name}")
                return company_name
            else:
                # Fallback to cleaned ticker
                clean_ticker = ticker.replace('.NS', '').replace('.BO', '')
                self.logger.warning(f"Could not fetch company name for {ticker}, using: {clean_ticker}")
                return clean_ticker

        except Exception as e:
            # Fallback to cleaned ticker on error
            clean_ticker = ticker.replace('.NS', '').replace('.BO', '')
            self.logger.warning(f"Error fetching company name for {ticker}: {e}, using: {clean_ticker}")
            return clean_ticker


# Example usage
async def main():
    """Example usage of Perplexity search"""
    client = PerplexitySearchClient()

    # Search sentiment
    sentiment = await client.search_stock_sentiment('RELIANCE.NS', days=30)
    print("Sentiment Analysis:")
    print(sentiment)

    # Search news
    news = await client.search_stock_news('RELIANCE.NS', days=7)
    print("\nRecent News:")
    print(news)

    # Search analyst opinions
    analysts = await client.search_analyst_opinions('RELIANCE.NS')
    print("\nAnalyst Opinions:")
    print(analysts)


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
