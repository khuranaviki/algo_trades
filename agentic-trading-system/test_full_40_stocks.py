#!/usr/bin/env python3
"""
Full System Test with 40 Stocks

Tests complete hybrid LLM trading system with:
- Conflict detection
- Technical signal validation
- Pattern-based targets
- LLM conflict synthesis

Outputs:
- Summary report of all stocks
- BUY/SELL/HOLD breakdown
- Cost analysis
- Error tracking
"""

import asyncio
import sys
import logging
from datetime import datetime
import json
from typing import List, Dict, Any
import traceback

# Setup logging
logging.basicConfig(
    level=logging.WARNING,  # Reduce noise, only show warnings/errors
    format='%(asctime)s - %(levelname)s - %(message)s'
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
    ('BAJFINANCE.NS', 'Bajaj Finance'),
    ('HCLTECH.NS', 'HCL Technologies'),
    ('ASIANPAINT.NS', 'Asian Paints'),
    ('AXISBANK.NS', 'Axis Bank'),
    ('MARUTI.NS', 'Maruti Suzuki'),
    ('TITAN.NS', 'Titan Company'),
    ('SUNPHARMA.NS', 'Sun Pharmaceutical'),
    ('ULTRACEMCO.NS', 'UltraTech Cement'),
    ('NESTLEIND.NS', 'Nestle India'),
    ('WIPRO.NS', 'Wipro'),
    ('KOTAKBANK.NS', 'Kotak Mahindra Bank'),
    ('ADANIENT.NS', 'Adani Enterprises'),
    ('POWERGRID.NS', 'Power Grid Corporation'),
    ('NTPC.NS', 'NTPC'),
    ('TATAMOTORS.NS', 'Tata Motors'),
    ('ONGC.NS', 'Oil & Natural Gas Corporation'),
    ('TATASTEEL.NS', 'Tata Steel'),
    ('HINDALCO.NS', 'Hindalco Industries'),
    ('JSWSTEEL.NS', 'JSW Steel'),
    ('COALINDIA.NS', 'Coal India'),
    ('BRITANNIA.NS', 'Britannia Industries'),
    ('DIVISLAB.NS', 'Divi\'s Laboratories'),
    ('APOLLOHOSP.NS', 'Apollo Hospitals'),
    ('TECHM.NS', 'Tech Mahindra'),
    ('INDUSINDBK.NS', 'IndusInd Bank'),
    ('GRASIM.NS', 'Grasim Industries'),
    ('EICHERMOT.NS', 'Eicher Motors'),
    ('HEROMOTOCO.NS', 'Hero MotoCorp'),
    ('DRREDDY.NS', 'Dr. Reddy\'s Laboratories'),
    ('M&M.NS', 'Mahindra & Mahindra'),
]


class StockTestResults:
    """Track results across all stocks"""

    def __init__(self):
        self.results = []
        self.errors = []
        self.start_time = datetime.now()

    def add_result(self, ticker: str, company: str, result: Dict[str, Any]):
        """Add successful result"""
        self.results.append({
            'ticker': ticker,
            'company': company,
            'decision': result.get('decision', 'ERROR'),
            'confidence': result.get('confidence', 0),
            'composite_score': result.get('composite_score', 0),
            'agent_scores': result.get('agent_scores', {}),
            'conflict_level': result.get('conflict_analysis', {}).get('conflict_level', 'none'),
            'has_technical_signal': result.get('technical_signal', {}).get('has_signal', False),
            'used_llm_synthesis': result.get('used_llm_synthesis', False),
            'vetoes': result.get('vetoes', []),
            'execution_time': result.get('execution_time_seconds', 0)
        })

    def add_error(self, ticker: str, company: str, error: str):
        """Add error"""
        self.errors.append({
            'ticker': ticker,
            'company': company,
            'error': str(error),
            'traceback': traceback.format_exc()
        })

    def get_summary(self) -> Dict[str, Any]:
        """Generate summary statistics"""
        total = len(self.results)
        if total == 0:
            return {'error': 'No results to analyze'}

        decisions = {}
        for r in self.results:
            decision = r['decision']
            decisions[decision] = decisions.get(decision, 0) + 1

        conflict_levels = {}
        for r in self.results:
            level = r['conflict_level']
            conflict_levels[level] = conflict_levels.get(level, 0) + 1

        llm_synthesis_count = sum(1 for r in self.results if r['used_llm_synthesis'])
        technical_signal_count = sum(1 for r in self.results if r['has_technical_signal'])

        avg_execution_time = sum(r['execution_time'] for r in self.results) / total
        total_time = (datetime.now() - self.start_time).total_seconds()

        return {
            'total_stocks': total,
            'decisions': decisions,
            'buy_rate': decisions.get('BUY', 0) / total * 100 if total > 0 else 0,
            'strong_buy_rate': decisions.get('STRONG BUY', 0) / total * 100 if total > 0 else 0,
            'conflict_levels': conflict_levels,
            'llm_synthesis_used': llm_synthesis_count,
            'llm_synthesis_rate': llm_synthesis_count / total * 100 if total > 0 else 0,
            'technical_signals_found': technical_signal_count,
            'technical_signal_rate': technical_signal_count / total * 100 if total > 0 else 0,
            'avg_execution_time_per_stock': round(avg_execution_time, 2),
            'total_execution_time': round(total_time, 2),
            'errors': len(self.errors)
        }


async def analyze_stock(
    orchestrator: Orchestrator,
    ticker: str,
    company_name: str,
    results_tracker: StockTestResults,
    index: int,
    total: int
) -> Dict[str, Any]:
    """Analyze single stock with error handling"""

    print(f"\n[{index}/{total}] 🔍 Analyzing {ticker} ({company_name})...", flush=True)

    try:
        result = await orchestrator.analyze(ticker, {
            'company_name': company_name,
            'market_regime': 'neutral'
        })

        # Track result
        results_tracker.add_result(ticker, company_name, result)

        # Print concise summary
        decision = result.get('decision', 'UNKNOWN')
        score = result.get('composite_score', 0)
        conflict = result.get('conflict_analysis', {}).get('conflict_level', 'none')
        has_signal = result.get('technical_signal', {}).get('has_signal', False)
        used_llm = result.get('used_llm_synthesis', False)

        print(f"  ✓ {decision} (Score: {score:.1f}/100)", flush=True)
        print(f"    Conflict: {conflict} | Tech Signal: {'✅' if has_signal else '❌'} | LLM: {'✅' if used_llm else '❌'}", flush=True)

        if result.get('vetoes'):
            print(f"    ⚠️  Vetoes: {len(result['vetoes'])}", flush=True)

        return result

    except Exception as e:
        print(f"  ❌ ERROR: {str(e)}", flush=True)
        results_tracker.add_error(ticker, company_name, str(e))
        return {'error': str(e)}


async def test_all_stocks():
    """Test all 40 stocks"""

    print("="*80)
    print("  FULL SYSTEM TEST: 40 STOCKS")
    print("  Hybrid LLM Trading System with Conflict Resolution")
    print("="*80)

    # Initialize orchestrator with hybrid LLM config
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

        # Agent configs with LLMs enabled
        'fundamental_config': {
            'use_perplexity': True,
            'use_llm': True,
            'llm_provider': 'openai',
            'llm_model': 'gpt-4-turbo'
        },
        'technical_config': {
            'detect_patterns': True,
            'lookback_days': 1825  # 5 years for comprehensive technical analysis
        },
        'backtest_config': {
            'historical_years': 5,
            'min_win_rate': 70.0
        },
        'sentiment_config': {
            'news_lookback_days': 30,
            'use_perplexity': True
        },
        'management_config': {
            'quarters_to_analyze': 4,
            'use_llm': True
        }
    }

    orchestrator = Orchestrator(config)
    results_tracker = StockTestResults()

    print(f"\nTesting {len(STOCKS_40)} stocks...")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Analyze all stocks sequentially
    for i, (ticker, company) in enumerate(STOCKS_40, 1):
        await analyze_stock(orchestrator, ticker, company, results_tracker, i, len(STOCKS_40))

        # Small delay to avoid rate limits
        if i < len(STOCKS_40):
            await asyncio.sleep(1)

    # Generate summary
    print("\n" + "="*80)
    print("  TEST COMPLETE - GENERATING SUMMARY")
    print("="*80)

    summary = results_tracker.get_summary()

    # Print summary
    print(f"\n📊 OVERALL STATISTICS:")
    print(f"  Total Stocks Analyzed: {summary['total_stocks']}")
    print(f"  Errors: {summary['errors']}")
    print(f"  Total Time: {summary['total_execution_time']:.1f}s ({summary['avg_execution_time_per_stock']:.1f}s/stock)")

    print(f"\n💹 DECISION BREAKDOWN:")
    for decision, count in sorted(summary['decisions'].items()):
        pct = count / summary['total_stocks'] * 100
        print(f"  {decision:12s}: {count:2d} stocks ({pct:5.1f}%)")

    print(f"\n🎯 KEY METRICS:")
    print(f"  BUY Rate: {summary['buy_rate']:.1f}%")
    print(f"  Technical Signals Found: {summary['technical_signals_found']} ({summary['technical_signal_rate']:.1f}%)")
    print(f"  LLM Synthesis Used: {summary['llm_synthesis_used']} ({summary['llm_synthesis_rate']:.1f}%)")

    print(f"\n⚠️  CONFLICT ANALYSIS:")
    for level, count in sorted(summary['conflict_levels'].items()):
        pct = count / summary['total_stocks'] * 100
        print(f"  {level.capitalize():12s}: {count:2d} stocks ({pct:5.1f}%)")

    # BUY recommendations
    buy_stocks = [r for r in results_tracker.results if r['decision'] in ['BUY', 'STRONG BUY']]
    if buy_stocks:
        print(f"\n✅ BUY RECOMMENDATIONS ({len(buy_stocks)}):")
        for stock in buy_stocks:
            print(f"  • {stock['ticker']:15s} {stock['company']:30s} - {stock['decision']} (Score: {stock['composite_score']:.1f})")
            if stock['has_technical_signal']:
                print(f"    ✓ Technical signal confirmed")
            if stock['used_llm_synthesis']:
                print(f"    🤖 LLM synthesis used")
    else:
        print(f"\n❌ NO BUY RECOMMENDATIONS")
        print(f"   Likely due to:")
        print(f"   - Lack of technical signals ({summary['technical_signal_rate']:.1f}% had signals)")
        print(f"   - Strict backtest validation (70% win rate requirement)")

    # Errors
    if results_tracker.errors:
        print(f"\n🚨 ERRORS ({len(results_tracker.errors)}):")
        for error in results_tracker.errors[:5]:  # Show first 5
            print(f"  • {error['ticker']:15s} - {error['error']}")

    # Save detailed results
    output_file = f"full_40_stocks_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    output_data = {
        'summary': summary,
        'results': results_tracker.results,
        'errors': results_tracker.errors,
        'config': config,
        'timestamp': datetime.now().isoformat()
    }

    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2, default=str)

    print(f"\n💾 Detailed results saved to: {output_file}")

    print("\n" + "="*80)
    print("  ANALYSIS COMPLETE")
    print("="*80 + "\n")

    return output_data


if __name__ == '__main__':
    try:
        results = asyncio.run(test_all_stocks())
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        traceback.print_exc()
        sys.exit(1)
