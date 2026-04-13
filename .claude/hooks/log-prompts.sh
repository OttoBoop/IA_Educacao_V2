#!/bin/bash
# Hook: UserPromptSubmit — logs every user message to a session-specific file
# The Claude model classifies messages (🔴/🟡/⚪) periodically, not this script.

INPUT=$(cat)
PROMPT=$(echo "$INPUT" | jq -r '.prompt // empty')
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // "unknown"')
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
CWD=$(echo "$INPUT" | jq -r '.cwd // "."')

# Find project root (look for docs/ directory)
PROJECT_DIR="$CWD"
while [ "$PROJECT_DIR" != "/" ] && [ ! -d "$PROJECT_DIR/docs" ]; do
    PROJECT_DIR=$(dirname "$PROJECT_DIR")
done

if [ "$PROJECT_DIR" = "/" ]; then
    PROJECT_DIR="$CWD"
fi

PROMPTS_DIR="$PROJECT_DIR/docs/prompts"
mkdir -p "$PROMPTS_DIR"

# Short session ID for filename (first 8 chars)
SHORT_ID=$(echo "$SESSION_ID" | cut -c1-8)
LOG_FILE="$PROMPTS_DIR/sessao_${SHORT_ID}.md"

# Create header if file doesn't exist
if [ ! -f "$LOG_FILE" ]; then
    cat > "$LOG_FILE" << HEADER
---
sessao: $SESSION_ID
inicio: $TIMESTAMP
---

# Log de Prompts — Sessão $SHORT_ID

HEADER
fi

# Append message (skip empty prompts and very short system messages)
if [ -n "$PROMPT" ] && [ ${#PROMPT} -gt 2 ]; then
    echo "" >> "$LOG_FILE"
    echo "### [$TIMESTAMP]" >> "$LOG_FILE"
    echo "$PROMPT" >> "$LOG_FILE"
fi

exit 0
