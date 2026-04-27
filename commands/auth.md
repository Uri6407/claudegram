---
description: Авторизация Telegram-сессии через MCP-tools (без терминала).
allowed-tools:
  - mcp__plugin_claudegram_claudegram__health_check
  - mcp__plugin_claudegram_claudegram__auth_request_code
  - mcp__plugin_claudegram_claudegram__auth_submit_code
  - mcp__plugin_claudegram_claudegram__auth_cancel
  - AskUserQuestion
---

Двухшаговый интерактивный логин в Telegram прямо из активной Claude-сессии.

Шаги:
1. Запусти `mcp__plugin_claudegram_claudegram__health_check` — если уже
   `authorized: true`, скажи юзеру и выйди.
2. Иначе вызови `auth_request_code()` — Telegram пришлёт SMS-код на привязанный
   номер. Покажи юзеру `phone` (маскированный).
3. Спроси у юзера код через `AskUserQuestion` (поле `code`, 5 цифр).
   Если в userConfig не было пароля 2FA — спроси и его (опционально).
4. Вызови `auth_submit_code(code=<код>, password_2fa=<2fa или "">)`.
5. Если в ответе `needs_2fa: true` — спроси пароль и повтори с ним.
6. Если в ответе `error: PhoneCodeInvalidError/Expired` — предложи запросить
   новый код через `auth_request_code()`.
7. После успеха вызови `health_check` — должен показать `ok=true`,
   `authorized=true`, `self_id`. Скажи юзеру что готово.

Важно: НЕ предлагай `! claudegram-auth` через Bash — он требует интерактивного
stdin, который Bash tool в Claude Code не предоставляет (commands/auth.md
устаревший подход). Используй ТОЛЬКО эти MCP-tools.
