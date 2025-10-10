#!/usr/bin/env python3
"""
Extract detailed decision-making information from test output
Shows what each agent reported and how the orchestrator resolved it
"""

import re
import json
from typing import Dict, List, Any

def parse_log_file(log_file: str) -> List[Dict[str, Any]]:
    """Parse log file and extract detailed decision information"""

    stocks = []
    current_stock = None

    with open(log_file, 'r') as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        # Detect new stock analysis
        match = re.match(r'\[(\d+)/\d+\] 🔍 Analyzing (\S+) \((.+)\)', line)
        if match:
            if current_stock:
                stocks.append(current_stock)

            current_stock = {
                'index': int(match.group(1)),
                'ticker': match.group(2),
                'company': match.group(3),
                'agents': {},
                'decision': {}
            }
            continue

        if not current_stock:
            continue

        # Extract agent scores and summaries
        if 'Fundamental Analyst - INFO - GPT-4 analysis complete' in line:
            current_stock['agents']['fundamental'] = {'llm': 'GPT-4'}

        if 'Agent.Fundamental Analyst - INFO -   Score:' in line:
            score = float(line.split('Score:')[1].strip())
            if 'fundamental' not in current_stock['agents']:
                current_stock['agents']['fundamental'] = {}
            current_stock['agents']['fundamental']['score'] = score

        if 'Agent.Technical Analyst - INFO -   Score:' in line:
            score = float(line.split('Score:')[1].strip())
            current_stock['agents']['technical'] = {'score': score}

        if 'Agent.Sentiment Analyst - INFO -   Score:' in line:
            score = float(line.split('Score:')[1].strip())
            current_stock['agents']['sentiment'] = {'score': score}

        if 'Agent.Management Analyst - INFO -   Score:' in line:
            score = float(line.split('Score:')[1].strip())
            current_stock['agents']['management'] = {'score': score}

        # Extract summaries
        if 'Agent.Sentiment Analyst - INFO -   Summary:' in line:
            summary = line.split('Summary:')[1].strip()
            if 'sentiment' in current_stock['agents']:
                current_stock['agents']['sentiment']['summary'] = summary

        if 'Agent.Management Analyst - INFO -   Summary:' in line:
            summary = line.split('Summary:')[1].strip()
            if 'management' in current_stock['agents']:
                current_stock['agents']['management']['summary'] = summary

        if 'Agent.Technical Analyst - INFO -   Summary:' in line:
            summary = line.split('Summary:')[1].strip()
            if 'technical' in current_stock['agents']:
                current_stock['agents']['technical']['summary'] = summary

        # Extract conflict information
        if 'Conflict detected' in line:
            match = re.search(r'Conflict detected \((\w+)\): Variance=([\d.]+), Disagreements=(\d+)', line)
            if match:
                current_stock['decision']['conflict_level'] = match.group(1)
                current_stock['decision']['variance'] = float(match.group(2))
                current_stock['decision']['disagreements'] = int(match.group(3))

        # Extract technical signal
        if 'No technical signal - cannot BUY' in line:
            current_stock['decision']['technical_signal'] = False

        if 'Technical signal found' in line:
            current_stock['decision']['technical_signal'] = True

        # Extract LLM synthesis usage
        if 'Using LLM synthesis for final decision' in line:
            current_stock['decision']['used_llm'] = True

        # Extract final decision
        if '  ✓ SELL (Score:' in line or '  ✓ BUY (Score:' in line or '  ✓ WAIT (Score:' in line or '  ✓ HOLD (Score:' in line:
            match = re.search(r'✓ (\w+) \(Score: ([\d.]+)', line)
            if match:
                current_stock['decision']['action'] = match.group(1)
                current_stock['decision']['composite_score'] = float(match.group(2))

        # Extract vetoes
        if '⚠️  Vetoes:' in line:
            match = re.search(r'Vetoes: (\d+)', line)
            if match:
                current_stock['decision']['veto_count'] = int(match.group(1))

    # Add last stock
    if current_stock:
        stocks.append(current_stock)

    return stocks


def print_stock_analysis(stock: Dict[str, Any]):
    """Pretty print single stock analysis"""

    print(f"\n{'='*80}")
    print(f"[{stock['index']}/40] {stock['ticker']} - {stock['company']}")
    print(f"{'='*80}")

    # Agent Scores
    print("\n📊 AGENT INPUTS:")
    agents = stock['agents']

    if 'fundamental' in agents:
        f = agents['fundamental']
        llm_info = f"({f.get('llm', '')})" if 'llm' in f else ""
        score = f.get('score', 0)
        print(f"  Fundamental: {score:.1f}/100 {llm_info}")

    if 'technical' in agents:
        t = agents['technical']
        score = t.get('score', 0)
        print(f"  Technical:   {score:.1f}/100")
        if 'summary' in t:
            print(f"    └─ {t['summary']}")

    if 'sentiment' in agents:
        s = agents['sentiment']
        score = s.get('score', 0)
        print(f"  Sentiment:   {score:.1f}/100")
        if 'summary' in s:
            print(f"    └─ {s['summary']}")

    if 'management' in agents:
        m = agents['management']
        score = m.get('score', 0)
        print(f"  Management:  {score:.1f}/100")
        if 'summary' in m:
            print(f"    └─ {m['summary']}")

    # Calculate score variance
    scores = [agents[a]['score'] for a in agents if 'score' in agents[a]]
    if scores:
        import numpy as np
        mean = np.mean(scores)
        std = np.std(scores)
        cv = std / mean if mean > 0 else 0
        print(f"\n  📈 Score Stats: Mean={mean:.1f}, StdDev={std:.1f}, Variance={cv:.3f}")

    # Conflict Analysis
    print("\n⚔️  CONFLICT ANALYSIS:")
    decision = stock['decision']

    if 'conflict_level' in decision:
        print(f"  Level: {decision['conflict_level'].upper()}")
        print(f"  Variance: {decision.get('variance', 0):.3f}")
        print(f"  Disagreements: {decision.get('disagreements', 0)}")
    else:
        print("  Level: NONE")

    # Technical Signal
    print("\n🎯 TECHNICAL SIGNAL:")
    has_signal = decision.get('technical_signal', False)
    print(f"  Has Signal: {'✅ YES' if has_signal else '❌ NO'}")

    # LLM Synthesis
    print("\n🤖 LLM SYNTHESIS:")
    used_llm = decision.get('used_llm', False)
    print(f"  Used: {'✅ YES' if used_llm else '❌ NO'}")

    # Final Decision
    print("\n⚖️  FINAL DECISION:")
    print(f"  Action: {decision.get('action', 'UNKNOWN')}")
    print(f"  Composite Score: {decision.get('composite_score', 0):.1f}/100")
    print(f"  Vetoes: {decision.get('veto_count', 0)}")

    print("\n" + "="*80)


def main():
    log_file = 'full_test_output_fixed.log'

    print("\n" + "="*80)
    print(" DETAILED DECISION ANALYSIS")
    print("="*80)

    stocks = parse_log_file(log_file)

    print(f"\n✅ Parsed {len(stocks)} stocks\n")

    # Show last 3 stocks in detail
    print("\n📋 LAST 3 STOCKS (DETAILED):\n")
    for stock in stocks[-3:]:
        print_stock_analysis(stock)

    # Summary statistics
    print("\n" + "="*80)
    print(" SUMMARY STATISTICS")
    print("="*80)

    total = len(stocks)

    # Decision breakdown
    decisions = {}
    for s in stocks:
        action = s['decision'].get('action', 'UNKNOWN')
        decisions[action] = decisions.get(action, 0) + 1

    print(f"\n📊 DECISION BREAKDOWN ({total} stocks):")
    for action, count in sorted(decisions.items()):
        pct = count / total * 100
        print(f"  {action:12s}: {count:2d} ({pct:5.1f}%)")

    # Conflict levels
    conflicts = {}
    for s in stocks:
        level = s['decision'].get('conflict_level', 'none')
        conflicts[level] = conflicts.get(level, 0) + 1

    print(f"\n⚔️  CONFLICT LEVELS:")
    for level, count in sorted(conflicts.items()):
        pct = count / total * 100
        print(f"  {level.capitalize():12s}: {count:2d} ({pct:5.1f}%)")

    # Technical signals
    tech_signals = sum(1 for s in stocks if s['decision'].get('technical_signal', False))
    print(f"\n🎯 TECHNICAL SIGNALS:")
    print(f"  Found: {tech_signals}/{total} ({tech_signals/total*100:.1f}%)")

    # LLM usage
    llm_used = sum(1 for s in stocks if s['decision'].get('used_llm', False))
    print(f"\n🤖 LLM SYNTHESIS:")
    print(f"  Used: {llm_used}/{total} ({llm_used/total*100:.1f}%)")

    # Average scores by agent
    print(f"\n📊 AVERAGE AGENT SCORES:")

    for agent_name in ['fundamental', 'technical', 'sentiment', 'management']:
        scores = [s['agents'][agent_name]['score']
                  for s in stocks
                  if agent_name in s['agents'] and 'score' in s['agents'][agent_name]]
        if scores:
            avg = sum(scores) / len(scores)
            print(f"  {agent_name.capitalize():12s}: {avg:.1f}/100")

    print("\n" + "="*80 + "\n")


if __name__ == '__main__':
    import numpy as np
    main()
