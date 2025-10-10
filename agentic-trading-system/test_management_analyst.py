#!/usr/bin/env python3
"""
Test Management Analyst Agent

Usage: python test_management_analyst.py
"""

import asyncio
import sys
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from agents.management_analyst import ManagementAnalyst

async def test_management_analyst():
    """Test Management Analyst with real stocks"""

    print("="*80)
    print("  TESTING MANAGEMENT ANALYST AGENT")
    print("="*80)

    # Configure agent
    config = {
        'quarters_to_analyze': 4,
        'min_confidence': 60.0
    }

    analyst = ManagementAnalyst(config)

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

            if 'error' in result and result.get('score') == 50:
                print(f"⚠️  Limited data: {result.get('error', 'Unknown')}")
                print(f"   Continuing with available data...")

            # Display results
            print(f"\n📊 Management Score: {result['score']}/100")
            print(f"🏷️  Management Tone: {result.get('management_tone', 'Unknown')}")
            print(f"📅 Quarters Analyzed: {result.get('quarters_analyzed', 0)}")
            print(f"📝 Summary: {result.get('summary', 'N/A')}")

            # Category scores
            print(f"\n📈 Category Breakdown:")

            if result.get('guidance'):
                guidance = result['guidance']
                print(f"  Guidance Quality:    {guidance['score']}/100")
                print(f"    Clarity: {guidance.get('clarity', 'unknown')}")
                if guidance.get('signals'):
                    for signal in guidance['signals'][:2]:
                        print(f"      • {signal}")

            if result.get('strategy'):
                strategy = result['strategy']
                print(f"\n  Strategic Vision:    {strategy['score']}/100")
                print(f"    Vision Clarity: {strategy.get('vision_clarity', 'unknown')}")
                if strategy.get('signals'):
                    for signal in strategy['signals'][:2]:
                        print(f"      • {signal}")

            if result.get('communication'):
                comm = result['communication']
                print(f"\n  Communication:       {comm['score']}/100")
                print(f"    Tone: {comm.get('tone', 'unknown')}")
                print(f"    Transparency: {comm.get('transparency', 'unknown')}")

            if result.get('risk_management'):
                risk = result['risk_management']
                print(f"\n  Risk Management:     {risk['score']}/100")
                print(f"    Disclosure: {risk.get('disclosure', 'unknown')}")
                print(f"    Risks Disclosed: {risk.get('risks_disclosed', 0)}")

            if result.get('capital_allocation'):
                capital = result['capital_allocation']
                print(f"\n  Capital Allocation:  {capital['score']}/100")
                print(f"    Focus: {capital.get('focus', 'unclear')}")

            # Key insights
            if result.get('key_initiatives'):
                print(f"\n🎯 Key Strategic Initiatives:")
                for i, initiative in enumerate(result['key_initiatives'][:5], 1):
                    print(f"  {i}. {initiative}")
            else:
                print(f"\n🎯 Strategic Initiatives: Not extracted")

            if result.get('risks_disclosed'):
                print(f"\n⚠️  Risks Disclosed:")
                for i, risk in enumerate(result['risks_disclosed'][:3], 1):
                    risk_text = risk[:100] + "..." if len(risk) > 100 else risk
                    print(f"  {i}. {risk_text}")

            # Conference calls analyzed
            if result.get('conference_calls'):
                print(f"\n📞 Conference Calls Analyzed:")
                for call in result['conference_calls'][:3]:
                    print(f"  • {call.get('quarter', 'Unknown')} ({call.get('date', 'Unknown')})")
                    print(f"    Tone: {call.get('management_tone', 'Unknown')}")

            # Overall assessment
            print(f"\n{'='*80}")
            score = result['score']
            if score >= 75:
                print(f"  🟢 EXCELLENT - Strong management team")
            elif score >= 60:
                print(f"  🟢 GOOD - Competent management")
            elif score >= 40:
                print(f"  🟡 AVERAGE - Adequate management")
            else:
                print(f"  🔴 BELOW AVERAGE - Management concerns")
            print(f"{'='*80}")

        except Exception as e:
            print(f"❌ Exception: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'='*80}")
    print("  MANAGEMENT ANALYST TEST COMPLETE")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    asyncio.run(test_management_analyst())
