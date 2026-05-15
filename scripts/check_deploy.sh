#!/usr/bin/env bash
# check_deploy.sh — Verify that the live Render deployment is recent.
#
# Usage:
#   ./scripts/check_deploy.sh [EXPECTED_HASH]
#
# If EXPECTED_HASH is omitted, checks if the deployed hash is among
# the last 5 commits on the current branch.
#
# Prefer /api/deploy-info, which reports the backend runtime commit. The
# HTML meta tag is only a fallback because Render rootDir=backend can leave
# frontend-only markers stale.
#
# Exit codes: 0 = recent deploy found, 1 = stale or unreachable.

set -euo pipefail

SITE_URL="${NOVOCR_URL:-https://ia-educacao-v2.onrender.com}"

echo "Checking deploy at $SITE_URL ..."

EXPECTED="${1:-}"

json_field() {
    local field="$1"
    python3 -c 'import json,sys; data=json.load(sys.stdin); value=data.get(sys.argv[1]); print(value or "")' "$field" 2>/dev/null
}

DEPLOY_INFO=$(curl -fsS "$SITE_URL/api/deploy-info" 2>/dev/null || true)
if [ -n "$DEPLOY_INFO" ]; then
    DEPLOYED=$(printf '%s' "$DEPLOY_INFO" | json_field commit)
    DEPLOYED_FULL=$(printf '%s' "$DEPLOY_INFO" | json_field full_commit)
    SOURCE=$(printf '%s' "$DEPLOY_INFO" | json_field source)

    if [ -n "$DEPLOYED" ] && [ "$DEPLOYED" != "unknown" ]; then
        if [ -n "$EXPECTED" ]; then
            if [ "$DEPLOYED" = "$EXPECTED" ] || [ "$DEPLOYED_FULL" = "$EXPECTED" ] || [[ "$DEPLOYED_FULL" == "$EXPECTED"* ]]; then
                echo "PASS: Backend runtime matches commit $EXPECTED (source: $SOURCE)"
                exit 0
            fi
            echo "FAIL: Expected $EXPECTED but backend reports ${DEPLOYED_FULL:-$DEPLOYED} (source: $SOURCE)"
            exit 1
        fi

        RECENT=$(git log --oneline -5 --format='%h')
        if echo "$RECENT" | grep -q "$DEPLOYED"; then
            echo "PASS: Backend runtime $DEPLOYED is among recent commits (source: $SOURCE)"
            echo "Recent commits:"
            git log --oneline -5
            exit 0
        fi

        echo "FAIL: Backend runtime $DEPLOYED is NOT among recent commits (source: $SOURCE)"
        echo "Recent commits:"
        git log --oneline -5
        exit 1
    fi
fi

echo "WARN: /api/deploy-info unavailable or unknown; falling back to HTML marker"

DEPLOYED=$(curl -s "$SITE_URL/" | grep -oP 'novocr-deploy.*?content="\K[^"]+' || echo "NOT_FOUND")

if [ "$DEPLOYED" = "NOT_FOUND" ] || [ "$DEPLOYED" = "PENDING" ]; then
    echo "FAIL: No deploy version found in HTML (missing or PENDING meta tag)"
    exit 1
fi

if [ -n "$EXPECTED" ]; then
    # Exact match mode
    if [ "$DEPLOYED" = "$EXPECTED" ]; then
        echo "PASS: Live HTML marker matches commit $EXPECTED"
        exit 0
    else
        echo "FAIL: Expected $EXPECTED but found $DEPLOYED"
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
