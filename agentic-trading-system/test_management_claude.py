#!/usr/bin/env python3
"""
Test Management Analyst with Claude-3.5-Sonnet

Tests:
- Perplexity for conference call data fetching
- Claude-3.5-Sonnet for deep transcript analysis
"""

import asyncio
import logging

logging.basicConfig(level=logging.INFO)

from agents.management_analyst import ManagementAnalyst

async def test_management_claude():
    print("="*80)
    print("  TESTING MANAGEMENT ANALYST WITH CLAUDE")
    print("  Perplexity (data) + Claude-3.5 (analysis)")
    print("="*80)

    # Enable Claude LLM
    config = {
        'quarters_to_analyze': 4,
        'min_confidence': 60.0,
        'use_llm': True  # Enable Claude analysis
    }

    analyst = ManagementAnalyst(config)

    ticker = 'HDFCBANK.NS'
    print(f"\nAnalyzing: {ticker}\n")

    result = await analyst.analyze(ticker, {'company_name': 'HDFC Bank'})

    print(f"\n⭐ Management Score: {result['score']}/100")
    print(f"📊 Management Tone: {result.get('management_tone', 'Unknown')}")
    print(f"📅 Quarters Analyzed: {result.get('quarters_analyzed', 0)}")

    if result.get('llm_analysis'):
        llm = result['llm_analysis']
        print(f"\n🤖 Claude-3.5 Analysis:")

        if llm.get('management_score'):
            print(f"   Management Score: {llm.get('management_score', 'N/A')}/100")

        if llm.get('credibility_score'):
            print(f"   Credibility: {llm.get('credibility_score', 'N/A')}/100")

        if llm.get('transparency_score'):
            print(f"   Transparency: {llm.get('transparency_score', 'N/A')}/100")

        if llm.get('recommendation'):
            print(f"   Recommendation: {llm.get('recommendation', 'N/A')}")

        if llm.get('promises_kept'):
            print(f"\n   Promises Kept:")
            for p in llm['promises_kept'][:3]:
                print(f"     ✅ {p}")

        if llm.get('red_flags'):
            print(f"\n   Red Flags:")
            for r in llm['red_flags']:
                print(f"     🚩 {r}")

        # If just summary available
        if 'summary' in llm and not llm.get('management_score'):
            print(f"\n   Summary: {llm['summary'][:500]}...")

    print(f"\n📝 Summary: {result.get('summary', 'N/A')}")

    print("\n" + "="*80)
    print("  TEST COMPLETE")
    print("="*80)

if __name__ == '__main__':
    asyncio.run(test_management_claude())
