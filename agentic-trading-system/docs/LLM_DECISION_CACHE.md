# LLM Decision Cache

## Overview

The LLM Decision Cache system reduces dependency on OpenAI API by caching and reusing LLM synthesis decisions. It learns from historical decisions to handle similar scenarios without calling the API.

## How It Works

### 1. Cache Strategy

**Cache Key Generation:**
- Ticker symbol
- Agent scores (rounded to nearest 5 for fuzzy matching)
- Conflict level (none/low/medium/high)
- Composite score (rounded to nearest 5)

**Lookup Strategy:**
1. **Exact Match**: Same ticker + similar scores + same conflict level
2. **Similar Match**: Same ticker + conflict level + 85%+ similarity in agent scores

### 2. Similarity Calculation

```python
# Example similar scenarios that would match:
Scenario 1:                  Scenario 2:
- Fundamental: 45           - Fundamental: 48
- Technical: 65             - Technical: 62
- Sentiment: 50             - Sentiment: 52
- Management: 55            - Management: 57
Similarity: 92% ✅ Would match
```

## Benefits

###  **Reduced API Costs**
- Typical cache hit rate: **60-80%** after initial learning phase
- Saves ~$0.01-0.02 per cached decision (GPT-4 pricing)
- For September 2025 simulation: 220 decisions × $0.01 = **$2.20 saved**

### **Faster Decisions**
- Cache lookup: **<1ms**
- LLM API call: **2-10 seconds**
- **10,000x+ faster** for cached decisions

### **Offline Operation**
- System can run without OpenAI API for similar scenarios
- Graceful degradation when quota exceeded
- Continues trading even when API is down

### **Learning Over Time**
- Builds historical decision database
- Identifies recurring patterns
- Can export for model fine-tuning

## Usage

### Automatic (No Configuration Needed)

The cache is **automatically enabled** in the Orchestrator. When LLM synthesis is needed:

1. Check cache first
2. If found: Use cached decision
3. If not found: Call LLM API and cache result

### Manual Cache Management

```python
from tools.llm_decision_cache import LLMDecisionCache

# Initialize
cache = LLMDecisionCache()

# Get statistics
stats = cache.get_statistics()
print(f"Hit rate: {stats['hit_rate']:.1f}%")
print(f"Total decisions: {stats['total_decisions']}")
print(f"Cache hits: {stats['cache_hits']}")
print(f"Similar matches: {stats['similar_matches']}")

# Analyze patterns
patterns = cache.analyze_patterns(min_occurrences=3)
for pattern in patterns:
    print(f"{pattern['conflict_level']} conflict, "
          f"score {pattern['score_range']}: "
          f"{pattern['recommendation']} ({pattern['count']} times)")

# Export for training
cache.export_training_data("llm_training_export.json")
```

## Cache Statistics

### Example Output

```
LLM Decision Cache Statistics:
├── Total Decisions: 220
├── Cache Hits (Exact): 98 (44.5%)
├── Cache Hits (Similar): 73 (33.2%)
├── Cache Misses: 49 (22.3%)
└── Overall Hit Rate: 77.7%

API Calls Saved: 171
Estimated Cost Savings: $1.71
Average Response Time:
├── Cached: 0.3ms
└── LLM API: 3.2s
```

## Pattern Analysis

The cache can identify recurring decision patterns:

```python
patterns = cache.analyze_patterns()

# Output example:
[
    {
        'conflict_level': 'medium',
        'score_range': '40-50',
        'recommendation': 'HOLD',
        'count': 45,
        'avg_confidence': 52.3,
        'tickers': ['RELIANCE.NS', 'TCS.NS', ...]
    },
    {
        'conflict_level': 'high',
        'score_range': '60-70',
        'recommendation': 'BUY',
        'count': 23,
        'avg_confidence': 68.1,
        'tickers': ['INFY.NS', 'HDFCBANK.NS', ...]
    }
]
```

##  When Cache is Used

LLM synthesis (and caching) is triggered when:

1. **Medium/High Conflict** between agents
   - Agents disagree by >40 points
   - High variance in scores

2. **Borderline Scores** (40-70)
   - Not clearly BUY (>70) or SELL (<40)
   - Needs nuanced judgment

## Cache Storage

**Location**: `storage/llm_decisions/`

**Files**:
- `decisions.jsonl`: All cached decisions (append-only log)
- `cache_stats.json`: Statistics and hit rates

**Format**:
```json
{
  "cache_key": "a3f9c2e...",
  "ticker": "RELIANCE.NS",
  "agent_scores": {
    "fundamental": 45,
    "technical": 65,
    "sentiment": 50,
    "management": 55
  },
  "conflict_level": "medium",
  "composite_score": 52.5,
  "decision": {
    "final_recommendation": "HOLD",
    "confidence": 55,
    "key_insights": ["..."],
    "adjusted_score": 53.0
  },
  "cached_at": "2025-09-15T10:30:00"
}
```

## Advanced: Training Data Export

Export cached decisions for fine-tuning your own model:

```bash
python -c "
from tools.llm_decision_cache import LLMDecisionCache
cache = LLMDecisionCache()
cache.export_training_data('training_data.json')
"
```

This creates training data in format:
```json
[
  {
    "input": {
      "ticker": "RELIANCE.NS",
      "agent_scores": {...},
      "conflict_level": "medium",
      "composite_score": 52.5
    },
    "output": {
      "final_recommendation": "HOLD",
      "confidence": 55,
      ...
    }
  }
]
```

## Maintenance

### Clear Cache

```bash
rm -rf storage/llm_decisions/
```

### Backup Cache

```bash
cp -r storage/llm_decisions/ backups/llm_cache_$(date +%Y%m%d)/
```

### Monitor Performance

```python
from tools.llm_decision_cache import LLMDecisionCache

cache = LLMDecisionCache()
stats = cache.get_statistics()

if stats['hit_rate'] < 50:
    print("⚠️ Low cache hit rate - need more historical data")
elif stats['hit_rate'] > 80:
    print("✅ Excellent cache performance")
```

## Configuration

### Adjust Similarity Threshold

```python
# In orchestrator.py, line 643:
llm_synthesis = self.llm_cache.get_cached_decision(
    ticker=ticker,
    agent_scores=agent_scores,
    conflict_info=conflict_info,
    composite_score=composite_score,
    similarity_threshold=0.85  # Adjust between 0.7-0.95
)
```

**Recommended Thresholds:**
- `0.95`: Very strict, only near-exact matches
- `0.85`: Balanced (default) - good accuracy + hit rate
- `0.75`: Loose, higher hit rate but less accurate
- `0.70`: Very loose, may give incorrect decisions

## Limitations

1. **Cold Start**: No benefit until cache is populated (first run)
2. **Market Conditions**: Cached decisions don't account for changing market conditions
3. **Ticker-Specific**: Cache is ticker-specific, doesn't generalize across stocks
4. **Score Rounding**: Scores rounded to nearest 5, may lose precision

## Future Enhancements

- [ ] Cross-ticker pattern recognition
- [ ] Market regime awareness in cache keys
- [ ] Time-decay for old decisions
- [ ] ML-based similarity scoring
- [ ] Auto-tune similarity threshold
- [ ] Cache warming strategies
