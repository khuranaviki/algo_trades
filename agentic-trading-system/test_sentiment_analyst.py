#!/usr/bin/env python3
"""
Test Sentiment Analyst Agent

Usage: python test_sentiment_analyst.py
"""

import asyncio
import sys
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from agents.sentiment_analyst import SentimentAnalyst

async def test_sentiment_analyst():
    """Test Sentiment Analyst with real stocks"""

    print("="*80)
    print("  TESTING SENTIMENT ANALYST AGENT")
    print("="*80)

    # Configure agent
    config = {
        'news_lookback_days': 30,
        'social_lookback_days': 7,
        'min_news_confidence': 60.0
    }

    analyst = SentimentAnalyst(config)

    # Test stocks
    test_stocks = [
        ('RELIANCE.NS', 'Reliance Industries'),
        ('TCS.NS', 'Tata Consultancy Services')
    ]

    for ticker, company_name in test_stocks:
        print(f"\n{'='*80}")
        print(f"  Analyzing: {company_name} ({ticker})")
        print(f"{'='*80}")

        try:
            result = await analyst.analyze(ticker, {'company_name': company_name})

            if 'error' in result and result.get('sentiment_label') == 'Unknown':
                print(f"❌ ERROR: {result['error']}")
                continue

            # Display results
            print(f"\n📊 Sentiment Score: {result['score']}/100")
            print(f"🏷️  Sentiment Label: {result['sentiment_label']}")
            print(f"📈 Confidence: {result['confidence']}%")
            print(f"📝 Summary: {result['summary']}")

            # Category scores
            print(f"\n📰 Category Breakdown:")
            news = result['news_sentiment']
            analyst_sent = result['analyst_sentiment']
            social = result['social_sentiment']

            print(f"  News Sentiment:     {news['score']}/100")
            if news.get('signals'):
                for signal in news['signals'][:3]:
                    print(f"    • {signal}")

            print(f"\n  Analyst Sentiment:  {analyst_sent['score']}/100")
            print(f"    Consensus: {analyst_sent.get('consensus', 'Unknown')}")
            if analyst_sent.get('signals'):
                for signal in analyst_sent['signals'][:3]:
                    print(f"    • {signal}")

            print(f"\n  Social Sentiment:   {social['score']}/100")
            print(f"    Buzz Level: {social.get('buzz_level', 'unknown')}")
            if social.get('signals'):
                for signal in social['signals'][:3]:
                    print(f"    • {signal}")

            # Headlines
            if result.get('headlines'):
                print(f"\n📰 Top Headlines:")
                for i, headline in enumerate(result['headlines'][:5], 1):
                    print(f"  {i}. {headline}")
            else:
                print(f"\n📰 Headlines: None extracted")

            # Themes
            if result.get('themes'):
                print(f"\n🔑 Key Themes: {', '.join(result['themes'])}")

            # Overall assessment
            print(f"\n{'='*80}")
            score = result['score']
            if score >= 75:
                print(f"  🟢 VERY POSITIVE - Strong bullish sentiment")
            elif score >= 60:
                print(f"  🟢 POSITIVE - Bullish sentiment")
            elif score >= 40:
                print(f"  🟡 NEUTRAL - Mixed sentiment")
            elif score >= 25:
                print(f"  🔴 NEGATIVE - Bearish sentiment")
            else:
                print(f"  🔴 VERY NEGATIVE - Strong bearish sentiment")
            print(f"{'='*80}")

        except Exception as e:
            print(f"❌ Exception: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'='*80}")
    print("  SENTIMENT ANALYST TEST COMPLETE")
    print(f"{'='*80}\n")


async def test_sentiment_components():
    """Test individual sentiment components"""

    print("\n" + "="*80)
    print("  TESTING SENTIMENT COMPONENTS")
    print("="*80)

    config = {
        'news_lookback_days': 30,
        'social_lookback_days': 7
    }

    analyst = SentimentAnalyst(config)

    ticker = 'RELIANCE.NS'
    company_name = 'Reliance Industries'

    print(f"\nTesting components for {company_name}")

    # Get Perplexity client
    perplexity = analyst.perplexity

    print(f"\n1. News Search:")
    news = await perplexity.search_stock_news(ticker, days=7)
    if 'error' not in news:
        print(f"   ✅ News data retrieved")
        print(f"   Response length: {len(news.get('raw_response', ''))} chars")
    else:
        print(f"   ❌ News search failed: {news['error']}")

    print(f"\n2. Sentiment Search:")
    sentiment = await perplexity.search_stock_sentiment(ticker, days=7)
    if 'error' not in sentiment:
        print(f"   ✅ Sentiment data retrieved")
        print(f"   Response length: {len(sentiment.get('raw_response', ''))} chars")
    else:
        print(f"   ❌ Sentiment search failed: {sentiment['error']}")

    print(f"\n3. Analyst Opinions Search:")
    analysts = await perplexity.search_analyst_opinions(ticker)
    if 'error' not in analysts:
        print(f"   ✅ Analyst data retrieved")
        print(f"   Response length: {len(analysts.get('raw_response', ''))} chars")
    else:
        print(f"   ❌ Analyst search failed: {analysts['error']}")

    print(f"\n{'='*80}")
    print("  COMPONENT TEST COMPLETE")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    asyncio.run(test_sentiment_analyst())
    asyncio.run(test_sentiment_components())
