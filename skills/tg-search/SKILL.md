---
name: tg-search
description: Поиск по сообщениям Telegram (глобально или в одном чате) через MCP-сервер claudegram. Запускать при просьбах «найди в тг», «искать в чате X», «поищи переписку про Y».
argument-hint: "<запрос> [@chat_or_id]"
arguments: query chat
allowed-tools:
  - mcp__plugin_claudegram_claudegram__search_messages
  - mcp__plugin_claudegram_claudegram__resolve_username
  - mcp__plugin_claudegram_claudegram__get_chat_info
---

Найди сообщения в Telegram по запросу: **$query**.

Если задан `$chat` — ограничь поиск им. Иначе ищи глобально.

Алгоритм:

1. Если `$chat` начинается с `@` — преобразуй через
   `mcp__plugin_claudegram_claudegram__resolve_username` в id.
2. Вызови `mcp__plugin_claudegram_claudegram__search_messages` с
   `query="$query"`, `chat=<id или None>`, `limit=30`.
3. Выведи результаты таблицей: дата | чат | отправитель | фрагмент текста (≤100 символов).
4. Сортируй от новых к старым.

Если результатов нет — предложи переформулировать или расширить поиск
(убрать фильтр чата). Не выдумывай результаты.
