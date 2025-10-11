#!/bin/bash
# Start automated paper trading during market hours

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR" || exit 1

# Create logs directory
mkdir -p logs

# Check if it's a weekday (Monday=1, Friday=5)
DAY_OF_WEEK=$(date +%u)
if [ "$DAY_OF_WEEK" -gt 5 ]; then
    echo "⏸️  Today is weekend - markets are closed"
    echo "   Paper trading will start on Monday"
    exit 0
fi

# Check if it's during market hours (9:15 AM - 3:30 PM IST)
CURRENT_HOUR=$(date +%H)
CURRENT_MINUTE=$(date +%M)
CURRENT_TIME=$((10#$CURRENT_HOUR * 60 + 10#$CURRENT_MINUTE))

MARKET_OPEN=$((9 * 60 + 15))   # 9:15 AM
MARKET_CLOSE=$((15 * 60 + 30))  # 3:30 PM

if [ "$CURRENT_TIME" -lt "$MARKET_OPEN" ]; then
    echo "⏰ Markets not open yet (opens at 9:15 AM IST)"
    echo "   Current time: $(date +%H:%M)"
    echo "   Waiting..."
    sleep $((($MARKET_OPEN - $CURRENT_TIME) * 60))
fi

if [ "$CURRENT_TIME" -gt "$MARKET_CLOSE" ]; then
    echo "🔔 Markets are closed (closed at 3:30 PM IST)"
    echo "   Current time: $(date +%H:%M)"
    echo "   Paper trading will resume tomorrow"
    exit 0
fi

echo "🚀 Starting Automated Paper Trading..."
echo "📁 Project directory: $PROJECT_DIR"
echo "📅 Date: $(date +%Y-%m-%d)"
echo "⏰ Time: $(date +%H:%M:%S)"
echo ""

# Check API keys
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ Error: OPENAI_API_KEY not set"
    exit 1
fi

if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "❌ Error: ANTHROPIC_API_KEY not set"
    exit 1
fi

echo "✅ API keys configured"
echo ""

# Start paper trading in background
echo "💼 Starting paper trading engine..."
nohup python3 paper_trading/run_paper_trading.py > logs/paper_trading.log 2>&1 &
PAPER_PID=$!
echo "   Paper Trading PID: $PAPER_PID"

# Save PID
echo "$PAPER_PID" > logs/paper_trading.pid

echo ""
echo "✅ Paper trading started successfully!"
echo ""
echo "📋 Monitor logs:"
echo "   • tail -f logs/paper_trading.log"
echo ""
echo "📊 View portfolio:"
echo "   • curl http://localhost:8000/portfolio"
echo ""
echo "🛑 To stop: ./deploy/stop_services.sh"
echo ""

# Create a scheduled job to stop at market close if needed
STOP_TIME=$((($MARKET_CLOSE - $CURRENT_TIME) * 60))
if [ "$STOP_TIME" -gt 0 ]; then
    echo "⏰ Will auto-stop at 3:30 PM (in $((STOP_TIME / 60)) minutes)"
    (
        sleep "$STOP_TIME"
        if [ -f logs/paper_trading.pid ]; then
            PAPER_PID=$(cat logs/paper_trading.pid)
            kill "$PAPER_PID" 2>/dev/null
            rm logs/paper_trading.pid
            echo "$(date +%Y-%m-%d\ %H:%M:%S) - Market closed, stopped paper trading" >> logs/paper_trading.log
        fi
    ) &
fi

echo ""
echo "🎯 Paper trading is now active!"
echo "   Markets close at 3:30 PM IST"
