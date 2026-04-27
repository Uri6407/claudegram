# Security Policy

## Threat model

Claudegram даёт MCP-клиенту (Claude Code) **полный программный доступ** к
личному Telegram-аккаунту через MTProto. Это эквивалентно официальному клиенту
Telegram, авторизованному паролем + 2FA.

Возможные угрозы:

| Угроза | Уровень | Митигация |
|---|---|---|
| Утечка `*.session` файла | 🔴 Critical | Хранится в `${CLAUDE_PLUGIN_DATA}` (не в git/чате); 0600 perms; никогда не логируется |
| Утечка `api_hash` / `2fa_password` | 🔴 Critical | Sensitive userConfig → системный keychain (per Claude Code docs) |
| Prompt injection через входящее сообщение в channel-режиме | 🟠 High | Allowlist gate по `event.sender_id`; skill `tg-channel-incoming` явно запрещает реагировать на injection |
| AI деструктивно действует (kick/ban/delete) без явного запроса | 🟠 High | 4 уровня PreToolUse hooks: `guard-delete` (revoke), `guard-destructive` (kick/ban/leave), `guard-confirm` (rename/raw_api/privacy), `disable-model-invocation` для send/reply skills |
| AI отправляет сообщение от моего имени | 🟠 High | `telegram-workflow` skill требует явного "отправляй" перед каждым `send_message` |
| FloodWait → бан Telegram-аккаунта | 🟡 Medium | `safe_tool` middleware возвращает `retry_after` вместо ретраев; rate-limit awareness в skills |
| Уязвимость Telethon (CVE) | 🟡 Medium | Pin минорной версии в `pyproject.toml`; следить за `telethon` security advisories |
| Cross-channel permission relay abuse | 🟡 Medium | `claude/channel/permission` объявляется только при наличии sender allowlist |
| Channel push в Claude до initialize handshake | 🟢 Low | 2-секундный warm-up в `run_listener` |

## Reporting a vulnerability

**НЕ открывай публичный issue.** Напиши на:

- Email: <sanjar68x@gmail.com> (тема: `[claudegram-security]`)
- Или: [GitHub Security Advisory](https://github.com/sanjar-x/claudegram/security/advisories/new) (приватное раскрытие)

Ожидаемое время реакции: 72 часа.

## Secrets handling

| Secret | Где хранится | Как читается |
|---|---|---|
| `api_id` | `userConfig.tg_api_id` (number) | env `${user_config.tg_api_id}` → `TG_API_ID` |
| `api_hash` | `userConfig.tg_api_hash` (sensitive) | системный keychain → env `${user_config.tg_api_hash}` |
| `phone` | `userConfig.tg_phone` (sensitive) | keychain |
| `2fa_password` | `userConfig.tg_2fa_password` (sensitive, optional) | keychain |
| `*.session` | `${CLAUDE_PLUGIN_DATA}/<name>.session` | `Telethon` SQLite, 0600 |

`server/middleware.py:sanitize()` маскирует эти ключи в логах.

## Hooks coverage

Все деструктивные tools покрыты `PreToolUse` hooks:

```
mcp__plugin_claudegram_claudegram__delete_message       → guard-delete (revoke=true → ask)
mcp__plugin_claudegram_claudegram__ban_participant      → guard-destructive
mcp__plugin_claudegram_claudegram__kick_participant     → guard-destructive
mcp__plugin_claudegram_claudegram__terminate_authorization → guard-destructive
mcp__plugin_claudegram_claudegram__leave_chat           → guard-destructive
mcp__plugin_claudegram_claudegram__delete_dialog        → guard-destructive
mcp__plugin_claudegram_claudegram__delete_forum_topic   → guard-destructive
mcp__plugin_claudegram_claudegram__delete_stories       → guard-destructive
mcp__plugin_claudegram_claudegram__delete_scheduled     → guard-destructive
mcp__plugin_claudegram_claudegram__demote_admin         → guard-destructive
mcp__plugin_claudegram_claudegram__block_user           → guard-destructive
mcp__plugin_claudegram_claudegram__invoke_raw           → guard-confirm
mcp__plugin_claudegram_claudegram__set_privacy          → guard-confirm
mcp__plugin_claudegram_claudegram__update_username      → guard-confirm
mcp__plugin_claudegram_claudegram__edit_chat_title      → guard-confirm
mcp__plugin_claudegram_claudegram__edit_chat_about      → guard-confirm
mcp__plugin_claudegram_claudegram__edit_chat_photo      → guard-confirm
mcp__plugin_claudegram_claudegram__toggle_forum_mode    → guard-confirm
```

`send_message` / `tg-reply` дополнительно защищены через `disable-model-invocation: true`
в `skills/tg-send/SKILL.md` и `tg-reply/SKILL.md` — Claude может вызвать только
по явной user-команде.

## Recommended user actions

1. **Используй отдельный Telegram-аккаунт** для экспериментов с Claudegram.
   Massive автоматизация на основном аккаунте → блокировка Telegram.

2. **Не делай `chmod 644` или `chmod 777` на session-файл.**

3. **Не запускай Claude Code в `bypassPermissions` режиме** с включённым Claudegram —
   все hook-гейты будут проигнорированы.

4. **Перед публикацией плагина сторонним пользователям**:
   - Замени дефолтный marketplace `claudegram-local` на свой
   - Подай в [Anthropic official marketplace](https://claude.ai/settings/plugins/submit) для security review

5. **Регулярно проверяй `get_authorizations`** на незнакомые сессии.
