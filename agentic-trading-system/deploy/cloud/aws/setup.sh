#!/bin/bash
# AWS EC2 Setup Script - Automated deployment
# Run this on a fresh Ubuntu 22.04 EC2 instance

set -e  # Exit on error

echo "============================================"
echo "🚀 Agentic Trading System - AWS EC2 Setup"
echo "============================================"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "❌ Please run as normal user, not root"
    exit 1
fi

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
echo "🐍 Installing Python 3.11..."
sudo apt install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev -y

# Install pip for Python 3.11
echo "📥 Installing pip..."
curl -sS https://bootstrap.pypa.io/get-pip.py | sudo python3.11

# Install system dependencies
echo "📚 Installing system dependencies..."
sudo apt install -y \
    git \
    curl \
    wget \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3.11-dev

# Create project directory if not exists
PROJECT_DIR="$HOME/agentic-trading-system"
if [ ! -d "$PROJECT_DIR" ]; then
    echo "📂 Project directory not found. Please clone the repository first:"
    echo "   git clone https://github.com/yourusername/agentic-trading-system.git $PROJECT_DIR"
    exit 1
fi

cd "$PROJECT_DIR"

# Install Python dependencies
echo "📦 Installing Python dependencies..."
python3.11 -m pip install --upgrade pip
python3.11 -m pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs data backups

# Prompt for API keys
echo ""
echo "🔑 Please enter your API keys:"
echo ""
read -p "OpenAI API Key: " OPENAI_KEY
read -p "Anthropic API Key: " ANTHROPIC_KEY

# Create .env file
cat > .env << EOF
OPENAI_API_KEY=$OPENAI_KEY
ANTHROPIC_API_KEY=$ANTHROPIC_KEY
EOF

chmod 600 .env

# Add to bashrc for permanent environment variables
if ! grep -q "OPENAI_API_KEY" ~/.bashrc; then
    echo "export OPENAI_API_KEY=\"$OPENAI_KEY\"" >> ~/.bashrc
    echo "export ANTHROPIC_API_KEY=\"$ANTHROPIC_KEY\"" >> ~/.bashrc
fi

# Source environment
source ~/.bashrc
export OPENAI_API_KEY="$OPENAI_KEY"
export ANTHROPIC_API_KEY="$ANTHROPIC_KEY"

# Create systemd service
echo "⚙️  Creating systemd service..."
sudo tee /etc/systemd/system/agentic-trading.service > /dev/null << EOF
[Unit]
Description=Agentic Trading System
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment="OPENAI_API_KEY=$OPENAI_KEY"
Environment="ANTHROPIC_API_KEY=$ANTHROPIC_KEY"
ExecStart=/bin/bash $PROJECT_DIR/deploy/start_services.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable agentic-trading

# Start service
echo "🚀 Starting services..."
sudo systemctl start agentic-trading

# Wait for services to start
sleep 5

# Check status
echo ""
echo "✅ Checking service status..."
sudo systemctl status agentic-trading --no-pager

# Setup cron for Monday trading
echo ""
echo "📅 Setting up cron for Monday morning trading..."
(crontab -l 2>/dev/null; echo "0 9 * * 1-5 $PROJECT_DIR/deploy/start_paper_trading.sh >> $PROJECT_DIR/logs/cron.log 2>&1") | crontab -

# Get instance IP
INSTANCE_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)

echo ""
echo "============================================"
echo "✅ Setup Complete!"
echo "============================================"
echo ""
echo "📊 Access Points:"
echo "   • Streamlit Dashboard: http://$INSTANCE_IP:8501"
echo "   • FastAPI Docs: http://$INSTANCE_IP:8000/docs"
echo "   • API Health: http://$INSTANCE_IP:8000/health"
echo ""
echo "📋 Useful Commands:"
echo "   • View logs: sudo journalctl -u agentic-trading -f"
echo "   • Restart service: sudo systemctl restart agentic-trading"
echo "   • Stop service: sudo systemctl stop agentic-trading"
echo "   • Check status: sudo systemctl status agentic-trading"
echo ""
echo "📁 Important Directories:"
echo "   • Logs: $PROJECT_DIR/logs/"
echo "   • Data: $PROJECT_DIR/data/"
echo "   • Backups: $PROJECT_DIR/backups/"
echo ""
echo "🔒 Security Reminder:"
echo "   • Ensure Security Group allows ports 8000 and 8501"
echo "   • Restrict access to your IP only"
echo "   • API keys stored in: ~/.bashrc and /etc/systemd/system/agentic-trading.service"
echo ""
echo "🎯 Next Steps:"
echo "   1. Open http://$INSTANCE_IP:8501 in your browser"
echo "   2. Test stock analysis"
echo "   3. Monitor logs: tail -f logs/paper_trading.log"
echo "   4. System will auto-trade Monday-Friday 9 AM IST"
echo ""
echo "🚀 Happy Trading!"
echo ""
