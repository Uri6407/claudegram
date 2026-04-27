#!/usr/bin/env bash
# SessionEnd hook: лог конца сессии с метриками Claudegram.
# Не блокирует — exit 0 всегда.
set -euo pipefail

LOG_DIR="${CLAUDE_PLUGIN_DATA:-${CLAUDE_PLUGIN_ROOT}}/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/sessions.log"

ts="$(date -Iseconds)"
session_id="${CLAUDE_SESSION_ID:-unknown}"
echo "[$ts] session=$session_id event=end" >> "$LOG_FILE"

exit 0
