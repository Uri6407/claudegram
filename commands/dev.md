---
description: Запустить MCP Inspector для отладки плагина (без участия Claude).
allowed-tools: Bash
---

Подними MCP Inspector с подключённым Claudegram-сервером:

```
! claudegram-dev
```

Inspector откроется на http://localhost:6274. Сможешь:
- Видеть все 120 tools / 9 resources / 6 templates / 7 prompts.
- Вызывать любой tool с произвольными аргументами.
- Смотреть `outputSchema` и `structuredContent`.
- Тестировать `completion` и `prompts`.

Channel-режим и permission-relay в Inspector не работают — это лимитация
`mcp dev` (запускает наш `mcp` объект напрямую, в обход кастомного `_run_async`).
