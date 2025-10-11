# 🔗 GitHub Actions Quick Links

## ✅ Your Workflow is Already on GitHub!

The workflow file has been pushed. You just need to navigate to the correct page.

---

## 📍 Where to Go

### **Main Actions Page (See all workflows)**
👉 **https://github.com/khuranaviki/algo_trades/actions**

This shows:
- All workflow runs (past and current)
- Status of each run (success, running, failed)
- Ability to trigger manual runs

### **Paper Trading Workflow Page (Direct link)**
👉 **https://github.com/khuranaviki/algo_trades/actions/workflows/paper-trading.yml**

This shows:
- Only the "Paper Trading (Cloud)" workflow
- Green "Run workflow" button (top right)
- Schedule information
- Past runs of this specific workflow

---

## 🚀 How to Manually Trigger the Workflow

1. **Go to:** https://github.com/khuranaviki/algo_trades/actions/workflows/paper-trading.yml

2. **Look for:** Green "Run workflow" button (top right corner)

3. **Click it**, then you'll see:
   - Branch selector (select "main")
   - Green "Run workflow" button again

4. **Click the second "Run workflow" button**

5. **Watch:** The workflow will appear in the list below within 5-10 seconds

---

## 📊 What You'll See After Triggering

The workflow run will show:
```
Paper Trading (Cloud)
#1 - main

● In progress
Started X seconds ago
```

Click on it to see live logs!

---

## ⚠️ Common Issues

### Issue: "No workflows found"
**Solution:** You were on `/actions/new` (create page). Go to `/actions` (view page)

### Issue: Can't find "Run workflow" button
**Solution:** 
1. Make sure you're logged in to GitHub
2. Make sure you have write access to the repo
3. Go directly to: https://github.com/khuranaviki/algo_trades/actions/workflows/paper-trading.yml

### Issue: Workflow doesn't start
**Solution:**
1. Check if GitHub Actions is enabled: Settings → Actions → General → "Allow all actions"
2. Refresh the page
3. Try a different browser

---

## 📅 Automatic Schedule

Your workflow will also run automatically:
- **Time:** 3:00 PM IST (9:30 AM UTC)
- **Days:** Monday to Friday
- **No action needed** - it runs automatically

Next automatic run: Check the workflow page for the schedule

---

## 🎯 Quick Test Now

**Option 1: Direct Browser Link**
```
1. Click this link: https://github.com/khuranaviki/algo_trades/actions/workflows/paper-trading.yml
2. Click green "Run workflow" button (top right)
3. Select "main" branch
4. Click "Run workflow" again
5. Wait 5-10 seconds and refresh
6. Click on the new workflow run to see logs
```

**Option 2: Using GitHub CLI** (if installed)
```bash
gh workflow run "paper-trading.yml" --ref main
gh run watch
```

---

## 🔍 Monitoring Links

### **All Runs**
https://github.com/khuranaviki/algo_trades/actions

### **This Workflow Only**
https://github.com/khuranaviki/algo_trades/actions/workflows/paper-trading.yml

### **Latest Run** (after you trigger it)
Will be at the top of the list when you visit the workflow page

### **Settings**
https://github.com/khuranaviki/algo_trades/settings/actions

---

## 📧 Email Notifications

After each run, you'll receive email at: **khuranaviki@gmail.com**

Make sure these secrets are set:
- https://github.com/khuranaviki/algo_trades/settings/secrets/actions

---

**Last Updated:** October 11, 2025  
**Status:** ✅ Workflow is live and ready to run  
**Action Required:** Click the links above to access your workflows

