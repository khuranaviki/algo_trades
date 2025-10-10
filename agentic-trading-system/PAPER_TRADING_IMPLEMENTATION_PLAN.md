# Paper Trading Implementation Plan
## Option A: Real-Time Trading Integration (Phase 1)

**Last Updated:** October 9, 2025
**Status:** 🚧 **IN PROGRESS**

---

## 📋 Executive Summary

Implement a complete paper trading system that:
1. Monitors stocks in real-time
2. Executes simulated trades based on orchestrator decisions
3. Tracks portfolio performance
4. Provides live monitoring dashboard
5. Validates strategy in live market conditions WITHOUT risking capital

**Timeline:** 3 weeks
**Estimated Cost:** $0 (using free data APIs for testing)

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    PAPER TRADING SYSTEM                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌────────────────┐        ┌─────────────────┐            │
│  │  Data Stream   │───────▶│  Signal Monitor │            │
│  │  (WebSocket)   │        │  (Orchestrator) │            │
│  └────────────────┘        └─────────────────┘            │
│         │                           │                      │
│         │                           ▼                      │
│         │                  ┌─────────────────┐            │
│         │                  │  Order Router   │            │
│         │                  └─────────────────┘            │
│         │                           │                      │
│         ▼                           ▼                      │
│  ┌────────────────┐        ┌─────────────────┐            │
│  │  Price Cache   │        │  Order Executor │            │
│  │  (Redis)       │◀───────│  (Simulator)    │            │
│  └────────────────┘        └─────────────────┘            │
│         │                           │                      │
│         │                           ▼                      │
│         │                  ┌─────────────────┐            │
│         │                  │   Portfolio     │            │
│         └─────────────────▶│   Manager       │            │
│                            └─────────────────┘            │
│                                     │                      │
│                                     ▼                      │
│                            ┌─────────────────┐            │
│                            │  Dashboard      │            │
│                            │  (Streamlit)    │            │
│                            └─────────────────┘            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 Module Structure

```
agentic-trading-system/
├── paper_trading/
│   ├── __init__.py
│   ├── engine.py              # Core paper trading orchestrator
│   ├── portfolio.py           # Portfolio state & P&L tracking
│   ├── order_executor.py      # Simulated order execution
│   ├── data_stream.py         # Real-time data handler
│   ├── signal_monitor.py      # Continuous stock screening
│   ├── risk_manager.py        # Portfolio risk controls
│   └── transaction_costs.py   # Brokerage/slippage simulation
│
├── dashboard/
│   ├── __init__.py
│   ├── app.py                 # Streamlit main app
│   ├── components/
│   │   ├── portfolio_view.py  # Portfolio visualization
│   │   ├── signal_view.py     # Live signals
│   │   ├── decision_view.py   # Agent breakdown
│   │   └── analytics_view.py  # Performance metrics
│   └── utils.py
│
├── data/
│   ├── live_prices.db         # SQLite for live price history
│   └── paper_trades.db        # SQLite for trade history
│
└── tests/
    ├── test_paper_engine.py
    ├── test_order_executor.py
    └── test_portfolio.py
```

---

## 🔧 Phase 1: Real-Time Data Pipeline (Week 1)

### Objective
Stream live market data and normalize it for the orchestrator.

### Tasks

#### 1.1 Research & Select Data Provider
**Options:**
- **Yahoo Finance (yfinance)** - FREE, 15-min delay for NSE
- **Alpha Vantage** - FREE tier: 5 API calls/min, 500/day
- **IEX Cloud** - FREE tier: 50k messages/month
- **Polygon.io** - Paid but comprehensive

**Recommendation:** Start with **yfinance** for simplicity, upgrade later.

#### 1.2 Implement Data Streaming

**File:** `paper_trading/data_stream.py`

**Core functionality:**
```python
class LiveDataStream:
    """Real-time price streaming with 1-minute intervals"""

    def __init__(self, tickers: List[str], update_interval: int = 60):
        self.tickers = tickers
        self.update_interval = update_interval
        self.cache = {}
        self.subscribers = []

    async def start(self):
        """Start streaming prices"""

    async def get_latest_price(self, ticker: str) -> Dict:
        """Get latest price with OHLCV"""

    def subscribe(self, callback: Callable):
        """Subscribe to price updates"""

    def is_market_open(self) -> bool:
        """Check if NSE is open (9:15 AM - 3:30 PM IST)"""
```

**Data format:**
```json
{
    "ticker": "RELIANCE.NS",
    "timestamp": "2025-10-09T14:30:00+05:30",
    "price": 2847.50,
    "open": 2840.00,
    "high": 2850.00,
    "low": 2835.00,
    "volume": 1234567,
    "bid": 2847.00,
    "ask": 2848.00
}
```

#### 1.3 Implement Caching Layer

**File:** `paper_trading/data_stream.py`

**Use in-memory cache (dict) initially, Redis later for production.**

```python
class PriceCache:
    """Cache recent prices for technical analysis"""

    def __init__(self, max_history: int = 1825):
        self.cache = {}  # ticker -> list of prices
        self.max_history = max_history

    def update(self, ticker: str, price_data: Dict):
        """Add new price data"""

    def get_history(self, ticker: str, days: int) -> pd.DataFrame:
        """Get historical data for technical analysis"""

    def has_sufficient_data(self, ticker: str, min_days: int) -> bool:
        """Check if we have enough data"""
```

#### 1.4 Market Hours Detection

**File:** `paper_trading/data_stream.py`

```python
def is_market_open() -> Dict[str, Any]:
    """Check if NSE is currently open"""

    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)

    # NSE hours: 9:15 AM - 3:30 PM IST, Mon-Fri
    weekday = now.weekday()
    if weekday >= 5:  # Saturday or Sunday
        return {'open': False, 'reason': 'weekend'}

    market_open = now.replace(hour=9, minute=15, second=0)
    market_close = now.replace(hour=15, minute=30, second=0)

    if now < market_open:
        return {'open': False, 'reason': 'before_market', 'opens_at': market_open}
    elif now > market_close:
        return {'open': False, 'reason': 'after_market', 'opens_at': market_open + timedelta(days=1)}
    else:
        return {'open': True, 'closes_at': market_close}
```

---

## 🎯 Phase 2: Paper Trading Engine (Week 1-2)

### Objective
Simulate trade execution with realistic constraints.

### Tasks

#### 2.1 Portfolio State Management

**File:** `paper_trading/portfolio.py`

```python
@dataclass
class Position:
    """Single stock position"""
    ticker: str
    quantity: int
    avg_entry_price: float
    current_price: float
    stop_loss: Optional[float]
    target_price: Optional[float]
    entry_date: datetime
    unrealized_pnl: float
    unrealized_pnl_pct: float

@dataclass
class Trade:
    """Executed trade record"""
    trade_id: str
    ticker: str
    action: str  # BUY, SELL
    quantity: int
    price: float
    timestamp: datetime
    reason: str  # orchestrator decision reasoning
    transaction_cost: float

class Portfolio:
    """Manage virtual portfolio state"""

    def __init__(self, initial_capital: float = 1000000):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: Dict[str, Position] = {}
        self.trade_history: List[Trade] = []
        self.daily_snapshots: List[Dict] = []

    def get_total_value(self, current_prices: Dict[str, float]) -> float:
        """Calculate total portfolio value"""

    def get_position_size(self, ticker: str, score: float, risk_level: str) -> int:
        """Calculate position size based on score and risk"""
        # Kelly Criterion or fixed-fractional

    def can_open_position(self, ticker: str, estimated_cost: float) -> bool:
        """Check if we have enough cash"""

    def open_position(self, ticker: str, quantity: int, price: float,
                     stop_loss: float, target: float, reason: str):
        """Execute BUY"""

    def close_position(self, ticker: str, price: float, reason: str):
        """Execute SELL"""

    def update_prices(self, current_prices: Dict[str, float]):
        """Update unrealized P&L"""

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Calculate Sharpe, returns, win rate, etc."""
```

#### 2.2 Order Executor

**File:** `paper_trading/order_executor.py`

```python
class OrderExecutor:
    """Simulates realistic order execution"""

    def __init__(self, slippage_pct: float = 0.05, transaction_cost_pct: float = 0.1):
        self.slippage_pct = slippage_pct
        self.transaction_cost_pct = transaction_cost_pct

    def execute_market_order(self, ticker: str, action: str, quantity: int,
                            current_price: float) -> Dict[str, Any]:
        """
        Simulate market order with:
        - Slippage (0.05% default)
        - Transaction costs (0.1% default = brokerage + STT + taxes)
        - Realistic fill price
        """

        # Simulate slippage
        if action == 'BUY':
            fill_price = current_price * (1 + self.slippage_pct / 100)
        else:
            fill_price = current_price * (1 - self.slippage_pct / 100)

        # Calculate costs
        order_value = fill_price * quantity
        transaction_cost = order_value * (self.transaction_cost_pct / 100)

        return {
            'status': 'filled',
            'fill_price': fill_price,
            'quantity': quantity,
            'transaction_cost': transaction_cost,
            'timestamp': datetime.now()
        }

    def check_stop_loss(self, position: Position, current_price: float) -> bool:
        """Check if stop loss hit"""

    def check_target(self, position: Position, current_price: float) -> bool:
        """Check if target hit"""
```

#### 2.3 Transaction Cost Modeling

**File:** `paper_trading/transaction_costs.py`

```python
class TransactionCostModel:
    """Realistic Indian stock market transaction costs"""

    # NSE cost structure (as of 2025)
    BROKERAGE = 0.03  # 0.03% or ₹20 per order (whichever lower)
    STT = 0.025  # 0.025% on sell side
    EXCHANGE_CHARGES = 0.00325  # 0.00325%
    GST = 0.18  # 18% on brokerage + exchange charges
    SEBI_CHARGES = 0.0001  # ₹10 per crore
    STAMP_DUTY = 0.015  # 0.015% on buy side

    @classmethod
    def calculate_total_cost(cls, order_value: float, action: str) -> Dict[str, float]:
        """Calculate all transaction costs"""

        costs = {}

        # Brokerage
        costs['brokerage'] = min(order_value * cls.BROKERAGE / 100, 20)

        # STT (only on sell)
        if action == 'SELL':
            costs['stt'] = order_value * cls.STT / 100
        else:
            costs['stt'] = 0

        # Exchange charges
        costs['exchange'] = order_value * cls.EXCHANGE_CHARGES / 100

        # GST
        costs['gst'] = (costs['brokerage'] + costs['exchange']) * cls.GST

        # SEBI
        costs['sebi'] = order_value * cls.SEBI_CHARGES / 100

        # Stamp duty (only on buy)
        if action == 'BUY':
            costs['stamp'] = order_value * cls.STAMP_DUTY / 100
        else:
            costs['stamp'] = 0

        costs['total'] = sum(costs.values())
        costs['percentage'] = (costs['total'] / order_value) * 100

        return costs
```

**Expected total costs:** ~0.15% on BUY, ~0.10% on SELL

#### 2.4 Paper Trading Engine

**File:** `paper_trading/engine.py`

```python
class PaperTradingEngine:
    """Main paper trading orchestrator"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.portfolio = Portfolio(config['initial_capital'])
        self.order_executor = OrderExecutor()
        self.data_stream = LiveDataStream(config['watchlist'])
        self.orchestrator = Orchestrator(config['orchestrator_config'])
        self.risk_manager = RiskManager(config['risk_config'])

        self.is_running = False

    async def start(self):
        """Start paper trading"""
        self.is_running = True

        # Start data stream
        await self.data_stream.start()

        # Monitor loop
        while self.is_running:
            if self.data_stream.is_market_open():
                await self._scan_and_trade()

            await asyncio.sleep(60)  # Check every minute

    async def _scan_and_trade(self):
        """Scan watchlist and execute trades"""

        for ticker in self.config['watchlist']:
            # Get latest price
            price_data = await self.data_stream.get_latest_price(ticker)

            # Check existing positions for stop-loss/target
            if ticker in self.portfolio.positions:
                await self._manage_position(ticker, price_data)

            # Check for new entry signals
            else:
                await self._check_entry_signal(ticker, price_data)

    async def _check_entry_signal(self, ticker: str, price_data: Dict):
        """Check if orchestrator signals BUY"""

        # Run orchestrator analysis
        result = await self.orchestrator.analyze(ticker, {
            'company_name': self._get_company_name(ticker),
            'market_regime': self._detect_market_regime()
        })

        decision = result.get('decision')

        if decision in ['BUY', 'STRONG BUY']:
            # Risk check
            if not self.risk_manager.can_open_position(self.portfolio, ticker, result):
                self.logger.warning(f"❌ Risk check failed for {ticker}")
                return

            # Calculate position size
            quantity = self.portfolio.get_position_size(
                ticker,
                result['composite_score'],
                result.get('risk_level', 'medium')
            )

            # Execute order
            order_result = self.order_executor.execute_market_order(
                ticker, 'BUY', quantity, price_data['price']
            )

            # Update portfolio
            self.portfolio.open_position(
                ticker=ticker,
                quantity=order_result['quantity'],
                price=order_result['fill_price'],
                stop_loss=result.get('stop_loss'),
                target=result.get('target_price'),
                reason=result.get('decision_reasoning', '')
            )

            self.logger.info(f"✅ OPENED {ticker}: {quantity} shares @ ₹{order_result['fill_price']:.2f}")

    async def _manage_position(self, ticker: str, price_data: Dict):
        """Manage existing position (stop-loss, target, trailing)"""

        position = self.portfolio.positions[ticker]
        current_price = price_data['price']

        # Check stop loss
        if self.order_executor.check_stop_loss(position, current_price):
            await self._close_position(ticker, current_price, 'stop_loss_hit')
            return

        # Check target
        if self.order_executor.check_target(position, current_price):
            await self._close_position(ticker, current_price, 'target_reached')
            return

        # Re-analyze for exit signals
        result = await self.orchestrator.analyze(ticker, {})
        if result.get('decision') == 'SELL':
            await self._close_position(ticker, current_price, 'sell_signal')

    async def _close_position(self, ticker: str, price: float, reason: str):
        """Close position"""

        position = self.portfolio.positions[ticker]

        order_result = self.order_executor.execute_market_order(
            ticker, 'SELL', position.quantity, price
        )

        self.portfolio.close_position(ticker, order_result['fill_price'], reason)

        self.logger.info(f"✅ CLOSED {ticker}: P&L = ₹{position.realized_pnl:.2f} ({reason})")
```

---

## 🛡️ Phase 3: Risk Management (Week 2)

### Objective
Implement portfolio-level risk controls.

### Tasks

#### 3.1 Risk Manager

**File:** `paper_trading/risk_manager.py`

```python
class RiskManager:
    """Portfolio-level risk controls"""

    def __init__(self, config: Dict[str, Any]):
        self.max_position_size_pct = config.get('max_position_size_pct', 5.0)
        self.max_portfolio_risk_pct = config.get('max_portfolio_risk_pct', 2.0)
        self.max_open_positions = config.get('max_open_positions', 10)
        self.max_sector_exposure_pct = config.get('max_sector_exposure_pct', 30.0)
        self.max_drawdown_pct = config.get('max_drawdown_pct', 10.0)

    def can_open_position(self, portfolio: Portfolio, ticker: str,
                         analysis: Dict[str, Any]) -> bool:
        """Check if position passes risk checks"""

        checks = []

        # Check 1: Max open positions
        if len(portfolio.positions) >= self.max_open_positions:
            checks.append(('max_positions', False, f"Already have {len(portfolio.positions)} positions"))
        else:
            checks.append(('max_positions', True, ''))

        # Check 2: Position size limit
        estimated_cost = analysis.get('estimated_cost', 0)
        position_pct = (estimated_cost / portfolio.get_total_value()) * 100
        if position_pct > self.max_position_size_pct:
            checks.append(('position_size', False, f"Position {position_pct:.1f}% > {self.max_position_size_pct}%"))
        else:
            checks.append(('position_size', True, ''))

        # Check 3: Portfolio risk (stop-loss based)
        stop_loss = analysis.get('stop_loss')
        current_price = analysis.get('current_price')
        if stop_loss and current_price:
            risk_per_share = current_price - stop_loss
            total_risk = risk_per_share * analysis.get('quantity', 0)
            risk_pct = (total_risk / portfolio.cash) * 100

            if risk_pct > self.max_portfolio_risk_pct:
                checks.append(('portfolio_risk', False, f"Risk {risk_pct:.1f}% > {self.max_portfolio_risk_pct}%"))
            else:
                checks.append(('portfolio_risk', True, ''))

        # Check 4: Drawdown limit
        current_drawdown = portfolio.get_current_drawdown_pct()
        if current_drawdown > self.max_drawdown_pct:
            checks.append(('drawdown', False, f"Drawdown {current_drawdown:.1f}% > {self.max_drawdown_pct}%"))
        else:
            checks.append(('drawdown', True, ''))

        # All checks must pass
        all_passed = all(check[1] for check in checks)

        if not all_passed:
            failed = [check for check in checks if not check[1]]
            self.logger.warning(f"❌ Risk checks failed for {ticker}:")
            for check in failed:
                self.logger.warning(f"  - {check[0]}: {check[2]}")

        return all_passed

    def get_position_size(self, portfolio: Portfolio, analysis: Dict[str, Any]) -> int:
        """Calculate safe position size using Kelly Criterion"""

        # Kelly Criterion: f = (bp - q) / b
        # where f = fraction to bet, b = odds, p = win probability, q = loss probability

        win_rate = analysis.get('backtest', {}).get('win_rate', 50) / 100
        avg_win = analysis.get('backtest', {}).get('avg_win_pct', 5) / 100
        avg_loss = analysis.get('backtest', {}).get('avg_loss_pct', 3) / 100

        if avg_loss == 0:
            kelly_fraction = 0.02  # Default 2%
        else:
            kelly_fraction = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
            kelly_fraction = max(0, min(kelly_fraction, 0.05))  # Cap at 5%

        # Use fraction of Kelly (0.5x for safety)
        position_value = portfolio.get_total_value() * kelly_fraction * 0.5

        current_price = analysis.get('current_price', 0)
        if current_price == 0:
            return 0

        quantity = int(position_value / current_price)

        return quantity
```

---

## 📊 Phase 4: Monitoring Dashboard (Week 2-3)

### Objective
Build Streamlit dashboard for live monitoring.

### Tasks

#### 4.1 Main Dashboard

**File:** `dashboard/app.py`

```python
import streamlit as st
from paper_trading.engine import PaperTradingEngine
from paper_trading.portfolio import Portfolio

st.set_page_config(page_title="Paper Trading Dashboard", layout="wide")

st.title("🤖 Agentic Trading System - Paper Trading")

# Sidebar: Controls
with st.sidebar:
    st.header("Controls")

    if st.button("▶️ Start Paper Trading"):
        st.session_state.engine_running = True

    if st.button("⏸️ Pause"):
        st.session_state.engine_running = False

    st.header("Settings")
    initial_capital = st.number_input("Initial Capital (₹)", value=1000000, step=100000)
    watchlist_input = st.text_area("Watchlist (one per line)", value="RELIANCE.NS\nTCS.NS\nHDFCBANK.NS")

# Main area: Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Portfolio", "🎯 Signals", "📈 Analytics", "🤖 Decisions"])

with tab1:
    # Portfolio overview
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Value", f"₹{portfolio.get_total_value():,.2f}")

    with col2:
        total_return = portfolio.get_total_return_pct()
        st.metric("Total Return", f"{total_return:+.2f}%", delta=f"₹{portfolio.get_unrealized_pnl():,.2f}")

    with col3:
        st.metric("Open Positions", len(portfolio.positions))

    with col4:
        st.metric("Cash", f"₹{portfolio.cash:,.2f}")

    # Positions table
    st.subheader("Open Positions")
    if portfolio.positions:
        positions_df = portfolio.get_positions_df()
        st.dataframe(positions_df, use_container_width=True)
    else:
        st.info("No open positions")

    # Recent trades
    st.subheader("Recent Trades")
    if portfolio.trade_history:
        trades_df = portfolio.get_trades_df()
        st.dataframe(trades_df.tail(10), use_container_width=True)

with tab2:
    # Live signals
    st.subheader("Live Signals")

    for ticker in watchlist:
        with st.expander(f"📊 {ticker}"):
            # Show latest orchestrator decision
            signal = get_latest_signal(ticker)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Decision", signal['decision'])
            with col2:
                st.metric("Score", f"{signal['score']:.1f}/100")
            with col3:
                st.metric("Confidence", f"{signal['confidence']}%")

            # Agent scores breakdown
            st.write("**Agent Scores:**")
            agent_scores = signal.get('agent_scores', {})
            st.bar_chart(agent_scores)

with tab3:
    # Performance analytics
    st.subheader("Performance Metrics")

    col1, col2, col3 = st.columns(3)

    metrics = portfolio.get_performance_metrics()

    with col1:
        st.metric("Sharpe Ratio", f"{metrics.get('sharpe_ratio', 0):.2f}")
        st.metric("Win Rate", f"{metrics.get('win_rate', 0):.1f}%")

    with col2:
        st.metric("Max Drawdown", f"{metrics.get('max_drawdown', 0):.1f}%")
        st.metric("Avg Win", f"{metrics.get('avg_win_pct', 0):.1f}%")

    with col3:
        st.metric("Total Trades", metrics.get('total_trades', 0))
        st.metric("Avg Loss", f"{metrics.get('avg_loss_pct', 0):.1f}%")

    # Equity curve
    st.subheader("Equity Curve")
    equity_df = portfolio.get_equity_curve()
    st.line_chart(equity_df)

with tab4:
    # Agent decision details
    st.subheader("Agent Decisions Breakdown")

    selected_ticker = st.selectbox("Select Stock", watchlist)

    if selected_ticker:
        decision_details = get_decision_details(selected_ticker)

        # Show conflict analysis
        if decision_details.get('conflict_analysis', {}).get('has_conflict'):
            st.warning("⚔️ Agent Conflict Detected")

            conflict = decision_details['conflict_analysis']
            st.write(f"**Level:** {conflict['conflict_level']}")
            st.write(f"**Variance:** {conflict['variance']:.3f}")

        # Show LLM synthesis
        if decision_details.get('used_llm_synthesis'):
            st.info("🤖 LLM Synthesis Used")

            llm = decision_details['llm_synthesis']
            st.write(f"**Reasoning:** {llm['reasoning']}")
            st.write("**Key Insights:**")
            for insight in llm['key_insights']:
                st.write(f"- {insight}")
```

---

## 🧪 Phase 5: Testing & Validation (Week 3)

### Tasks

#### 5.1 Unit Tests

**File:** `tests/test_paper_engine.py`

```python
import pytest
from paper_trading.engine import PaperTradingEngine
from paper_trading.portfolio import Portfolio

@pytest.fixture
def engine():
    config = {
        'initial_capital': 1000000,
        'watchlist': ['RELIANCE.NS', 'TCS.NS'],
        'orchestrator_config': {...},
        'risk_config': {...}
    }
    return PaperTradingEngine(config)

def test_portfolio_initialization(engine):
    assert engine.portfolio.cash == 1000000
    assert len(engine.portfolio.positions) == 0

def test_position_opening(engine):
    engine.portfolio.open_position(
        ticker='RELIANCE.NS',
        quantity=100,
        price=2850.0,
        stop_loss=2800.0,
        target=2950.0,
        reason='test'
    )

    assert 'RELIANCE.NS' in engine.portfolio.positions
    assert engine.portfolio.cash < 1000000  # Cash reduced

def test_stop_loss_trigger(engine):
    # Open position
    engine.portfolio.open_position('RELIANCE.NS', 100, 2850.0, 2800.0, 2950.0, 'test')

    # Price drops to stop loss
    position = engine.portfolio.positions['RELIANCE.NS']
    assert engine.order_executor.check_stop_loss(position, 2795.0) == True

def test_transaction_costs(engine):
    order_value = 285000  # 100 shares @ 2850
    costs = engine.order_executor.transaction_cost_model.calculate_total_cost(order_value, 'BUY')

    assert costs['total'] > 0
    assert costs['percentage'] < 0.5  # Should be under 0.5%
```

#### 5.2 Integration Test

**File:** `tests/test_integration_paper_trading.py`

```python
@pytest.mark.asyncio
async def test_full_paper_trading_cycle():
    """Test complete cycle: signal detection -> order execution -> position management -> exit"""

    engine = PaperTradingEngine({...})

    # Start engine
    await engine.start()

    # Wait for market open
    await asyncio.sleep(10)

    # Simulate BUY signal
    # (mock orchestrator to return BUY decision)

    # Verify position opened
    assert len(engine.portfolio.positions) > 0

    # Simulate price movement to target
    # Verify position closed

    # Check P&L recorded
    assert len(engine.portfolio.trade_history) == 2  # BUY + SELL
```

---

## 📋 Configuration File

**File:** `config/paper_trading_config.yaml`

```yaml
paper_trading:
  initial_capital: 1000000

  watchlist:
    - RELIANCE.NS
    - TCS.NS
    - HDFCBANK.NS
    - INFY.NS
    - ICICIBANK.NS
    - BHARTIARTL.NS
    - BAJFINANCE.NS
    - TITAN.NS
    - MARUTI.NS
    - TATAMOTORS.NS

  data_stream:
    provider: yfinance
    update_interval_seconds: 60
    cache_max_days: 1825

  order_execution:
    slippage_pct: 0.05
    transaction_cost_pct: 0.15  # Total costs

  risk_management:
    max_position_size_pct: 5.0
    max_portfolio_risk_pct: 2.0
    max_open_positions: 10
    max_sector_exposure_pct: 30.0
    max_drawdown_pct: 10.0

  orchestrator:
    weights:
      fundamental: 0.25
      technical: 0.20
      sentiment: 0.20
      management: 0.15
      market_regime: 0.10
      risk_adjustment: 0.10

    buy_threshold: 70.0
    strong_buy_threshold: 85.0
    sell_threshold: 40.0

    technical_config:
      lookback_days: 1825
      min_pattern_confidence: 70.0

    backtest_config:
      historical_years: 5
      min_win_rate: 70.0

  dashboard:
    port: 8501
    refresh_interval_seconds: 5
```

---

## 🚀 Deployment Steps

### Week 1: Foundation
1. ✅ Implement `data_stream.py` with yfinance
2. ✅ Implement `portfolio.py` with state management
3. ✅ Implement `order_executor.py` with transaction costs
4. ✅ Test basic position opening/closing

### Week 2: Core Engine
1. ✅ Implement `engine.py` with main loop
2. ✅ Implement `risk_manager.py`
3. ✅ Connect to orchestrator
4. ✅ Test signal detection → order execution flow

### Week 3: Dashboard & Testing
1. ✅ Build Streamlit dashboard
2. ✅ Add live monitoring views
3. ✅ Write comprehensive tests
4. ✅ Run 1-week live paper trading test

---

## 📊 Success Metrics

**After 1 week of paper trading:**
- System runs without crashes
- All orders executed successfully
- Stop-losses and targets working
- Risk limits respected
- Performance metrics calculated correctly

**After 1 month of paper trading:**
- Evaluate strategy performance vs buy-and-hold
- Assess win rate vs backtested expectations
- Measure Sharpe ratio
- Identify any system improvements needed

**Minimum acceptable results (1 month):**
- Win rate ≥ 60%
- Sharpe ratio ≥ 1.0
- Max drawdown < 10%
- Avg win > Avg loss (R:R > 1.5)

If metrics acceptable → proceed to broker API integration for real trading

---

## 💰 Estimated Costs

| Component | Cost |
|-----------|------|
| Data (yfinance) | FREE |
| LLM calls (GPT-4) | ~$0.01/stock/day |
| Hosting (local) | FREE |
| Dashboard | FREE |
| **Total (10 stocks)** | **~$0.10/day = $3/month** |

---

## 🔄 Next Steps After Paper Trading Success

1. **Broker API Integration**
   - Zerodha Kite Connect
   - IBKR API
   - Real order execution

2. **Production Deployment**
   - AWS/GCP hosting
   - Redis for caching
   - PostgreSQL for data
   - Monitoring/alerting

3. **Advanced Features**
   - Portfolio optimization
   - Multi-timeframe analysis
   - Advanced order types (trailing stop, OCO)
   - Risk parity position sizing

---

**Status:** 📋 **PLAN COMPLETE - READY TO IMPLEMENT**
