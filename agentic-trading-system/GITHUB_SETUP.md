# Secure GitHub Setup Guide

Complete guide to deploy your Agentic Trading System on GitHub with **maximum security** - no API key leaks!

## 🔒 Security First Approach

This guide ensures:
✅ **No API keys in code** - Ever
✅ **GitHub Secrets** for sensitive data
✅ **Automated security scanning**
✅ **Free cloud execution** via GitHub Actions
✅ **Automated Monday-Friday trading**

---

## Step 1: Security Check (CRITICAL!)

Before pushing to GitHub, verify no secrets are in your code:

```bash
# Run security scan
./deploy/cloud/github/pre-push-security-check.sh
```

This script will:
- Scan for API keys
- Check for sensitive data
- Verify .gitignore is correct
- Warn about any risks

---

## Step 2: Create GitHub Repository

### Option A: Via GitHub Website

1. Go to [github.com](https://github.com/new)
2. Repository name: `agentic-trading-system`
3. Description: "AI-powered multi-agent trading system"
4. Visibility: **Private** (recommended for trading systems)
5. **DO NOT** initialize with README (we already have one)
6. Click "Create repository"

### Option B: Via GitHub CLI

```bash
# Install GitHub CLI (if needed)
# macOS: brew install gh
# Linux: see https://github.com/cli/cli#installation

# Login
gh auth login

# Create private repository
gh repo create agentic-trading-system --private --source=. --remote=origin
```

---

## Step 3: Prepare for Push (Security Audit)

```bash
# 1. Check current status
git status

# 2. Review what will be committed
git add .
git status

# 3. IMPORTANT: Check for sensitive data
git diff --cached | grep -i "sk-"  # Check for API keys
git diff --cached | grep -i "api_key"
git diff --cached | grep -i "secret"

# 4. If you see ANY API keys, DO NOT PUSH!
# Remove them and add to .gitignore
```

---

## Step 4: Initial Commit (Safe)

```bash
# Add files (respecting .gitignore)
git add .

# Commit
git commit -m "Initial commit: Agentic Trading System with cloud deployment

- Multi-agent architecture (6 agents)
- 5-year pattern validation
- Paper trading engine
- Streamlit dashboard
- FastAPI backend
- Cloud deployment configs (AWS, GitHub Actions, Docker)
- Complete documentation

Security: All API keys excluded via .gitignore"

# Push to GitHub
git branch -M main
git push -u origin main
```

---

## Step 5: Add GitHub Secrets (CRITICAL!)

GitHub Secrets are encrypted and never exposed in logs.

### Via GitHub Website:

1. Go to your repository: `https://github.com/YOUR_USERNAME/agentic-trading-system`
2. Click `Settings` tab
3. Left sidebar: Click `Secrets and variables` → `Actions`
4. Click `New repository secret`

Add these secrets:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `OPENAI_API_KEY` | `sk-your-actual-openai-key` | Your OpenAI API key |
| `ANTHROPIC_API_KEY` | `sk-ant-your-actual-anthropic-key` | Your Anthropic API key |

### Via GitHub CLI:

```bash
# Set OpenAI API key
gh secret set OPENAI_API_KEY

# Set Anthropic API key
gh secret set ANTHROPIC_API_KEY

# Verify secrets are set
gh secret list
```

---

## Step 6: Enable GitHub Actions

GitHub Actions is **already configured** in `.github/workflows/paper-trading.yml`

### What it does:

- ✅ Runs **Monday-Friday at 9:00 AM IST** automatically
- ✅ Executes paper trading for market hours (6.25 hours)
- ✅ Uses your GitHub Secrets for API keys
- ✅ Uploads portfolio data and logs as artifacts
- ✅ **Completely FREE** (2000 minutes/month free tier)

### Verify it's enabled:

1. Go to repository: `https://github.com/YOUR_USERNAME/agentic-trading-system`
2. Click `Actions` tab
3. You should see "Paper Trading (Cloud)" workflow
4. Click on it to see schedule

### Manual Trigger (Optional):

```bash
# Trigger workflow manually
gh workflow run paper-trading.yml

# View workflow runs
gh run list --workflow=paper-trading.yml
```

---

## Step 7: Test the Workflow

### Option 1: Wait for Monday 9 AM

The workflow will auto-run Monday-Friday at 9:00 AM IST.

### Option 2: Trigger Manually Now

1. Go to `Actions` tab on GitHub
2. Click "Paper Trading (Cloud)"
3. Click "Run workflow" button (top right)
4. Select branch: `main`
5. Click green "Run workflow" button

### Monitor the run:

```bash
# Watch live logs
gh run watch

# Or view in browser
# Actions tab → Click on the running workflow
```

---

## Step 8: Download Results

After each run, GitHub stores portfolio data and logs.

### Via GitHub Website:

1. Go to `Actions` tab
2. Click on completed workflow run
3. Scroll to "Artifacts" section
4. Download:
   - `portfolio-data-XXX` - Portfolio state and summary
   - `trading-logs-XXX` - Detailed logs

### Via GitHub CLI:

```bash
# List artifacts from latest run
gh run list --workflow=paper-trading.yml --limit 1

# Download artifacts
gh run download RUN_ID
```

---

## Step 9: Security Best Practices

### 1. Enable Secret Scanning

```bash
# Enable via GitHub CLI
gh api -X PATCH /repos/YOUR_USERNAME/agentic-trading-system \
  -f has_vulnerability_alerts=true

# Or via web:
# Settings → Code security and analysis → Enable all features
```

### 2. Add .env.example (Template)

Create `.env.example` with placeholders:

```bash
cat > .env.example << 'EOF'
# API Keys (DO NOT COMMIT REAL KEYS HERE!)
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
EOF

git add .env.example
git commit -m "Add .env.example template"
git push
```

### 3. Enable Branch Protection

```bash
# Protect main branch
gh api -X PUT /repos/YOUR_USERNAME/agentic-trading-system/branches/main/protection \
  -f required_status_checks='{"strict":true,"contexts":[]}' \
  -f enforce_admins=true \
  -f required_pull_request_reviews=null \
  -f restrictions=null
```

### 4. Regular Security Audits

```bash
# Check for exposed secrets in history
git log --all --oneline | xargs -I {} git show {} | grep -i "sk-"

# If found, use git-filter-repo or BFG to clean history
```

---

## Step 10: Collaborate Securely

If sharing with others:

### 1. Add Collaborators

```bash
gh repo set-default YOUR_USERNAME/agentic-trading-system
gh repo edit --add-collaborator COLLABORATOR_USERNAME --permission write
```

### 2. Secrets Access

- Secrets are ONLY accessible to workflows
- Collaborators CANNOT see secret values
- Only admins can update secrets

### 3. Share .env Template

```markdown
# Share this with collaborators:

1. Clone the repository
2. Copy `.env.example` to `.env`
3. Add your own API keys to `.env`
4. Never commit `.env` (it's in .gitignore)
```

---

## Step 11: Monitoring & Alerts

### Email Notifications

GitHub automatically sends emails for:
- ✅ Workflow completion
- ❌ Workflow failures
- ⚠️ Security alerts

### Custom Notifications (Optional)

Add to `.github/workflows/paper-trading.yml`:

```yaml
- name: Send Slack notification
  if: always()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

---

## Complete Setup Checklist

- [ ] Run pre-push security check
- [ ] Create GitHub repository (private)
- [ ] Verify .gitignore excludes all secrets
- [ ] Initial commit (no API keys!)
- [ ] Push to GitHub
- [ ] Add GitHub Secrets (OPENAI_API_KEY, ANTHROPIC_API_KEY)
- [ ] Verify GitHub Actions is enabled
- [ ] Test workflow manually
- [ ] Enable secret scanning
- [ ] Add .env.example template
- [ ] Enable branch protection
- [ ] Set up email notifications

---

## Troubleshooting

### "Workflow not running"

1. Check if Actions is enabled:
   - Settings → Actions → General → Allow all actions

2. Verify secrets are set:
   ```bash
   gh secret list
   ```

3. Check workflow file syntax:
   ```bash
   cat .github/workflows/paper-trading.yml
   ```

### "API key errors in logs"

GitHub automatically masks secrets in logs. If you see:
```
Error: Invalid API key: ***
```

This is normal - the `***` shows GitHub is protecting your secret.

### "How to rotate API keys"

1. Generate new API keys from OpenAI/Anthropic
2. Update GitHub secrets:
   ```bash
   gh secret set OPENAI_API_KEY
   gh secret set ANTHROPIC_API_KEY
   ```
3. Revoke old keys from provider dashboards

### "Accidentally committed API key"

**DO NOT JUST DELETE THE FILE!** The key is still in git history.

1. Immediately revoke the key from provider
2. Generate new API key
3. Clean git history:
   ```bash
   # Install BFG Repo Cleaner
   brew install bfg  # macOS

   # Remove all API keys from history
   bfg --replace-text <(echo 'sk-XXXXX==>REMOVED') .git

   # Garbage collect
   git reflog expire --expire=now --all
   git gc --prune=now --aggressive

   # Force push
   git push --force
   ```

---

## Cost Monitoring

### GitHub Actions (Free Tier)

- **2,000 minutes/month free** for private repos
- **Unlimited minutes** for public repos
- Each trading session = ~6.5 hours = 390 minutes
- **5 trading days/week = ~1,950 minutes/month**
- **You're within free tier!** 🎉

### API Costs (Pay-as-you-go)

- OpenAI GPT-4: ~$0.01-0.03 per analysis
- Anthropic Claude: ~$0.01-0.02 per analysis
- 10 stocks × 60 scans/day × 5 days = ~3,000 analyses/month
- **Estimated: $30-90/month**

Monitor in dashboards:
- OpenAI: https://platform.openai.com/usage
- Anthropic: https://console.anthropic.com/settings/usage

---

## Next Steps

1. ✅ **Push code to GitHub** (secure!)
2. ✅ **Add GitHub Secrets**
3. ✅ **Test workflow manually**
4. ⏰ **Wait for Monday 9 AM** or trigger manually
5. 📊 **Download results** from Actions artifacts
6. 🔄 **Iterate based on performance**

---

## Support & Resources

- **GitHub Actions Docs**: https://docs.github.com/en/actions
- **GitHub Secrets**: https://docs.github.com/en/actions/security-guides/encrypted-secrets
- **Security Best Practices**: https://docs.github.com/en/code-security

---

**Your trading system is now secure and cloud-ready!** 🚀🔒

No local dependencies needed - everything runs on GitHub's infrastructure for free!
