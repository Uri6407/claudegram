#!/usr/bin/env bash
# Notification hook: лог уведомлений Claude Code (idle-prompts, permission-asks).
# Best-effort: ничего не блокирует. Полезно для observability в connection-режиме.
set -euo pipefail

LOG_DIR="${CLAUDE_PLUGIN_DATA:-${CLAUDE_PLUGIN_ROOT}}/logs"
mkdir -p "$LOG_DIR"

ts="$(date -Iseconds)"
session_id="${CLAUDE_SESSION_ID:-unknown}"
INPUT="$(cat)"

if command -v jq >/dev/null 2>&1; then
  msg="$(printf '%s' "$INPUT" | jq -r '.message // empty')"
else
  msg=""
fi

echo "[$ts] session=$session_id event=notification msg=${msg:0:200}" >> "$LOG_DIR/sessions.log"
exit 0
