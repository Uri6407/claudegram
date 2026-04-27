---
description: Быстрая диагностика Claudegram — соединение, версии, latency.
allowed-tools:
  - mcp__plugin_claudegram_claudegram__health_check
  - mcp__plugin_claudegram_claudegram__get_server_version
---

Покажи короткий отчёт о состоянии плагина:
1. `mcp__plugin_claudegram_claudegram__health_check` — connected/authorized/latency.
2. `mcp__plugin_claudegram_claudegram__get_server_version` — версии claudegram/telethon/mcp/python.
3. Если `health_check.ok=false` — покажи `message` и предложи fix.

Формат ответа: компактный markdown-блок без лишних рассуждений.
