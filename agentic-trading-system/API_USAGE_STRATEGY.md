# API Usage Strategy
## Three-API Hybrid Approach

**Date**: 2025-10-08
**Status**: Implementation Guide

---

## 🎯 Strategic API Selection

### **Perplexity Sonar** (Grounded Search)
**Best For**: Real-time data fetching with citations
**Cost**: $5 per 1M tokens (input + output)
**Speed**: Fast (search-optimized)

**Use Cases**:
1. ✅ Stock news and sentiment
2. ✅ Conference call transcripts
3. ✅ Analyst opinions and ratings
4. ✅ Fundamental metrics gap filling
5. ✅ Management commentary extraction

**Why**: Real-time web access, grounded in actual sources, cost-effective for data retrieval

---

### **OpenAI GPT-4 Turbo** (Complex Reasoning)
**Best For**: Complex analysis and synthesis
**Cost**: $10 in / $30 out per 1M tokens
**Speed**: Medium
**Context**: 128k tokens

**Use Cases**:
1. ✅ Fundamental valuation reasoning ("Is PE of 25 justified?")
2. ✅ Red flag detection (accounting irregularities)
3. ✅ Technical pattern interpretation
4. ✅ Final decision synthesis (Orchestrator)
5. ✅ Risk assessment

**Why**: Best-in-class reasoning, excellent at connecting dots, structured outputs

---

### **Claude-3.5-Sonnet** (Long Context)
**Best For**: Long document analysis
**Cost**: $3 in / $15 out per 1M tokens
**Speed**: Fast
**Context**: 200k tokens

**Use Cases**:
1. ✅ Conference call transcript analysis (full text)
2. ✅ Annual report parsing
3. ✅ Management promise vs performance correlation
4. ✅ Multi-quarter trend analysis
5. ✅ Strategy extraction from backtests

**Why**: Longest context window, cheaper than GPT-4, excellent at long-form analysis

---

## 📊 Implementation by Agent

### 1. Fundamental Analyst

**Data Fetching** (Perplexity):
- Gap fill missing metrics
- Real-time financial data
- **Cost**: ~$0.003/stock

**Reasoning** (GPT-4 Turbo):
- Valuation context analysis
- Red flag detection
- Only for borderline scores (40-60)
- **Cost**: ~$0.02/stock (selective)

**Total**: ~$0.023/stock

---

### 2. Technical Analyst

**No API calls needed**:
- Pure mathematical indicators
- Rule-based pattern detection
- **Cost**: $0

---

### 3. Backtest Validator

**Reasoning** (Claude-3.5-Sonnet):
- Strategy rule extraction (when needed)
- Result interpretation (failures only)
- 90-day caching
- **Cost**: ~$0.01/stock first time, $0 cached

---

### 4. Sentiment Analyst

**Data Fetching** (Perplexity):
- News headlines and sentiment
- Social media buzz
- Analyst opinions
- **Cost**: ~$0.015/stock (3 searches)

**No additional reasoning needed**:
- Keyword-based sentiment scoring works well

**Total**: ~$0.015/stock

---

### 5. Management Analyst

**Data Fetching** (Perplexity):
- Conference call transcripts
- Earnings call summaries
- Management commentary
- **Cost**: ~$0.005/stock

**Reasoning** (Claude-3.5-Sonnet):
- Full transcript analysis (200k context)
- Promise vs performance correlation
- Management tone assessment
- Strategic initiative extraction
- **Cost**: ~$0.30/stock (quarterly cache)

**Total**: ~$0.305/stock (first analysis)
**Cached**: ~$0.005/stock (90-day cache, 85% hit rate)

---

### 6. Orchestrator

**Reasoning** (GPT-4 Turbo):
- Final decision synthesis
- Conflict resolution (when agents disagree)
- Only when composite score is 50-70 (borderline)
- **Cost**: ~$0.02/stock (selective)

---

## 💰 Cost Summary

### Per Stock Cost:

| Agent | Perplexity | OpenAI | Claude | Total |
|-------|-----------|---------|---------|-------|
| **Fundamental** | $0.003 | $0.02* | - | $0.023 |
| **Technical** | - | - | - | $0.00 |
| **Backtest** | - | - | $0.01* | $0.01 |
| **Sentiment** | $0.015 | - | - | $0.015 |
| **Management** | $0.005 | - | $0.30* | $0.305 |
| **Orchestrator** | - | $0.02* | - | $0.02 |
| **TOTAL** | **$0.028** | **$0.04** | **$0.31** | **$0.378** |

*Selective usage or cached

### With Caching (Month 2+):

| Agent | First Analysis | Cached | Avg (70% cache) |
|-------|---------------|---------|-----------------|
| Management | $0.305 | $0.005 | $0.10 |
| Backtest | $0.01 | $0.00 | $0.003 |
| **Others** | $0.063 | $0.063 | $0.063 |
| **TOTAL** | **$0.378** | **$0.068** | **$0.166** |

### Monthly Cost (50 stocks/day):

**Month 1** (no cache):
- 50 stocks × $0.378 × 22 days = **$415/month**

**Month 2+** (70% cache):
- 50 stocks × $0.166 × 22 days = **$182/month**

**Annual**: ~$2,200/year

---

## 🎯 Comparison to Original Plan

| Metric | Original Plan | Current Hybrid | Savings |
|--------|--------------|----------------|---------|
| **Per Stock** | $2.20 | $0.378 | 83% ↓ |
| **Monthly (Month 1)** | $2,420 | $415 | 83% ↓ |
| **Monthly (Cached)** | $484 | $182 | 62% ↓ |
| **Annual** | $5,808 | $2,200 | 62% ↓ |

### What We Kept:
✅ Deep reasoning for critical decisions
✅ Long context for con-call analysis
✅ Real-time data fetching

### What We Optimized:
✅ Selective GPT-4 usage (only borderline cases)
✅ 90-day caching on stable analyses
✅ Rule-based where sufficient

---

## 🚀 Implementation Priority

### Phase 1 (This Session): ✅
1. ✅ Add API keys to .env
2. ✅ Fix OpenAI client for API v1.0
3. ⏳ Update Fundamental Analyst (GPT-4 reasoning)
4. ⏳ Update Management Analyst (Claude long context)

### Phase 2 (Next):
5. ⏳ Update Orchestrator (GPT-4 synthesis)
6. ⏳ Update Backtest Validator (Claude interpretation)
7. ⏳ Test end-to-end with 10 stocks

### Phase 3 (Future):
8. ⏳ Implement smart caching
9. ⏳ A/B test reasoning quality
10. ⏳ Optimize prompt lengths

---

## 📝 Implementation Notes

### Perplexity Usage:
```python
# Already implemented - working well
perplexity = PerplexitySearchClient()
result = await perplexity.search(query)
```

### OpenAI Usage (GPT-4):
```python
from tools.llm.llm_client import LLMClient

llm = LLMClient()
response = await llm.chat(
    messages=[...],
    provider="openai",
    model="gpt-4-turbo",
    temperature=0.2
)
```

### Claude Usage (3.5-Sonnet):
```python
from tools.llm.llm_client import LLMClient

llm = LLMClient()
response = await llm.chat(
    messages=[...],
    provider="anthropic",
    model="claude-3.5-sonnet",
    temperature=0.2
)
```

---

## ✅ Quality Benefits

### With Hybrid LLM Approach:

1. **Better Fundamental Analysis**:
   - Can explain "why" scores are what they are
   - Contextual valuation understanding
   - Red flag detection

2. **Smarter Management Analysis**:
   - Full transcript analysis (not keywords)
   - Promise vs performance tracking
   - Nuanced tone detection

3. **Intelligent Decision Making**:
   - Orchestrator can resolve conflicts
   - Contextual risk assessment
   - Explainable decisions

4. **Backtest Interpretation**:
   - Understand why strategies work/fail
   - Extract learnings
   - Improve over time

---

**Status**: API Keys Added, Implementation In Progress
**Next**: Update agents with LLM reasoning
**Target Cost**: $0.38/stock (first) → $0.17/stock (cached)
