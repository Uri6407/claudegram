#!/usr/bin/env bash
# PreToolUse hook для операций со средним риском
# (изменение профиля/чата/raw-API). Просит подтверждение.
set -euo pipefail

cat <<'EOF'
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"Изменяющая операция (raw-API/настройки/название). Покажи параметры юзеру и дождись подтверждения."}}
EOF
exit 0
