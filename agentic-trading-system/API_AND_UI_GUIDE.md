# API & Streamlit Dashboard Guide

**Status:** ✅ Implemented (Week 9)

---

## Overview

The Agentic Trading System now includes:
1. **FastAPI REST API** - Backend API for stock analysis and portfolio management
2. **Streamlit Dashboard** - Interactive web UI for real-time analysis and monitoring

---

## Quick Start

### Option 1: Run Streamlit Dashboard (Recommended)

The Streamlit dashboard is the easiest way to interact with the system:

```bash
# Start the dashboard
streamlit run streamlit_app.py

# Access at: http://localhost:8501
```

The dashboard includes:
- 📊 **Live Analysis**: Real-time stock analysis with quick-select buttons
- 💼 **Portfolio**: View current positions and P&L
- 📈 **Performance**: Equity curves and analytics
- ⚙️ **Settings**: Configure trading parameters and agent weights

### Option 2: Run FastAPI Server

For API access or integration with other services:

```bash
# Start the API server
python3 api/main.py

# Or with uvicorn directly:
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Access at: http://localhost:8000
# API Docs: http://localhost:8000/api/docs
# ReDoc: http://localhost:8000/api/redoc
```

### Option 3: Run Both (Full Stack)

```bash
# Terminal 1: Start API server
uvicorn api.main:app --reload --port 8000

# Terminal 2: Start Streamlit dashboard
streamlit run streamlit_app.py --server.port 8501
```

---

## FastAPI Endpoints

### Health & Status

#### `GET /`
Root endpoint with API info

**Response:**
```json
{
  "message": "Agentic Trading System API",
  "version": "1.0.0",
  "docs": "/api/docs"
}
```

#### `GET /api/v1/health`
Health check endpoint

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-10T...",
  "orchestrator_ready": true,
  "portfolio_ready": true
}
```

### Analysis

#### `POST /api/v1/analyze/{ticker}`
Analyze a stock and get trading recommendation

**Parameters:**
- `ticker` (path): Stock ticker symbol (e.g., RELIANCE.NS)
- `use_llm` (query, optional): Whether to use LLM analysis (default: true)

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/analyze/RELIANCE.NS?use_llm=false"
```

**Response:**
```json
{
  "ticker": "RELIANCE.NS",
  "decision": "BUY",
  "score": 72.5,
  "confidence": 75,
  "technical_score": 68.0,
  "fundamental_score": 75.0,
  "sentiment_score": 70.0,
  "management_score": 72.0,
  "market_regime_score": 65.0,
  "technical_signal": {
    "pattern_type": "Bull Flag",
    "entry_price": 2450.0,
    "target_price": 2650.0,
    "stop_loss": 2350.0
  },
  "reasoning": "Strong fundamentals with bullish technical pattern...",
  "timestamp": "2025-10-10T...",
  "used_llm": false
}
```

### Portfolio

#### `GET /api/v1/portfolio`
Get current portfolio status

**Response:**
```json
{
  "total_value": 1250000.0,
  "cash": 750000.0,
  "positions": [
    {
      "ticker": "RELIANCE.NS",
      "quantity": 100,
      "avg_price": 2450.0,
      "current_price": 2500.0,
      "value": 250000.0,
      "pnl": 5000.0,
      "pnl_pct": 2.04,
      "stop_loss": 2350.0,
      "target": 2650.0
    }
  ],
  "total_return_pct": 25.0,
  "realized_pnl": 50000.0,
  "unrealized_pnl": 5000.0
}
```

### Decision History

#### `GET /api/v1/decisions`
Get recent trading decisions

**Parameters:**
- `limit` (query, optional): Max decisions to return (default: 50)
- `ticker` (query, optional): Filter by ticker

**Response:**
```json
[
  {
    "ticker": "RELIANCE.NS",
    "decision": "BUY",
    "score": 72.5,
    "date": "2025-10-10T..."
  }
]
```

### Backtest

#### `GET /api/v1/backtest`
Get backtest results (placeholder - implementation pending)

**Parameters:**
- `months` (query): Number of months to backtest (default: 6)
- `ticker` (query, optional): Filter by ticker

---

## Streamlit Dashboard Features

### Page 1: Live Analysis

**Features:**
- Text input for stock ticker entry
- Quick-select buttons for popular stocks (RELIANCE, TCS, HDFCBANK, INFY, ICICIBANK)
- Real-time analysis with decision display (BUY/SELL/WAIT)
- Agent score breakdown (Fundamental, Technical, Sentiment, Management, Market Regime)
- Technical signal details (pattern, entry, target, stop loss)
- Analysis reasoning and veto warnings
- Recent analysis history sidebar

**Usage:**
1. Enter ticker (e.g., "RELIANCE.NS") or click quick-select button
2. Click "🔍 Analyze"
3. View decision, scores, and reasoning

### Page 2: Portfolio

**Features:**
- Portfolio metrics (Total Value, Cash, P&L, Return %)
- Current positions table with:
  - Ticker, Quantity, Avg Price, Current Price
  - Position value and P&L (₹ and %)
  - Stop loss and target prices

**Usage:**
- View all open positions and their performance
- Monitor overall portfolio health

### Page 3: Performance

**Features:**
- Portfolio equity curve chart
- Performance analytics (placeholder for future metrics)

**Usage:**
- Track portfolio growth over time
- Visualize returns and drawdowns

### Page 4: Settings

**Features:**
- Trading configuration:
  - Initial capital
  - Max position size (%)
  - Max open positions
  - Max drawdown (%)
  - Daily loss limit (%)
  - LLM analysis toggle
- Agent weights adjustment:
  - Fundamental (0.0-1.0)
  - Technical (0.0-1.0)
  - Sentiment (0.0-1.0)
  - Management (0.0-1.0)
  - Market Regime (0.0-1.0)

**Usage:**
- Adjust risk parameters
- Fine-tune agent weights
- Enable/disable LLM analysis

---

## Configuration

### Environment Variables

Ensure `.env` file is properly configured:

```bash
# LLM APIs
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
PERPLEXITY_API_KEY=pplx-...

# Optional: News API
NEWSAPI_KEY=...
```

### Startup Initialization

The API automatically initializes on startup:
- ✅ Orchestrator (all 6 agents)
- ✅ Portfolio (₹10L initial capital)
- ✅ Paper Trading Engine (with default watchlist)

Default watchlist: RELIANCE.NS, TCS.NS, HDFCBANK.NS

---

## Testing

### Unit Tests

```bash
# Test API endpoints
python3 test_api.py
```

**Expected Output:**
```
✅ Root endpoint: {'message': 'Agentic Trading System API', ...}
✅ Health check: {'status': 'healthy', ...}
✅ Portfolio endpoint: Total Value: ₹1,000,000
✅ Decision history: 0 decisions
```

### Manual Testing

#### Test Stock Analysis (via API):
```bash
# Analyze without LLM (faster)
curl -X POST "http://localhost:8000/api/v1/analyze/AXISBANK.NS?use_llm=false"

# Analyze with LLM (full analysis)
curl -X POST "http://localhost:8000/api/v1/analyze/AXISBANK.NS?use_llm=true"
```

#### Test via Streamlit:
1. Start dashboard: `streamlit run streamlit_app.py`
2. Click "RELIANCE" quick-select button
3. Click "🔍 Analyze"
4. Verify decision display and agent scores

---

## API Response Models

### AnalyzeResponse
```python
{
    ticker: str
    decision: str  # "BUY" | "STRONG_BUY" | "SELL" | "WAIT"
    score: float  # 0-100
    confidence: int  # 0-100
    technical_score: float
    fundamental_score: float
    sentiment_score: float
    management_score: float
    market_regime_score: float
    technical_signal: Dict[str, Any]
    reasoning: str
    timestamp: datetime
    used_llm: bool
}
```

### PortfolioResponse
```python
{
    total_value: float
    cash: float
    positions: List[Dict]
    total_return_pct: float
    realized_pnl: float
    unrealized_pnl: float
}
```

### HealthResponse
```python
{
    status: str  # "healthy" | "degraded"
    timestamp: datetime
    orchestrator_ready: bool
    portfolio_ready: bool
}
```

---

## CORS Configuration

The API includes CORS middleware for web integration:

```python
allow_origins=["*"]  # Configure for production
allow_credentials=True
allow_methods=["*"]
allow_headers=["*"]
```

**⚠️ Production Note:** Update `allow_origins` to specific domains before deployment.

---

## Performance Considerations

### API Performance:
- **With LLM**: ~30-60 seconds per analysis (3-5 LLM calls)
- **Without LLM**: ~5-10 seconds per analysis (no LLM calls)
- **Caching**: Fundamental data cached for 24 hours

### Streamlit Performance:
- Uses `@st.cache_resource` for Orchestrator singleton
- Session state for portfolio and analysis history
- Async analysis with spinner feedback

### Recommendations:
1. Use `use_llm=false` for quick backtests
2. Clear cache if data seems stale: `rm storage/cache/cache.db*`
3. Limit concurrent analyses to avoid API rate limits

---

## Next Steps (Week 10-11)

### Week 10: Deployment Preparation
- [ ] Add authentication (JWT tokens)
- [ ] Implement decision history storage (SQLite)
- [ ] Add backtest results endpoint
- [ ] Create Docker containers
- [ ] Set up CI/CD pipeline

### Week 11: Production Deployment
- [ ] Deploy to cloud (AWS/GCP/Azure)
- [ ] Configure production database
- [ ] Set up monitoring and alerting
- [ ] Enable live paper trading

---

## Troubleshooting

### Issue: "Module 'fastapi' not found"
**Solution:** Install dependencies
```bash
pip3 install fastapi "uvicorn[standard]" streamlit plotly
```

### Issue: "Orchestrator not initialized"
**Solution:** Check environment variables in `.env`

### Issue: API returns 503 errors
**Solution:** Verify startup logs for initialization errors

### Issue: Streamlit shows "Connection error"
**Solution:** Ensure no other service is using port 8501

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Streamlit Dashboard                   │
│           (Live Analysis, Portfolio, Settings)           │
└───────────────────────┬─────────────────────────────────┘
                        │
                        │ Direct Python Import
                        │
┌───────────────────────▼─────────────────────────────────┐
│                     Orchestrator                         │
│              (6 Specialized Agents)                      │
└───────────────────────┬─────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
┌───────▼──────┐ ┌─────▼─────┐ ┌──────▼──────┐
│ Data Fetchers│ │ Portfolio  │ │ Paper Trade │
│ (Screener.in)│ │ Management │ │   Engine    │
└──────────────┘ └────────────┘ └─────────────┘
        │
        │
┌───────▼──────────────────────────────────────┐
│              Cache (SQLite)                   │
└───────────────────────────────────────────────┘
```

---

## Summary

✅ **FastAPI**: Full REST API with 8 endpoints
✅ **Streamlit**: 4-page interactive dashboard
✅ **Testing**: Unit tests passing
✅ **Documentation**: Complete usage guide
🎯 **Ready**: For Week 10 (Authentication & Deployment)
