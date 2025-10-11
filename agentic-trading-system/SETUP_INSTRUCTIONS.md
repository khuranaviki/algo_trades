# 🚀 GitHub Deployment - Final Setup Steps

Your code has been successfully pushed to GitHub! Now complete these final steps to enable automated trading with email notifications.

## Repository
**https://github.com/khuranaviki/algo_trades**

## Step 1: Add GitHub Secrets (CRITICAL!)

Go to your repository settings and add these secrets:

**URL:** https://github.com/khuranaviki/algo_trades/settings/secrets/actions

### Required Secrets:

1. **OPENAI_API_KEY**
   - Value: Your OpenAI API key (starts with `sk-`)
   - Get from: https://platform.openai.com/api-keys

2. **ANTHROPIC_API_KEY**
   - Value: Your Anthropic API key (starts with `sk-ant-`)
   - Get from: https://console.anthropic.com/settings/keys

3. **EMAIL_USERNAME** (for Gmail notifications)
   - Value: Your Gmail address (e.g., `your-email@gmail.com`)
   - This will be used to send emails

4. **EMAIL_PASSWORD** (Gmail App Password)
   - Value: Gmail App Password (NOT your regular password!)
   - How to create:
     1. Go to https://myaccount.google.com/apppasswords
     2. Select "Mail" and "Other (Custom name)"
     3. Name it "Trading Bot"
     4. Copy the 16-character password
     5. Paste it as EMAIL_PASSWORD secret

### How to Add Secrets:

1. Go to: https://github.com/khuranaviki/algo_trades/settings/secrets/actions
2. Click **"New repository secret"**
3. Name: `OPENAI_API_KEY`
4. Secret: Paste your OpenAI API key
5. Click **"Add secret"**
6. Repeat for all 4 secrets above

## Step 2: Verify GitHub Actions is Enabled

1. Go to: https://github.com/khuranaviki/algo_trades/actions
2. If you see a message about workflows being disabled, click **"I understand my workflows, go ahead and enable them"**
3. You should see "Paper Trading (Cloud)" workflow listed

## Step 3: Test the Workflow (Manual Trigger)

1. Go to: https://github.com/khuranaviki/algo_trades/actions
2. Click on **"Paper Trading (Cloud)"** workflow
3. Click **"Run workflow"** button (top right)
4. Select branch: **main**
5. Click **"Run workflow"**

This will start a test run immediately. You should receive an email at **khuranaviki@gmail.com** when it completes.

## Step 4: Schedule

The workflow is configured to run:
- **Time:** 3:00 PM IST (Monday-Friday)
- **Cron:** `30 9 * * 1-5` (9:30 AM UTC = 3:00 PM IST)

It will run automatically every weekday at 3 PM.

## What Happens During Each Run?

1. ✅ System starts at 3:00 PM IST
2. ✅ Runs for 6.25 hours (market duration)
3. ✅ Analyzes stocks using 6 AI agents
4. ✅ Executes paper trades (no real money)
5. ✅ Generates performance report
6. ✅ Sends email to khuranaviki@gmail.com with:
   - Portfolio summary
   - Recent trades
   - Performance metrics
   - Link to full logs

## Email Notification Contents

You'll receive an email with:
```
Subject: Trading System Alert: Session Completed - #123

Body:
- Run status (success/failure)
- Portfolio value and return %
- Recent trades (BUY/SELL)
- Cash balance
- Link to GitHub Actions logs

Attachment:
- summary.md (detailed report)
```

## Monitoring

### View Live Runs:
https://github.com/khuranaviki/algo_trades/actions

### Download Artifacts:
Each run saves:
- Portfolio data (JSON files)
- Trading logs
- Performance summary

Artifacts are available for 30 days after each run.

## Cost Monitoring

### GitHub Actions (FREE Tier):
- ✅ 2,000 minutes/month FREE for private repos
- Each session = ~375 minutes (6.25 hours)
- 5 days/week × 4 weeks = ~7,500 minutes/month
- **You'll need GitHub Pro or run fewer days**

### Alternative: Run 2 days/week to stay within free tier

Edit `.github/workflows/paper-trading.yml`:
```yaml
# Change from Mon-Fri to just Mon and Thu
- cron: '30 9 * * 1,4'  # Monday and Thursday only
```

### API Costs (Pay-as-you-go):
- OpenAI: ~$0.01-0.03 per analysis
- Anthropic: ~$0.01-0.02 per analysis
- **Estimated:** $30-90/month for daily trading

Monitor usage:
- OpenAI: https://platform.openai.com/usage
- Anthropic: https://console.anthropic.com/settings/usage

## Troubleshooting

### No email received?
1. Check GitHub Actions run completed successfully
2. Verify EMAIL_USERNAME and EMAIL_PASSWORD secrets are correct
3. Check spam folder
4. Ensure Gmail App Password was created (not regular password)

### Workflow not running?
1. Verify secrets are added correctly
2. Check Actions tab for any error messages
3. Manually trigger workflow to test

### API errors?
1. Verify API keys in GitHub Secrets
2. Check API key validity at provider websites
3. Ensure you have credit balance

## Security Notes

✅ All API keys are stored as GitHub Secrets (encrypted)
✅ Never commit `.env` files to git
✅ Pre-push security scan prevents accidental key leaks
✅ Email password is app-specific (not your Gmail password)

## Next Steps

1. ✅ Add all 4 GitHub Secrets
2. ✅ Test workflow manually
3. ✅ Wait for 3 PM Monday for first auto-run
4. ✅ Check email for completion notification
5. ✅ Monitor performance and adjust strategy

## Support

- GitHub Actions Docs: https://docs.github.com/en/actions
- Workflow File: `.github/workflows/paper-trading.yml`
- Setup Guide: `GITHUB_SETUP.md`

---

**Your trading system is ready to go! 🎉**

Just add the secrets and you're all set for automated trading at 3 PM daily with email notifications.
