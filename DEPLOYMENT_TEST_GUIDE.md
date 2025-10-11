# GitHub Actions Deployment Test Guide

## 📋 Overview

Your paper trading system is configured to run **automatically at 3:00 PM IST (9:30 AM UTC)** every weekday via GitHub Actions.

**Workflow File:** `.github/workflows/paper-trading.yml`  
**Execution Script:** `paper_trading/run_paper_trading.py`  
**Repository:** https://github.com/khuranaviki/algo_trades  

---

## ⚙️ **Required GitHub Secrets**

Navigate to: `https://github.com/khuranaviki/algo_trades/settings/secrets/actions`

Add these secrets:

| Secret Name | Description | Required |
|-------------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for GPT-4 | ✅ Yes |
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude | ✅ Yes |
| `EMAIL_USERNAME` | Gmail username for notifications | ⚠️ Optional |
| `EMAIL_PASSWORD` | Gmail app password | ⚠️ Optional |

### Setting Gmail App Password (for email notifications)

1. Go to https://myaccount.google.com/security
2. Enable 2-Step Verification
3. Search for "App passwords"
4. Generate password for "Mail"
5. Copy the 16-character password
6. Add to GitHub Secrets as `EMAIL_PASSWORD`

---

## 🧪 **Testing Methods**

### **Method 1: Manual Workflow Trigger (Recommended)**

Test the workflow **immediately** without waiting for the schedule:

1. Go to: https://github.com/khuranaviki/algo_trades/actions
2. Click on "Paper Trading (Cloud)" workflow
3. Click "Run workflow" dropdown (top right)
4. Select branch: `main`
5. Click green "Run workflow" button

**Expected behavior:**
- Workflow starts immediately
- Runs for ~6 hours or until market closes
- Generates logs and portfolio data
- Sends email notification with summary
- Uploads artifacts (logs, portfolio data)

---

### **Method 2: Local Testing (Before Pushing)**

Test the script locally to ensure it works:

```bash
# 1. Navigate to project
cd /Users/delhivery/Documents/To_Backup/Codes/streamlit-market-analysis/agentic-trading-system

# 2. Set environment variables
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"

# 3. Install dependencies (if not done)
pip install -r requirements.txt

# 4. Create required directories
mkdir -p logs data backups

# 5. Run paper trading script (test mode - will timeout after 30s)
timeout 30 python3 paper_trading/run_paper_trading.py || echo "Test completed"

# 6. Check logs
cat logs/paper_trading.log
```

**What to look for:**
- ✅ Script starts without errors
- ✅ Initializes portfolio and watchlist
- ✅ Connects to data sources
- ✅ No API key errors
- ✅ Logs are being written

---

### **Method 3: Dry Run with GitHub Actions Locally**

Test the exact GitHub Actions environment using `act`:

```bash
# Install act (GitHub Actions local runner)
brew install act  # macOS
# or
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash  # Linux

# Navigate to repo
cd /Users/delhivery/Documents/To_Backup/Codes/streamlit-market-analysis

# Create secrets file for local testing
cat > .secrets <<EOF
OPENAI_API_KEY=your-key-here
ANTHROPIC_API_KEY=your-key-here
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-gmail-app-password
EOF

# Run workflow locally
act workflow_dispatch -W agentic-trading-system/.github/workflows/paper-trading.yml --secret-file .secrets

# Clean up secrets file
rm .secrets
```

---

## 📊 **Monitoring the Workflow**

### **During Execution**

1. **Live Logs:** https://github.com/khuranaviki/algo_trades/actions
   - Click on running workflow
   - View real-time logs

2. **Expected Log Output:**
   ```
   🤖 AGENTIC TRADING SYSTEM - PAPER TRADING MODE
   ================================================================================
   Start Time: 2025-10-11 15:00:00
   Configuration: 1,000,000 INR
   Watchlist: 40 stocks
   Update Interval: 60s
   ================================================================================
   
   🔧 Initializing paper trading engine...
   ✅ Engine initialized successfully
   
   🚀 Starting paper trading...
   📡 Starting data stream...
   📊 Scanning watchlist: 40 stocks...
   ```

### **After Execution**

1. **Email Notification** → Check khuranaviki@gmail.com
   - Subject: "Trading System Alert: Session Completed"
   - Contains: Portfolio summary, trades, activity log

2. **GitHub Artifacts** → Download from workflow run page
   - `portfolio-data-{run_number}` (30-day retention)
   - `trading-logs-{run_number}` (7-day retention)

3. **Summary Report** → View in workflow logs
   - Portfolio status (total value, return, positions)
   - Recent trades (buy/sell activity)
   - Recent activity (last 50 log lines)

---

## 🔍 **Troubleshooting**

### **Issue: Workflow Doesn't Start**

**Check:**
1. Is it Monday-Friday? (Weekends are skipped)
2. Is it after 3:00 PM IST?
3. Is the workflow enabled? (Actions tab → Enable workflow)

**Fix:**
```bash
# Manually trigger workflow
# Go to: https://github.com/khuranaviki/algo_trades/actions
# Click "Run workflow" → Select "main" → Run
```

### **Issue: API Key Errors**

**Error:** `OPENAI_API_KEY not found` or `Invalid API key`

**Fix:**
1. Verify secrets are set: https://github.com/khuranaviki/algo_trades/settings/secrets/actions
2. Check secret names match exactly (case-sensitive)
3. Re-generate API keys if expired

### **Issue: Import Errors**

**Error:** `ModuleNotFoundError: No module named 'agents'`

**Fix:**
1. Ensure all dependencies are in `requirements.txt`
2. Check Python path in script (should have `sys.path.insert(0, ...)`)
3. Verify directory structure matches expected layout

### **Issue: No Email Notifications**

**Check:**
1. Are `EMAIL_USERNAME` and `EMAIL_PASSWORD` secrets set?
2. Is Gmail 2-Step Verification enabled?
3. Is App Password (not regular password) being used?

**Fix:**
- Generate new Gmail App Password
- Update GitHub secret
- Test email action separately

### **Issue: Timeout Too Short/Long**

**Current:** 22,500 seconds (6.25 hours)

**Adjust in workflow file:**
```yaml
run: |
  timeout 10800 python3 paper_trading/run_paper_trading.py || true  # 3 hours
  # or
  timeout 28800 python3 paper_trading/run_paper_trading.py || true  # 8 hours
```

---

## 🚀 **Quick Test Commands**

### **Test 1: Validate Configuration**

```bash
cd /Users/delhivery/Documents/To_Backup/Codes/streamlit-market-analysis/agentic-trading-system

# Check if config file exists and is valid
python3 -c "from config.paper_trading_config import PAPER_TRADING_CONFIG; print('✅ Config loaded:', PAPER_TRADING_CONFIG.get('initial_capital'))"
```

### **Test 2: Validate Dependencies**

```bash
# Check all imports work
python3 -c "
from paper_trading.engine import PaperTradingEngine
from agents.orchestrator import Orchestrator
from config.paper_trading_config import PAPER_TRADING_CONFIG
print('✅ All imports successful')
"
```

### **Test 3: Quick 30-Second Run**

```bash
# Run for 30 seconds only (test mode)
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"
timeout 30 python3 paper_trading/run_paper_trading.py || echo "✅ Test run completed"
```

### **Test 4: Check GitHub Actions Syntax**

```bash
# Install actionlint
brew install actionlint  # macOS
# or download from: https://github.com/rhysd/actionlint/releases

# Validate workflow file
cd /Users/delhivery/Documents/To_Backup/Codes/streamlit-market-analysis/agentic-trading-system
actionlint .github/workflows/paper-trading.yml
```

---

## 📝 **Deployment Checklist**

Before going live:

- [ ] ✅ GitHub secrets configured (OPENAI_API_KEY, ANTHROPIC_API_KEY)
- [ ] ✅ Email notifications configured (optional but recommended)
- [ ] ✅ Local test passed (script runs without errors)
- [ ] ✅ Manual workflow trigger test passed
- [ ] ✅ Workflow syntax validated (actionlint)
- [ ] ✅ Dependencies installed correctly (requirements.txt)
- [ ] ✅ Configuration file validated (paper_trading_config.py)
- [ ] ✅ Watchlist configured (40 stocks)
- [ ] ✅ Initial capital set (default: ₹10,00,000)
- [ ] ✅ Timeout configured (6.25 hours for full market day)
- [ ] ✅ Logs directory created
- [ ] ✅ Artifacts retention configured (30/7 days)

---

## 📅 **Schedule Verification**

### **Cron Expression:** `30 9 * * 1-5`

**Translation:**
- `30` → 30th minute
- `9` → 9th hour (UTC)
- `*` → Every day
- `*` → Every month
- `1-5` → Monday to Friday only

**IST Conversion:**
- UTC 9:30 AM = IST 3:00 PM ✅

**Next 5 Runs** (example):
```
Monday,    Oct 13, 2025 at 3:00 PM IST
Tuesday,   Oct 14, 2025 at 3:00 PM IST
Wednesday, Oct 15, 2025 at 3:00 PM IST
Thursday,  Oct 16, 2025 at 3:00 PM IST
Friday,    Oct 17, 2025 at 3:00 PM IST
```

Use https://crontab.guru/ to verify cron expressions.

---

## 🎯 **Expected Workflow Output**

### **Successful Run Example:**

```
Run paper trading
  Run timeout 22500 python3 paper_trading/run_paper_trading.py || true
  
🤖 AGENTIC TRADING SYSTEM - PAPER TRADING MODE
================================================================================
Start Time: 2025-10-11 15:00:23
Configuration: 1,000,000 INR
Watchlist: 40 stocks
Update Interval: 60s
================================================================================

🔧 Initializing paper trading engine...
✅ Engine initialized successfully

🚀 Starting paper trading...
📡 Starting data stream...
✅ Data stream started

🔍 Monitoring loop started (every 60s)

[15:01:23] 📊 Scanning watchlist (40 stocks)...
[15:01:25] ⚡ RELIANCE.NS - Analyzing...
[15:01:45] ✅ RELIANCE.NS - BUY signal detected (Score: 78/100)
[15:01:46] 💰 POSITION OPENED: BUY RELIANCE.NS @ ₹2,450.50 (20 shares)
...
[21:30:00] 🛑 Market closed. Shutting down...

================================================================================
📊 FINAL STATISTICS
================================================================================
Total Value: ₹10,15,234.50
Cash: ₹9,51,010.00
Positions: 3
Total Return: 1.52%
Realized P&L: ₹5,234.50
Unrealized P&L: ₹10,000.00
================================================================================
```

---

## 📞 **Support & Monitoring**

### **Where to Check:**

1. **GitHub Actions:** https://github.com/khuranaviki/algo_trades/actions
2. **Email:** khuranaviki@gmail.com (daily reports)
3. **Logs:** Download from workflow artifacts
4. **Code:** https://github.com/khuranaviki/algo_trades

### **Monitoring Best Practices:**

1. **Check email daily** for trading summaries
2. **Review artifacts weekly** to analyze performance
3. **Monitor API costs** via OpenAI/Anthropic dashboards
4. **Check workflow status** if email not received by 10 PM IST
5. **Backup portfolio data** monthly from artifacts

---

## 🔐 **Security Reminders**

- ✅ Never commit API keys to repository
- ✅ Use GitHub Secrets for all sensitive data
- ✅ Enable 2FA on GitHub account
- ✅ Use Gmail App Passwords (not regular password)
- ✅ Review workflow logs for exposed secrets
- ✅ Rotate API keys every 90 days
- ✅ Limit GitHub Actions to specific branches
- ✅ Monitor unusual API usage

---

## 📚 **Additional Resources**

- **GitHub Actions Docs:** https://docs.github.com/en/actions
- **Cron Expression Tester:** https://crontab.guru/
- **Workflow Syntax:** https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions
- **Action Secrets:** https://docs.github.com/en/actions/security-guides/encrypted-secrets

---

**Last Updated:** October 11, 2025  
**Repository:** https://github.com/khuranaviki/algo_trades  
**Maintainer:** khuranaviki@gmail.com

