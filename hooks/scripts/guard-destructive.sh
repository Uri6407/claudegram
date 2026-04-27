#!/usr/bin/env bash
# PreToolUse hook для деструктивных операций (ban/kick/leave/delete и т.п.).
# Принудительно требует явного подтверждения юзера.
set -euo pipefail

cat <<'EOF'
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"Деструктивная операция — требует явного подтверждения. Покажи юзеру, что именно произойдёт, и дождись 'да/подтверждаю'."}}
EOF
exit 0
