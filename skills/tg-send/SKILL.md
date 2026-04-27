---
name: tg-send
description: Отправить сообщение в Telegram-чат через MCP-сервер claudegram. Только пользователь явно вызывает — Claude сам не запускает.
argument-hint: "<@chat_or_id> <текст с любым числом слов и переносов>"
disable-model-invocation: true
allowed-tools:
  - mcp__plugin_claudegram_claudegram__send_message
  - mcp__plugin_claudegram_claudegram__resolve_username
  - mcp__plugin_claudegram_claudegram__get_chat_info
---

Отправить сообщение в Telegram.

Аргументы пришли как: `$ARGUMENTS`

Парсинг:

1. **Получатель** — первое слово в `$ARGUMENTS` (`@username`, `username` или числовой id).
2. **Текст** — всё остальное после первого пробела. Сохрани переносы строк, не трогай регистр.

Алгоритм:

1. Разбери `$ARGUMENTS` по правилу выше. Если получатель пустой или текст пустой — попроси уточнить, не выдумывай.
2. Если получатель — `@username`, преобразуй через
   `mcp__plugin_claudegram_claudegram__resolve_username`.
3. Покажи мне краткую инфу о чате (тип, имя, id) через
   `mcp__plugin_claudegram_claudegram__get_chat_info`.
4. Покажи мне финальный текст в блоке кода, чтобы я перечитал.
5. **Жди явного подтверждения** прежде чем вызывать
   `mcp__plugin_claudegram_claudegram__send_message`.
6. Если в тексте есть `*`, `_`, `[`, `]`, `~`, `\`` без явного намерения форматирования —
   передай `parse_mode="none"`. Иначе оставь дефолт `"markdown"`.
7. После отправки покажи `id` отправленного сообщения (на случай редактирования / удаления).
