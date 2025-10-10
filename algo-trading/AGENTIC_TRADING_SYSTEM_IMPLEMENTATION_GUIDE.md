# Agentic Trading System - Complete Implementation Guide

## 📋 Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Architecture](#2-system-architecture)
3. [Agent Specifications](#3-agent-specifications)
4. [Data Flow Architecture](#4-data-flow-architecture)
5. [LLM Strategy & Cost Estimation](#5-llm-strategy--cost-estimation)
6. [Tools & Technologies](#6-tools--technologies)
7. [Implementation Roadmap](#7-implementation-roadmap)
8. [Testing Strategy](#8-testing-strategy)
9. [Deployment & Operations](#9-deployment--operations)
10. [Appendices](#10-appendices)

---

## 1. Executive Summary

### 1.1 System Overview

**Agentic Trading System (ATS)** is a multi-agent AI platform that makes highly informed stock trading decisions by analyzing:
- **Fundamentals**: Financial health, growth, valuation
- **Technicals**: Chart patterns with mandatory 5-year backtest validation (>70% win rate)
- **Sentiment**: News, social media, analyst ratings
- **Management Quality**: Conference calls, annual reports, promise-vs-performance tracking

### 1.2 Key Innovation

**Dual Validation Framework**:
1. **Historical Validation**: Every technical strategy must prove >70% win rate on 5-year backtest
2. **Multi-Agent Consensus**: All dimensions analyzed before any trade

### 1.3 Expected Performance

| Metric | Target | Current (V40) | Improvement |
|--------|--------|---------------|-------------|
| CAGR | 18-22% | 13% | +5-9% |
| Win Rate | 75-85% | 75% | 0-10% |
| Max Drawdown | <12% | ~20% | -40% |
| Sharpe Ratio | >1.5 | ~1.2 | +25% |

### 1.4 Project Timeline

**Total Duration**: 11 weeks (Proof of Concept to Production)

**Budget**:
- Development: ~$15,000 (if outsourced)
- LLM Costs: ~$5,000/year (50 stocks analyzed daily)
- Infrastructure: ~$2,000/year (cloud hosting, databases)

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE LAYER                         │
│  - Dashboard (Streamlit/Gradio)                                     │
│  - API Endpoints (FastAPI)                                          │
│  - Notification System (Email/Telegram)                             │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                    ORCHESTRATION LAYER                               │
│  - LangGraph State Machine                                          │
│  - Agent Coordinator                                                │
│  - Decision Synthesizer                                             │
│  - Portfolio Manager                                                │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                      AGENT LAYER                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │Fundamen- │  │Technical │  │Sentiment │  │Mgmt      │           │
│  │tal       │  │Analyst   │  │Analyst   │  │Quality   │           │
│  │Analyst   │  └────┬─────┘  └──────────┘  │Analyst   │           │
│  └──────────┘       │                       └──────────┘           │
│                     │                                               │
│                ┌────▼─────┐                                         │
│                │Backtest  │                                         │
│                │Validator │                                         │
│                └──────────┘                                         │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                      TOOL LAYER                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │Data      │  │Pattern   │  │LLM       │  │Document  │           │
│  │Fetchers  │  │Detectors │  │Clients   │  │Parsers   │           │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘           │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                      DATA LAYER                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │Market    │  │Documents │  │Backtest  │  │Agent     │           │
│  │Data DB   │  │Storage   │  │Cache     │  │State DB  │           │
│  │(Parquet) │  │(PDF/TXT) │  │(Redis)   │  │(SQLite)  │           │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘           │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Technology Stack Summary

**Core Framework**:
- **Python 3.11+**: Primary language
- **LangGraph**: Agent orchestration (state machine)
- **LangChain**: LLM integration, prompt management
- **Backtrader**: Backtesting engine (existing)

**LLM Providers**:
- **Anthropic Claude-3.5-Sonnet**: Long context (annual reports, con-calls)
- **OpenAI GPT-4-Turbo**: Complex analysis, synthesis
- **Claude-3.5-Haiku**: Fast, cheap sentiment analysis

**Data & Storage**:
- **PostgreSQL**: Agent state, decisions, audit logs
- **Redis**: Backtest validation cache (90-day TTL)
- **Parquet**: OHLCV historical data (5+ years)
- **S3/MinIO**: Document storage (PDFs)

**APIs & Services**:
- **yfinance**: Market data (OHLCV)
- **Screener.in API**: Indian stock fundamentals
- **NewsAPI**: News aggregation
- **Twitter API**: Social sentiment
- **BSE/NSE APIs**: Official data

**Infrastructure**:
- **Docker**: Containerization
- **Docker Compose**: Local development
- **GitHub Actions**: CI/CD
- **AWS/GCP**: Cloud deployment (optional)

---

## 3. Agent Specifications

### 3.1 Agent Overview

The system consists of **6 core agents**:

1. **Orchestrator Agent**: Master coordinator, decision maker
2. **Fundamental Analyst**: Financial analysis
3. **Technical Analyst**: Pattern detection
4. **Backtest Validator**: Strategy validation (5-year historical)
5. **Sentiment Analyst**: Market sentiment
6. **Management Quality Analyst**: Con-calls, annual reports

### 3.2 Base Agent Class

**File**: `agents/base_agent.py`

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
import logging

class BaseAgent(ABC):
    """
    Abstract base class for all agents in the system
    """

    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialize base agent

        Args:
            name: Agent identifier
            config: Configuration dictionary
        """
        self.name = name
        self.config = config
        self.logger = logging.getLogger(f"Agent.{name}")
        self.state = {}
        self.created_at = datetime.now()

    @abstractmethod
    async def analyze(self, ticker: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main analysis method - must be implemented by subclasses

        Args:
            ticker: Stock ticker symbol
            context: Additional context from other agents

        Returns:
            Analysis results dictionary
        """
        pass

    def validate_input(self, ticker: str) -> bool:
        """Validate input parameters"""
        if not ticker or len(ticker) < 2:
            self.logger.error(f"Invalid ticker: {ticker}")
            return False
        return True

    def log_analysis(self, ticker: str, result: Dict[str, Any]) -> None:
        """Log analysis results for audit trail"""
        self.logger.info(f"Analysis complete for {ticker}: {result.get('score', 'N/A')}")

    def get_state(self) -> Dict[str, Any]:
        """Return current agent state"""
        return {
            'name': self.name,
            'state': self.state,
            'uptime': (datetime.now() - self.created_at).total_seconds()
        }
```

**Key Features**:
- ✅ Abstract base for consistency
- ✅ Built-in logging
- ✅ State management
- ✅ Input validation

---

### 3.3 ORCHESTRATOR AGENT

**File**: `agents/orchestrator.py`

**Responsibilities**:
1. Coordinate all agents
2. Synthesize multi-dimensional analysis
3. Apply decision framework with veto rules
4. Manage portfolio constraints
5. Execute final buy/sell decisions

**Key Decision Logic**:

```python
def check_vetos(self, fund: dict, tech: dict, sent: dict, mgmt: dict) -> dict:
    """
    Apply veto rules - any agent can block trade

    Veto Conditions:
    1. Fundamental score < 50
    2. Management score < 40
    3. Technical strategy NOT backtest-validated
    4. Backtest win rate < 70%
    """

    # Veto 1: Weak fundamentals
    if fund['score'] < 50:
        return {
            'vetoed': True,
            'reason': f"Weak fundamentals (score: {fund['score']})",
            'agent': 'Fundamental Analyst'
        }

    # Veto 2: Poor management
    if mgmt['score'] < 40:
        return {
            'vetoed': True,
            'reason': f"Poor management quality (score: {mgmt['score']})",
            'agent': 'Management Analyst'
        }

    # Veto 3: Backtest validation (CRITICAL)
    if not tech.get('backtest_validated', False):
        return {
            'vetoed': True,
            'reason': "Technical strategy not validated via backtest",
            'agent': 'Backtest Validator'
        }

    # Veto 4: Low backtest win rate
    if tech.get('historical_win_rate', 0) < 70:
        return {
            'vetoed': True,
            'reason': f"Backtest win rate ({tech['historical_win_rate']}%) < 70%",
            'agent': 'Backtest Validator'
        }

    return {'vetoed': False}

def calculate_composite_score(self, fund: dict, tech: dict,
                               sent: dict, mgmt: dict) -> float:
    """
    Calculate weighted composite score

    Weights:
    - Fundamental: 30%
    - Technical: 30%
    - Sentiment: 20%
    - Management: 20%
    """

    weights = {
        'fundamental': 0.30,
        'technical': 0.30,
        'sentiment': 0.20,
        'management': 0.20
    }

    # Boost technical score if backtest exceptional
    tech_score = tech['score']
    if tech.get('historical_win_rate', 0) >= 80:
        tech_score = min(tech_score + 5, 100)  # +5 bonus

    composite = (
        weights['fundamental'] * fund['score'] +
        weights['technical'] * tech_score +
        weights['sentiment'] * sent['score'] +
        weights['management'] * mgmt['score']
    )

    return composite
```

**Decision Thresholds**:

| Composite Score | Decision | Position Size | Conviction |
|----------------|----------|---------------|------------|
| ≥ 80 | STRONG BUY | 5% | HIGH |
| 70-79 | BUY | 3% | MEDIUM |
| 60-69 | WATCHLIST | 0% | LOW |
| < 60 | REJECT | 0% | NONE |

**LLM Usage**:
- **Model**: GPT-4-Turbo
- **Frequency**: ~20% of decisions (borderline cases, scores 68-73)
- **Cost per Call**: ~$0.05
- **Purpose**: Nuanced synthesis when scores are borderline

---

### 3.4 FUNDAMENTAL ANALYST AGENT

**File**: `agents/fundamental_analyst.py`

**Responsibilities**:
1. Financial health assessment (ROCE, ROE, Debt/Equity)
2. Growth trajectory analysis (Revenue, Profit CAGR)
3. Valuation analysis (P/E, DCF, peer comparison)
4. Red flag detection (deteriorating margins, rising debt)

**Analysis Components**:

```
┌─────────────────────────────────────────┐
│     FUNDAMENTAL ANALYST WORKFLOW        │
└─────────────────────────────────────────┘

1. Financial Health (40% weight)
   ├── ROCE Score: min(ROCE/25 × 100, 100)
   ├── ROE Score: min(ROE/20 × 100, 100)
   └── Debt Score: 100 - (D/E penalty)

2. Growth Profile (30% weight)
   ├── Revenue CAGR 3Y
   ├── Profit CAGR 3Y
   └── Consistency Score

3. Valuation (30% weight) [LLM-based]
   ├── P/E vs Peers
   ├── PEG Ratio
   └── DCF Fair Value

4. Red Flag Detection [LLM-based]
   ├── Declining Margins
   ├── Rising Debt
   ├── Negative Cash Flow
   └── Revenue Quality Issues

Final Score = (Health × 0.4 + Growth × 0.3 + Valuation × 0.3) - Red Flag Penalty
```

**LLM Calls**:

1. **Valuation Analysis**:
   - Model: Claude-3.5-Sonnet
   - Input: Financial metrics + peer comparison
   - Output: Fair value estimate, upside/downside
   - Tokens: ~10k in, ~2k out
   - Cost: ~$0.03

2. **Red Flag Detection**:
   - Model: GPT-4-Turbo
   - Input: YoY metrics, quarterly trends
   - Output: List of red flags with severity
   - Tokens: ~8k in, ~1k out
   - Cost: ~$0.02

**Total Cost per Stock**: ~$0.05

---

### 3.5 TECHNICAL ANALYST AGENT

**File**: `agents/technical_analyst.py`

**Responsibilities**:
1. Pattern detection (RHS, CWH, breakouts)
2. Technical indicator analysis (SMA, RSI, MACD)
3. **Coordinate with Backtest Validator** for strategy validation
4. Entry/exit price recommendations

**Workflow**:

```
┌─────────────────────────────────────────┐
│     TECHNICAL ANALYST WORKFLOW          │
└─────────────────────────────────────────┘

1. Fetch OHLCV Data (250 days)
   └── yfinance API

2. Detect Patterns
   ├── RHS (Reverse Head & Shoulder)
   ├── CWH (Cup with Handle)
   └── Breakout Patterns

3. Calculate Indicators
   ├── SMA 20, 50, 200
   ├── RSI (14)
   ├── MACD
   └── Volume Profile

4. For Each Detected Pattern:
   └── Request Backtest Validation
       ├── Backtest Validator runs 5-year simulation
       ├── Returns: Win Rate, Avg Return, Sample Size
       └── Approve if Win Rate ≥ 70%

5. Select Best Validated Strategy
   └── Max(Win Rate among validated strategies)

6. LLM Interpretation
   └── Assess setup quality, timing, risks

7. Calculate Technical Score
   └── 50% Backtest + 30% LLM + 20% Indicators
```

**Key Rule**: 🚨 **NO ENTRY WITHOUT VALIDATED BACKTEST** 🚨

**LLM Calls**:
1. **Technical Setup Interpretation**:
   - Model: GPT-4-Turbo
   - Input: Strategy details + indicators
   - Output: Setup quality score, strengths/risks
   - Tokens: ~5k in, ~1k out
   - Cost: ~$0.03

**Total Cost per Stock**: ~$0.03

---

### 3.6 BACKTEST VALIDATOR AGENT ⭐

**File**: `agents/backtest_validator.py`

**Responsibilities**:
1. Validate technical strategies via 5-year backtest
2. Calculate win rate, profit factor, drawdown
3. Apply 70% win rate threshold
4. Cache validated strategies (90-day TTL)
5. Use LLM for strategy rule extraction and result interpretation

**Validation Workflow**:

```
┌─────────────────────────────────────────────────────┐
│     BACKTEST VALIDATOR WORKFLOW                     │
└─────────────────────────────────────────────────────┘

INPUT: ticker="RELIANCE.NS", strategy="RHS_BREAKOUT"

1. Check Cache (Redis, 90-day TTL)
   ├── Cache Hit → Return cached result ($0)
   └── Cache Miss → Proceed to backtest

2. Fetch 5-Year Historical Data
   └── yfinance: 2020-10-07 to 2025-10-07

3. LLM: Extract Strategy Rules
   ├── Model: Claude-3.5-Sonnet
   ├── Input: High-level strategy description
   ├── Output: Precise backtest rules (JSON)
   └── Cost: ~$0.01

4. Run Historical Simulation
   ├── Scan 5 years for pattern occurrences
   ├── Execute trades on breakout
   ├── Exit at calculated targets
   └── Track: Entry, Exit, P&L, Hold Days

5. Calculate Metrics
   ├── Win Rate: 75% (12 wins / 16 trades)
   ├── Avg Return: +18.5%
   ├── Profit Factor: 2.3
   ├── Max Drawdown: -8.2%
   └── Sharpe Ratio: 1.8

6. LLM: Interpret Results
   ├── Model: GPT-4-Turbo
   ├── Input: Metrics + trade distribution
   ├── Output: Confidence score, insights
   └── Cost: ~$0.015

7. Apply Validation Rules
   ✅ Win Rate (75%) ≥ 70% threshold
   ✅ Sample Size (16) ≥ 10 minimum
   ✅ Profit Factor (2.3) ≥ 1.5
   ✅ VALIDATION PASSED

8. Cache Result (90 days)
   └── Redis: key=RELIANCE_NS_RHS_BREAKOUT

9. Save Detailed Report
   └── storage/backtest_validation/backtest_results/

OUTPUT: {validated: true, win_rate: 75.0, confidence: 85}
```

**Validation Rules**:

| Rule | Threshold | Purpose |
|------|-----------|---------|
| Win Rate | ≥ 70% | Minimum acceptable success rate |
| Sample Size | ≥ 10 trades | Statistical significance |
| Profit Factor | ≥ 1.5 | Gross profit > 1.5× gross loss |
| Max Drawdown | ≥ -25% | Risk tolerance |
| Avg Return | ≥ 10% | Minimum profit per trade |

**LLM Calls**:

1. **Strategy Rule Extraction**:
   - Model: Claude-3.5-Sonnet
   - Tokens: ~3k in, ~1.5k out
   - Cost: ~$0.01
   - Purpose: Convert strategy → executable rules

2. **Backtest Result Interpretation**:
   - Model: GPT-4-Turbo
   - Tokens: ~2k in, ~1k out
   - Cost: ~$0.015
   - Purpose: Contextual analysis beyond raw metrics

**Total Cost per Stock**:
- First time: ~$0.025
- Cached: $0.00

**Cache Hit Rate (After Month 1)**: ~70%

---

### 3.7 SENTIMENT ANALYST AGENT

**File**: `agents/sentiment_analyst.py`

**Responsibilities**:
1. News sentiment analysis (last 30 days)
2. Social media sentiment (Twitter, Reddit)
3. Analyst ratings and consensus
4. Institutional activity (FII/DII data for Indian stocks)

**Analysis Components**:

```
┌─────────────────────────────────────────┐
│     SENTIMENT ANALYST WORKFLOW          │
└─────────────────────────────────────────┘

1. News Sentiment (40% weight) [LLM-based]
   ├── Fetch: Last 30 days headlines
   ├── LLM Analysis: Claude-3.5-Haiku
   ├── Score: -100 to +100 (normalized to 0-100)
   └── Trend: IMPROVING/STABLE/DETERIORATING

2. Analyst Consensus (40% weight) [Rule-based]
   ├── Fetch: Latest ratings (Buy/Hold/Sell)
   ├── Calculate: (Buy% - Sell%) weighted score
   ├── Avg Target Price vs Current
   └── Recent Upgrades/Downgrades

3. Social Media Sentiment (20% weight) [LLM-based]
   ├── Fetch: Last 7 days (Twitter/Reddit)
   ├── LLM Analysis: Claude-3.5-Haiku
   ├── Volume Level: HIGH/MEDIUM/LOW
   └── Hype Detection: 0-100

Final Score = News × 0.4 + Analyst × 0.4 + Social × 0.2
```

**LLM Calls**:

1. **News Sentiment**:
   - Model: Claude-3.5-Haiku (fast, cheap)
   - Input: 20 recent headlines
   - Output: Sentiment score, trends, themes
   - Tokens: ~4k in, ~0.5k out
   - Cost: ~$0.004

2. **Social Media Sentiment**:
   - Model: Claude-3.5-Haiku
   - Input: 30 sample posts
   - Output: Sentiment score, volume, topics
   - Tokens: ~4k in, ~0.5k out
   - Cost: ~$0.004

**Total Cost per Stock**: ~$0.01

---

### 3.8 MANAGEMENT QUALITY ANALYST AGENT

**File**: `agents/management_analyst.py`

**Responsibilities**:
1. Parse conference call transcripts (last 12 quarters)
2. Parse annual reports (last 3 years)
3. Extract management promises and commitments
4. Correlate promises with actual performance
5. Analyze risk disclosures and margin decline explanations
6. Governance assessment

**Analysis Workflow** (Most LLM-Intensive):

```
┌─────────────────────────────────────────────────────┐
│     MANAGEMENT QUALITY ANALYST WORKFLOW             │
└─────────────────────────────────────────────────────┘

1. Fetch Documents
   ├── 12 Quarterly Conference Calls (3 years)
   └── 3 Annual Reports

2. LLM: Extract Management Promises
   ├── Model: Claude-3.5-Sonnet (200k context)
   ├── Input: 12 con-call transcripts (~100k tokens)
   ├── Output: List of specific commitments
   └── Cost: ~$0.50

   Example Promises:
   - "Launch 50 stores in FY23" (Q1FY23)
   - "Reduce debt by 20% in 2 years" (Q3FY22)
   - "EBITDA margin to reach 20%" (Q2FY23)

3. LLM: Extract Actual Performance
   ├── Model: GPT-4-Turbo (128k context)
   ├── Input: 3 annual reports (~100k tokens)
   ├── Output: Actual business metrics
   └── Cost: ~$0.65

   Example Actuals:
   - Launched 48 stores in FY23
   - Reduced debt by 22% in 2 years
   - EBITDA margin reached 19.5%

4. LLM: Correlate Promises vs Performance
   ├── Model: Claude-3.5-Sonnet
   ├── Input: Promises + Actual outcomes
   ├── Output: Credibility score (0-100)
   └── Cost: ~$0.08

   Analysis:
   - 9/10 promises met → Credibility = 90%

5. LLM: Risk Assessment
   ├── Model: GPT-4-Turbo
   ├── Input: Risk factors, MD&A sections
   ├── Output: Temporary vs structural issues
   └── Cost: ~$0.65

6. LLM: Governance Check
   ├── Model: Claude-3.5-Sonnet
   ├── Input: Governance section, RPTs, pledging
   ├── Output: Governance score, red flags
   └── Cost: ~$0.16

Final Score = Credibility × 0.5 + Risk × 0.25 + Governance × 0.25
```

**LLM Calls** (Most Expensive Agent):

1. **Promise Extraction**: ~$0.50
2. **Performance Extraction**: ~$0.65
3. **Promise-Performance Correlation**: ~$0.08
4. **Risk Analysis**: ~$0.65
5. **Governance Analysis**: ~$0.16

**Total Cost per Stock**:
- First time: ~$2.04
- Cached (90 days): ~$0.30 (incremental update)

**Cache Hit Rate (After Q1)**: ~85%

---

## 4. Data Flow Architecture

### 4.1 Complete System Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 1: DATA INGESTION                                             │
└─────────────────────────────────────────────────────────────────────┘

┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐
│ yfinance │      │Screener  │      │ NewsAPI  │      │ BSE/NSE  │
│ (OHLCV)  │      │ .in API  │      │ (News)   │      │ (Docs)   │
└────┬─────┘      └────┬─────┘      └────┬─────┘      └────┬─────┘
     │                 │                  │                  │
     └─────────────────┴──────────────────┴──────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │  DATA FETCHERS    │
                    │  (Tool Layer)     │
                    └─────────┬─────────┘
                              │
     ┌────────────────────────┼────────────────────────┐
     │                        │                        │
┌────▼─────┐         ┌───────▼────────┐      ┌───────▼────────┐
│ Parquet  │         │   PostgreSQL   │      │    S3/MinIO    │
│ Files    │         │   (Metadata)   │      │  (Documents)   │
│ (OHLCV)  │         └────────────────┘      │  (PDFs, TXT)   │
└──────────┘                                  └────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 2: AGENT ANALYSIS (Parallel Execution)                        │
└─────────────────────────────────────────────────────────────────────┘

         ┌────────────────────────────────────┐
         │    ORCHESTRATOR TRIGGERS AGENTS    │
         │    for ticker="RELIANCE.NS"        │
         └────────────────┬───────────────────┘
                          │
      ┌───────────────────┼───────────────────┬──────────────┐
      │                   │                   │              │
┌─────▼──────┐    ┌──────▼────────┐    ┌────▼──────┐  ┌───▼─────┐
│Fundamental │    │   Technical   │    │ Sentiment │  │  Mgmt   │
│  Analyst   │    │    Analyst    │    │  Analyst  │  │ Quality │
└─────┬──────┘    └──────┬────────┘    └────┬──────┘  └───┬─────┘
      │                  │                   │             │
      │            ┌─────▼─────┐            │             │
      │            │ Backtest  │            │             │
      │            │ Validator │            │             │
      │            └─────┬─────┘            │             │
      │                  │                   │             │
      │            [Cache Check]            │             │
      │            ┌─────▼─────┐            │             │
      │            │   Redis   │            │             │
      │            │  (90-day) │            │             │
      │            └───────────┘            │             │
      │                                     │             │
      └─────────────────┬───────────────────┴─────────────┘
                        │
                        │ All Agent Results Collected
                        │
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 3: DECISION SYNTHESIS                                         │
└─────────────────────────────────────────────────────────────────────┘

                  ┌────────────────┐
                  │  ORCHESTRATOR  │
                  │   SYNTHESIS    │
                  └────────┬───────┘
                           │
                  ┌────────▼────────┐
                  │  Check Vetos    │
                  │  ✅ Fund ≥ 50   │
                  │  ✅ Mgmt ≥ 40   │
                  │  ✅ Tech Valid  │
                  │  ✅ WR ≥ 70%    │
                  └────────┬────────┘
                           │
                  ┌────────▼────────┐
                  │ Composite Score │
                  │  = 82.5/100     │
                  └────────┬────────┘
                           │
                  ┌────────▼────────┐
                  │ Decision Logic  │
                  │ STRONG BUY (5%) │
                  └────────┬────────┘
                           │
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 4: EXECUTION & LOGGING                                        │
└─────────────────────────────────────────────────────────────────────┘

                  ┌────────────────┐
                  │   EXECUTION    │
                  │     AGENT      │
                  └────────┬───────┘
                           │
                  ┌────────▼────────┐
                  │ Execute Trade   │
                  │ BUY RELIANCE.NS │
                  │ 20 shares @ 2505│
                  └────────┬────────┘
                           │
                  ┌────────▼────────┐
                  │  Log Decision   │
                  │  PostgreSQL DB  │
                  │  (Audit Trail)  │
                  └─────────────────┘
```

### 4.2 Daily Workflow Example

**Scenario**: Analyze RELIANCE.NS at market open

```
09:15 AM - Market Open
├── Orchestrator receives trigger
├── Load watchlist (50 stocks)
└── For RELIANCE.NS:

09:15:30 - Parallel Agent Dispatch
├── Fundamental Analyst START
├── Technical Analyst START
├── Sentiment Analyst START
└── Management Analyst START

09:16:00 - Fundamental Analysis Complete
└── Score: 80/100 (Strong financials, 25% CAGR)

09:16:15 - Technical Analysis (with Backtest)
├── Pattern Detected: RHS breakout
├── Request to Backtest Validator
│   ├── Cache Check: MISS
│   ├── Fetch 5Y data: 1,250 bars
│   ├── LLM: Extract rules (~15 sec)
│   ├── Simulate: 16 trades found
│   ├── Win Rate: 75% ✅
│   ├── LLM: Interpret (~10 sec)
│   └── APPROVED (cached 90 days)
└── Score: 85/100 (Validated, 75% WR)

09:16:45 - Sentiment Analysis Complete
└── Score: 70/100 (Positive news, analyst upgrades)

09:18:30 - Management Analysis Complete
├── Cache Check: HIT (analyzed 45 days ago)
└── Score: 90/100 (High credibility, low risk)

09:18:31 - Orchestrator Synthesis
├── Veto Check: ✅ All passed
├── Composite: (80×0.3 + 85×0.3 + 70×0.2 + 90×0.2) = 82.5
├── Decision: STRONG BUY
└── Position: 5%

09:18:32 - Execution
├── Order: BUY 20 shares @ market
├── Filled: 20 @ ₹2,505
└── Logged: PostgreSQL + Trade CSV

Total Time: ~3 minutes (with backtest)
Total Time (cached): ~30 seconds
```

### 4.3 Data Storage Structure

```
storage/
├── market_data/
│   ├── ohlcv/
│   │   ├── RELIANCE_NS_5y.parquet       # 5-year historical
│   │   ├── INFY_NS_5y.parquet
│   │   └── index.db                      # SQLite metadata
│   │
│   └── fundamentals/
│       ├── RELIANCE_NS_financials.json
│       └── RELIANCE_NS_peers.json
│
├── documents/
│   ├── annual_reports/
│   │   ├── RELIANCE_NS_2023.pdf
│   │   ├── RELIANCE_NS_2022.pdf
│   │   └── RELIANCE_NS_2021.pdf
│   │
│   ├── concalls/
│   │   ├── RELIANCE_NS_Q1FY24.txt
│   │   ├── RELIANCE_NS_Q2FY24.txt
│   │   └── ... (12 quarters)
│   │
│   └── processed/
│       ├── RELIANCE_NS_promises.json     # Extracted promises
│       └── RELIANCE_NS_mgmt_analysis.json
│
├── backtest_validation/
│   ├── cache/                            # Redis backup
│   │   ├── RELIANCE_NS_RHS_BREAKOUT.json
│   │   ├── RELIANCE_NS_CWH_BREAKOUT.json
│   │   └── index.db
│   │
│   ├── historical_data/                  # Symlink to market_data/ohlcv
│   │
│   └── backtest_results/                 # Detailed reports
│       ├── RELIANCE_NS_RHS_20251007/
│       │   ├── trades.csv                # All 16 historical trades
│       │   ├── metrics.json              # Performance metrics
│       │   ├── equity_curve.png          # Visualization
│       │   └── llm_analysis.json         # LLM insights
│       └── ...
│
├── agent_state/
│   ├── portfolio.json                    # Current positions
│   ├── watchlist.json                    # Stocks under consideration
│   ├── analysis_cache/                   # Agent results (24hr TTL)
│   │   ├── RELIANCE_NS_fundamental_20251007.json
│   │   └── RELIANCE_NS_technical_20251007.json
│   │
│   └── decisions_log.db                  # PostgreSQL
│       ├── Table: decisions
│       │   ├── id, timestamp, ticker
│       │   ├── decision (BUY/SELL/HOLD)
│       │   ├── composite_score
│       │   ├── agent_scores (JSON)
│       │   └── reasoning (TEXT)
│       │
│       └── Table: trades
│           ├── id, timestamp, ticker
│           ├── action (BUY/SELL)
│           ├── price, quantity
│           └── decision_id (FK)
│
└── logs/
    ├── orchestrator_20251007.log
    ├── fundamental_analyst_20251007.log
    └── ... (agent-specific logs)
```

---

## 5. LLM Strategy & Cost Estimation

### 5.1 LLM Call Summary by Agent

| Agent | LLM Calls | Models | Cost/Stock (First) | Cost/Stock (Cached) |
|-------|-----------|--------|-------------------|---------------------|
| **Orchestrator** | 1-2 | GPT-4 | $0.05 | $0.05 |
| **Fundamental** | 2 | Claude-3.5 + GPT-4 | $0.05 | $0.05 |
| **Technical** | 1 | GPT-4 | $0.03 | $0.03 |
| **Backtest Validator** | 2 | Claude-3.5 + GPT-4 | $0.025 | $0.00 |
| **Sentiment** | 2 | Claude-Haiku | $0.01 | $0.01 |
| **Management** | 5 | Claude-3.5 + GPT-4 | $2.04 | $0.30 |
| **TOTAL** | **13-15** | **Mixed** | **$2.20** | **$0.44** |

### 5.2 Monthly Cost Projection (50 Stocks Daily)

**Month 1** (No cache):
- Daily: 50 stocks × $2.20 = $110/day
- Monthly: $110 × 22 trading days = **$2,420**

**Month 2+** (70% cache hit on backtest, 85% on management):
- Backtest cache savings: 50 × 0.70 × $0.025 = $0.875/day saved
- Management cache savings: 50 × 0.85 × $1.74 = $73.95/day saved
- Daily: 50 stocks × $0.44 (avg) = $22/day
- Monthly: $22 × 22 trading days = **$484**

**Annual Cost**:
- Year 1: $2,420 + ($484 × 11) = **~$7,744**
- Year 2+: $484 × 12 = **~$5,808**

### 5.3 Cost Optimization Strategies

**1. Caching Layer**:
```python
# Redis cache with TTL
cache_ttl = {
    'backtest_validation': 90,    # 90 days
    'management_analysis': 90,    # 90 days (quarterly refresh)
    'fundamental_analysis': 7,    # 7 days (weekly)
    'technical_analysis': 1,      # 1 day (daily patterns change)
    'sentiment_analysis': 1       # 1 day (news changes daily)
}
```

**2. Incremental Updates**:
- Management: Only re-analyze on earnings release or annual report
- Backtest: Only re-validate on strategy parameter changes
- Fundamental: Only re-fetch on quarterly results

**3. Batch Processing**:
- Analyze multiple stocks in single LLM call where possible
- Example: "Analyze sentiment for these 10 stocks..." (not implemented yet, future optimization)

**4. Model Selection**:
- Use cheaper models (Haiku) for simpler tasks (sentiment)
- Reserve expensive models (GPT-4) for complex reasoning
- Use Claude-3.5-Sonnet for long context (con-calls, reports)

**5. Token Optimization**:
- Compress prompts (remove redundant instructions)
- Truncate documents to relevant sections only
- Use structured outputs (JSON) to reduce token usage

### 5.4 Model Selection Matrix

| Task Type | Complexity | Context Length | Best Model | Cost/1M Tokens |
|-----------|-----------|----------------|------------|----------------|
| **Long Documents** (Annual Reports, Con-calls) | High | 100k-200k | Claude-3.5-Sonnet | $3.00 in / $15.00 out |
| **Complex Reasoning** (Synthesis, Correlation) | High | <128k | GPT-4-Turbo | $10.00 in / $30.00 out |
| **Fast Analysis** (Sentiment, News) | Low-Medium | <50k | Claude-3.5-Haiku | $0.80 in / $4.00 out |
| **Structured Output** (Strategy Rules) | Medium | <20k | Claude-3.5-Sonnet | $3.00 in / $15.00 out |

### 5.5 Cost-Benefit Analysis

**Comparison: Agentic System vs Buy & Hold**

| Metric | Agentic System | Buy & Hold |
|--------|---------------|------------|
| **CAGR** | 18-22% (target) | 30% (V40 baseline) |
| **Annual LLM Cost** | $5,808 | $0 |
| **Infrastructure Cost** | $2,000 | $0 |
| **Total Cost** | $7,808/year | $0 |
| **Management Time** | 2-3 hrs/week | 0 hrs |
| **Break-even Capital** | ~₹5,00,000 | N/A |

**Break-even Analysis**:
- If system improves returns by 5% over buy & hold
- On ₹5,00,000 capital: 5% = ₹25,000 extra gain
- Cost: ₹7,808
- Net benefit: ₹17,192

**Conclusion**: System is cost-effective for portfolios > ₹5L

---

## 6. Tools & Technologies

### 6.1 Complete Technology Stack

```
┌─────────────────────────────────────────────────────────────────────┐
│                       TECHNOLOGY STACK                               │
└─────────────────────────────────────────────────────────────────────┘

LANGUAGES & FRAMEWORKS
├── Python 3.11+                    Core language
├── FastAPI                         REST API endpoints
├── Streamlit / Gradio              Dashboard UI
└── Docker / Docker Compose         Containerization

AGENT ORCHESTRATION
├── LangGraph                       State machine for agents
├── LangChain                       LLM integration & prompts
└── asyncio                         Async agent execution

LLM PROVIDERS
├── Anthropic Claude-3.5-Sonnet     Long context (200k tokens)
├── Anthropic Claude-3.5-Haiku      Fast sentiment analysis
└── OpenAI GPT-4-Turbo              Complex reasoning (128k)

DATA MANAGEMENT
├── PostgreSQL                      Agent state, decisions, trades
├── Redis                           Backtest cache (90-day TTL)
├── Parquet (PyArrow)               OHLCV historical data
└── S3 / MinIO                      Document storage (PDFs)

BACKTESTING & TECHNICAL ANALYSIS
├── Backtrader                      Backtesting framework (existing)
├── TA-Lib / pandas-ta              Technical indicators
├── scipy                           Pattern detection (find_peaks)
└── numpy / pandas                  Data manipulation

DATA SOURCES & APIs
├── yfinance                        Market data (OHLCV)
├── Screener.in API (unofficial)    Indian stock fundamentals
├── NewsAPI / Google News           News aggregation
├── Twitter API (X API)             Social sentiment
├── Reddit API (PRAW)               Reddit sentiment
└── BSE/NSE APIs                    Official exchange data

DOCUMENT PROCESSING
├── PyPDF2 / pdfplumber             PDF parsing (annual reports)
├── BeautifulSoup4                  HTML parsing (web scraping)
├── Camelot / Tabula                Table extraction from PDFs
└── Tesseract (optional)            OCR for scanned documents

MONITORING & LOGGING
├── Python logging                  Application logs
├── Prometheus (optional)           Metrics collection
├── Grafana (optional)              Metrics visualization
└── Sentry (optional)               Error tracking

DEPLOYMENT
├── GitHub Actions                  CI/CD pipeline
├── AWS / GCP / DigitalOcean        Cloud hosting
└── Nginx                           Reverse proxy

TESTING
├── pytest                          Unit & integration tests
├── pytest-asyncio                  Async test support
└── unittest.mock                   Mocking for LLM calls
```

### 6.2 File Structure

```
agentic_trading_system/
│
├── agents/
│   ├── __init__.py
│   ├── base_agent.py                 # Abstract base class
│   ├── orchestrator.py               # Master coordinator
│   ├── fundamental_analyst.py        # Financial analysis
│   ├── technical_analyst.py          # Pattern detection
│   ├── backtest_validator.py         # Strategy validation ⭐
│   ├── sentiment_analyst.py          # Market sentiment
│   ├── management_analyst.py         # Con-calls, annual reports
│   └── execution_agent.py            # Trade executor
│
├── tools/
│   ├── data_fetchers/
│   │   ├── __init__.py
│   │   ├── market_data.py            # yfinance wrapper
│   │   ├── fundamental_data.py       # Screener.in integration
│   │   ├── news_fetcher.py           # NewsAPI wrapper
│   │   ├── social_fetcher.py         # Twitter/Reddit APIs
│   │   └── document_fetcher.py       # PDF downloads (BSE/NSE)
│   │
│   ├── analyzers/
│   │   ├── __init__.py
│   │   ├── technical_indicators.py   # TA-Lib wrapper
│   │   ├── pattern_detector.py       # RHS, CWH detection
│   │   ├── backtest_engine.py        # Historical simulation
│   │   ├── strategy_simulator.py     # Strategy-specific backtests
│   │   ├── metrics_calculator.py     # Win rate, profit factor
│   │   └── financial_ratios.py       # DCF, ROCE, ROE
│   │
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── llm_client.py             # OpenAI + Anthropic wrapper
│   │   ├── prompts.py                # Prompt templates
│   │   ├── backtest_prompts.py       # Backtest-specific prompts
│   │   └── document_processor.py     # PDF parsing, chunking
│   │
│   └── caching/
│       ├── __init__.py
│       ├── backtest_cache.py         # Redis cache manager
│       └── redis_client.py           # Redis connection pool
│
├── orchestration/
│   ├── __init__.py
│   ├── langgraph_workflow.py         # LangGraph state machine
│   ├── state_manager.py              # Agent state tracking
│   └── decision_logger.py            # Audit trail (PostgreSQL)
│
├── storage/
│   ├── market_data/                  # Parquet files
│   ├── documents/                    # PDFs, transcripts
│   ├── backtest_validation/          # Validation cache & reports
│   └── agent_state/                  # Portfolio, decisions
│
├── config/
│   ├── agent_config.yaml             # Agent parameters
│   ├── llm_config.yaml               # Model selection, API keys
│   ├── backtest_config.yaml          # Validation rules
│   └── trading_config.yaml           # Position limits, thresholds
│
├── api/
│   ├── __init__.py
│   ├── main.py                       # FastAPI app
│   ├── routes.py                     # API endpoints
│   └── schemas.py                    # Pydantic models
│
├── ui/
│   ├── dashboard.py                  # Streamlit dashboard
│   └── components/                   # UI components
│
├── backtest/
│   ├── __init__.py
│   ├── agentic_backtest_engine.py    # Run agents on historical data
│   └── performance_analyzer.py       # Compare with V40
│
├── scripts/
│   ├── run_daily_analysis.py         # Daily stock screening
│   ├── backtest_agentic_system.py    # Historical backtest
│   ├── refresh_backtest_cache.py     # Quarterly cache refresh
│   └── setup_database.py             # Initialize PostgreSQL
│
├── tests/
│   ├── unit/                         # Unit tests
│   ├── integration/                  # Integration tests
│   └── mocks/                        # Mock LLM responses
│
├── docker/
│   ├── Dockerfile                    # Application container
│   ├── docker-compose.yml            # Multi-container setup
│   └── docker-compose.dev.yml        # Development setup
│
├── .github/
│   └── workflows/
│       ├── ci.yml                    # CI pipeline
│       └── deploy.yml                # Deployment pipeline
│
├── requirements.txt                  # Python dependencies
├── requirements-dev.txt              # Development dependencies
├── setup.py                          # Package setup
├── .env.example                      # Environment variables template
├── .gitignore
└── README.md
```

### 6.3 Key Dependencies (requirements.txt)

```txt
# Core Framework
python>=3.11
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.4.0
pydantic-settings>=2.0.0

# Agent Orchestration
langgraph>=0.0.40
langchain>=0.1.0
langchain-anthropic>=0.1.0
langchain-openai>=0.0.5

# LLM Providers
anthropic>=0.18.0
openai>=1.12.0

# Data Management
psycopg2-binary>=2.9.9
redis>=5.0.0
pyarrow>=14.0.0
pandas>=2.1.0
numpy>=1.24.0

# Backtesting & Technical Analysis
backtrader>=1.9.78
ta-lib>=0.4.28
scipy>=1.11.0

# Data Sources
yfinance>=0.2.32
beautifulsoup4>=4.12.0
requests>=2.31.0
aiohttp>=3.9.0

# Document Processing
PyPDF2>=3.0.0
pdfplumber>=0.10.0
camelot-py[cv]>=0.11.0
python-dateutil>=2.8.0

# API Integration
newsapi-python>=0.2.7
tweepy>=4.14.0
praw>=7.7.0

# Async Support
asyncio
aiofiles>=23.2.0

# UI (Optional)
streamlit>=1.29.0
plotly>=5.18.0
matplotlib>=3.8.0

# Monitoring & Logging
python-json-logger>=2.0.7
sentry-sdk>=1.39.0

# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
pytest-mock>=3.12.0

# Development
black>=23.11.0
flake8>=6.1.0
mypy>=1.7.0
ipython>=8.18.0
```

### 6.4 Environment Variables (.env.example)

```bash
# LLM API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Data APIs
NEWS_API_KEY=...
TWITTER_API_KEY=...
TWITTER_API_SECRET=...
REDDIT_CLIENT_ID=...
REDDIT_CLIENT_SECRET=...

# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=agentic_trading
POSTGRES_USER=trading_user
POSTGRES_PASSWORD=secure_password

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# Storage
S3_BUCKET=agentic-trading-docs
S3_ACCESS_KEY=...
S3_SECRET_KEY=...

# Trading Configuration
INITIAL_CASH=100000
MAX_POSITION_SIZE=0.05
MAX_CONCURRENT_POSITIONS=10

# Monitoring
SENTRY_DSN=https://...
LOG_LEVEL=INFO

# Development
DEBUG=True
```

---

## 7. Implementation Roadmap

### 7.1 Phase-wise Implementation (11 Weeks)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    IMPLEMENTATION TIMELINE                           │
└─────────────────────────────────────────────────────────────────────┘

WEEK 1-2: FOUNDATION
├── Set up project structure
├── Configure development environment (Docker, PostgreSQL, Redis)
├── Implement base agent class
├── Build LLM client wrapper (OpenAI + Anthropic)
├── Create data fetchers (yfinance, Screener.in)
├── Set up logging and error handling
└── Milestone: Base infrastructure ready

WEEK 3: BACKTEST VALIDATOR ⭐ (CRITICAL PATH)
├── Build historical backtester engine
├── Implement strategy simulator (RHS, CWH, Golden Cross)
├── Create metrics calculator (win rate, profit factor)
├── Implement LLM-based strategy rule extraction
├── Implement LLM-based result interpretation
├── Build Redis caching layer (90-day TTL)
├── Test on existing V40 strategies for baseline
└── Milestone: Backtest validation working

WEEK 4: FUNDAMENTAL ANALYST
├── Build financial data fetcher (Screener.in API)
├── Implement financial health calculator (ROCE, ROE, Debt)
├── Implement growth analyzer (CAGR, consistency)
├── Implement LLM-based valuation analysis
├── Implement LLM-based red flag detection
├── Unit tests for all components
└── Milestone: Fundamental analysis working

WEEK 5: TECHNICAL ANALYST
├── Implement pattern detector (RHS, CWH, breakouts)
├── Build technical indicator calculator (SMA, RSI, MACD)
├── Integrate with Backtest Validator
├── Implement LLM-based setup interpretation
├── Build entry/exit price calculator
├── Unit tests
└── Milestone: Technical analysis + validation working

WEEK 6: SENTIMENT & MANAGEMENT ANALYSTS
├── Build news fetcher (NewsAPI, web scraping)
├── Build social media fetcher (Twitter, Reddit)
├── Implement LLM-based news sentiment analysis
├── Implement LLM-based social sentiment analysis
├── Build analyst data fetcher
├── Implement document fetcher (annual reports, con-calls)
├── Build PDF parser
├── Implement LLM-based management analysis (all 5 steps)
└── Milestone: All analysts operational

WEEK 7: ORCHESTRATOR
├── Implement agent coordinator
├── Build veto check logic
├── Implement composite score calculator
├── Build decision framework (thresholds)
├── Implement LLM-based synthesis for borderline cases
├── Build portfolio manager
├── Integration tests across all agents
└── Milestone: End-to-end workflow complete

WEEK 8: BACKTESTING & VALIDATION
├── Build agentic backtest engine (run on historical data)
├── Run 2-year backtest (Oct 2023 - Oct 2025)
├── Compare with V40 Validated Strategy
├── Analyze performance metrics
├── Optimize agent weights and thresholds
├── Test edge cases and error handling
└── Milestone: System validated on historical data

WEEK 9: API & UI
├── Build FastAPI REST endpoints
│   ├── POST /analyze/{ticker}
│   ├── GET /decisions
│   ├── GET /portfolio
│   └── GET /backtest_results
├── Build Streamlit dashboard
│   ├── Live analysis view
│   ├── Portfolio overview
│   ├── Decision history
│   └── Performance charts
├── Implement authentication & authorization
└── Milestone: API and UI ready

WEEK 10: DEPLOYMENT PREP
├── Containerize application (Docker)
├── Set up CI/CD pipeline (GitHub Actions)
├── Configure production database (PostgreSQL)
├── Set up Redis cluster (production)
├── Configure S3/MinIO for document storage
├── Set up monitoring (logs, metrics)
├── Load testing and performance optimization
└── Milestone: Production-ready

WEEK 11: PRODUCTION DEPLOYMENT & MONITORING
├── Deploy to cloud (AWS/GCP)
├── Configure domain and SSL
├── Set up automated backups
├── Implement alerting (email, Telegram)
├── Run paper trading for 1 week
├── Monitor LLM costs and cache hit rates
├── Fine-tune parameters based on live data
└── Milestone: System live in production
```

### 7.2 Detailed Task Breakdown

**WEEK 1-2: Foundation**

| Task | Time | Priority | Dependencies |
|------|------|----------|--------------|
| Project structure setup | 0.5d | HIGH | None |
| Docker compose setup (PostgreSQL, Redis) | 1d | HIGH | None |
| Base agent class | 1d | HIGH | None |
| LLM client wrapper (OpenAI) | 1d | HIGH | None |
| LLM client wrapper (Anthropic) | 0.5d | HIGH | LLM client |
| Market data fetcher (yfinance) | 1d | HIGH | None |
| Fundamental data fetcher (Screener.in) | 2d | MEDIUM | None |
| Logging & error handling | 1d | HIGH | None |
| Unit tests for base components | 1d | MEDIUM | All above |

**WEEK 3: Backtest Validator (CRITICAL)**

| Task | Time | Priority | Dependencies |
|------|------|----------|--------------|
| Historical data fetcher (5 years) | 0.5d | HIGH | Market data fetcher |
| Strategy simulator base class | 1d | HIGH | None |
| RHS pattern simulator | 1d | HIGH | Simulator base |
| CWH pattern simulator | 1d | HIGH | Simulator base |
| Golden Cross simulator | 0.5d | HIGH | Simulator base |
| Metrics calculator | 1d | HIGH | None |
| LLM strategy rule extraction | 1d | HIGH | LLM client |
| LLM result interpretation | 1d | HIGH | LLM client |
| Redis cache implementation | 1d | HIGH | Redis setup |
| Integration testing | 1d | HIGH | All above |

**WEEK 4: Fundamental Analyst**

| Task | Time | Priority | Dependencies |
|------|------|----------|--------------|
| Financial health calculator | 1d | HIGH | Fundamental fetcher |
| Growth analyzer | 1d | HIGH | Fundamental fetcher |
| LLM valuation analysis | 1d | HIGH | LLM client |
| LLM red flag detection | 1d | HIGH | LLM client |
| Composite score calculator | 0.5d | HIGH | All above |
| Unit tests | 0.5d | MEDIUM | All above |

**WEEK 5: Technical Analyst**

| Task | Time | Priority | Dependencies |
|------|------|----------|--------------|
| Pattern detector (RHS, CWH) | 1.5d | HIGH | scipy |
| Technical indicators (SMA, RSI, MACD) | 1d | HIGH | TA-Lib |
| Backtest Validator integration | 1d | HIGH | Week 3 |
| LLM setup interpretation | 1d | HIGH | LLM client |
| Entry/exit calculator | 0.5d | HIGH | All above |
| Unit tests | 1d | MEDIUM | All above |

**WEEK 6: Sentiment & Management**

| Task | Time | Priority | Dependencies |
|------|------|----------|--------------|
| News fetcher (NewsAPI) | 0.5d | MEDIUM | None |
| Social media fetcher | 1d | MEDIUM | Twitter/Reddit APIs |
| LLM news sentiment | 1d | MEDIUM | LLM client |
| LLM social sentiment | 0.5d | MEDIUM | LLM client |
| Analyst data fetcher | 0.5d | MEDIUM | None |
| Document fetcher (PDFs) | 1d | HIGH | BSE/NSE access |
| PDF parser | 1d | HIGH | PyPDF2 |
| LLM promise extraction | 1d | HIGH | LLM client |
| LLM performance extraction | 0.5d | HIGH | LLM client |
| LLM promise-performance correlation | 0.5d | HIGH | LLM client |
| LLM risk assessment | 0.5d | HIGH | LLM client |
| LLM governance analysis | 0.5d | HIGH | LLM client |

**WEEK 7: Orchestrator**

| Task | Time | Priority | Dependencies |
|------|------|----------|--------------|
| Agent coordinator | 1d | HIGH | All agents |
| Veto check logic | 0.5d | HIGH | Agent coordinator |
| Composite score calculator | 0.5d | HIGH | All agents |
| Decision framework | 1d | HIGH | Score calculator |
| LLM synthesis for borderline | 1d | MEDIUM | LLM client |
| Portfolio manager | 1d | HIGH | None |
| Integration tests | 1d | HIGH | All above |

**WEEK 8: Backtesting**

| Task | Time | Priority | Dependencies |
|------|------|----------|--------------|
| Agentic backtest engine | 2d | HIGH | All agents |
| Run 2-year backtest | 1d | HIGH | Backtest engine |
| Performance analysis | 1d | HIGH | Backtest results |
| Compare with V40 | 0.5d | HIGH | V40 results |
| Parameter optimization | 1d | MEDIUM | Analysis |
| Edge case testing | 0.5d | MEDIUM | All above |

**WEEK 9: API & UI**

| Task | Time | Priority | Dependencies |
|------|------|----------|--------------|
| FastAPI app setup | 0.5d | HIGH | None |
| API endpoints | 1.5d | HIGH | All agents |
| Pydantic schemas | 0.5d | HIGH | API endpoints |
| Authentication | 1d | MEDIUM | FastAPI |
| Streamlit dashboard | 2d | MEDIUM | API |
| UI components | 1d | MEDIUM | Dashboard |
| API tests | 0.5d | MEDIUM | All above |

**WEEK 10: Deployment Prep**

| Task | Time | Priority | Dependencies |
|------|------|----------|--------------|
| Dockerfile | 1d | HIGH | All code |
| Docker compose prod | 0.5d | HIGH | Dockerfile |
| CI/CD pipeline | 1.5d | HIGH | GitHub |
| Production database setup | 0.5d | HIGH | PostgreSQL |
| Redis cluster | 0.5d | HIGH | Redis |
| S3/MinIO setup | 0.5d | MEDIUM | AWS/GCP |
| Monitoring setup | 1d | MEDIUM | Logs |
| Load testing | 1d | MEDIUM | All above |

**WEEK 11: Production**

| Task | Time | Priority | Dependencies |
|------|------|----------|--------------|
| Cloud deployment | 1d | HIGH | Week 10 |
| Domain & SSL | 0.5d | HIGH | Deployment |
| Backup configuration | 0.5d | HIGH | Database |
| Alerting setup | 1d | MEDIUM | Monitoring |
| Paper trading (1 week) | 5d | HIGH | All above |
| Cost monitoring | Ongoing | HIGH | LLM calls |
| Parameter tuning | Ongoing | MEDIUM | Live data |

### 7.3 Critical Path

```
Base Infrastructure (Week 1-2)
    ↓
Backtest Validator (Week 3) ⭐ CRITICAL
    ↓
Technical Analyst (Week 5) [depends on Week 3]
    ↓
Orchestrator (Week 7) [depends on all agents]
    ↓
System Backtest (Week 8) [depends on Week 7]
    ↓
Production (Week 10-11)
```

**Critical Path Duration**: 8 weeks minimum

**Parallel Tracks**:
- Week 4 (Fundamental) can run parallel to Week 5 (Technical)
- Week 6 (Sentiment + Management) can run parallel to Week 5
- Week 9 (API/UI) can start during Week 8

---

## 8. Testing Strategy

### 8.1 Testing Pyramid

```
                    ┌─────────────────┐
                    │   E2E Tests     │  5%
                    │  (Full workflow)│
                    └─────────────────┘
                ┌───────────────────────┐
                │  Integration Tests    │  15%
                │  (Agent interactions) │
                └───────────────────────┘
           ┌──────────────────────────────┐
           │      Unit Tests              │  80%
           │  (Individual components)     │
           └──────────────────────────────┘
```

### 8.2 Unit Tests (80% coverage target)

**Test Files**:

```
tests/
├── unit/
│   ├── agents/
│   │   ├── test_base_agent.py
│   │   ├── test_orchestrator.py
│   │   ├── test_fundamental_analyst.py
│   │   ├── test_technical_analyst.py
│   │   ├── test_backtest_validator.py
│   │   ├── test_sentiment_analyst.py
│   │   └── test_management_analyst.py
│   │
│   ├── tools/
│   │   ├── test_data_fetchers.py
│   │   ├── test_pattern_detector.py
│   │   ├── test_backtest_engine.py
│   │   ├── test_metrics_calculator.py
│   │   └── test_llm_client.py
│   │
│   └── orchestration/
│       ├── test_langgraph_workflow.py
│       └── test_decision_logger.py
```

**Example Unit Test**:

```python
# tests/unit/agents/test_backtest_validator.py

import pytest
from unittest.mock import Mock, patch, AsyncMock
from agents.backtest_validator import BacktestValidatorAgent

@pytest.fixture
def backtest_validator():
    config = {'llm': {'provider': 'openai', 'model': 'gpt-4'}}
    return BacktestValidatorAgent(config)

@pytest.mark.asyncio
async def test_validate_strategy_cache_hit(backtest_validator):
    """Test that cached validation results are returned"""

    # Mock cache hit
    cached_result = {
        'validated': True,
        'win_rate': 75.0,
        'confidence_score': 85
    }
    backtest_validator.cache.get = AsyncMock(return_value=cached_result)

    result = await backtest_validator.validate_strategy(
        ticker='RELIANCE.NS',
        strategy_name='RHS_BREAKOUT',
        strategy_params={}
    )

    assert result['validated'] == True
    assert result['win_rate'] == 75.0
    assert result['confidence_score'] == 85

@pytest.mark.asyncio
async def test_validate_strategy_insufficient_data(backtest_validator):
    """Test rejection when insufficient historical data"""

    # Mock cache miss
    backtest_validator.cache.get = AsyncMock(return_value=None)

    # Mock data fetch returning insufficient data
    backtest_validator.data_fetcher.fetch_ohlcv = AsyncMock(
        return_value=pd.DataFrame({'Close': [100, 101, 102]})  # Only 3 rows
    )

    result = await backtest_validator.validate_strategy(
        ticker='NEWSTOCK.NS',
        strategy_name='RHS_BREAKOUT',
        strategy_params={}
    )

    assert result['validated'] == False
    assert 'Insufficient' in result['reason']

@pytest.mark.asyncio
async def test_validate_strategy_below_threshold(backtest_validator):
    """Test rejection when win rate < 70%"""

    # Mock full backtest flow
    backtest_validator.cache.get = AsyncMock(return_value=None)
    backtest_validator.data_fetcher.fetch_ohlcv = AsyncMock(
        return_value=pd.DataFrame({'Close': range(1000)})  # Sufficient data
    )

    # Mock LLM rule extraction
    backtest_validator.llm_extract_strategy_rules = AsyncMock(
        return_value={'entry': {}, 'exit': {}}
    )

    # Mock backtest with low win rate
    backtest_validator.backtester.simulate_strategy = Mock(
        return_value=[
            {'pnl_pct': 10, 'hold_days': 30},  # Win
            {'pnl_pct': -5, 'hold_days': 20},  # Loss
            {'pnl_pct': -3, 'hold_days': 15},  # Loss
            # Win rate = 33% < 70%
        ]
    )

    backtest_validator.llm_interpret_backtest = AsyncMock(
        return_value={'confidence_score': 40}
    )

    result = await backtest_validator.validate_strategy(
        ticker='LOWWIN.NS',
        strategy_name='RHS_BREAKOUT',
        strategy_params={}
    )

    assert result['validated'] == False
    assert 'win_rate' in result['validation_checks']
    assert result['validation_checks']['win_rate']['passed'] == False
```

### 8.3 Integration Tests (15%)

**Test Scenarios**:

```python
# tests/integration/test_full_workflow.py

@pytest.mark.asyncio
async def test_full_analysis_workflow():
    """Test complete workflow from trigger to decision"""

    orchestrator = OrchestratorAgent(config)

    # Mock agent responses
    orchestrator.agents['fundamental'].analyze = AsyncMock(
        return_value={'score': 80}
    )
    orchestrator.agents['technical'].analyze = AsyncMock(
        return_value={
            'score': 85,
            'backtest_validated': True,
            'historical_win_rate': 75.0
        }
    )
    orchestrator.agents['sentiment'].analyze = AsyncMock(
        return_value={'score': 70}
    )
    orchestrator.agents['management'].analyze = AsyncMock(
        return_value={'score': 90}
    )

    result = await orchestrator.analyze_stock('RELIANCE.NS')

    assert result['decision'] == 'STRONG_BUY'
    assert result['composite_score'] > 80
    assert result['position_size_pct'] == 0.05

@pytest.mark.asyncio
async def test_veto_mechanism():
    """Test that veto rules are enforced"""

    orchestrator = OrchestratorAgent(config)

    # Set up scenario where backtest validation fails
    orchestrator.agents['fundamental'].analyze = AsyncMock(
        return_value={'score': 85}
    )
    orchestrator.agents['technical'].analyze = AsyncMock(
        return_value={
            'score': 90,
            'backtest_validated': False  # VETO!
        }
    )

    result = await orchestrator.analyze_stock('RELIANCE.NS')

    assert result['decision'] == 'REJECT'
    assert 'veto' in result['reason'].lower()
    assert result['vetoed_by'] == 'Backtest Validator'
```

### 8.4 End-to-End Tests (5%)

**Test Scenarios**:

1. **Full Daily Workflow**:
   - Trigger daily analysis
   - Analyze 10 stocks
   - Generate decisions
   - Execute trades (paper)
   - Log all actions
   - Verify database state

2. **Backtest on Historical Data**:
   - Run system on 2-year historical period
   - Verify performance metrics
   - Compare with V40 baseline
   - Check all decisions were logged

3. **Error Recovery**:
   - Simulate LLM API failure
   - Simulate database connection loss
   - Simulate Redis cache failure
   - Verify graceful degradation

### 8.5 LLM Mocking Strategy

**For unit tests, mock LLM responses**:

```python
# tests/mocks/llm_responses.py

MOCK_LLM_RESPONSES = {
    'valuation_analysis': {
        'valuation_score': 75,
        'fair_pe': 50,
        'upside_pct': 15,
        'reasoning': 'Stock is fairly valued given growth profile'
    },

    'backtest_interpretation': {
        'confidence_score': 85,
        'setup_quality_score': 90,
        'key_strengths': ['High win rate', 'Consistent across years'],
        'key_risks': ['Limited sample size in recent data'],
        'recommendation': 'APPROVE'
    },

    # ... more mock responses
}

# Usage in tests
@patch('agents.fundamental_analyst.LLMClient.call')
async def test_valuation_analysis(mock_llm_call):
    mock_llm_call.return_value = json.dumps(
        MOCK_LLM_RESPONSES['valuation_analysis']
    )

    analyst = FundamentalAnalystAgent(config)
    result = await analyst.analyze_valuation('RELIANCE.NS', data)

    assert result['valuation_score'] == 75
```

### 8.6 Performance Testing

**Load Test Scenarios**:

1. **Concurrent Analysis**:
   - Analyze 50 stocks simultaneously
   - Measure: Response time, memory usage, LLM queue
   - Target: <5 minutes for 50 stocks

2. **Cache Performance**:
   - Measure cache hit rate after 1 month
   - Target: >70% for backtests, >85% for management

3. **Database Performance**:
   - 10,000 decisions logged
   - Query performance: <100ms for recent decisions

**Load Testing Tool**: `locust` or `pytest-benchmark`

```python
# tests/performance/test_concurrent_analysis.py

from locust import User, task, between
import asyncio

class TradingSystemUser(User):
    wait_time = between(1, 5)

    @task
    def analyze_stock(self):
        response = self.client.post("/analyze/RELIANCE.NS")
        assert response.status_code == 200
```

---

## 9. Deployment & Operations

### 9.1 Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     PRODUCTION DEPLOYMENT                            │
└─────────────────────────────────────────────────────────────────────┘

                        ┌─────────────┐
                        │   USERS     │
                        │  (Browser)  │
                        └──────┬──────┘
                               │
                        ┌──────▼──────┐
                        │   Nginx     │
                        │ (SSL/Proxy) │
                        └──────┬──────┘
                               │
                ┌──────────────┴──────────────┐
                │                             │
         ┌──────▼──────┐            ┌────────▼────────┐
         │   FastAPI   │            │   Streamlit     │
         │ (REST API)  │            │   (Dashboard)   │
         └──────┬──────┘            └─────────────────┘
                │
         ┌──────▼──────┐
         │ Orchestrator│
         │   + Agents  │
         └──────┬──────┘
                │
    ┌───────────┼───────────┬───────────┐
    │           │           │           │
┌───▼───┐  ┌───▼───┐  ┌───▼───┐  ┌───▼────┐
│Postgre│  │ Redis │  │Parquet│  │S3/MinIO│
│  SQL  │  │(Cache)│  │ Files │  │  (Docs)│
└───────┘  └───────┘  └───────┘  └────────┘
```

### 9.2 Docker Compose (Production)

**File**: `docker/docker-compose.yml`

```yaml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:16-alpine
    container_name: trading_postgres
    environment:
      POSTGRES_DB: agentic_trading
      POSTGRES_USER: trading_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U trading_user"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: trading_redis
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  # MinIO (S3-compatible storage)
  minio:
    image: minio/minio:latest
    container_name: trading_minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ACCESS_KEY}
      MINIO_ROOT_PASSWORD: ${MINIO_SECRET_KEY}
    volumes:
      - minio_data:/data
    ports:
      - "9000:9000"
      - "9001:9001"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3
    restart: unless-stopped

  # Main Application (FastAPI + Agents)
  app:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    container_name: trading_app
    environment:
      - POSTGRES_HOST=postgres
      - POSTGRES_PORT=5432
      - POSTGRES_DB=agentic_trading
      - POSTGRES_USER=trading_user
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - REDIS_PASSWORD=${REDIS_PASSWORD}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - S3_ENDPOINT=http://minio:9000
      - S3_ACCESS_KEY=${MINIO_ACCESS_KEY}
      - S3_SECRET_KEY=${MINIO_SECRET_KEY}
    volumes:
      - ./storage:/app/storage
      - ./logs:/app/logs
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      minio:
        condition: service_healthy
    restart: unless-stopped

  # Streamlit Dashboard
  dashboard:
    build:
      context: ..
      dockerfile: docker/Dockerfile.dashboard
    container_name: trading_dashboard
    environment:
      - API_URL=http://app:8000
    ports:
      - "8501:8501"
    depends_on:
      - app
    restart: unless-stopped

  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    container_name: trading_nginx
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - app
      - dashboard
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  minio_data:
```

### 9.3 CI/CD Pipeline (GitHub Actions)

**File**: `.github/workflows/ci.yml`

```yaml
name: CI Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_pass
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Cache dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run linters
        run: |
          black --check .
          flake8 .
          mypy agents/ tools/

      - name: Run unit tests
        run: |
          pytest tests/unit -v --cov=agents --cov=tools --cov-report=xml
        env:
          POSTGRES_HOST: localhost
          POSTGRES_PORT: 5432
          REDIS_HOST: localhost
          REDIS_PORT: 6379
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY_TEST }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY_TEST }}

      - name: Run integration tests
        run: |
          pytest tests/integration -v
        env:
          POSTGRES_HOST: localhost
          REDIS_HOST: localhost

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Build Docker image
        run: |
          docker build -t trading-system:${{ github.sha }} -f docker/Dockerfile .

      - name: Push to registry
        run: |
          echo "${{ secrets.DOCKER_PASSWORD }}" | docker login -u "${{ secrets.DOCKER_USERNAME }}" --password-stdin
          docker tag trading-system:${{ github.sha }} ${{ secrets.DOCKER_USERNAME }}/trading-system:latest
          docker push ${{ secrets.DOCKER_USERNAME }}/trading-system:latest
```

### 9.4 Monitoring & Alerting

**Logging Configuration**:

```python
# config/logging_config.py

import logging
from pythonjsonlogger import jsonlogger

def setup_logging():
    """Configure structured logging"""

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Console handler (pretty print for dev)
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler (JSON for production)
    file_handler = logging.FileHandler('logs/app.log')
    json_formatter = jsonlogger.JsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s'
    )
    file_handler.setFormatter(json_formatter)
    logger.addHandler(file_handler)

    return logger
```

**Alerting Rules**:

```python
# scripts/monitoring.py

import smtplib
from email.mime.text import MIMEText

def send_alert(subject: str, message: str):
    """Send email alert"""

    msg = MIMEText(message)
    msg['Subject'] = f"[Trading System] {subject}"
    msg['From'] = "alerts@tradingsystem.com"
    msg['To'] = "admin@tradingsystem.com"

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.send_message(msg)

# Alert triggers
def check_system_health():
    """Monitor system health and alert on issues"""

    # Check 1: LLM API failures
    if llm_failure_rate > 0.1:  # 10% failure rate
        send_alert("High LLM API Failure Rate", f"Failure rate: {llm_failure_rate:.1%}")

    # Check 2: Cache hit rate
    if cache_hit_rate < 0.5:  # 50% hit rate
        send_alert("Low Cache Hit Rate", f"Hit rate: {cache_hit_rate:.1%}")

    # Check 3: Daily LLM costs
    if daily_llm_cost > 100:  # $100/day threshold
        send_alert("High LLM Costs", f"Daily cost: ${daily_llm_cost:.2f}")

    # Check 4: Database connection
    if not postgres_healthy:
        send_alert("Database Connection Lost", "PostgreSQL is unreachable")

    # Check 5: Backtest validation failures
    if backtest_failure_rate > 0.5:  # 50% of stocks failing validation
        send_alert("High Backtest Failure Rate", f"Failure rate: {backtest_failure_rate:.1%}")
```

### 9.5 Backup & Disaster Recovery

**Automated Backups**:

```bash
# scripts/backup.sh

#!/bin/bash

# Backup PostgreSQL
pg_dump -h localhost -U trading_user agentic_trading | gzip > "backups/postgres_$(date +%Y%m%d).sql.gz"

# Backup Redis (RDB snapshot)
redis-cli --rdb "backups/redis_$(date +%Y%m%d).rdb"

# Backup storage directory
tar -czf "backups/storage_$(date +%Y%m%d).tar.gz" storage/

# Upload to S3
aws s3 sync backups/ s3://trading-system-backups/

# Cleanup old backups (keep last 30 days)
find backups/ -mtime +30 -delete
```

**Cron Schedule**:

```bash
# Daily backup at 2 AM
0 2 * * * /app/scripts/backup.sh

# Weekly full backup on Sunday
0 3 * * 0 /app/scripts/full_backup.sh

# Quarterly cache refresh
0 4 1 1,4,7,10 * python /app/scripts/refresh_backtest_cache.py
```

### 9.6 Scaling Considerations

**Horizontal Scaling**:

```
                  ┌──────────────┐
                  │ Load Balancer│
                  │    (Nginx)   │
                  └──────┬───────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
   ┌────▼────┐      ┌────▼────┐     ┌────▼────┐
   │  App 1  │      │  App 2  │     │  App 3  │
   │(Agents) │      │(Agents) │     │(Agents) │
   └────┬────┘      └────┬────┘     └────┬────┘
        │                │                │
        └────────────────┼────────────────┘
                         │
                ┌────────┴────────┐
                │                 │
         ┌──────▼──────┐   ┌─────▼──────┐
         │ PostgreSQL  │   │   Redis    │
         │  (Primary)  │   │  Cluster   │
         └─────────────┘   └────────────┘
```

**Scaling Triggers**:
- **CPU > 70%**: Add more app instances
- **Queue Length > 50**: Add more workers
- **LLM API rate limit**: Implement request queuing
- **Database connections > 80%**: Add read replicas

---

## 10. Appendices

### Appendix A: Glossary

| Term | Definition |
|------|------------|
| **Agent** | Autonomous software component that analyzes a specific dimension (fundamental, technical, etc.) |
| **Backtest** | Simulation of trading strategy on historical data |
| **CAGR** | Compound Annual Growth Rate |
| **Composite Score** | Weighted average of all agent scores |
| **LLM** | Large Language Model (GPT-4, Claude, etc.) |
| **RHS** | Reverse Head & Shoulder chart pattern |
| **CWH** | Cup with Handle chart pattern |
| **Win Rate** | % of profitable trades |
| **Profit Factor** | Gross profit / Gross loss |
| **Sharpe Ratio** | Risk-adjusted return metric |
| **Veto** | Agent's power to block a trade decision |
| **Cache Hit Rate** | % of requests served from cache (without recomputation) |
| **TTL** | Time To Live (cache expiration) |

### Appendix B: API Endpoints Reference

**Base URL**: `https://api.tradingsystem.com/v1`

| Endpoint | Method | Description | Request | Response |
|----------|--------|-------------|---------|----------|
| `/analyze/{ticker}` | POST | Analyze a stock | `{}` | `{decision, scores, reasoning}` |
| `/decisions` | GET | Get recent decisions | `?limit=50` | `[{decision}, ...]` |
| `/portfolio` | GET | Get current portfolio | `{}` | `{positions, cash, value}` |
| `/backtest/{ticker}/{strategy}` | GET | Get backtest results | `{}` | `{validation, metrics}` |
| `/agents/status` | GET | Get agent health | `{}` | `{agents: [{name, status}]}` |
| `/cache/stats` | GET | Get cache statistics | `{}` | `{hit_rate, size}` |

**Example Request**:

```bash
curl -X POST https://api.tradingsystem.com/v1/analyze/RELIANCE.NS \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

**Example Response**:

```json
{
  "ticker": "RELIANCE.NS",
  "timestamp": "2025-10-07T10:30:00Z",
  "decision": "STRONG_BUY",
  "conviction": "HIGH",
  "composite_score": 82.5,
  "position_size_pct": 0.05,
  "scores": {
    "fundamental": 80,
    "technical": 85,
    "sentiment": 70,
    "management": 90
  },
  "backtest_validation": {
    "strategy": "RHS_BREAKOUT",
    "validated": true,
    "win_rate": 75.0,
    "confidence": 85
  },
  "entry_price": 2500.0,
  "target_price": 2850.0,
  "reasoning": "Strong fundamentals (25% CAGR) + validated technical setup (75% WR) + high management quality (90% credibility). Pattern: RHS breakout with 1.3x volume confirmation."
}
```

### Appendix C: Configuration Files

**agent_config.yaml**:

```yaml
orchestrator:
  weights:
    fundamental: 0.30
    technical: 0.30
    sentiment: 0.20
    management: 0.20

  decision_thresholds:
    strong_buy: 80
    buy: 70
    watchlist: 60

  position_sizing:
    strong_buy: 0.05  # 5%
    buy: 0.03         # 3%
    max_total: 0.95   # 95% max total exposure

fundamental:
  min_roce: 20.0
  min_roe: 15.0
  max_debt_equity: 1.0
  min_revenue_growth_3y: 15.0

technical:
  lookback_period: 250
  volume_threshold: 1.3
  indicators:
    - SMA: [20, 50, 200]
    - RSI: 14
    - MACD: [12, 26, 9]

backtest_validator:
  validation_rules:
    min_win_rate: 70.0
    min_trades: 10
    min_profit_factor: 1.5
    max_drawdown: -25.0

  cache_ttl_days: 90
  historical_years: 5

sentiment:
  news_lookback_days: 30
  social_lookback_days: 7
  min_news_articles: 5

management:
  concalls_quarters: 12
  annual_reports_years: 3
  cache_ttl_days: 90
  min_credibility_score: 60.0
```

**llm_config.yaml**:

```yaml
providers:
  anthropic:
    api_key: ${ANTHROPIC_API_KEY}
    base_url: https://api.anthropic.com
    models:
      sonnet: claude-3-5-sonnet-20241022
      haiku: claude-3-5-haiku-20241022

  openai:
    api_key: ${OPENAI_API_KEY}
    base_url: https://api.openai.com/v1
    models:
      gpt4: gpt-4-turbo-preview
      gpt35: gpt-3.5-turbo

usage:
  orchestrator:
    model: openai.gpt4
    temperature: 0.3
    max_tokens: 2000

  fundamental:
    valuation:
      model: anthropic.sonnet
      temperature: 0.2
      max_tokens: 2000
    red_flags:
      model: openai.gpt4
      temperature: 0.1
      max_tokens: 1500

  technical:
    setup_interpretation:
      model: openai.gpt4
      temperature: 0.2
      max_tokens: 1500

  backtest_validator:
    strategy_rules:
      model: anthropic.sonnet
      temperature: 0.1
      max_tokens: 3000
    result_interpretation:
      model: openai.gpt4
      temperature: 0.3
      max_tokens: 2000

  sentiment:
    news:
      model: anthropic.haiku
      temperature: 0.2
      max_tokens: 1500
    social:
      model: anthropic.haiku
      temperature: 0.2
      max_tokens: 1500

  management:
    promises:
      model: anthropic.sonnet
      temperature: 0.1
      max_tokens: 10000
    performance:
      model: openai.gpt4
      temperature: 0.1
      max_tokens: 5000
    correlation:
      model: anthropic.sonnet
      temperature: 0.2
      max_tokens: 8000
    risks:
      model: openai.gpt4
      temperature: 0.2
      max_tokens: 5000
    governance:
      model: anthropic.sonnet
      temperature: 0.1
      max_tokens: 4000

rate_limits:
  anthropic:
    requests_per_minute: 50
    tokens_per_minute: 100000
  openai:
    requests_per_minute: 60
    tokens_per_minute: 150000
```

### Appendix D: Performance Benchmarks

**Expected Performance (50 stocks)**:

| Metric | Value | Notes |
|--------|-------|-------|
| **Analysis Time (uncached)** | 3-5 min | With backtest validation |
| **Analysis Time (cached)** | 30-60 sec | 70% backtest cache hit |
| **Memory Usage** | <4 GB | Per app instance |
| **Database Connections** | <50 | PostgreSQL |
| **LLM Calls/Stock** | 13-15 | First analysis |
| **LLM Calls/Stock (cached)** | 8-10 | With cache |
| **Daily LLM Cost (50 stocks)** | $22 | After month 1 |
| **Cache Hit Rate (Month 2+)** | 70% | Backtest validation |
| **Cache Hit Rate (Management)** | 85% | Quarterly refresh |

### Appendix E: Troubleshooting Guide

| Issue | Possible Cause | Solution |
|-------|---------------|----------|
| **High LLM costs** | Low cache hit rate | Check Redis, verify TTL settings |
| **Slow analysis** | Too many backtest validations | Increase cache TTL, parallelize agents |
| **Low win rate in live trading** | Overfitting to backtest data | Re-validate strategies, increase sample size |
| **Frequent vetos** | Thresholds too strict | Adjust veto thresholds in config |
| **Database connection errors** | Connection pool exhausted | Increase max_connections in PostgreSQL |
| **Redis memory full** | Cache not expiring | Check TTL, implement LRU eviction |
| **LLM API rate limits** | Too many concurrent calls | Implement request queuing, increase rate limits |
| **Backtest validation always fails** | Insufficient historical data | Reduce historical_years to 3 |

### Appendix F: Future Enhancements

**Phase 2 Features** (Post-MVP):

1. **Real-time Trading Integration**:
   - Zerodha Kite API integration
   - Automatic trade execution
   - Position monitoring

2. **Advanced Strategies**:
   - Machine learning models for price prediction
   - Options strategy analyzer
   - Pairs trading agent

3. **Portfolio Optimization**:
   - Modern Portfolio Theory (MPT)
   - Risk parity
   - Factor-based allocation

4. **Multi-Agent Collaboration**:
   - Agents can negotiate and vote
   - Confidence-weighted decisions
   - Agent performance tracking

5. **Enhanced UI**:
   - Real-time charts
   - Backtesting playground
   - Strategy builder interface

6. **Advanced Caching**:
   - Semantic cache (similar stocks)
   - Predictive cache refresh
   - Distributed cache (multi-region)

---

## Summary

This comprehensive implementation guide provides:

✅ **Complete Architecture**: Multi-agent system with 6 specialized agents
✅ **Dual Validation**: Historical 70% win rate + Multi-dimensional analysis
✅ **Detailed Implementation**: Week-by-week roadmap (11 weeks)
✅ **Cost Estimation**: $5,808/year for 50 stocks (after Month 1)
✅ **Technology Stack**: Python, LangGraph, Claude-3.5, GPT-4, PostgreSQL, Redis
✅ **Testing Strategy**: 80% unit, 15% integration, 5% E2E
✅ **Deployment Guide**: Docker, CI/CD, monitoring, backups
✅ **Performance Targets**: 18-22% CAGR, 75-85% win rate, <12% drawdown

**Key Differentiator**: Every technical entry requires proven >70% win rate on 5-year backtest, combined with LLM-powered deep analysis of fundamentals, sentiment, and management quality.

**Ready to implement!** 🚀

---

*Document Version: 1.0*
*Last Updated: October 7, 2025*
*Author: Agentic Trading System Development Team*
