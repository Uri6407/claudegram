---
name: tg-history
description: Показать последние сообщения из конкретного Telegram-чата через MCP-сервер claudegram. Запускать при «покажи переписку с X», «история чата X», «что писали в чате Y».
argument-hint: "<@chat_or_id> [лимит, по умолчанию 30]"
arguments: chat limit
allowed-tools:
  - mcp__plugin_claudegram_claudegram__get_history
  - mcp__plugin_claudegram_claudegram__resolve_username
  - mcp__plugin_claudegram_claudegram__get_chat_info
---

Показать последние сообщения чата `$chat`.

Лимит — `$limit` (если пусто, используй **30**; если задано больше **200** —
отрежь до 200, это хард-кап Telethon, и предупреди меня).

Алгоритм:

1. Если `$chat` начинается с `@` — `resolve_username` → id.
2. Покажи краткую инфу о чате через `get_chat_info`.
3. Вызови `get_history` с `chat=<id>` и `limit=<вычисленный по правилу выше>`.
4. Выведи список: время · отправитель · текст (или иконка media-type для вложений).
5. Если у сообщения есть `reply_to_msg_id` — пометь стрелочкой "↳ #<id>".
