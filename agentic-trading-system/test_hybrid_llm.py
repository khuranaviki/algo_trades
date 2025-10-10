#!/usr/bin/env python3
"""
Test Hybrid LLM System
- Perplexity for data fetching
- GPT-4 for fundamental reasoning
- Claude for management analysis (future)
"""

import asyncio
import logging

logging.basicConfig(level=logging.INFO)

from agents.fundamental_analyst import FundamentalAnalyst

async def test_hybrid():
    print("="*80)
    print("  TESTING HYBRID LLM SYSTEM")
    print("  Perplexity (data) + GPT-4 (reasoning)")
    print("="*80)

    # Enable LLM
    config = {
        'use_perplexity': True,
        'use_llm': True,
        'llm_provider': 'openai',
        'llm_model': 'gpt-4-turbo'
    }

    analyst = FundamentalAnalyst(config)

    ticker = 'HDFCBANK.NS'
    print(f"\nAnalyzing: {ticker}\n")

    result = await analyst.analyze(ticker, {'company_name': 'HDFC Bank'})

    print(f"\n⭐ Score: {result['score']}/100")
    print(f"📊 Recommendation: {result['recommendation']}")

    if result.get('llm_analysis'):
        llm = result['llm_analysis']
        print(f"\n🤖 GPT-4 Analysis:")
        print(f"   Fundamental Score: {llm.get('fundamental_score', 'N/A')}")
        print(f"   Recommendation: {llm.get('recommendation', 'N/A')}")
        print(f"   Reasoning: {llm.get('reasoning', 'N/A')}")

        if llm.get('strengths'):
            print(f"\n   Strengths:")
            for s in llm['strengths'][:3]:
                print(f"     • {s}")

        if llm.get('red_flags'):
            print(f"\n   Red Flags:")
            for r in llm['red_flags']:
                print(f"     🚩 {r}")

    print("\n" + "="*80)
    print("  TEST COMPLETE")
    print("="*80)

if __name__ == '__main__':
    asyncio.run(test_hybrid())
