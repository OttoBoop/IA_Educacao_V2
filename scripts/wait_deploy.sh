#!/usr/bin/env bash
# wait_deploy.sh — Poll Render until deploy matches a marker, or timeout.
#
# Usage:
#   ./scripts/wait_deploy.sh MARKER [TIMEOUT_SECONDS] [INTERVAL_SECONDS]
#
# MARKER: a string to grep for in the live HTML (e.g. "welcome-scream" or a commit hash)
# TIMEOUT: max seconds to wait (default: 600 = 10 min)
# INTERVAL: seconds between polls (default: 30)
#
# Exit codes: 0 = found, 1 = timeout

set -euo pipefail

SITE_URL="${NOVOCR_URL:-https://ia-educacao-v2.onrender.com}"
MARKER="${1:?Usage: wait_deploy.sh MARKER [TIMEOUT] [INTERVAL]}"
TIMEOUT="${2:-600}"
INTERVAL="${3:-30}"

echo "Waiting for '$MARKER' at $SITE_URL (timeout: ${TIMEOUT}s, interval: ${INTERVAL}s)"

ELAPSED=0
while [ "$ELAPSED" -lt "$TIMEOUT" ]; do
    COUNT=$(curl -s "$SITE_URL/" 2>/dev/null | grep -c "$MARKER" || true)
    if [ "$COUNT" -gt 0 ]; then
        echo "FOUND after ${ELAPSED}s — '$MARKER' appears $COUNT time(s)"
        exit 0
    fi
    echo "  ${ELAPSED}s — not yet..."
    sleep "$INTERVAL"
    ELAPSED=$((ELAPSED + INTERVAL))
done

echo "TIMEOUT after ${TIMEOUT}s — '$MARKER' not found"
echo "Last-modified: $(curl -sI "$SITE_URL/" 2>/dev/null | grep -i last-modified || echo 'unknown')"
exit 1
