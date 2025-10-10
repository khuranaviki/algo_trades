# Conflict Resolution Framework for Orchestrator

## Problem Statement

**Current System**: Simple weighted averaging of agent scores
- Doesn't detect when agents strongly disagree
- No reasoning about WHY agents conflict
- Misses important trading nuances (e.g., "good company, bad timing")

**Example Conflict**:
```
Fundamental: 85/100 (Strong financials, undervalued)
Technical: 25/100 (Bearish pattern, downtrend)
Sentiment: 70/100 (Positive news)
Management: 75/100 (Good execution)

Current: Composite = 50.5 → HOLD (no explanation)
Better: "Strong company, but wait for technical confirmation. Consider watchlist."
```

---

## Proposed Solution: LLM-Based Conflict Resolution

### Architecture

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│  PHASE 1: AGENT ANALYSIS (Parallel)                │
│  ├─ Fundamental Analyst (GPT-4)                    │
│  ├─ Technical Analyst (Rule-based)                 │
│  ├─ Sentiment Analyst (Perplexity + Rule-based)    │
│  └─ Management Analyst (GPT-4)                     │
│                                                     │
├─────────────────────────────────────────────────────┤
│                                                     │
│  PHASE 2: CONFLICT DETECTION (Rule-based)          │
│  ├─ Detect score variance (σ > 25 = conflict)      │
│  ├─ Identify disagreements (diff > 40 points)      │
│  └─ Flag critical vetoes                           │
│                                                     │
├─────────────────────────────────────────────────────┤
│                                                     │
│  PHASE 3: LLM SYNTHESIS (GPT-4)                    │
│  ├─ Analyze agent reasoning (not just scores)      │
│  ├─ Resolve conflicts with context                 │
│  ├─ Generate final recommendation                  │
│  └─ Explain decision rationale                     │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## Implementation Details

### 1. Conflict Detection Logic

```python
def _detect_conflicts(self, agent_scores: Dict[str, float]) -> Dict[str, Any]:
    """
    Detect conflicts between agents

    Returns:
        {
            'has_conflict': bool,
            'conflict_level': 'none' | 'low' | 'medium' | 'high',
            'disagreements': List[Dict],
            'variance': float
        }
    """
    scores = list(agent_scores.values())
    mean_score = np.mean(scores)
    std_dev = np.std(scores)

    # Calculate variance (conflict indicator)
    variance = std_dev / mean_score if mean_score > 0 else 0

    # Detect pairwise disagreements
    disagreements = []
    for agent1, score1 in agent_scores.items():
        for agent2, score2 in agent_scores.items():
            if agent1 < agent2:  # Avoid duplicates
                diff = abs(score1 - score2)

                # Major disagreement: >40 point difference
                if diff >= 40:
                    disagreements.append({
                        'agents': [agent1, agent2],
                        'difference': diff,
                        'scores': {agent1: score1, agent2: score2}
                    })

    # Classify conflict level
    if variance > 0.4 or disagreements:
        conflict_level = 'high'
    elif variance > 0.25:
        conflict_level = 'medium'
    elif variance > 0.15:
        conflict_level = 'low'
    else:
        conflict_level = 'none'

    return {
        'has_conflict': conflict_level != 'none',
        'conflict_level': conflict_level,
        'disagreements': disagreements,
        'variance': variance,
        'std_dev': std_dev
    }
```

### 2. LLM Conflict Resolution

```python
async def _llm_conflict_resolution(
    self,
    ticker: str,
    agent_results: Dict[str, Any],
    conflict_info: Dict[str, Any],
    composite_score: float
) -> Dict[str, Any]:
    """
    Use GPT-4 to synthesize agent outputs and resolve conflicts

    Args:
        ticker: Stock ticker
        agent_results: Full results from all agents
        conflict_info: Conflict detection output
        composite_score: Raw weighted average

    Returns:
        {
            'final_recommendation': 'BUY' | 'SELL' | 'HOLD' | 'WAIT',
            'adjusted_score': float,
            'reasoning': str,
            'key_insights': List[str],
            'risk_factors': List[str],
            'alternative_scenarios': List[Dict]
        }
    """
    from tools.llm.llm_client import LLMClient

    llm = LLMClient()

    # Build context for LLM
    context = f"""
You are a professional trading decision maker synthesizing analysis from 4 specialist agents.

STOCK: {ticker}
COMPOSITE SCORE (weighted avg): {composite_score:.1f}/100

AGENT ANALYSIS:

1. FUNDAMENTAL ANALYST (Weight: 25%)
   Score: {agent_results['fundamental'].get('score', 0)}/100
   Recommendation: {agent_results['fundamental'].get('recommendation', 'N/A')}
   Key Insights: {agent_results['fundamental'].get('llm_analysis', {}).get('reasoning', 'N/A')}
   Financial Health: {agent_results['fundamental'].get('financial_health', {}).get('score', 0)}/100
   Valuation: {agent_results['fundamental'].get('valuation', {}).get('score', 0)}/100
   Growth: {agent_results['fundamental'].get('growth', {}).get('score', 0)}/100

2. TECHNICAL ANALYST (Weight: 20%)
   Score: {agent_results['technical'].get('score', 0)}/100
   Trend: {agent_results['technical'].get('trend', 'N/A')}
   Primary Pattern: {agent_results['technical'].get('primary_pattern', {}).get('name', 'None')}
   Support/Resistance: {agent_results['technical'].get('backtest_context', {})}

3. SENTIMENT ANALYST (Weight: 20%)
   Score: {agent_results['sentiment'].get('score', 0)}/100
   Overall Sentiment: {agent_results['sentiment'].get('sentiment', 'N/A')}
   News Summary: {agent_results['sentiment'].get('summary', 'N/A')}

4. MANAGEMENT ANALYST (Weight: 15%)
   Score: {agent_results['management'].get('score', 0)}/100
   Credibility: {agent_results['management'].get('llm_analysis', {}).get('credibility_score', 'N/A')}/100
   Transparency: {agent_results['management'].get('llm_analysis', {}).get('transparency_score', 'N/A')}/100
   Key Insights: {agent_results['management'].get('llm_analysis', {}).get('recommendation', 'N/A')}

CONFLICT ANALYSIS:
Conflict Level: {conflict_info['conflict_level']}
Disagreements: {conflict_info['disagreements']}
Score Variance: {conflict_info['variance']:.2f}

TASK:
Analyze the above agent outputs and provide a FINAL trading decision. If agents conflict:
1. Identify WHY they disagree (timing vs fundamentals? short-term vs long-term?)
2. Determine which agent's view is most relevant for THIS trading decision
3. Provide nuanced recommendation (e.g., "WAIT for technical confirmation", "BUY with tight stop")

Return JSON with:
{{
    "final_recommendation": "BUY|SELL|HOLD|WAIT",
    "adjusted_score": <number 0-100>,
    "confidence": <number 0-100>,
    "reasoning": "<2-3 sentence explanation>",
    "key_insights": ["insight1", "insight2", "insight3"],
    "risk_factors": ["risk1", "risk2"],
    "alternative_scenarios": [
        {{"condition": "if X happens", "action": "then do Y"}}
    ],
    "time_horizon": "short-term|medium-term|long-term"
}}
"""

    messages = [
        {
            "role": "system",
            "content": "You are an expert trading decision synthesizer. Analyze agent outputs and resolve conflicts with nuanced, practical trading advice."
        },
        {
            "role": "user",
            "content": context
        }
    ]

    # Call GPT-4 for synthesis
    response = await llm.chat(
        messages=messages,
        provider="openai",
        model="gpt-4-turbo",
        temperature=0.2,
        json_mode=True
    )

    import json
    synthesis = json.loads(response.content)

    return synthesis
```

### 3. Enhanced Decision Making

```python
def _make_decision_with_llm_synthesis(
    self,
    fundamental: Dict[str, Any],
    technical: Dict[str, Any],
    sentiment: Dict[str, Any],
    management: Dict[str, Any],
    backtest: Dict[str, Any],
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Make final decision with LLM synthesis when conflicts detected
    """
    # Step 1: Calculate composite score (weighted average)
    agent_scores = {
        'fundamental': fundamental.get('score', 0),
        'technical': technical.get('score', 0),
        'sentiment': sentiment.get('score', 0),
        'management': management.get('score', 0)
    }

    composite_score = (
        agent_scores['fundamental'] * self.weights['fundamental'] +
        agent_scores['technical'] * self.weights['technical'] +
        agent_scores['sentiment'] * self.weights['sentiment'] +
        agent_scores['management'] * self.weights['management']
    )

    # Step 2: Detect conflicts
    conflict_info = self._detect_conflicts(agent_scores)

    # Step 3: Decide if LLM synthesis is needed
    use_llm_synthesis = (
        conflict_info['conflict_level'] in ['medium', 'high'] or
        40 <= composite_score <= 70  # Borderline cases
    )

    # Step 4: Get LLM synthesis if needed
    if use_llm_synthesis and self.use_llm_synthesis:
        self.logger.info(f"⚠️  Conflict detected ({conflict_info['conflict_level']}), using LLM synthesis")

        llm_synthesis = await self._llm_conflict_resolution(
            ticker,
            {
                'fundamental': fundamental,
                'technical': technical,
                'sentiment': sentiment,
                'management': management
            },
            conflict_info,
            composite_score
        )

        # Use LLM recommendation
        action = llm_synthesis['final_recommendation']
        confidence = llm_synthesis['confidence']
        adjusted_score = llm_synthesis['adjusted_score']

        return {
            'action': action,
            'confidence': confidence,
            'composite_score': adjusted_score,
            'reasoning': llm_synthesis['reasoning'],
            'key_insights': llm_synthesis['key_insights'],
            'risk_factors': llm_synthesis['risk_factors'],
            'conflict_resolution': {
                'method': 'llm_synthesis',
                'conflict_level': conflict_info['conflict_level'],
                'disagreements': conflict_info['disagreements']
            }
        }
    else:
        # Use rule-based decision (current logic)
        self.logger.info("✅ No major conflicts, using rule-based decision")
        return self._make_rule_based_decision(
            composite_score, agent_scores, backtest, context
        )
```

---

## Cost Analysis

### LLM Synthesis Usage

**When LLM Synthesis Triggers**:
- Medium/High conflict (score variance > 0.25)
- Borderline scores (40-70)
- Estimated: 30-40% of stocks

**Cost per Synthesis**:
- Prompt: ~1,500 tokens
- Response: ~400 tokens
- Total: ~1,900 tokens
- Cost: ~$0.025/stock

**Total Cost per Stock**:
```
Perplexity (data):        $0.028
GPT-4 Fundamental:        $0.0095
GPT-4 Management:         $0.0095
GPT-4 Synthesis (30%):    $0.0075  (30% of stocks × $0.025)
---
Total:                    $0.055/stock (avg)
Monthly (50 stocks/day):  $82.50
Annual:                   $990
```

**Still 97.5% cheaper than original $2.20/stock plan!**

---

## Benefits of LLM Conflict Resolution

1. **Contextual Understanding**: Distinguishes "good company, bad timing" from "bad company"
2. **Nuanced Recommendations**: Can suggest "WAIT", "BUY with tight stop", "Long-term HOLD"
3. **Explainable Decisions**: Clear reasoning for why decision was made
4. **Better Risk Management**: Identifies scenarios and conditions
5. **Handles Edge Cases**: Rule-based systems struggle with ambiguity

---

## Example Scenarios

### Scenario 1: Fundamental-Technical Conflict

**Input**:
- Fundamental: 85/100 (Undervalued, strong financials)
- Technical: 20/100 (Bearish breakdown)
- Sentiment: 60/100 (Mixed)
- Management: 75/100 (Good execution)

**Rule-based**: Composite = 58.5 → HOLD (no context)

**LLM Synthesis**:
```json
{
  "final_recommendation": "WAIT",
  "adjusted_score": 60,
  "confidence": 65,
  "reasoning": "Strong fundamentals suggest long-term value, but bearish technical breakdown indicates short-term downside risk. Wait for technical confirmation (moving average crossover or support bounce) before entering.",
  "key_insights": [
    "Fundamentally undervalued by 20-25%",
    "Technical breakdown suggests 10-15% downside possible",
    "Management executing well on strategy"
  ],
  "risk_factors": [
    "Further technical deterioration could push price lower",
    "Market sentiment currently negative"
  ],
  "alternative_scenarios": [
    {"condition": "If price bounces off support at ₹2,400", "action": "BUY with stop at ₹2,350"},
    {"condition": "If fundamental metrics deteriorate", "action": "Re-evaluate thesis"}
  ],
  "time_horizon": "medium-term"
}
```

### Scenario 2: Management-Sentiment Conflict

**Input**:
- Fundamental: 70/100 (Decent financials)
- Technical: 65/100 (Neutral)
- Sentiment: 30/100 (Very negative news)
- Management: 80/100 (Credible, transparent)

**Rule-based**: Composite = 60.75 → HOLD

**LLM Synthesis**:
```json
{
  "final_recommendation": "BUY",
  "adjusted_score": 68,
  "confidence": 70,
  "reasoning": "Recent negative news has created temporary sentiment overshoot. Management has strong track record of execution and transparency suggests the concerns are overblown. This is a contrarian opportunity.",
  "key_insights": [
    "News concerns appear temporary/fixable",
    "Management credibility suggests ability to resolve",
    "Technical setup remains neutral/constructive"
  ],
  "risk_factors": [
    "Sentiment could worsen before improving",
    "News catalysts may take time to resolve"
  ],
  "alternative_scenarios": [
    {"condition": "If next earnings call addresses concerns", "action": "Add to position"},
    {"condition": "If sentiment doesn't improve in 30 days", "action": "Exit"}
  ],
  "time_horizon": "medium-term"
}
```

---

## Implementation Priority

### Phase 1 (Immediate):
1. ✅ Add conflict detection logic
2. ✅ Implement LLM synthesis for high conflicts
3. ✅ Test with 10 stocks

### Phase 2 (Next Week):
4. Add "WAIT" as recommendation type
5. Implement alternative scenarios
6. Add time horizon classification

### Phase 3 (Next Month):
7. A/B test: Rule-based vs LLM synthesis
8. Optimize when to trigger LLM (cost vs quality)
9. Add learning loop (track which decisions performed best)

---

## Next Steps

**Immediate**:
1. Add `_detect_conflicts()` to orchestrator.py
2. Add `_llm_conflict_resolution()` to orchestrator.py
3. Update `_make_decision()` to use LLM when conflicts detected
4. Test with HDFC Bank (has fundamental-technical conflict)

**After Testing**:
5. Run full 40-stock test comparing rule-based vs LLM decisions
6. Document which conflicts were resolved and how
7. Measure if LLM synthesis improves decision quality
