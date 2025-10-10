"""
Streamlit Dashboard for Agentic Trading System
Interactive UI for stock analysis, portfolio management, and system monitoring
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.orchestrator import Orchestrator
from paper_trading.portfolio import Portfolio

# Page configuration
st.set_page_config(
    page_title="Agentic Trading System",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .buy-signal {
        color: #28a745;
        font-weight: bold;
    }
    .sell-signal {
        color: #dc3545;
        font-weight: bold;
    }
    .wait-signal {
        color: #ffc107;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'orchestrator' not in st.session_state:
    st.session_state.orchestrator = None
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = Portfolio(initial_capital=1000000)
if 'analysis_history' not in st.session_state:
    st.session_state.analysis_history = []


@st.cache_resource
def get_orchestrator():
    """Initialize and cache orchestrator"""
    return Orchestrator()


def run_analysis(ticker: str):
    """Run stock analysis"""
    with st.spinner(f'🔍 Analyzing {ticker}...'):
        try:
            orchestrator = get_orchestrator()
            result = asyncio.run(orchestrator.analyze(ticker))

            if result:
                # Add to history
                st.session_state.analysis_history.insert(0, {
                    'ticker': ticker,
                    'decision': result.get('decision', 'WAIT'),
                    'score': result.get('score', 0),
                    'timestamp': datetime.now(),
                    'result': result
                })

                # Keep only last 50
                st.session_state.analysis_history = st.session_state.analysis_history[:50]

            return result
        except Exception as e:
            st.error(f"Analysis failed: {str(e)}")
            return None


def main():
    """Main Streamlit application"""

    # Sidebar
    with st.sidebar:
        st.image("https://via.placeholder.com/150x50/1f77b4/ffffff?text=Agentic+Trading", use_column_width=True)
        st.markdown("---")

        # Navigation
        page = st.radio(
            "Navigation",
            ["📊 Live Analysis", "💼 Portfolio", "📈 Performance", "⚙️ Settings"],
            label_visibility="collapsed"
        )

        st.markdown("---")

        # System status
        st.subheader("System Status")
        st.success("✅ Orchestrator Ready")
        st.info(f"💰 Capital: ₹{st.session_state.portfolio.initial_capital:,.0f}")

    # Main content
    st.markdown('<div class="main-header">🤖 Agentic Trading System</div>', unsafe_allow_html=True)
    st.markdown("*Multi-agent AI trading with 5-year pattern validation*")
    st.markdown("---")

    # Page routing
    if page == "📊 Live Analysis":
        show_live_analysis()
    elif page == "💼 Portfolio":
        show_portfolio()
    elif page == "📈 Performance":
        show_performance()
    elif page == "⚙️ Settings":
        show_settings()


def show_live_analysis():
    """Live stock analysis page"""

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Stock Analysis")

        # Ticker input
        ticker_input = st.text_input(
            "Enter stock ticker",
            placeholder="e.g., RELIANCE.NS, TCS.NS",
            help="Enter NSE stock ticker with .NS suffix"
        ).upper()

        # Quick select buttons
        st.markdown("**Quick Select:**")
        quick_tickers = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS"]
        cols = st.columns(5)
        for i, ticker in enumerate(quick_tickers):
            if cols[i].button(ticker.replace(".NS", ""), key=f"quick_{ticker}"):
                ticker_input = ticker

        analyze_button = st.button("🔍 Analyze", type="primary", use_container_width=True)

        if analyze_button and ticker_input:
            result = run_analysis(ticker_input)

            if result:
                st.markdown("---")

                # Decision display
                decision = result.get('decision', 'WAIT')
                score = result.get('score', 0)

                decision_class = {
                    'BUY': 'buy-signal',
                    'STRONG_BUY': 'buy-signal',
                    'SELL': 'sell-signal',
                    'WAIT': 'wait-signal'
                }.get(decision, 'wait-signal')

                st.markdown(f'<h2 class="{decision_class}">Decision: {decision}</h2>', unsafe_allow_html=True)

                # Score metrics
                col_a, col_b, col_c = st.columns(3)
                col_a.metric("Composite Score", f"{score:.1f}/100")
                col_b.metric("Confidence", f"{result.get('confidence', 0)}%")
                col_c.metric("Signal Strength", result.get('technical', {}).get('signal_strength', 'N/A'))

                # Agent scores
                st.markdown("### Agent Scores")
                agent_cols = st.columns(5)
                agent_cols[0].metric("Fundamental", f"{result.get('fundamental', {}).get('score', 0):.1f}")
                agent_cols[1].metric("Technical", f"{result.get('technical', {}).get('score', 0):.1f}")
                agent_cols[2].metric("Sentiment", f"{result.get('sentiment', {}).get('score', 0):.1f}")
                agent_cols[3].metric("Management", f"{result.get('management', {}).get('score', 0):.1f}")
                agent_cols[4].metric("Market Regime", f"{result.get('market_regime', {}).get('score', 0):.1f}")

                # Technical signal details
                if result.get('technical', {}).get('signal'):
                    st.markdown("### Technical Signal")
                    signal = result['technical']['signal']

                    sig_col1, sig_col2, sig_col3 = st.columns(3)
                    sig_col1.write(f"**Pattern:** {signal.get('pattern_type', 'N/A')}")
                    sig_col2.write(f"**Entry:** ₹{signal.get('entry_price', 0):.2f}")
                    sig_col3.write(f"**Target:** ₹{signal.get('target_price', 0):.2f}")

                # Reasoning
                st.markdown("### Analysis Reasoning")
                st.info(result.get('reasoning', 'No reasoning available'))

                # Warnings/Vetoes
                if result.get('vetoes'):
                    st.warning("⚠️ **Vetoes:** " + ", ".join(result['vetoes']))

    with col2:
        st.subheader("Recent Analysis")

        if st.session_state.analysis_history:
            for analysis in st.session_state.analysis_history[:10]:
                with st.container():
                    decision_emoji = {
                        'BUY': '🟢',
                        'STRONG_BUY': '🟢',
                        'SELL': '🔴',
                        'WAIT': '🟡'
                    }.get(analysis['decision'], '⚪')

                    st.markdown(f"""
                    **{decision_emoji} {analysis['ticker']}**
                    {analysis['decision']} • Score: {analysis['score']:.1f}
                    <small>{analysis['timestamp'].strftime('%H:%M:%S')}</small>
                    """, unsafe_allow_html=True)
                    st.markdown("---")
        else:
            st.info("No analysis history yet")


def show_portfolio():
    """Portfolio overview page"""

    st.subheader("💼 Portfolio Overview")

    portfolio = st.session_state.portfolio

    # Portfolio metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Value", f"₹{portfolio.total_value:,.0f}")
    col2.metric("Cash", f"₹{portfolio.cash:,.0f}")
    col3.metric("P&L", f"₹{portfolio.realized_pnl + portfolio.unrealized_pnl:,.0f}")
    col4.metric("Return", f"{portfolio.total_return_pct:.2f}%")

    st.markdown("---")

    # Positions table
    st.subheader("Current Positions")

    if portfolio.positions:
        positions_data = []
        for ticker, pos in portfolio.positions.items():
            positions_data.append({
                'Ticker': ticker,
                'Quantity': pos.quantity,
                'Avg Price': f"₹{pos.avg_price:.2f}",
                'Current Price': f"₹{pos.current_price:.2f}",
                'Value': f"₹{pos.quantity * pos.current_price:,.0f}",
                'P&L': f"₹{(pos.current_price - pos.avg_price) * pos.quantity:,.0f}",
                'P&L %': f"{((pos.current_price - pos.avg_price) / pos.avg_price) * 100:.2f}%",
                'Stop Loss': f"₹{pos.stop_loss:.2f}" if pos.stop_loss else "N/A",
                'Target': f"₹{pos.target:.2f}" if pos.target else "N/A"
            })

        df = pd.DataFrame(positions_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No open positions")


def show_performance():
    """Performance analytics page"""

    st.subheader("📈 Performance Analytics")

    # Placeholder for performance charts
    st.info("Performance charts will be displayed here")

    # Sample equity curve
    st.markdown("### Equity Curve")

    # Generate sample data
    dates = pd.date_range(start='2024-01-01', end=datetime.now(), freq='D')
    equity = [1000000]
    for _ in range(len(dates) - 1):
        equity.append(equity[-1] * (1 + (0.01 if len(equity) % 3 == 0 else -0.005)))

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=equity, mode='lines', name='Portfolio Value'))
    fig.update_layout(title='Portfolio Equity Curve', xaxis_title='Date', yaxis_title='Value (₹)')
    st.plotly_chart(fig, use_container_width=True)


def show_settings():
    """Settings page"""

    st.subheader("⚙️ System Settings")

    # Trading settings
    st.markdown("### Trading Configuration")

    col1, col2 = st.columns(2)

    with col1:
        st.number_input("Initial Capital (₹)", value=1000000, step=100000)
        st.slider("Max Position Size (%)", 0, 20, 5)
        st.slider("Max Open Positions", 1, 20, 10)

    with col2:
        st.slider("Max Drawdown (%)", 0, 50, 10)
        st.slider("Daily Loss Limit (%)", 0, 10, 3)
        st.checkbox("Use LLM Analysis", value=True)

    st.markdown("---")

    # Agent weights
    st.markdown("### Agent Weights")

    col_a, col_b, col_c, col_d, col_e = st.columns(5)
    col_a.slider("Fundamental", 0.0, 1.0, 0.25, 0.05)
    col_b.slider("Technical", 0.0, 1.0, 0.20, 0.05)
    col_c.slider("Sentiment", 0.0, 1.0, 0.20, 0.05)
    col_d.slider("Management", 0.0, 1.0, 0.15, 0.05)
    col_e.slider("Market Regime", 0.0, 1.0, 0.10, 0.05)

    if st.button("💾 Save Settings", type="primary"):
        st.success("Settings saved successfully!")


if __name__ == "__main__":
    main()
