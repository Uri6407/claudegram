---
name: tg-digest
description: Сводка непрочитанных сообщений по чатам Telegram. Использует MCP-сервер claudegram. Запускать при просьбах «что у меня в тг», «дайджест непрочитанных», «что я пропустил».
argument-hint: "[лимит чатов, по умолчанию 20]"
arguments: chat_limit
allowed-tools:
  - mcp__plugin_claudegram_claudegram__list_chats
  - mcp__plugin_claudegram_claudegram__get_history
  - mcp__plugin_claudegram_claudegram__get_chat_info
---

Собери сводку непрочитанных сообщений из Telegram.

Параметр `$chat_limit` (по умолчанию 20) ограничивает число чатов.

Алгоритм:

1. Вызови `mcp__plugin_claudegram_claudegram__list_chats` с
   `only_unread=true` и `limit` равным `$chat_limit` (если пусто — `20`).
2. Для каждого чата с непрочитанными вызови
   `mcp__plugin_claudegram_claudegram__get_history` с `limit=min(unread_count, 20)`.
3. Сгруппируй по чатам и выдай сводку на русском:
   - **Чат** (тип, имя, кто пишет)
   - 1-2 строки сути сообщений
   - Если есть прямой вопрос ко мне — выдели **жирным**
4. В конце — список чатов, требующих срочного ответа.

Не помечай прочитанными автоматически. Если попрошу — вызовешь
`mcp__plugin_claudegram_claudegram__mark_read`.
