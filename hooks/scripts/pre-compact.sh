#!/usr/bin/env bash
# PreCompact hook: перед сжатием контекста инжектим reminder, чтобы
# Claude не потерял важные telegram-state'ы (последние draft'ы, allowlist).
set -euo pipefail

cat <<'EOF'
{"hookSpecificOutput":{"hookEventName":"PreCompact","additionalContext":"Перед компактом: если у тебя есть несохранённый draft Telegram-сообщения — сохрани его явно через save_draft. Если есть permission_request в ожидании verdict — отметь request_id, чтобы не потерять."}}
EOF

exit 0
