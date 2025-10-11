# Cloud Deployment Guide

Deploy your Agentic Trading System to the cloud with **zero local dependencies**.

## 🌟 Recommended: AWS EC2 (Best for 24/7 Trading)

### Why AWS EC2?
- ✅ Runs 24/7 without your laptop
- ✅ Dedicated resources
- ✅ No session timeouts
- ✅ Professional grade
- ✅ ~$10-15/month for t3.medium

### Quick Deploy to AWS EC2

#### Step 1: Launch EC2 Instance

```bash
# Use AWS Console or CLI
# Instance Type: t3.medium (2 vCPU, 4GB RAM)
# OS: Ubuntu 22.04 LTS
# Storage: 20GB SSD
# Security Group: Allow ports 22, 8000, 8501
```

Or use our automated script:

```bash
# On your local machine (one-time setup)
cd deploy/cloud/aws
./launch_ec2.sh
```

#### Step 2: Connect and Deploy

```bash
# SSH into your instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# Clone your repository
git clone https://github.com/yourusername/agentic-trading-system.git
cd agentic-trading-system

# Run automated setup
./deploy/cloud/aws/setup.sh
```

The setup script will:
1. Install Python 3.11
2. Install all dependencies
3. Set up environment variables
4. Configure systemd services (auto-restart on boot)
5. Set up cron for Monday 9 AM trading

#### Step 3: Set API Keys

```bash
# Create .env file
cat > .env << EOF
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
EOF

chmod 600 .env
```

#### Step 4: Start Services

```bash
# Start everything
sudo systemctl start agentic-trading

# Check status
sudo systemctl status agentic-trading

# View logs
sudo journalctl -u agentic-trading -f
```

#### Access Your Dashboard

```
http://your-ec2-ip:8501
```

---

## 🚀 Option 2: Google Cloud Run (Serverless)

### Why Cloud Run?
- ✅ Pay only when running
- ✅ Automatic scaling
- ✅ No server management
- ✅ ~$5-10/month

### Quick Deploy to Cloud Run

```bash
# 1. Install Google Cloud CLI
curl https://sdk.cloud.google.com | bash
gcloud init

# 2. Deploy
cd deploy/cloud/gcp
./deploy_cloud_run.sh

# 3. Set API keys
gcloud run services update agentic-trading \
  --update-env-vars OPENAI_API_KEY=your-key,ANTHROPIC_API_KEY=your-key
```

Your service URL: `https://agentic-trading-xxxxx-uc.a.run.app`

---

## 💻 Option 3: GitHub Actions (Free!)

### Why GitHub Actions?
- ✅ Completely free for public repos
- ✅ 2,000 free minutes/month for private repos
- ✅ Automated trading on schedule
- ✅ Zero infrastructure management

### Quick Setup

1. **Push your code to GitHub**
```bash
git add .
git commit -m "Add cloud deployment"
git push origin main
```

2. **Add API keys as GitHub Secrets**
- Go to: `Settings > Secrets and variables > Actions`
- Add secrets:
  - `OPENAI_API_KEY`
  - `ANTHROPIC_API_KEY`

3. **GitHub Actions workflow is already set up!**

The workflow file `.github/workflows/paper-trading.yml` will:
- Run Monday-Friday at 9:00 AM IST
- Execute paper trading for market hours
- Upload results as artifacts
- Email you a summary

**View Results:**
- Go to: `Actions` tab in GitHub
- Click on latest run
- Download portfolio results

---

## 🎯 Option 4: Railway (Easiest!)

### Why Railway?
- ✅ Easiest deployment (1 click)
- ✅ Free $5/month credit
- ✅ Automatic deployments from GitHub
- ✅ Built-in monitoring

### Quick Deploy to Railway

1. **One-Click Deploy**

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/agentic-trading)

2. **Or Manual Deploy**

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Deploy
cd agentic-trading-system
railway init
railway up
```

3. **Set Environment Variables**

In Railway dashboard:
- Add `OPENAI_API_KEY`
- Add `ANTHROPIC_API_KEY`

**Access Dashboard:**
```
https://agentic-trading.up.railway.app
```

---

## 🐳 Option 5: Docker + Any Cloud Provider

### Why Docker?
- ✅ Works on any cloud provider
- ✅ Consistent environment
- ✅ Easy to scale

### Quick Docker Deploy

```bash
# Build image
docker build -t agentic-trading .

# Run locally (test)
docker run -p 8501:8501 -p 8000:8000 \
  -e OPENAI_API_KEY=your-key \
  -e ANTHROPIC_API_KEY=your-key \
  agentic-trading

# Push to Docker Hub
docker tag agentic-trading yourusername/agentic-trading
docker push yourusername/agentic-trading

# Deploy to any cloud provider
# AWS ECS, Azure Container Instances, Google Cloud Run, etc.
```

---

## 🔄 Option 6: Replit (No Setup Required!)

### Why Replit?
- ✅ Zero setup
- ✅ Browser-based IDE
- ✅ Always-on with Replit Hacker plan ($7/month)
- ✅ Great for quick testing

### Quick Deploy to Replit

1. Go to [replit.com](https://replit.com)
2. Click "Create Repl"
3. Import from GitHub: `your-repo-url`
4. Add secrets:
   - `OPENAI_API_KEY`
   - `ANTHROPIC_API_KEY`
5. Click "Run"

Replit automatically:
- Installs dependencies
- Starts services
- Gives you a public URL

---

## 📊 Cost Comparison

| Provider | Cost/Month | Effort | Reliability | Best For |
|----------|------------|--------|-------------|----------|
| **AWS EC2 (t3.medium)** | $10-15 | Medium | ⭐⭐⭐⭐⭐ | 24/7 trading, production |
| **Google Cloud Run** | $5-10 | Low | ⭐⭐⭐⭐ | Serverless, pay-per-use |
| **GitHub Actions** | **Free** | Low | ⭐⭐⭐ | Scheduled trading only |
| **Railway** | $5 | **Very Low** | ⭐⭐⭐⭐ | Easiest setup |
| **Replit** | $7 | **Very Low** | ⭐⭐⭐ | Quick testing |
| **Docker + Cloud** | Varies | Medium | ⭐⭐⭐⭐⭐ | Flexibility |

---

## 🎯 Recommendation by Use Case

### For Production Trading (Best Quality)
**→ AWS EC2** - Most reliable, runs 24/7, professional grade

### For Easiest Setup (Quickest Start)
**→ Railway** - One-click deploy, automatic HTTPS, built-in monitoring

### For Free/Low Cost (Budget)
**→ GitHub Actions** - Completely free, perfect for scheduled trading

### For Quick Testing (No Commitment)
**→ Replit** - Browser-based, zero setup, instant deployment

---

## 🚀 Step-by-Step: Deploy to AWS EC2 (Recommended)

### Complete Tutorial

#### 1. Launch EC2 Instance

```bash
# Using AWS CLI (install from https://aws.amazon.com/cli/)
aws ec2 run-instances \
  --image-id ami-0c7217cdde317cfec \
  --instance-type t3.medium \
  --key-name your-key-pair \
  --security-group-ids sg-xxxxxxxx \
  --subnet-id subnet-xxxxxxxx \
  --block-device-mappings DeviceName=/dev/sda1,Ebs={VolumeSize=20} \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=agentic-trading}]'
```

Or use AWS Console:
1. Go to EC2 Dashboard
2. Click "Launch Instance"
3. Choose "Ubuntu Server 22.04 LTS"
4. Instance type: "t3.medium"
5. Storage: 20 GB
6. Security Group: Allow SSH (22), HTTP (8000, 8501)
7. Launch

#### 2. Connect to Instance

```bash
# Get your instance IP from AWS Console
ssh -i your-key.pem ubuntu@your-ec2-ip
```

#### 3. Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev -y

# Install pip
curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11

# Install git
sudo apt install git -y
```

#### 4. Clone and Setup

```bash
# Clone repository
git clone https://github.com/yourusername/agentic-trading-system.git
cd agentic-trading-system

# Install dependencies
python3.11 -m pip install -r requirements.txt

# Set API keys
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"

# Make permanent
echo 'export OPENAI_API_KEY="your-key"' >> ~/.bashrc
echo 'export ANTHROPIC_API_KEY="your-key"' >> ~/.bashrc
```

#### 5. Setup Systemd Service (Auto-Start on Boot)

```bash
# Create service file
sudo tee /etc/systemd/system/agentic-trading.service > /dev/null << EOF
[Unit]
Description=Agentic Trading System
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/agentic-trading-system
Environment="OPENAI_API_KEY=your-key"
Environment="ANTHROPIC_API_KEY=your-key"
ExecStart=/home/ubuntu/agentic-trading-system/deploy/start_services.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable agentic-trading
sudo systemctl start agentic-trading

# Check status
sudo systemctl status agentic-trading
```

#### 6. Setup Cron for Monday Trading

```bash
crontab -e

# Add this line
0 9 * * 1-5 /home/ubuntu/agentic-trading-system/deploy/start_paper_trading.sh >> /home/ubuntu/logs/cron.log 2>&1
```

#### 7. Access Dashboard

```
http://your-ec2-ip:8501
```

#### 8. Monitor Logs

```bash
# Service logs
sudo journalctl -u agentic-trading -f

# Paper trading logs
tail -f logs/paper_trading.log

# API logs
tail -f logs/api.log
```

---

## 🔒 Security Best Practices

### 1. Use Environment Variables for API Keys

```bash
# Never hardcode keys
# Use .env file or environment variables
```

### 2. Restrict Security Group

```bash
# AWS Security Group rules:
# - SSH (22): Your IP only
# - HTTP (8000, 8501): Your IP only or use VPN
```

### 3. Use HTTPS

```bash
# Install Caddy for automatic HTTPS
sudo apt install caddy
```

### 4. Regular Backups

```bash
# Automated daily backups
0 0 * * * aws s3 sync /home/ubuntu/agentic-trading-system/data s3://your-backup-bucket/
```

---

## 📱 Monitoring & Alerts

### Setup Email Alerts

```bash
# Install mailutils
sudo apt install mailutils -y

# Add to cron for daily summary
0 18 * * 1-5 /home/ubuntu/agentic-trading-system/scripts/send_daily_report.sh
```

### Setup Telegram Alerts

```python
# Add to config/paper_trading_config.py
'alerts': {
    'telegram_bot_token': 'your-bot-token',
    'telegram_chat_id': 'your-chat-id'
}
```

---

## 🛠️ Troubleshooting Cloud Deployments

### Issue: Services won't start
```bash
# Check logs
sudo journalctl -u agentic-trading -n 50

# Check dependencies
python3.11 -m pip install -r requirements.txt --force-reinstall
```

### Issue: Can't access dashboard
```bash
# Check if ports are open
sudo netstat -tulpn | grep -E '8000|8501'

# Check AWS Security Group allows your IP
```

### Issue: High API costs
```bash
# Reduce scan frequency in config/paper_trading_config.py
'update_interval_seconds': 300  # 5 minutes instead of 60 seconds
```

---

## 📚 Next Steps

1. **Choose your cloud provider** based on the comparison above
2. **Follow the deployment guide** for your chosen provider
3. **Set up monitoring and alerts**
4. **Test with small capital** first
5. **Scale up** once confident

---

## 🎯 Recommended Setup: AWS EC2

For production-grade 24/7 trading:

```bash
# 1. Launch EC2 (t3.medium, Ubuntu 22.04)
# 2. SSH and run:
git clone https://github.com/yourusername/agentic-trading-system.git
cd agentic-trading-system
./deploy/cloud/aws/setup.sh

# 3. Add API keys when prompted
# 4. Access dashboard: http://your-ip:8501
# 5. Monitor: tail -f logs/paper_trading.log
```

**Total time: 10 minutes**
**Monthly cost: ~$12**

---

**Questions?** Check the specific deployment scripts in `deploy/cloud/` directory.
