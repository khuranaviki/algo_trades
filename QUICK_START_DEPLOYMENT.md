# 🚀 Quick Start: Test GitHub Actions Deployment

## ✅ Status: ALL TESTS PASSED

Your paper trading system is **ready for deployment**! All local tests passed successfully.

---

## 📋 What's Configured

| Setting | Value |
|---------|-------|
| **Schedule** | Mon-Fri at 3:00 PM IST (9:30 AM UTC) |
| **Repository** | https://github.com/khuranaviki/algo_trades |
| **Workflow File** | `.github/workflows/paper-trading.yml` |
| **Script** | `paper_trading/run_paper_trading.py` |
| **Initial Capital** | ₹10,00,000 |
| **Watchlist** | 10 stocks |
| **Runtime** | 6.25 hours (full market day) |
| **Email Alerts** | khuranaviki@gmail.com |

---

## 🧪 Step 1: Verify GitHub Secrets

Before triggering the workflow, ensure these secrets are set:

**Go to:** https://github.com/khuranaviki/algo_trades/settings/secrets/actions

**Required Secrets:**

| Secret Name | Value | Status |
|-------------|-------|--------|
| `OPENAI_API_KEY` | Your OpenAI API key | ✅ Set locally |
| `ANTHROPIC_API_KEY` | Your Anthropic API key | ✅ Set locally |
| `EMAIL_USERNAME` | khuranaviki@gmail.com | ⚠️ Check GitHub |
| `EMAIL_PASSWORD` | Gmail App Password | ⚠️ Check GitHub |

### How to Set Secrets:

1. Click "New repository secret"
2. Name: `OPENAI_API_KEY`
3. Value: Paste your key (starts with `sk-proj-...`)
4. Click "Add secret"
5. Repeat for other secrets

---

## 🎯 Step 2: Test Deployment (3 Methods)

### **Method A: Manual Trigger (RECOMMENDED)**

Test the workflow **right now** without waiting for 3 PM:

1. **Go to:** https://github.com/khuranaviki/algo_trades/actions

2. **Click:** "Paper Trading (Cloud)" workflow (left sidebar)

3. **Click:** "Run workflow" button (top right)

4. **Select:** Branch = `main`

5. **Click:** Green "Run workflow" button

6. **Watch:** Live logs appear in ~10 seconds

**Expected runtime:** 6.25 hours (or until market closes)

---

### **Method B: Test Locally First**

Run the exact same script that GitHub Actions will run:

```bash
# Navigate to project
cd /Users/delhivery/Documents/To_Backup/Codes/streamlit-market-analysis/agentic-trading-system

# Run for 60 seconds (test mode)
timeout 60 python3 paper_trading/run_paper_trading.py || echo "Test completed"

# Check logs
tail -50 logs/paper_trading.log
```

---

### **Method C: Automated Tests**

We already ran this and it passed! But you can run again:

```bash
cd /Users/delhivery/Documents/To_Backup/Codes/streamlit-market-analysis/agentic-trading-system

# Run full test suite
python3 test_deployment.py
```

**✅ Result:** All 7 tests passed!

---

## 📊 Step 3: Monitor Execution

### **During Workflow:**

1. **Live Logs:** https://github.com/khuranaviki/algo_trades/actions
   - Click the running workflow
   - View real-time output

2. **Expected Output:**
   ```
   🤖 AGENTIC TRADING SYSTEM - PAPER TRADING MODE
   ================================================================================
   Start Time: 2025-10-11 15:00:00
   Configuration: 1,000,000 INR
   Watchlist: 10 stocks
   Update Interval: 60s
   ================================================================================
   
   🚀 Starting paper trading...
   📡 Starting data stream...
   🔍 Monitoring loop started...
   ```

### **After Workflow:**

1. **Email:** Check khuranaviki@gmail.com for summary report
2. **Artifacts:** Download logs and portfolio data from workflow page
3. **Summary:** View final statistics in workflow logs

---

## 📅 Step 4: Verify Automatic Schedule

The workflow will run **automatically** at these times:

```
Monday,    Oct 13, 2025  →  3:00 PM IST
Tuesday,   Oct 14, 2025  →  3:00 PM IST
Wednesday, Oct 15, 2025  →  3:00 PM IST
Thursday,  Oct 16, 2025  →  3:00 PM IST
Friday,    Oct 17, 2025  →  3:00 PM IST
```

**No runs on weekends** (Saturday/Sunday).

### Verify Schedule:

```bash
# Check cron expression
cat .github/workflows/paper-trading.yml | grep cron

# Should show: - cron: '30 9 * * 1-5'
# Translation: 9:30 AM UTC = 3:00 PM IST
```

---

## 🔍 Troubleshooting

### **Issue: Workflow doesn't appear**

**Check:**
- Is the `.github/workflows/` folder in the repo root?
- Did you push the workflow file to GitHub?
- Is GitHub Actions enabled for the repo?

**Fix:**
```bash
cd /Users/delhivery/Documents/To_Backup/Codes/streamlit-market-analysis
git add .github/workflows/paper-trading.yml
git commit -m "Add GitHub Actions workflow"
git push origin main
```

### **Issue: Secrets not found**

**Error:** `Error: Secret OPENAI_API_KEY not found`

**Fix:**
1. Go to: https://github.com/khuranaviki/algo_trades/settings/secrets/actions
2. Verify secret name matches **exactly** (case-sensitive)
3. Re-add secret if needed

### **Issue: Import errors**

**Error:** `ModuleNotFoundError: No module named 'agents'`

**Fix:** Ensure `requirements.txt` is up-to-date:
```bash
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Update requirements"
git push origin main
```

### **Issue: Email not received**

**Check:**
1. Email secrets set correctly (`EMAIL_USERNAME`, `EMAIL_PASSWORD`)
2. Gmail App Password generated (not regular password)
3. Workflow completed successfully (check Actions page)

**Gmail App Password Setup:**
1. Go to: https://myaccount.google.com/security
2. Enable 2-Step Verification
3. Search "App passwords" → Generate → Copy
4. Add to GitHub Secrets as `EMAIL_PASSWORD`

---

## 📝 Quick Commands Reference

### **Check Status:**
```bash
# View workflow runs
open https://github.com/khuranaviki/algo_trades/actions

# Check local logs
tail -f /Users/delhivery/Documents/To_Backup/Codes/streamlit-market-analysis/agentic-trading-system/logs/paper_trading.log
```

### **Test Locally:**
```bash
cd /Users/delhivery/Documents/To_Backup/Codes/streamlit-market-analysis/agentic-trading-system

# Quick test (30 seconds)
timeout 30 python3 paper_trading/run_paper_trading.py || echo "Done"

# Full test suite
python3 test_deployment.py

# Check configuration
python3 -c "from config.paper_trading_config import PAPER_TRADING_CONFIG; print(PAPER_TRADING_CONFIG)"
```

### **Trigger Manually:**
```bash
# Using GitHub CLI (if installed)
gh workflow run "Paper Trading (Cloud)" --ref main

# Or use browser:
open https://github.com/khuranaviki/algo_trades/actions/workflows/paper-trading.yml
```

---

## 📈 Expected Results

### **After First Run:**

**Email Report:**
```
Subject: Trading System Alert: Session Completed - #123

Paper Trading Session Completed

Run Number: 123
Date: 2025-10-11 21:30:00
Status: success

Summary:
## Portfolio Status
Total Value: ₹10,15,234.50
Cash: ₹9,51,010.00
Positions: 3
Total Return: 1.52%
Realized P&L: ₹5,234.50
Unrealized P&L: ₹10,000.00

## Recent Trades
[15:01:46] POSITION OPENED: BUY RELIANCE.NS @ ₹2,450.50 (20 shares)
[16:45:23] POSITION CLOSED: SELL TCS.NS @ ₹3,567.80 (15 shares, +2.3%)
```

**Artifacts Downloaded:**
- `portfolio-data-123.zip` (30-day retention)
- `trading-logs-123.zip` (7-day retention)

---

## ✅ Pre-Deployment Checklist

Before going live, confirm:

- [x] ✅ All local tests passed (7/7)
- [x] ✅ API keys working locally
- [ ] ⚠️ GitHub secrets configured
- [ ] ⚠️ Email credentials set (optional)
- [x] ✅ Workflow file committed to repo
- [x] ✅ Configuration validated
- [x] ✅ Dependencies installed
- [x] ✅ Engine initializes successfully

**Next action:** Set up GitHub Secrets → Test with Manual Trigger

---

## 🎯 Success Criteria

Your deployment is successful when:

1. ✅ Manual workflow trigger completes without errors
2. ✅ Email notification received
3. ✅ Artifacts uploaded (logs, portfolio data)
4. ✅ No API key errors
5. ✅ Portfolio value tracked correctly
6. ✅ Trades executed (if signals detected)

---

## 🔗 Important Links

- **GitHub Actions:** https://github.com/khuranaviki/algo_trades/actions
- **Workflow File:** https://github.com/khuranaviki/algo_trades/blob/main/.github/workflows/paper-trading.yml
- **Secrets Settings:** https://github.com/khuranaviki/algo_trades/settings/secrets/actions
- **Email Setup:** https://myaccount.google.com/security
- **Cron Tester:** https://crontab.guru/#30_9_*_*_1-5

---

## 📞 Need Help?

**If something goes wrong:**

1. Check workflow logs: https://github.com/khuranaviki/algo_trades/actions
2. Review detailed guide: `DEPLOYMENT_TEST_GUIDE.md`
3. Run local tests: `python3 test_deployment.py`
4. Check email: khuranaviki@gmail.com

---

**Last Updated:** October 11, 2025  
**Status:** ✅ Ready for Deployment  
**Next Run:** Check GitHub Actions page or wait until 3:00 PM IST Mon-Fri  

🚀 **You're all set! Click "Run workflow" to test now.**

