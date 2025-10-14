#!/bin/bash
# Pre-Push Security Check
# Scans for API keys and sensitive data before pushing to GitHub

set -e

echo "🔒 Running Pre-Push Security Check..."
echo "===================================="
echo ""

FAILED=0

# Check 1: Scan for OpenAI API keys
echo "✓ Checking for OpenAI API keys..."
if git grep -n "sk-[a-zA-Z0-9]\{48\}" -- ':!.gitignore' ':!GITHUB_SETUP.md' ':!*.md' 2>/dev/null; then
    echo "❌ FAIL: Found OpenAI API key pattern in code!"
    FAILED=1
else
    echo "  ✅ No OpenAI API keys found"
fi
echo ""

# Check 2: Scan for Anthropic API keys
echo "✓ Checking for Anthropic API keys..."
if git grep -n "sk-ant-[a-zA-Z0-9]\{95,110\}" -- ':!.gitignore' ':!GITHUB_SETUP.md' ':!*.md' 2>/dev/null; then
    echo "❌ FAIL: Found Anthropic API key pattern in code!"
    FAILED=1
else
    echo "  ✅ No Anthropic API keys found"
fi
echo ""

# Check 3: Scan for generic API key patterns
echo "✓ Checking for generic API key patterns..."
if git grep -niE "api[_-]?key\s*[:=]\s*['\"][a-zA-Z0-9]{20,}['\"]" -- ':!.gitignore' ':!GITHUB_SETUP.md' ':!*.md' ':!*.sh' 2>/dev/null; then
    echo "❌ FAIL: Found potential API key assignment!"
    FAILED=1
else
    echo "  ✅ No generic API key patterns found"
fi
echo ""

# Check 4: Ensure .env files are gitignored (except .env.example)
echo "✓ Checking .env files..."
if git ls-files | grep -E "\.env$|\.env\." | grep -v "\.env\.example" 2>/dev/null; then
    echo "❌ FAIL: .env files are being tracked by git!"
    echo "  Run: git rm --cached .env*"
    FAILED=1
else
    echo "  ✅ No .env files tracked (except safe .env.example)"
fi
echo ""

# Check 5: Check for hardcoded secrets
echo "✓ Checking for hardcoded secrets..."
if git grep -niE "password\s*[:=]\s*['\"][^'\"]+['\"]|secret\s*[:=]\s*['\"][^'\"]+['\"]" -- ':!.gitignore' ':!GITHUB_SETUP.md' ':!*.md' 2>/dev/null | grep -v "your-.*-here" | grep -v "REMOVED" | grep -v "example"; then
    echo "❌ FAIL: Found hardcoded passwords or secrets!"
    FAILED=1
else
    echo "  ✅ No hardcoded secrets found"
fi
echo ""

# Check 6: Verify critical files in .gitignore
echo "✓ Checking .gitignore coverage..."
REQUIRED_IGNORES=(
    "*.env"
    "*.pem"
    "*.key"
    "credentials.json"
    "data/"
    "logs/"
)

for pattern in "${REQUIRED_IGNORES[@]}"; do
    if grep -q "^$pattern" .gitignore; then
        echo "  ✅ $pattern is ignored"
    else
        echo "  ❌ $pattern is NOT in .gitignore!"
        FAILED=1
    fi
done
echo ""

# Check 7: Scan for AWS credentials
echo "✓ Checking for AWS credentials..."
if git grep -niE "AKIA[0-9A-Z]{16}" -- ':!.gitignore' ':!*.md' 2>/dev/null; then
    echo "❌ FAIL: Found AWS Access Key ID!"
    FAILED=1
else
    echo "  ✅ No AWS credentials found"
fi
echo ""

# Check 8: Scan for private keys
echo "✓ Checking for private keys..."
PRIVATE_KEYS=$(git grep -n "BEGIN.*PRIVATE KEY" -- ':!*.md' ':!*.sh' 2>/dev/null || true)
if [ -n "$PRIVATE_KEYS" ]; then
    echo "❌ FAIL: Found private key in code!"
    echo "$PRIVATE_KEYS"
    FAILED=1
else
    echo "  ✅ No private keys found"
fi
echo ""

# Check 9: Verify sensitive files are not staged
echo "✓ Checking staged files..."
SENSITIVE_FILES=$(git diff --cached --name-only | grep -E "\.env$|\.pem$|credentials\.json|portfolio_state\.json|trade_history\.csv" || true)
if [ -n "$SENSITIVE_FILES" ]; then
    echo "❌ FAIL: Sensitive files are staged:"
    echo "$SENSITIVE_FILES"
    echo "  Run: git reset HEAD <file>"
    FAILED=1
else
    echo "  ✅ No sensitive files staged"
fi
echo ""

# Final result
echo "===================================="
if [ $FAILED -eq 1 ]; then
    echo "❌ SECURITY CHECK FAILED!"
    echo ""
    echo "⚠️  DO NOT PUSH TO GITHUB!"
    echo ""
    echo "Fix the issues above before pushing."
    echo "If you accidentally committed secrets:"
    echo "  1. Revoke the API key immediately"
    echo "  2. Generate a new key"
    echo "  3. Use 'git reset' to remove the commit"
    echo "  4. Or use BFG Repo-Cleaner to remove from history"
    echo ""
    exit 1
else
    echo "✅ SECURITY CHECK PASSED!"
    echo ""
    echo "Safe to push to GitHub 🚀"
    echo ""
    echo "Next steps:"
    echo "  1. git push origin main"
    echo "  2. Add secrets to GitHub (Settings → Secrets)"
    echo "  3. Read GITHUB_SETUP.md for complete guide"
    echo ""
fi
