#!/usr/bin/env bash
# check_deploy.sh — Verify that the live Render deployment is recent.
#
# Usage:
#   ./scripts/check_deploy.sh [EXPECTED_HASH]
#
# If EXPECTED_HASH is omitted, checks if the deployed hash is among
# the last 5 commits on the current branch.
#
# The meta tag is updated by a separate commit after changes, so the
# deployed hash will typically be 1 commit behind HEAD. The script
# accounts for this by checking the last 5 commits.
#
# Exit codes: 0 = recent deploy found, 1 = stale or unreachable.

set -euo pipefail

SITE_URL="${NOVOCR_URL:-https://ia-educacao-v2.onrender.com}"

echo "Checking deploy at $SITE_URL ..."

DEPLOYED=$(curl -s "$SITE_URL/" | grep -oP 'novocr-deploy.*?content="\K[^"]+' || echo "NOT_FOUND")

if [ "$DEPLOYED" = "NOT_FOUND" ] || [ "$DEPLOYED" = "PENDING" ]; then
    echo "FAIL: No deploy version found in HTML (missing or PENDING meta tag)"
    exit 1
fi

if [ -n "${1:-}" ]; then
    # Exact match mode
    if [ "$DEPLOYED" = "$1" ]; then
        echo "PASS: Live site matches commit $1"
        exit 0
    else
        echo "FAIL: Expected $1 but found $DEPLOYED"
        exit 1
    fi
fi

# Recent-commits mode: check if deployed hash is among last 5 commits
RECENT=$(git log --oneline -5 --format='%h')
if echo "$RECENT" | grep -q "$DEPLOYED"; then
    echo "PASS: Deployed version $DEPLOYED is among recent commits"
    echo "Recent commits:"
    git log --oneline -5
    exit 0
else
    echo "FAIL: Deployed version $DEPLOYED is NOT among recent commits"
    echo "Recent commits:"
    git log --oneline -5
    echo ""
    echo "Debug:"
    curl -sI "$SITE_URL/" 2>/dev/null | grep -iE "last-modified|server" || true
    exit 1
fi
