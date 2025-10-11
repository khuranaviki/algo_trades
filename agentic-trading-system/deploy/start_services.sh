#!/bin/bash
# Start both FastAPI and Streamlit services

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR" || exit 1

# Create logs directory
mkdir -p logs

echo "🚀 Starting Agentic Trading System..."
echo "📁 Project directory: $PROJECT_DIR"
echo ""

# Check API keys
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  Warning: OPENAI_API_KEY not set"
fi

if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⚠️  Warning: ANTHROPIC_API_KEY not set"
fi

echo ""

# Start FastAPI in background
echo "🔧 Starting FastAPI server on port 8000..."
nohup uvicorn api.main:app --host 0.0.0.0 --port 8000 > logs/api.log 2>&1 &
API_PID=$!
echo "   FastAPI PID: $API_PID"

# Wait for API to be ready
sleep 3

# Start Streamlit in background
echo "📊 Starting Streamlit dashboard on port 8501..."
nohup streamlit run streamlit_app.py --server.port 8501 --server.headless true > logs/streamlit.log 2>&1 &
STREAMLIT_PID=$!
echo "   Streamlit PID: $STREAMLIT_PID"

# Wait for Streamlit to be ready
sleep 3

echo ""
echo "✅ Services started successfully!"
echo ""
echo "📍 Access points:"
echo "   • Streamlit Dashboard: http://localhost:8501"
echo "   • FastAPI Swagger Docs: http://localhost:8000/docs"
echo "   • API Health: http://localhost:8000/health"
echo ""
echo "📋 Logs:"
echo "   • API: tail -f logs/api.log"
echo "   • Streamlit: tail -f logs/streamlit.log"
echo ""
echo "🛑 To stop services: ./deploy/stop_services.sh"
echo ""

# Save PIDs for later
echo "$API_PID" > logs/api.pid
echo "$STREAMLIT_PID" > logs/streamlit.pid

# Health check
echo "🔍 Running health checks..."
sleep 2

if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "   ✅ FastAPI is healthy"
else
    echo "   ❌ FastAPI health check failed"
fi

if curl -s http://localhost:8501/_stcore/health > /dev/null 2>&1; then
    echo "   ✅ Streamlit is healthy"
else
    echo "   ❌ Streamlit health check failed (might still be starting)"
fi

echo ""
echo "🎯 Ready for trading!"
