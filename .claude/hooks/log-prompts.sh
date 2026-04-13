#!/bin/bash
# Hook: UserPromptSubmit — logs every user message to a session-specific file
# No external dependencies (no jq) — uses bash string manipulation only

INPUT=$(cat)
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Extract JSON fields without jq (basic regex extraction)
# Pattern: "field": "value" or "field": value
extract_field() {
    local field="$1"
    local input="$2"
    # Try quoted value first
    echo "$input" | grep -oP "\"${field}\"\s*:\s*\"[^\"]*\"" | head -1 | sed "s/\"${field}\"\s*:\s*\"//" | sed 's/"$//'
}

PROMPT=$(extract_field "prompt" "$INPUT")
SESSION_ID=$(extract_field "session_id" "$INPUT")
CWD=$(extract_field "cwd" "$INPUT")

# Fallbacks
[ -z "$SESSION_ID" ] && SESSION_ID="unknown"
[ -z "$CWD" ] && CWD="."

# Find project root (look for docs/ directory)
PROJECT_DIR="$CWD"
while [ "$PROJECT_DIR" != "/" ] && [ ! -d "$PROJECT_DIR/docs" ]; do
    PROJECT_DIR=$(dirname "$PROJECT_DIR")
done
[ "$PROJECT_DIR" = "/" ] && PROJECT_DIR="$CWD"

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

# Append message (skip empty prompts and very short messages)
if [ -n "$PROMPT" ] && [ ${#PROMPT} -gt 2 ]; then
    echo "" >> "$LOG_FILE"
    echo "### [$TIMESTAMP]" >> "$LOG_FILE"
    echo "$PROMPT" >> "$LOG_FILE"
fi

exit 0
