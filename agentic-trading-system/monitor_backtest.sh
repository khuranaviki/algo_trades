#!/bin/bash

# Monitor backtest progress and watch for bugs

LOG_FILE="v40_backtest_FINAL.log"

echo "====================================="
echo "  BACKTEST MONITOR"
echo "====================================="
echo ""

while true; do
    clear
    echo "====================================="
    echo "  BACKTEST PROGRESS MONITOR"
    echo "  $(date '+%Y-%m-%d %H:%M:%S')"
    echo "====================================="
    echo ""

    # Check if process is running
    if ps aux | grep -q "[r]un_historical_backtest.py.*RELIANCE.*HEROMOTOCO"; then
        echo "✅ Status: RUNNING"
    else
        echo "❌ Status: NOT RUNNING"
    fi
    echo ""

    # Show progress
    echo "📊 Progress:"
    tail -50 "$LOG_FILE" | grep -E "Simulating:|Downloaded" | tail -3
    echo ""

    # Show recent decisions
    echo "🎯 Recent Decisions:"
    tail -100 "$LOG_FILE" | grep "Decision:" | tail -5
    echo ""

    # Check for errors
    ERROR_COUNT=$(tail -200 "$LOG_FILE" | grep -c "ERROR")
    if [ $ERROR_COUNT -gt 0 ]; then
        echo "⚠️  Errors detected: $ERROR_COUNT"
        echo "Latest errors:"
        tail -200 "$LOG_FILE" | grep "ERROR" | tail -3
    else
        echo "✅ No errors in last 200 lines"
    fi
    echo ""

    # Check for crashes
    if tail -50 "$LOG_FILE" | grep -q "AttributeError\|KeyError\|TypeError"; then
        echo "🚨 CRASH DETECTED!"
        tail -50 "$LOG_FILE" | grep -A3 "Error\|Traceback"
    fi
    echo ""

    # Show Perplexity API status
    PERP_401=$(tail -100 "$LOG_FILE" | grep -c "401 Authorization")
    if [ $PERP_401 -gt 5 ]; then
        echo "⚠️  Perplexity 401 errors: $PERP_401 (API key issue)"
    else
        echo "✅ Perplexity API: OK"
    fi
    echo ""

    echo "====================================="
    echo "Press Ctrl+C to stop monitoring"
    echo "Refreshing in 30 seconds..."
    sleep 30
done
