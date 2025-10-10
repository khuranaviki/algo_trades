#!/bin/bash

# Start FastAPI Server for Agentic Trading System

echo "🚀 Starting Agentic Trading System API Server..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📍 API will be available at:"
echo "   http://localhost:8000"
echo ""
echo "📚 API Documentation:"
echo "   Swagger UI: http://localhost:8000/api/docs"
echo "   ReDoc:      http://localhost:8000/api/redoc"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  WARNING: .env file not found!"
    echo "   Please create .env with API keys (see .env.example)"
    echo ""
fi

# Start uvicorn server
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
