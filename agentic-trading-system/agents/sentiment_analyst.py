"""
Sentiment Analyst Agent

Analyzes market sentiment using Perplexity AI's grounded search for:
- Recent news and headlines
- Social media discussions (Reddit, Twitter/X, StockTwits)
- Analyst opinions and rating changes
- Overall market sentiment

Uses Perplexity Sonar API for real-time sentiment analysis with citations.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging
import json
import re

from agents.base_agent import BaseAgent
from tools.data_fetchers.perplexity_search import PerplexitySearchClient


class SentimentAnalyst(BaseAgent):
    """
    Analyzes market sentiment using Perplexity grounded search

    Core responsibilities:
    1. Fetch and analyze recent news sentiment
    2. Analyze social media buzz and retail sentiment
    3. Gather analyst opinions and ratings
    4. Generate composite sentiment score (0-100)

    Sentiment Score Breakdown:
    - News Sentiment (40%): Recent headlines and articles
    - Analyst Consensus (40%): Professional analyst ratings and targets
    - Social Media Buzz (20%): Retail investor sentiment
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Sentiment Analyst

        Args:
            config: Configuration dict with sentiment settings
        """
        super().__init__("Sentiment Analyst", config)

        # Initialize Perplexity client
        self.perplexity = PerplexitySearchClient()

        # Sentiment settings
        self.news_lookback_days = config.get('news_lookback_days', 30)
        self.social_lookback_days = config.get('social_lookback_days', 7)
        self.min_news_confidence = config.get('min_news_confidence', 60.0)

        # Scoring weights
        self.weights = {
            'news': 0.40,
            'analysts': 0.40,
            'social': 0.20
        }

        # Sentiment keywords
        self.positive_keywords = [
            'upgrade', 'outperform', 'buy', 'bullish', 'growth', 'strong',
            'beat', 'exceed', 'positive', 'rally', 'surge', 'gain'
        ]
        self.negative_keywords = [
            'downgrade', 'underperform', 'sell', 'bearish', 'decline', 'weak',
            'miss', 'concerns', 'negative', 'fall', 'drop', 'loss'
        ]

    async def analyze(self, ticker: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform sentiment analysis on a stock

        Args:
            ticker: Stock ticker
            context: Additional context (company name, etc.)

        Returns:
            Dict with sentiment analysis results
        """
        if not self.validate_input(ticker):
            return self._error_response(ticker, "Invalid ticker")

        self.logger.info(f"Analyzing sentiment for {ticker}")

        try:
            # Get company name from context or fetch it
            company_name = context.get('company_name')
            if not company_name:
                company_name = self.perplexity._ticker_to_company(ticker)

            # Run all sentiment searches in parallel
            news_task = self.perplexity.search_stock_news(ticker, days=self.news_lookback_days)
            sentiment_task = self.perplexity.search_stock_sentiment(ticker, days=self.social_lookback_days)
            analyst_task = self.perplexity.search_analyst_opinions(ticker)

            # Wait for all results
            news_data, sentiment_data, analyst_data = await asyncio.gather(
                news_task,
                sentiment_task,
                analyst_task,
                return_exceptions=True
            )

            # Handle exceptions
            if isinstance(news_data, Exception):
                self.logger.warning(f"News search failed: {news_data}")
                news_data = {'error': str(news_data)}

            if isinstance(sentiment_data, Exception):
                self.logger.warning(f"Sentiment search failed: {sentiment_data}")
                sentiment_data = {'error': str(sentiment_data)}

            if isinstance(analyst_data, Exception):
                self.logger.warning(f"Analyst search failed: {analyst_data}")
                analyst_data = {'error': str(analyst_data)}

            # Parse and score each category
            news_score = self._score_news_sentiment(news_data)
            analyst_score = self._score_analyst_sentiment(analyst_data)
            social_score = self._score_social_sentiment(sentiment_data)

            # Calculate composite sentiment score
            composite_score = (
                news_score['score'] * self.weights['news'] +
                analyst_score['score'] * self.weights['analysts'] +
                social_score['score'] * self.weights['social']
            )

            # Determine overall sentiment
            sentiment_label = self._get_sentiment_label(composite_score)

            # Extract key themes
            themes = self._extract_themes(news_data, sentiment_data, analyst_data)

            # Build result
            result = {
                'score': round(composite_score, 2),
                'ticker': ticker,
                'company_name': company_name,
                'timestamp': datetime.now().isoformat(),

                # Category scores
                'news_sentiment': news_score,
                'analyst_sentiment': analyst_score,
                'social_sentiment': social_score,

                # Overall assessment
                'sentiment_label': sentiment_label,
                'confidence': self._calculate_confidence(news_score, analyst_score, social_score),

                # Key insights
                'themes': themes,
                'headlines': self._extract_headlines(news_data),
                'analyst_consensus': analyst_score.get('consensus', 'Unknown'),

                # Raw data for audit
                'raw_data': {
                    'news': news_data,
                    'sentiment': sentiment_data,
                    'analysts': analyst_data
                },

                # Summary
                'summary': self._generate_summary(composite_score, themes, analyst_score)
            }

            self.log_analysis(ticker, result)
            return result

        except Exception as e:
            self.logger.error(f"Error analyzing sentiment for {ticker}: {e}")
            import traceback
            traceback.print_exc()
            return self._error_response(ticker, str(e))

    def _score_news_sentiment(self, news_data: Dict[str, Any]) -> Dict[str, Any]:
        """Score news sentiment (0-100)"""
        score = 50  # Neutral default
        signals = []
        headlines_analyzed = 0

        if 'error' in news_data:
            return {
                'score': 50,
                'signals': ['News data unavailable'],
                'positive_count': 0,
                'negative_count': 0,
                'neutral_count': 0
            }

        try:
            raw_response = news_data.get('raw_response', '')

            # Try to parse structured response
            headlines = self._parse_headlines_from_response(raw_response)

            if not headlines:
                # Fallback: analyze raw text for sentiment keywords
                return self._analyze_text_sentiment(raw_response, 'news')

            # Analyze each headline
            positive_count = 0
            negative_count = 0
            neutral_count = 0

            for headline in headlines:
                headline_text = headline.get('title', '') + ' ' + headline.get('summary', '')
                headline_lower = headline_text.lower()

                # Count sentiment words
                pos_words = sum(1 for word in self.positive_keywords if word in headline_lower)
                neg_words = sum(1 for word in self.negative_keywords if word in headline_lower)

                if pos_words > neg_words:
                    positive_count += 1
                elif neg_words > pos_words:
                    negative_count += 1
                else:
                    neutral_count += 1

                headlines_analyzed += 1

            # Calculate score based on sentiment distribution
            if headlines_analyzed > 0:
                positive_ratio = positive_count / headlines_analyzed
                negative_ratio = negative_count / headlines_analyzed

                # Score: 0-100 based on positive vs negative ratio
                score = 50 + (positive_ratio * 40) - (negative_ratio * 40)

                if positive_count > negative_count * 2:
                    signals.append(f"Strongly positive news ({positive_count} positive vs {negative_count} negative)")
                elif positive_count > negative_count:
                    signals.append(f"Positive news bias ({positive_count} positive vs {negative_count} negative)")
                elif negative_count > positive_count * 2:
                    signals.append(f"Strongly negative news ({negative_count} negative vs {positive_count} positive)")
                elif negative_count > positive_count:
                    signals.append(f"Negative news bias ({negative_count} negative vs {positive_count} positive)")
                else:
                    signals.append(f"Neutral news coverage ({positive_count} positive, {negative_count} negative)")

            return {
                'score': max(0, min(100, score)),
                'signals': signals,
                'positive_count': positive_count,
                'negative_count': negative_count,
                'neutral_count': neutral_count,
                'headlines_analyzed': headlines_analyzed
            }

        except Exception as e:
            self.logger.warning(f"Error scoring news sentiment: {e}")
            return {
                'score': 50,
                'signals': ['Error analyzing news'],
                'positive_count': 0,
                'negative_count': 0,
                'neutral_count': 0
            }

    def _score_analyst_sentiment(self, analyst_data: Dict[str, Any]) -> Dict[str, Any]:
        """Score analyst sentiment (0-100)"""
        score = 50  # Neutral default
        signals = []
        consensus = 'Unknown'

        if 'error' in analyst_data:
            return {
                'score': 50,
                'signals': ['Analyst data unavailable'],
                'consensus': 'Unknown',
                'upgrades': 0,
                'downgrades': 0
            }

        try:
            raw_response = analyst_data.get('raw_response', '')

            # Look for consensus in response
            consensus_match = re.search(r'consensus[:\s]*(buy|sell|hold)', raw_response.lower())
            if consensus_match:
                consensus = consensus_match.group(1).upper()

                if consensus == 'BUY':
                    score = 75
                    signals.append("Analyst consensus: BUY")
                elif consensus == 'SELL':
                    score = 25
                    signals.append("Analyst consensus: SELL")
                else:
                    score = 50
                    signals.append("Analyst consensus: HOLD")

            # Count upgrades vs downgrades
            upgrades = len(re.findall(r'upgrade', raw_response.lower()))
            downgrades = len(re.findall(r'downgrade', raw_response.lower()))

            if upgrades > downgrades:
                score += 10
                signals.append(f"Recent upgrades ({upgrades} vs {downgrades} downgrades)")
            elif downgrades > upgrades:
                score -= 10
                signals.append(f"Recent downgrades ({downgrades} vs {upgrades} upgrades)")

            # Look for target price mentions
            if 'target' in raw_response.lower() and 'raised' in raw_response.lower():
                score += 5
                signals.append("Target price raised")
            elif 'target' in raw_response.lower() and 'lowered' in raw_response.lower():
                score -= 5
                signals.append("Target price lowered")

            return {
                'score': max(0, min(100, score)),
                'signals': signals,
                'consensus': consensus,
                'upgrades': upgrades,
                'downgrades': downgrades
            }

        except Exception as e:
            self.logger.warning(f"Error scoring analyst sentiment: {e}")
            return {
                'score': 50,
                'signals': ['Error analyzing analyst data'],
                'consensus': 'Unknown',
                'upgrades': 0,
                'downgrades': 0
            }

    def _score_social_sentiment(self, sentiment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Score social media sentiment (0-100)"""
        score = 50  # Neutral default
        signals = []

        if 'error' in sentiment_data:
            return {
                'score': 50,
                'signals': ['Social sentiment data unavailable'],
                'buzz_level': 'low'
            }

        try:
            raw_response = sentiment_data.get('raw_response', '')

            # Try to extract sentiment score from response
            score_match = re.search(r'sentiment[:\s]*(\d+)', raw_response.lower())
            if score_match:
                extracted_score = int(score_match.group(1))
                if 0 <= extracted_score <= 100:
                    score = extracted_score
                    signals.append(f"Social sentiment score: {extracted_score}/100")

            # Analyze text for sentiment keywords
            text_sentiment = self._analyze_text_sentiment(raw_response, 'social')
            if not score_match:
                score = text_sentiment['score']
                signals.extend(text_sentiment['signals'])

            # Detect buzz level
            buzz_keywords = ['trending', 'viral', 'popular', 'discussion', 'buzz']
            buzz_level = 'low'
            if any(word in raw_response.lower() for word in buzz_keywords):
                buzz_level = 'high'
                signals.append("High social media buzz")

            return {
                'score': score,
                'signals': signals,
                'buzz_level': buzz_level
            }

        except Exception as e:
            self.logger.warning(f"Error scoring social sentiment: {e}")
            return {
                'score': 50,
                'signals': ['Error analyzing social data'],
                'buzz_level': 'low'
            }

    def _analyze_text_sentiment(self, text: str, source: str) -> Dict[str, Any]:
        """Analyze text for sentiment using keyword matching"""
        text_lower = text.lower()

        # Count positive and negative keywords
        pos_count = sum(1 for word in self.positive_keywords if word in text_lower)
        neg_count = sum(1 for word in self.negative_keywords if word in text_lower)

        # Calculate score
        total_words = pos_count + neg_count
        if total_words == 0:
            score = 50
            signals = [f"Neutral {source} sentiment"]
        else:
            pos_ratio = pos_count / total_words
            score = 50 + (pos_ratio * 50) - ((1 - pos_ratio) * 50)

            if pos_count > neg_count * 2:
                signals = [f"Strongly positive {source} sentiment"]
            elif pos_count > neg_count:
                signals = [f"Positive {source} sentiment"]
            elif neg_count > pos_count * 2:
                signals = [f"Strongly negative {source} sentiment"]
            elif neg_count > pos_count:
                signals = [f"Negative {source} sentiment"]
            else:
                signals = [f"Mixed {source} sentiment"]

        return {
            'score': max(0, min(100, score)),
            'signals': signals,
            'positive_words': pos_count,
            'negative_words': neg_count
        }

    def _parse_headlines_from_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse headlines from Perplexity response"""
        headlines = []

        try:
            # Try to find JSON structure
            json_match = re.search(r'\{[^{}]*"headlines"[^{}]*\[.*?\]\s*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                headlines = data.get('headlines', [])
                return headlines

            # Fallback: Look for headline patterns
            # Match lines that look like headlines (Title - Source format)
            headline_pattern = r'(?:^|\n)\s*[-•*]\s*([^\n]+)'
            matches = re.findall(headline_pattern, response)

            for match in matches[:10]:  # Limit to 10 headlines
                headlines.append({
                    'title': match.strip(),
                    'summary': ''
                })

        except Exception as e:
            self.logger.debug(f"Error parsing headlines: {e}")

        return headlines

    def _extract_themes(self, news_data: Dict[str, Any], sentiment_data: Dict[str, Any],
                       analyst_data: Dict[str, Any]) -> List[str]:
        """Extract key themes from all sentiment sources"""
        themes = []

        # Combine all text
        all_text = ''
        if news_data.get('raw_response'):
            all_text += news_data['raw_response'] + ' '
        if sentiment_data.get('raw_response'):
            all_text += sentiment_data['raw_response'] + ' '
        if analyst_data.get('raw_response'):
            all_text += analyst_data['raw_response'] + ' '

        # Common market themes
        theme_keywords = {
            'earnings': ['earnings', 'profit', 'revenue', 'results'],
            'growth': ['growth', 'expansion', 'increase', 'rising'],
            'acquisition': ['acquisition', 'merger', 'buyout', 'takeover'],
            'regulatory': ['regulation', 'compliance', 'legal', 'regulatory'],
            'innovation': ['innovation', 'technology', 'new product', 'launch'],
            'competition': ['competition', 'competitor', 'market share'],
            'leadership': ['ceo', 'management', 'leadership', 'executive'],
            'financial_health': ['debt', 'cash', 'balance sheet', 'liquidity']
        }

        all_text_lower = all_text.lower()

        for theme, keywords in theme_keywords.items():
            if any(keyword in all_text_lower for keyword in keywords):
                themes.append(theme.replace('_', ' ').title())

        return themes[:5]  # Return top 5 themes

    def _extract_headlines(self, news_data: Dict[str, Any]) -> List[str]:
        """Extract top headlines from news data"""
        if 'error' in news_data or not news_data.get('raw_response'):
            return []

        headlines = self._parse_headlines_from_response(news_data['raw_response'])
        return [h.get('title', '') for h in headlines[:5]]  # Top 5 headlines

    def _calculate_confidence(self, news_score: Dict[str, Any], analyst_score: Dict[str, Any],
                              social_score: Dict[str, Any]) -> float:
        """Calculate confidence level in sentiment analysis"""
        confidence = 50.0

        # Higher confidence if all scores agree
        scores = [news_score['score'], analyst_score['score'], social_score['score']]
        avg_score = sum(scores) / len(scores)
        std_dev = (sum((s - avg_score) ** 2 for s in scores) / len(scores)) ** 0.5

        # Low standard deviation = high confidence
        if std_dev < 10:
            confidence = 90.0
        elif std_dev < 20:
            confidence = 75.0
        elif std_dev < 30:
            confidence = 60.0

        # Boost confidence if we have actual data (not errors)
        data_sources = 0
        if 'error' not in news_score:
            data_sources += 1
        if 'error' not in analyst_score:
            data_sources += 1
        if 'error' not in social_score:
            data_sources += 1

        confidence = confidence * (data_sources / 3)

        return round(confidence, 1)

    def _get_sentiment_label(self, score: float) -> str:
        """Convert sentiment score to label"""
        if score >= 75:
            return "Very Positive"
        elif score >= 60:
            return "Positive"
        elif score >= 40:
            return "Neutral"
        elif score >= 25:
            return "Negative"
        else:
            return "Very Negative"

    def _generate_summary(self, score: float, themes: List[str], analyst_score: Dict[str, Any]) -> str:
        """Generate human-readable summary"""
        summary_parts = []

        # Sentiment label
        sentiment_label = self._get_sentiment_label(score)
        summary_parts.append(f"{sentiment_label} sentiment ({score:.1f}/100)")

        # Analyst consensus
        if analyst_score.get('consensus') != 'Unknown':
            summary_parts.append(f"Analyst consensus: {analyst_score['consensus']}")

        # Key themes
        if themes:
            summary_parts.append(f"Key themes: {', '.join(themes[:3])}")

        return " | ".join(summary_parts)

    def _error_response(self, ticker: str, error: str) -> Dict[str, Any]:
        """Return error response"""
        return {
            'score': 50,
            'ticker': ticker,
            'error': error,
            'sentiment_label': 'Unknown',
            'timestamp': datetime.now().isoformat()
        }


# Example usage
async def main():
    """Example usage of Sentiment Analyst"""

    config = {
        'news_lookback_days': 30,
        'social_lookback_days': 7,
        'min_news_confidence': 60.0
    }

    analyst = SentimentAnalyst(config)

    # Analyze a stock
    result = await analyst.analyze('RELIANCE.NS', {'company_name': 'Reliance Industries'})

    print(f"Sentiment Score: {result['score']}")
    print(f"Sentiment Label: {result['sentiment_label']}")
    print(f"Confidence: {result['confidence']}%")
    print(f"Summary: {result['summary']}")

    print(f"\nCategory Scores:")
    print(f"  News:     {result['news_sentiment']['score']}")
    print(f"  Analysts: {result['analyst_sentiment']['score']}")
    print(f"  Social:   {result['social_sentiment']['score']}")

    if result.get('headlines'):
        print(f"\nTop Headlines:")
        for headline in result['headlines']:
            print(f"  • {headline}")


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
