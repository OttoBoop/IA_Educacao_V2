#!/usr/bin/env bash
# check_deploy.sh — Verify that the live Render deployment matches a given commit.
#
# Usage:
#   ./scripts/check_deploy.sh [COMMIT_HASH]
#
# If COMMIT_HASH is omitted, uses `git rev-parse --short HEAD`.
# Checks <meta name="novocr-deploy" content="HASH"> in the live HTML.
# Exit codes: 0 = match, 1 = mismatch or unreachable.

set -euo pipefail

SITE_URL="${NOVOCR_URL:-https://ia-educacao-v2.onrender.com}"
EXPECTED="${1:-$(git rev-parse --short HEAD)}"

echo "Checking deploy at $SITE_URL for commit $EXPECTED ..."

DEPLOYED=$(curl -s "$SITE_URL/" | grep -oP 'novocr-deploy.*?content="\K[^"]+' || echo "NOT_FOUND")

if [ "$DEPLOYED" = "$EXPECTED" ]; then
    echo "PASS: Live site matches commit $EXPECTED"
    exit 0
else
    echo "FAIL: Expected $EXPECTED but found '$DEPLOYED'"
    echo ""
    echo "Debug info:"
    curl -sI "$SITE_URL/" 2>/dev/null | grep -iE "last-modified|server|x-render" || true
    exit 1
fi
