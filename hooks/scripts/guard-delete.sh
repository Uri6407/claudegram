#!/usr/bin/env bash
# PreToolUse hook на mcp__plugin_claudegram_claudegram__delete_message.
# Если revoke=true (удаление у всех) — заставляет Claude переспросить юзера.
# Иначе пропускает.
#
# Hook input приходит JSON-ом по stdin. Используем jq, если есть; иначе python3.
set -euo pipefail

INPUT="$(cat)"

if command -v jq >/dev/null 2>&1; then
  REVOKE="$(printf '%s' "$INPUT" | jq -r '.tool_input.revoke // false')"
elif command -v python3 >/dev/null 2>&1; then
  REVOKE="$(printf '%s' "$INPUT" | python3 -c 'import json,sys; print(str(json.load(sys.stdin).get("tool_input",{}).get("revoke", False)).lower())')"
else
  # Если ни jq, ни python3 нет — на всякий случай блокируем.
  REVOKE="true"
fi

if [[ "$REVOKE" == "true" ]]; then
  if command -v jq >/dev/null 2>&1; then
    jq -n '{
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "ask",
        permissionDecisionReason: "Удаление сообщения у всех (revoke=true) необратимо. Подтверди явно."
      }
    }'
  else
    cat <<'EOF'
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"Удаление сообщения у всех (revoke=true) необратимо. Подтверди явно."}}
EOF
  fi
fi

exit 0
