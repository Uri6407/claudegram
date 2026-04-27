---
name: tg-reply
description: Ответить на конкретное сообщение в Telegram-чате через MCP-сервер claudegram. Только пользователь явно вызывает.
argument-hint: "<@chat_or_id> <message_id> <текст с любым числом слов>"
disable-model-invocation: true
allowed-tools:
  - mcp__plugin_claudegram_claudegram__send_message
  - mcp__plugin_claudegram_claudegram__get_history
  - mcp__plugin_claudegram_claudegram__resolve_username
---

Ответ на конкретное сообщение в Telegram.

Аргументы пришли как: `$ARGUMENTS`

Парсинг:

1. **Чат** — первое слово.
2. **message_id** — второе слово, целое число.
3. **Текст** — всё остальное.

Алгоритм:

1. Разбери `$ARGUMENTS`. Если хотя бы одного из трёх не хватает — попроси уточнить.
2. Если чат — `@username`, преобразуй через `resolve_username`.
3. Подтяни через `get_history(chat=..., limit=1, offset_id=<message_id>+1)` сообщение
   с нужным id и покажи мне его текст и автора — чтобы я убедился, что отвечаешь на правильное.
4. Покажи мне финальный текст ответа.
5. Жди подтверждения «отправляй».
6. Вызови `send_message(chat=..., text=<текст>, reply_to=<message_id>)`.
   Если в тексте есть символы Markdown без намерения форматирования — `parse_mode="none"`.
7. Покажи id ответа.
