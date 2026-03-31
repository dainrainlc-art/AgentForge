#!/bin/bash
# Check GitHub Actions CI/CD Status

echo "=========================================="
echo "🔍 GitHub Actions CI/CD Status Check"
echo "=========================================="
echo ""

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "⚠️  GitHub CLI (gh) not installed"
    echo ""
    echo "To install:"
    echo "  curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg"
    echo "  echo \"deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main\" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null"
    echo "  sudo apt update"
    echo "  sudo apt install gh"
    echo ""
    echo "Or visit: https://github.com/dainrainlc-art/AgentForge/actions"
    exit 1
fi

# Check if logged in
if ! gh auth status &> /dev/null; then
    echo "⚠️  Not logged in to GitHub CLI"
    echo "Run: gh auth login"
    exit 1
fi

# Get recent workflow runs
echo "📊 Recent Workflow Runs:"
echo "------------------------------"
gh run list --repo dainrainlc-art/AgentForge --limit 5

echo ""
echo "📋 Workflow Status:"
echo "------------------------------"
gh run view --repo dainrainlc-art/AgentForge --last

echo ""
echo "🔗 View in Browser:"
echo "https://github.com/dainrainlc-art/AgentForge/actions"
