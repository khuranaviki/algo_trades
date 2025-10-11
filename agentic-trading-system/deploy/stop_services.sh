#!/bin/bash
# Stop all running services

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR" || exit 1

echo "🛑 Stopping Agentic Trading System..."
echo ""

# Stop by PID files if they exist
if [ -f logs/api.pid ]; then
    API_PID=$(cat logs/api.pid)
    echo "🔧 Stopping FastAPI (PID: $API_PID)..."
    kill "$API_PID" 2>/dev/null && echo "   ✅ Stopped" || echo "   ⚠️  Not running"
    rm logs/api.pid
fi

if [ -f logs/streamlit.pid ]; then
    STREAMLIT_PID=$(cat logs/streamlit.pid)
    echo "📊 Stopping Streamlit (PID: $STREAMLIT_PID)..."
    kill "$STREAMLIT_PID" 2>/dev/null && echo "   ✅ Stopped" || echo "   ⚠️  Not running"
    rm logs/streamlit.pid
fi

if [ -f logs/paper_trading.pid ]; then
    PAPER_PID=$(cat logs/paper_trading.pid)
    echo "💼 Stopping Paper Trading (PID: $PAPER_PID)..."
    kill "$PAPER_PID" 2>/dev/null && echo "   ✅ Stopped" || echo "   ⚠️  Not running"
    rm logs/paper_trading.pid
fi

# Fallback: Kill by process name
echo ""
echo "🔍 Checking for any remaining processes..."

pkill -f "uvicorn api.main" && echo "   ✅ Killed uvicorn processes"
pkill -f "streamlit run" && echo "   ✅ Killed streamlit processes"
pkill -f "run_paper_trading" && echo "   ✅ Killed paper trading processes"

echo ""
echo "✅ All services stopped"
