"""
FastAPI main application for Agentic Trading System
Provides REST API endpoints for stock analysis and portfolio management
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncio
import logging

from agents.orchestrator import Orchestrator
from paper_trading.portfolio import Portfolio
from paper_trading.engine import PaperTradingEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Agentic Trading System API",
    description="Multi-agent AI trading system with 5-year pattern validation",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances (In production, use dependency injection)
orchestrator = None
portfolio = None
paper_trading_engine = None

# Pydantic models for request/response
class AnalyzeRequest(BaseModel):
    ticker: str
    use_llm: bool = True

class AnalyzeResponse(BaseModel):
    ticker: str
    decision: str
    score: float
    confidence: int
    technical_score: float
    fundamental_score: float
    sentiment_score: float
    management_score: float
    market_regime_score: float
    technical_signal: Dict[str, Any]
    reasoning: str
    timestamp: datetime
    used_llm: bool

class DecisionHistory(BaseModel):
    ticker: str
    decision: str
    score: float
    date: datetime

class PortfolioResponse(BaseModel):
    total_value: float
    cash: float
    positions: List[Dict[str, Any]]
    total_return_pct: float
    realized_pnl: float
    unrealized_pnl: float

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    orchestrator_ready: bool
    portfolio_ready: bool


@app.on_event("startup")
async def startup_event():
    """Initialize system on startup"""
    global orchestrator, portfolio, paper_trading_engine

    logger.info("🚀 Starting Agentic Trading System API...")

    try:
        # Initialize orchestrator
        orchestrator = Orchestrator()
        logger.info("✅ Orchestrator initialized")

        # Initialize portfolio
        portfolio = Portfolio(initial_capital=1000000)
        logger.info("✅ Portfolio initialized")

        # Initialize paper trading engine
        paper_trading_engine = PaperTradingEngine(
            orchestrator=orchestrator,
            portfolio=portfolio,
            watchlist=["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS"]  # Default watchlist
        )
        logger.info("✅ Paper Trading Engine initialized")

        logger.info("🎉 System ready!")

    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("👋 Shutting down Agentic Trading System API...")


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "Agentic Trading System API",
        "version": "1.0.0",
        "docs": "/api/docs"
    }


@app.get("/api/v1/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy" if orchestrator and portfolio else "degraded",
        timestamp=datetime.now(),
        orchestrator_ready=orchestrator is not None,
        portfolio_ready=portfolio is not None
    )


@app.post("/api/v1/analyze/{ticker}", response_model=AnalyzeResponse, tags=["Analysis"])
async def analyze_stock(
    ticker: str,
    use_llm: bool = True
):
    """
    Analyze a stock and get trading recommendation

    Args:
        ticker: Stock ticker symbol (e.g., RELIANCE.NS)
        use_llm: Whether to use LLM for analysis (default: True)

    Returns:
        AnalyzeResponse with decision, scores, and reasoning
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    try:
        logger.info(f"📊 Analyzing {ticker}...")

        # Run analysis
        result = await orchestrator.analyze(ticker)

        if not result:
            raise HTTPException(status_code=500, detail="Analysis failed")

        # Extract response data
        response = AnalyzeResponse(
            ticker=ticker,
            decision=result.get('decision', 'WAIT'),
            score=result.get('score', 0.0),
            confidence=result.get('confidence', 0),
            technical_score=result.get('technical', {}).get('score', 0.0),
            fundamental_score=result.get('fundamental', {}).get('score', 0.0),
            sentiment_score=result.get('sentiment', {}).get('score', 0.0),
            management_score=result.get('management', {}).get('score', 0.0),
            market_regime_score=result.get('market_regime', {}).get('score', 0.0),
            technical_signal=result.get('technical', {}).get('signal', {}),
            reasoning=result.get('reasoning', ''),
            timestamp=datetime.now(),
            used_llm=use_llm
        )

        logger.info(f"✅ Analysis complete: {response.decision} ({response.score:.1f}/100)")

        return response

    except Exception as e:
        logger.error(f"❌ Analysis failed for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/decisions", response_model=List[DecisionHistory], tags=["Decisions"])
async def get_decision_history(
    limit: int = 50,
    ticker: Optional[str] = None
):
    """
    Get recent trading decisions

    Args:
        limit: Maximum number of decisions to return (default: 50)
        ticker: Optional ticker filter

    Returns:
        List of recent decisions
    """
    # TODO: Implement decision history storage and retrieval
    # For now, return empty list
    return []


@app.get("/api/v1/portfolio", response_model=PortfolioResponse, tags=["Portfolio"])
async def get_portfolio():
    """
    Get current portfolio status

    Returns:
        PortfolioResponse with positions, value, and P&L
    """
    if not portfolio:
        raise HTTPException(status_code=503, detail="Portfolio not initialized")

    try:
        positions_list = [
            {
                "ticker": pos.ticker,
                "quantity": pos.quantity,
                "avg_price": pos.avg_price,
                "current_price": pos.current_price,
                "value": pos.quantity * pos.current_price,
                "pnl": (pos.current_price - pos.avg_price) * pos.quantity,
                "pnl_pct": ((pos.current_price - pos.avg_price) / pos.avg_price) * 100,
                "stop_loss": pos.stop_loss,
                "target": pos.target
            }
            for pos in portfolio.positions.values()
        ]

        return PortfolioResponse(
            total_value=portfolio.total_value,
            cash=portfolio.cash,
            positions=positions_list,
            total_return_pct=portfolio.total_return_pct,
            realized_pnl=portfolio.realized_pnl,
            unrealized_pnl=portfolio.unrealized_pnl
        )

    except Exception as e:
        logger.error(f"❌ Failed to get portfolio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/backtest", tags=["Backtest"])
async def get_backtest_results(
    months: int = 6,
    ticker: Optional[str] = None
):
    """
    Get backtest results

    Args:
        months: Number of months to backtest (default: 6)
        ticker: Optional ticker filter

    Returns:
        Backtest performance metrics
    """
    # TODO: Implement backtest results retrieval
    return {
        "message": "Backtest endpoint - Implementation pending",
        "months": months,
        "ticker": ticker
    }


@app.post("/api/v1/watchlist/add/{ticker}", tags=["Watchlist"])
async def add_to_watchlist(ticker: str):
    """Add a ticker to the watchlist"""
    if not paper_trading_engine:
        raise HTTPException(status_code=503, detail="Paper trading engine not initialized")

    # TODO: Implement watchlist management
    return {"message": f"{ticker} added to watchlist"}


@app.delete("/api/v1/watchlist/remove/{ticker}", tags=["Watchlist"])
async def remove_from_watchlist(ticker: str):
    """Remove a ticker from the watchlist"""
    if not paper_trading_engine:
        raise HTTPException(status_code=503, detail="Paper trading engine not initialized")

    # TODO: Implement watchlist management
    return {"message": f"{ticker} removed from watchlist"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
