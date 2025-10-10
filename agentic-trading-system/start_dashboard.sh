#!/bin/bash

# Start Streamlit Dashboard for Agentic Trading System

echo "🚀 Starting Agentic Trading System Dashboard..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📍 Dashboard will be available at:"
echo "   http://localhost:8501"
echo ""
echo "📊 Features:"
echo "   • Live Analysis: Real-time stock analysis"
echo "   • Portfolio: View positions and P&L"
echo "   • Performance: Charts and analytics"
echo "   • Settings: Configure trading parameters"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  WARNING: .env file not found!"
    echo "   Please create .env with API keys (see .env.example)"
    echo ""
fi

# Start Streamlit
streamlit run streamlit_app.py
