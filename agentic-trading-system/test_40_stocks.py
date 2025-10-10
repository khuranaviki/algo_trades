#!/usr/bin/env python3
"""
Test System with 40 Stocks
Analyzes top 40 stocks to identify BUY recommendations

Usage: python test_40_stocks.py
"""

import asyncio
import sys
import logging
from datetime import datetime
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from agents.orchestrator import Orchestrator

# Top 40 Indian stocks by market cap
STOCKS_40 = [
    ('RELIANCE.NS', 'Reliance Industries'),
    ('TCS.NS', 'Tata Consultancy Services'),
    ('HDFCBANK.NS', 'HDFC Bank'),
    ('INFY.NS', 'Infosys'),
    ('HINDUNILVR.NS', 'Hindustan Unilever'),
    ('ICICIBANK.NS', 'ICICI Bank'),
    ('BHARTIARTL.NS', 'Bharti Airtel'),
    ('ITC.NS', 'ITC Limited'),
    ('SBIN.NS', 'State Bank of India'),
    ('LT.NS', 'Larsen & Toubro'),
    # ('BAJFINANCE.NS', 'Bajaj Finance'),
    # ('HCLTECH.NS', 'HCL Technologies'),
    # ('ASIANPAINT.NS', 'Asian Paints'),
    # ('AXISBANK.NS', 'Axis Bank'),
    # ('MARUTI.NS', 'Maruti Suzuki'),
    # ('TITAN.NS', 'Titan Company'),
    # ('SUNPHARMA.NS', 'Sun Pharmaceutical'),
    # ('ULTRACEMCO.NS', 'UltraTech Cement'),
    # ('NESTLEIND.NS', 'Nestle India'),
    # ('WIPRO.NS', 'Wipro'),
    # ('KOTAKBANK.NS', 'Kotak Mahindra Bank'),
    # ('ADANIENT.NS', 'Adani Enterprises'),
    # ('POWERGRID.NS', 'Power Grid Corporation'),
    # ('NTPC.NS', 'NTPC'),
    # ('TATAMOTORS.NS', 'Tata Motors'),
    # ('ONGC.NS', 'Oil & Natural Gas Corporation'),
    # ('BAJAJFINSV.NS', 'Bajaj Finserv'),
    # ('TECHM.NS', 'Tech Mahindra'),
    # ('TATASTEEL.NS', 'Tata Steel'),
    # ('M&M.NS', 'Mahindra & Mahindra'),
    # ('ADANIPORTS.NS', 'Adani Ports'),
    # ('COALINDIA.NS', 'Coal India'),
    # ('DIVISLAB.NS', 'Divi\'s Laboratories'),
    # ('DRREDDY.NS', 'Dr. Reddy\'s Laboratories'),
    # ('EICHERMOT.NS', 'Eicher Motors'),
    # ('GRASIM.NS', 'Grasim Industries'),
    # ('HEROMOTOCO.NS', 'Hero MotoCorp'),
    # ('HINDALCO.NS', 'Hindalco Industries'),
    # ('INDUSINDBK.NS', 'IndusInd Bank'),
    # ('JSWSTEEL.NS', 'JSW Steel')
]

# Testing with first 10 stocks for now

async def analyze_40_stocks():
    """Analyze all 40 stocks and identify BUY recommendations"""

    print("="*100)
    print(f"  ANALYZING TOP {len(STOCKS_40)} INDIAN STOCKS")
    print("  Testing Full Agentic Trading System")
    print("="*100)

    # Configure orchestrator
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
        'fundamental_config': {
            'use_perplexity': True,
            'use_llm': False  # Disable LLM for faster testing
        },
        'technical_config': {
            'lookback_days': 200,
            'detect_patterns': True,
            'min_pattern_confidence': 70.0
        },
        'backtest_config': {
            'historical_years': 5,
            'min_win_rate': 70.0,
            'min_trades': 10,
            'use_market_regime_filter': True
        },
        'sentiment_config': {
            'news_lookback_days': 30,
            'social_lookback_days': 7
        },
        'management_config': {
            'quarters_to_analyze': 4,
            'min_confidence': 60.0
        }
    }

    orchestrator = Orchestrator(config)

    # Results storage
    all_results = []
    buy_recommendations = []
    strong_buy_recommendations = []
    hold_recommendations = []
    sell_recommendations = []
    errors = []

    start_time = datetime.now()

    # Analyze each stock
    for idx, (ticker, company_name) in enumerate(STOCKS_40, 1):
        print(f"\n{'='*100}")
        print(f"  [{idx}/{len(STOCKS_40)}] Analyzing: {company_name} ({ticker})")
        print(f"{'='*100}")

        stock_start = datetime.now()

        try:
            result = await orchestrator.analyze(ticker, {
                'company_name': company_name,
                'market_regime': 'neutral'
            })

            stock_time = (datetime.now() - stock_start).total_seconds()

            if 'error' in result and result.get('composite_score', 0) == 0:
                print(f"\n❌ ERROR: {result['error']}")
                errors.append({
                    'ticker': ticker,
                    'company': company_name,
                    'error': result['error']
                })
                continue

            # Store result
            result_summary = {
                'ticker': ticker,
                'company': company_name,
                'decision': result['decision'],
                'score': result['composite_score'],
                'confidence': result['confidence'],
                'execution_time': stock_time,
                'agent_scores': result['agent_scores'],
                'vetoes': result.get('vetoes', []),
                'warnings': result.get('warnings', []),
                'position_size': result.get('position_size', 0),
                'stop_loss': result.get('stop_loss'),
                'target_price': result.get('target_price'),
                'summary': result.get('summary', '')
            }

            all_results.append(result_summary)

            # Categorize by decision
            if result['decision'] == 'STRONG BUY':
                strong_buy_recommendations.append(result_summary)
                print(f"✅ 🟢🟢 STRONG BUY - Score: {result['composite_score']:.2f}")
            elif result['decision'] == 'BUY':
                buy_recommendations.append(result_summary)
                print(f"✅ 🟢 BUY - Score: {result['composite_score']:.2f}")
            elif result['decision'] == 'HOLD':
                hold_recommendations.append(result_summary)
                print(f"🟡 HOLD - Score: {result['composite_score']:.2f}")
            else:  # SELL
                sell_recommendations.append(result_summary)
                print(f"🔴 SELL - Score: {result['composite_score']:.2f}")

            # Show key metrics
            print(f"   Confidence: {result['confidence']:.1f}%")
            print(f"   Time: {stock_time:.2f}s")

            if result.get('vetoes'):
                print(f"   ⚠️  Vetoes: {len(result['vetoes'])}")

        except Exception as e:
            print(f"\n❌ Exception: {e}")
            errors.append({
                'ticker': ticker,
                'company': company_name,
                'error': str(e)
            })
            import traceback
            traceback.print_exc()

    total_time = (datetime.now() - start_time).total_seconds()

    # Print comprehensive summary
    print(f"\n\n{'='*100}")
    print(f"  ANALYSIS COMPLETE - TOP 40 STOCKS")
    print(f"{'='*100}\n")

    print(f"⏱️  Total Time: {total_time:.2f}s ({total_time/60:.2f} minutes)")
    print(f"📊 Stocks Analyzed: {len(all_results)}/{len(STOCKS_40)}")
    print(f"❌ Errors: {len(errors)}")

    # Decision breakdown
    print(f"\n📈 DECISION BREAKDOWN:")
    print(f"   🟢🟢 STRONG BUY: {len(strong_buy_recommendations)}")
    print(f"   🟢 BUY:        {len(buy_recommendations)}")
    print(f"   🟡 HOLD:       {len(hold_recommendations)}")
    print(f"   🔴 SELL:       {len(sell_recommendations)}")

    # STRONG BUY recommendations
    if strong_buy_recommendations:
        print(f"\n{'='*100}")
        print(f"  🟢🟢 STRONG BUY RECOMMENDATIONS ({len(strong_buy_recommendations)})")
        print(f"{'='*100}\n")

        for rec in sorted(strong_buy_recommendations, key=lambda x: x['score'], reverse=True):
            print(f"\n{rec['company']} ({rec['ticker']})")
            print(f"   Score: {rec['score']:.2f}/100 | Confidence: {rec['confidence']:.1f}%")
            print(f"   Position Size: {rec['position_size']*100:.2f}%")
            if rec.get('stop_loss'):
                print(f"   Stop Loss: ₹{rec['stop_loss']:.2f} | Target: ₹{rec['target_price']:.2f}")
            print(f"   Agent Scores: F:{rec['agent_scores']['fundamental']:.0f} T:{rec['agent_scores']['technical']:.0f} S:{rec['agent_scores']['sentiment']:.0f} M:{rec['agent_scores']['management']:.0f}")
            print(f"   Summary: {rec['summary'][:150]}...")

    # BUY recommendations
    if buy_recommendations:
        print(f"\n{'='*100}")
        print(f"  🟢 BUY RECOMMENDATIONS ({len(buy_recommendations)})")
        print(f"{'='*100}\n")

        for rec in sorted(buy_recommendations, key=lambda x: x['score'], reverse=True):
            print(f"\n{rec['company']} ({rec['ticker']})")
            print(f"   Score: {rec['score']:.2f}/100 | Confidence: {rec['confidence']:.1f}%")
            print(f"   Position Size: {rec['position_size']*100:.2f}%")
            if rec.get('stop_loss'):
                print(f"   Stop Loss: ₹{rec['stop_loss']:.2f} | Target: ₹{rec['target_price']:.2f}")
            print(f"   Agent Scores: F:{rec['agent_scores']['fundamental']:.0f} T:{rec['agent_scores']['technical']:.0f} S:{rec['agent_scores']['sentiment']:.0f} M:{rec['agent_scores']['management']:.0f}")
            print(f"   Summary: {rec['summary'][:150]}...")

    # Top 10 by score
    if all_results:
        print(f"\n{'='*100}")
        print(f"  TOP 10 STOCKS BY COMPOSITE SCORE")
        print(f"{'='*100}\n")

        top_10 = sorted(all_results, key=lambda x: x['score'], reverse=True)[:10]

        print(f"{'Rank':<6} {'Ticker':<15} {'Company':<30} {'Score':>8} {'Decision':<12} {'Conf%':>7}")
        print(f"{'-'*6} {'-'*15} {'-'*30} {'-'*8} {'-'*12} {'-'*7}")

        for rank, result in enumerate(top_10, 1):
            print(f"{rank:<6} {result['ticker']:<15} {result['company'][:30]:<30} {result['score']:>8.2f} {result['decision']:<12} {result['confidence']:>6.1f}%")

    # Errors summary
    if errors:
        print(f"\n{'='*100}")
        print(f"  ERRORS ({len(errors)})")
        print(f"{'='*100}\n")

        for err in errors:
            print(f"❌ {err['company']} ({err['ticker']})")
            print(f"   {err['error']}\n")

    # Save to JSON
    output_file = f"stock_analysis_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_time_seconds': total_time,
            'stocks_analyzed': len(all_results),
            'errors': len(errors),
            'strong_buy': len(strong_buy_recommendations),
            'buy': len(buy_recommendations),
            'hold': len(hold_recommendations),
            'sell': len(sell_recommendations),
            'results': all_results,
            'errors': errors
        }, f, indent=2)

    print(f"\n💾 Results saved to: {output_file}")

    print(f"\n{'='*100}")
    print(f"  ANALYSIS COMPLETE")
    print(f"{'='*100}\n")


if __name__ == '__main__':
    asyncio.run(analyze_40_stocks())
