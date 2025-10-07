# Stock Analysis Strategy Documentation

## Overview
This document details the comprehensive analysis strategy used by the Enhanced Multi-Agent Stock Analysis System, including buy/sell signals, screening criteria, and the decision-making framework.

---

## Table of Contents
1. [Search Space & Stock Universe](#search-space--stock-universe)
2. [Technical Analysis Strategy](#technical-analysis-strategy)
3. [Fundamental Analysis Strategy](#fundamental-analysis-strategy)
4. [Final Recommendation Logic](#final-recommendation-logic)
5. [Buy/Sell Signal Summary](#buysell-signal-summary)
6. [Position Sizing & Risk Management](#position-sizing--risk-management)

---

## 1. Search Space & Stock Universe

### Supported Markets
- **Indian Stocks (NSE)**: Primary focus - stocks with `.NS` suffix
- **US Stocks**: Secondary support - any US ticker symbols
- **Data Sources**:
  - Yahoo Finance: Real-time OHLCV data for all markets
  - Screener.in: Comprehensive fundamental data for Indian stocks only
  - ArthaLens: Management insights for Indian stocks only

### Stock Categories
The system classifies stocks into categories for strategy application:

- **V40 Stocks**: Premium category - eligible for advanced strategy analysis
- **V40 Next**: High-potential stocks - eligible for advanced strategy analysis
- **Other Categories**: Basic analysis only
- **Unknown**: Default category when not specified

**Strategy Eligibility**:
- Only **V40** and **V40 Next** categories receive comprehensive strategy backtesting and performance analysis
- Other stocks receive conservative fundamental + technical analysis only

### Data Requirements
- **Minimum Data Points**: 100 days of OHLCV data for technical analysis
- **Pattern Detection**: 200 days of data recommended for RHS/CWH pattern identification

---

## 2. Technical Analysis Strategy

### Core Technical Patterns

#### 2.1 Reverse Head & Shoulder (RHS) Pattern
**Pattern Identification**:
- Identifies 3 troughs: Left Shoulder, Head (deepest), Right Shoulder
- Validates neckline breakout with volume confirmation
- Checks symmetry and depth ratios

**Buy Signals**:
- Valid RHS pattern identified
- Price breaks above neckline
- Volume increase during breakout (>150% of average)
- Right shoulder higher than left shoulder

**Entry Point**:
- Base formation range calculated from pattern
- Entry at neckline breakout price
- Entry date recorded when breakout occurs

**Target Calculation**:
- **Technical Target** = Neckline + (Neckline - Head depth)
- **Lifetime High** = Historical all-time high price
- **Final Target** = Minimum of (Technical Target, Lifetime High)

**Example Output**:
```
Base Formation: ₹450.00 - ₹520.00
Entry Price: ₹515.50
Technical Target: ₹580.00
Lifetime High: ₹600.00
Final Target: ₹580.00
```

#### 2.2 Cup with Handle (CWH) Pattern
**Pattern Identification**:
- Cup formation: U-shaped price decline and recovery
- Handle formation: Small pullback after cup completion
- Volume decreases during cup, increases at breakout

**Buy Signals**:
- Valid cup formation (depth 12-33% of cup peak)
- Handle forms after cup (depth <15% of cup depth)
- Breakout above handle high with volume
- Handle duration: 5-30% of cup duration

**Entry Point**:
- Entry at handle breakout price
- Base formation range from cup low to handle high

**Target Calculation**:
- **Cup Depth** = Cup peak - Cup trough
- **Technical Target** = Breakout price + Cup depth
- **Final Target** = Minimum of (Technical Target, Lifetime High)

#### 2.3 Moving Average Strategies

**SMA 20/50 Crossover**:
- **Bullish Signal**: SMA 20 crosses above SMA 50
- **Bearish Signal**: SMA 20 crosses below SMA 50
- **Confirmation**: Price above both MAs

**Price vs Moving Averages**:
- Price > SMA 20 > SMA 50: Strong uptrend
- Price < SMA 20 < SMA 50: Strong downtrend

#### 2.4 RSI (Relative Strength Index)
- **Oversold (<30)**: Potential buy signal
- **Overbought (>70)**: Potential sell signal
- **Divergence**: Price makes new low but RSI doesn't (bullish divergence)

#### 2.5 Bollinger Bands
- **Lower Band Touch**: Support level - potential bounce (buy)
- **Upper Band Touch**: Resistance level - potential reversal (sell)
- **Band Squeeze**: Low volatility - potential breakout ahead

#### 2.6 Volume Analysis
- **Volume Spike** (>1.5x average): Confirms trend strength
- **High volume + breakout**: Strong buy/sell signal
- **Low volume**: Weak signal, avoid entry

#### 2.7 Lifetime High Strategy
- **Buy Signal**: Price reaches new all-time high with volume
- **Logic**: Breakout from consolidation at lifetime highs
- **Risk**: No overhead resistance

#### 2.8 V20 Strategy (Volatility-Based)
- **Calculation**: 20-day high-low range
- **Lines**:
  - Upper Line = Recent High
  - Lower Line = Recent Low
- **Buy Signal**: Price near lower line (buy at support)
- **Sell Signal**: Price near upper line (sell at resistance)
- **Minimum Range**: 20% range required for signal validity

### Technical Confidence Scoring
- **High Confidence**: Multiple patterns align + high volume + strong trend
- **Medium Confidence**: 1-2 patterns + moderate volume
- **Low Confidence**: Weak signals or conflicting indicators

---

## 3. Fundamental Analysis Strategy

### Core Fundamental Criteria

#### 3.1 Business Quality Assessment
**Excellent Business**:
- Strong competitive moat
- Pricing power in industry
- High market penetration
- Sustainable business model

**Scoring Factors**:
- Market leadership position
- Product/service differentiation
- Brand strength
- Regulatory advantages

#### 3.2 Growth Metrics Analysis

**Revenue Growth** (YoY, QoQ, 3Y Average):
- **Excellent**: >25% YoY growth
- **Good**: 15-25% YoY growth
- **Moderate**: 10-15% YoY growth
- **Poor**: <10% YoY growth

**Net Profit Growth** (YoY, QoQ, 3Y Average):
- **Excellent**: >30% YoY growth
- **Good**: 20-30% YoY growth
- **Moderate**: 10-20% YoY growth
- **Poor**: <10% YoY growth

**Operating Profit Growth**:
- Compared across quarterly and annual data
- Margin expansion tracked
- EBITDA growth consistency

**Growth Quality Score** (0-100):
- Revenue consistency: 30 points
- Profit consistency: 30 points
- Operating leverage: 20 points
- Growth acceleration: 20 points

**Growth Quality Grades**:
- **Excellent**: Score >80
- **Good**: Score 60-80
- **Moderate**: Score 40-60
- **Poor**: Score <40

#### 3.3 Profitability Ratios

**ROCE (Return on Capital Employed)**:
- **Excellent**: >25%
- **Good**: 20-25%
- **Moderate**: 15-20%
- **Poor**: <15%

**ROE (Return on Equity)**:
- **Excellent**: >20%
- **Good**: 15-20%
- **Moderate**: 10-15%
- **Poor**: <10%

**ROA (Return on Assets)**:
- Measures asset utilization efficiency
- Higher is better (depends on industry)

#### 3.4 Debt Analysis

**Debt-to-Equity Ratio**:
- **Excellent**: <0.5 (low debt)
- **Good**: 0.5-1.0 (moderate debt)
- **Caution**: 1.0-2.0 (high debt)
- **Risk**: >2.0 (very high debt)

**Interest Coverage Ratio**:
- **Excellent**: >5x (strong coverage)
- **Good**: 3-5x
- **Caution**: 1.5-3x
- **Risk**: <1.5x (distress risk)

#### 3.5 Valuation Metrics

**P/E Ratio (Price-to-Earnings)**:
- Compared against sector average
- Historical P/E range analysis
- Growth-adjusted P/E (PEG ratio)

**P/B Ratio (Price-to-Book)**:
- **Undervalued**: <1.5
- **Fair**: 1.5-3.0
- **Expensive**: >3.0

**P/S Ratio (Price-to-Sales)**:
- Useful for loss-making but growing companies
- Sector comparison critical

**EV/EBITDA**:
- Enterprise value relative to earnings
- Better than P/E for high-debt companies

#### 3.6 Shareholding Analysis

**Promoter Holding**:
- **Strong**: >50% with no pledging
- **Caution**: High pledging (>20%)
- **Risk**: Declining promoter holding

**Institutional Holding**:
- FII/DII interest indicates confidence
- Increasing institutional holding is positive

**Retail Shareholding**:
- Tracked for sentiment analysis
- High retail can indicate speculative interest

#### 3.7 Multibagger Potential Assessment

**High Potential Criteria**:
- Market Cap < ₹10,000 Cr AND ROCE > 25%
- Excellent growth quality (score >80)
- High business quality rating

**Moderate Potential**:
- Market Cap < ₹50,000 Cr AND ROCE > 20%
- Good growth quality (score 60-80)

**Limited Potential**:
- Large cap stocks (>₹50,000 Cr)
- Low ROCE (<20%)
- Poor growth quality

### Fundamental Confidence Scoring

**Strong Confidence**:
- 4+ data sections available (quarterly, annual, balance sheet, cash flow)
- Consistent growth across metrics
- Strong profitability ratios

**Medium Confidence**:
- 2-3 data sections available
- Mixed growth signals
- Moderate profitability

**Low Confidence**:
- Limited data (<2 sections)
- Inconsistent or negative growth
- Weak profitability

**Can't Say**:
- Insufficient data for analysis
- Data quality issues

---

## 4. Final Recommendation Logic

### Decision Framework

The Coordinator Agent synthesizes technical and fundamental analysis using this hierarchy:

#### **Tier 1: V40/V40 Next Stocks (Advanced Strategy Analysis)**

**Step 1: Strategy Performance Analysis**
- Historical backtesting of identified patterns
- Success rate calculation for each strategy
- Total signals count for statistical significance

**Step 2: Pattern-Based Recommendations**

**RHS Pattern Detected**:
- **Action**: BUY
- **Confidence**: High if success rate >60% AND signals ≥3
- **Position Size**: 3-5% of portfolio (based on success rate)
- **Strategy Used**: "RHS Strategy"

**CWH Pattern Detected**:
- **Action**: BUY
- **Confidence**: High if success rate >60% AND signals ≥3
- **Position Size**: 3-5% of portfolio (based on success rate)
- **Strategy Used**: "CWH Strategy"

**Step 3: Performance-Based Tiering**

**High Confidence** (Success Rate ≥60%, Signals ≥3):
- **Action**: BUY
- **Position Size**: 4-5% of portfolio
- **Time Horizon**: 3-6 months
- **Risk Level**: Medium-High

**Medium Confidence** (Success Rate ≥50%, Signals ≥2):
- **Action**: BUY
- **Position Size**: 3-4% of portfolio
- **Time Horizon**: 3-6 months
- **Risk Level**: Medium

**Low Confidence** (Success Rate ≥40%, Signals ≥1):
- **Action**: BUY
- **Position Size**: 2-3% of portfolio
- **Time Horizon**: 3-6 months
- **Risk Level**: Medium

**Below Threshold** (Success Rate <40% OR Signals <1):
- **Action**: HOLD
- **Position Size**: 1-2% of portfolio
- **Rationale**: Insufficient historical performance

**Step 4: Fallback Logic (if strategy analysis fails)**

Pattern priority:
1. RHS Pattern → BUY (Medium confidence)
2. CWH Pattern → BUY (Medium confidence)
3. Lifetime High → BUY (Medium confidence)
4. Strong Fundamental (Business Quality = "Strong") → BUY (Medium confidence)
5. Otherwise → HOLD (Low confidence)

#### **Tier 2: Other Categories (Basic Analysis)**

**Buy Criteria**:
- Strong fundamental business quality
- Good technical trend (Bullish)
- Reasonable valuation

**Action**: BUY (if all criteria met)
- **Confidence**: Medium (Basic Analysis)
- **Position Size**: 1-2% of portfolio (conservative)
- **Time Horizon**: 3-6 months
- **Risk Level**: Medium

**Hold Criteria**:
- Weak fundamentals OR bearish technicals
- Overvalued stock

**Action**: HOLD
- **Confidence**: Low (Basic Analysis)
- **Rationale**: Insufficient conviction for entry

### Key Risks Identification
All recommendations include:
- Market volatility risk
- Sector-specific risks
- Strategy performance uncertainty (past ≠ future)
- Company-specific risks (debt, management, competition)

---

## 5. Buy/Sell Signal Summary

### BUY SIGNALS

#### Technical Buy Signals:
1. **RHS Pattern Breakout** - Neckline break with volume
2. **CWH Pattern Breakout** - Handle breakout with volume
3. **SMA Crossover** - SMA 20 crosses above SMA 50
4. **RSI Oversold** - RSI < 30 with reversal
5. **Bollinger Lower Band** - Price at lower band with reversal
6. **Volume Spike on Breakout** - >150% average volume
7. **Lifetime High Breakout** - New ATH with strong volume
8. **V20 Lower Line** - Price at lower volatility range

#### Fundamental Buy Signals:
1. **High Growth Quality** - Growth score >80
2. **Excellent Profitability** - ROCE >25%, ROE >20%
3. **Low Debt** - D/E <0.5, Interest coverage >5x
4. **Strong Business** - Market leadership, pricing power
5. **Undervaluation** - Low P/E, P/B vs historical/sector
6. **Promoter Confidence** - Increasing holding, zero pledging
7. **Multibagger Potential** - Small cap + high ROCE + growth

#### Combined Buy Signals (Strongest):
- RHS/CWH pattern + Strong fundamentals + High success rate
- Lifetime high + Revenue/profit acceleration + Low debt
- Multiple technical patterns + Excellent growth quality

### SELL SIGNALS

#### Technical Sell Signals:
1. **RSI Overbought** - RSI >70 with reversal signs
2. **Bollinger Upper Band Rejection** - Price fails at upper band
3. **SMA Breakdown** - Price breaks below SMA 20/50
4. **Volume Decline on Rallies** - Weak uptrends
5. **Pattern Failure** - RHS/CWH neckline/handle breaks down

#### Fundamental Sell Signals:
1. **Deteriorating Growth** - Negative YoY revenue/profit
2. **Margin Compression** - Declining operating margins
3. **Rising Debt** - Increasing D/E ratio, falling coverage
4. **Promoter Pledging** - Increasing pledging >20%
5. **Overvaluation** - Extreme P/E, P/B vs history/sector
6. **Weak Business Quality** - Loss of pricing power, market share

#### HOLD Signal:
- Mixed technical and fundamental signals
- Low confidence from strategy backtesting
- Insufficient data for high-conviction call
- Awaiting pattern completion or fundamental catalyst

---

## 6. Position Sizing & Risk Management

### Position Sizing Framework

**V40/V40 Next Stocks**:
- **Success Rate ≥70%**: 5% of portfolio
- **Success Rate 60-70%**: 4% of portfolio
- **Success Rate 50-60%**: 3% of portfolio
- **Success Rate 40-50%**: 2% of portfolio
- **Success Rate <40%**: 1% of portfolio (or HOLD)

**Other Categories**:
- **Strong Conviction**: 2% of portfolio
- **Medium Conviction**: 1% of portfolio
- **Low Conviction**: HOLD (no position)

### Stop Loss Strategy

**Pattern-Based Stocks**:
- **RHS Pattern**: Stop loss below right shoulder low
- **CWH Pattern**: Stop loss below handle low
- **General**: 8-12% below entry price

**Fundamental Stocks**:
- **Time-Based**: Review after 6-12 months
- **Event-Based**: Re-evaluate on quarterly results
- **Price-Based**: 15-20% trailing stop for long-term holds

### Time Horizons

**Short-Term** (1-3 months):
- Quick technical patterns (V20, RSI, BB)
- Event-driven trades

**Medium-Term** (3-6 months):
- RHS/CWH patterns
- Strategy-based entries

**Long-Term** (6-12+ months):
- Multibagger candidates
- Fundamental growth stories

### Risk Levels

**Low Risk**:
- Large cap, strong fundamentals
- Established trends
- Position size: 1-2%

**Medium Risk**:
- Mid cap, good fundamentals
- Pattern-based entries
- Position size: 2-4%

**High Risk**:
- Small cap, high growth
- Speculative patterns
- Position size: 4-5% (max)

---

## System Workflow Summary

```
1. Stock Input (Ticker, Company Name, Sector, Category)
   ↓
2. Data Collection
   - Yahoo Finance: OHLCV data (200 days)
   - Screener.in: Fundamental data (Indian stocks)
   - ArthaLens: Management insights (Indian stocks)
   ↓
3. Technical Analysis Agent
   - Pattern detection (RHS, CWH)
   - Indicator calculation (RSI, BB, SMA, Volume)
   - Support/resistance identification
   - Entry/target/stop-loss calculation
   ↓
4. Fundamental Analysis Agent
   - Growth metrics calculation
   - Profitability ratios
   - Debt analysis
   - Valuation assessment
   - Multibagger potential scoring
   ↓
5. Strategy Performance Agent (V40/V40 Next only)
   - Historical backtesting
   - Success rate calculation
   - Strategy ranking
   ↓
6. Coordinator Agent (Final Recommendation)
   - Synthesize all signals
   - Apply decision framework
   - Generate BUY/HOLD/EXIT recommendation
   - Calculate position size
   - Set time horizon and risk level
   ↓
7. Report Generation
   - Comprehensive analysis report
   - PDF export
   - Cost tracking
```

---

## Appendix: Example Analysis Flow

**Input**: DELHIVERY.NS, Delhivery Ltd, Logistics, V40

**Technical Analysis**:
- RHS pattern identified (Entry: ₹365, Target: ₹425)
- RSI: 55 (Neutral)
- Price above SMA 20 and SMA 50 (Bullish)
- Volume spike confirmed

**Fundamental Analysis**:
- Revenue Growth: 28% YoY (Excellent)
- ROCE: 18%, ROE: 15% (Moderate)
- D/E: 0.3 (Low debt)
- Growth Quality Score: 75 (Good)
- Multibagger Potential: Moderate

**Strategy Performance**:
- RHS Strategy: 65% success rate, 4 historical signals
- Confidence: High

**Final Recommendation**:
- **Action**: BUY
- **Entry**: ₹360-₹365
- **Target**: ₹425 (16% upside)
- **Stop Loss**: ₹340 (7% below entry)
- **Position Size**: 4% of portfolio
- **Time Horizon**: 3-6 months
- **Confidence**: High (65% success rate, 4 signals)
- **Risk Level**: Medium
- **Strategy**: RHS Pattern Strategy

---

## Disclaimer

This system provides automated analysis based on historical patterns and fundamental metrics. **Past performance does not guarantee future results**. All investment decisions should consider:
- Individual risk tolerance
- Portfolio diversification
- Market conditions
- Company-specific developments
- Regulatory changes

**Use this analysis as one input among many in your investment decision-making process.**

---

*Document Version: 1.0*
*Last Updated: October 2025*
*System: Enhanced Multi-Agent Stock Analysis Framework*
