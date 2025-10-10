#!/bin/bash

# Full 6-Month Backtest on Nifty V40 Stocks
# With all fixes applied:
# - Pattern type bug fixed
# - Backtest validator consistency fixed
# - No holding period limits

echo "=================================="
echo "  FULL V40 6-MONTH BACKTEST"
echo "  All Fixes Applied"
echo "=================================="
echo ""
echo "Fixes:"
echo "  ✅ Pattern type recognition (CWH, RHS, etc.)"
echo "  ✅ Backtest validator consistency (trust pattern validator)"
echo "  ✅ No holding period limits"
echo ""
echo "Configuration:"
echo "  Period: Last 6 months"
echo "  Stocks: Nifty V40 (40 stocks)"
echo "  Initial Capital: ₹10,00,000"
echo "  Data: 5 years historical for each decision"
echo ""
echo "Starting backtest..."
echo ""

python3 run_historical_backtest.py \
  --months 6 \
  --stocks \
    RELIANCE.NS \
    TCS.NS \
    HDFCBANK.NS \
    INFY.NS \
    ICICIBANK.NS \
    HINDUNILVR.NS \
    ITC.NS \
    LT.NS \
    SBIN.NS \
    BHARTIARTL.NS \
    BAJFINANCE.NS \
    ASIANPAINT.NS \
    MARUTI.NS \
    HCLTECH.NS \
    TITAN.NS \
    KOTAKBANK.NS \
    ULTRACEMCO.NS \
    AXISBANK.NS \
    SUNPHARMA.NS \
    NESTLEIND.NS \
    WIPRO.NS \
    ONGC.NS \
    NTPC.NS \
    POWERGRID.NS \
    TATAMOTORS.NS \
    TATASTEEL.NS \
    TECHM.NS \
    ADANIPORTS.NS \
    INDUSINDBK.NS \
    JSWSTEEL.NS \
    BAJAJFINSV.NS \
    DIVISLAB.NS \
    DRREDDY.NS \
    BRITANNIA.NS \
    COALINDIA.NS \
    GRASIM.NS \
    HINDALCO.NS \
    BPCL.NS \
    EICHERMOT.NS \
    HEROMOTOCO.NS \
  2>&1 | tee v40_full_6month_backtest_FINAL.log
