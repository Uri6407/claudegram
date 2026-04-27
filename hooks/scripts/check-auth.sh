#!/usr/bin/env bash
# SessionStart hook: проверяет, что Telegram-сессия авторизована.
# Если файла .session нет — добавляет в контекст подсказку, как залогиниться.
# Exit 0 в любом случае — это не блокирующий хук.
set -euo pipefail

DATA_DIR="${CLAUDE_PLUGIN_DATA:-${CLAUDE_PLUGIN_ROOT}}"
SESSION_NAME_RAW="${CLAUDE_PLUGIN_OPTION_TG_SESSION_NAME:-claudegram}"
# Telethon сам добавляет .session — отрезаем суффикс если юзер его указал.
SESSION_NAME="${SESSION_NAME_RAW%.session}"
[[ -z "$SESSION_NAME" ]] && SESSION_NAME="claudegram"
SESSION_FILE="${DATA_DIR}/${SESSION_NAME}.session"

if [[ ! -f "$SESSION_FILE" ]]; then
  cat <<EOF
[claudegram] Telegram-сессия не найдена: ${SESSION_FILE}
Чтобы залогиниться, выполни в терминале:

    claudegram-auth

Или из каталога плагина:

    uv run python -m server.auth

Без авторизации MCP-инструменты mcp__plugin_claudegram_claudegram__* работать не будут.
EOF
fi

exit 0
