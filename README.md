<h1 align="center">Claudegram</h1>

<p align="center">
  <em>Личный Telegram-аккаунт как полноценный инструмент Claude Code — через MTProto, не Bot API.</em>
</p>

<p align="center">
  <a href="https://github.com/sanjar-x/claudegram/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/sanjar-x/claudegram/actions/workflows/ci.yml/badge.svg"></a>
  <a href="https://github.com/sanjar-x/claudegram/actions/workflows/codeql.yml"><img alt="CodeQL" src="https://github.com/sanjar-x/claudegram/actions/workflows/codeql.yml/badge.svg"></a>
  <a href="https://github.com/sanjar-x/claudegram/blob/main/LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-blue.svg"></a>
  <a href="https://www.python.org/downloads/release/python-3140/"><img alt="Python 3.14+" src="https://img.shields.io/badge/python-3.14%2B-blue.svg"></a>
  <a href="https://github.com/astral-sh/ruff"><img alt="Code style: ruff" src="https://img.shields.io/badge/code%20style-ruff-261230.svg"></a>
  <a href="https://github.com/astral-sh/uv"><img alt="uv" src="https://img.shields.io/badge/managed%20by-uv-261230.svg"></a>
  <a href="https://modelcontextprotocol.io"><img alt="MCP" src="https://img.shields.io/badge/MCP-1.27%2B-8A2BE2.svg"></a>
  <a href="https://code.claude.com/docs/en/plugins-reference"><img alt="Claude Code Plugin" src="https://img.shields.io/badge/Claude%20Code-Plugin-D97757.svg"></a>
</p>

<p align="center">
  <strong>120 MCP-tools</strong> · <strong>9 resources</strong> · <strong>6 templates</strong> · <strong>7 prompts</strong> · <strong>6 skills</strong> · <strong>4 уровня PreToolUse-гейтов</strong>
</p>

---

## TL;DR

Claudegram — production-grade плагин Claude Code, превращающий личный Telegram в управляемый AI-инструмент:

- **MTProto, не Bot API** — видит **всю** переписку, истории, поиск, медиа, статистику.
- **120 типизированных MCP-tools** через FastMCP, разбиты на 9 доменов; покрыты `safe_tool` middleware с FloodWait/RPCError handling и санитизацией секретов.
- **Channel-режим**: входящие сообщения push-ятся в активную сессию Claude как `<channel>` теги с permission relay (yes/no через `<id>`).
- **4-слойная safety net**: PreToolUse hooks (`guard-delete`, `guard-destructive`, `guard-confirm`) + `disable-model-invocation` для отправки сообщений + sensitive userConfig в системный keychain.
- **Skills + Prompts**: `tg-digest`, `tg-search`, `tg-history`, `tg-send`, `tg-reply`, `telegram-workflow` — готовые сценарии для рекрутерского тестового запуска.

Полный список возможностей — в таблице ниже.

## Why this project

- Реальный production-ready MCP-сервер: типизированные tools, structured output, prompt templates, completions, resource templates.
- Безопасность спроектирована up-front: модель угроз, hook-гейты, allowlist, sanitize в логах. См. [SECURITY.md](SECURITY.md).
- Чистая архитектура: 75 модулей, ~6.3k строк server-кода, ~900 строк тестов, ruff + mypy, CI на GitHub Actions, Codecov, CodeQL.
- Каждое решение объяснено docstring'ом и CHANGELOG'ом, без «магии».

## Quick start

```bash
git clone https://github.com/sanjar-x/claudegram.git && cd claudegram
uv sync
cp .env.example .env  # вставь api_id/api_hash/phone с https://my.telegram.org
uv run claudegram-auth
# затем в Claude Code: /plugin add . && /plugin install claudegram
```

Подробнее — в разделе «Установка» ниже.

В отличие от Bot API, Claudegram видит **всю историю**, **все чаты** и поддерживает **поиск**.
Архитектура и компоненты выровнены под официальную
[спеку Claude Code Plugins](https://code.claude.com/docs/en/plugins-reference).

## Возможности

| Слой              | Что внутри                                                             |
|-------------------|------------------------------------------------------------------------|
| **MCP-сервер**    | **118 типизированных tool'ов** через FastMCP + Telethon, разбиты по 9 доменам с подпакетами в `server/tools/` |
| **Production middleware** | `safe_tool` decorator с graceful FloodWait/RPCError handling, latency logging, sensitive-sanitization |
| **Health probe**  | `health_check` + `get_server_version` для readiness/liveness |
| **Channel-режим** | Push входящих Telegram-сообщений в активную сессию Claude как `<channel source="claudegram">` теги + permission relay (yes/no `<id>`) |
| **Skills**        | 6 skill'ов: `tg-digest`, `tg-search`, `tg-history`, `tg-send`, `tg-reply` + фоновые `telegram-workflow` и `tg-channel-incoming` |
| **Hooks**         | `SessionStart` — авто-проверка авторизации; `PreToolUse` — гейт перед `delete revoke=true` (с jq/python3 fallback) |
| **bin/**          | `claudegram-auth` — попадает в PATH **Bash tool** Claude Code (не в shell хоста); снаружи — `uv run claudegram-auth` |
| **userConfig**    | Креденшелы + sender-allowlist запрашиваются GUI-промптом плагина, сенситивные в системном keychain |
| **Persistent data** | `*.session` живёт в `${CLAUDE_PLUGIN_DATA}` — не теряется при апдейте плагина |
| **Marketplace**   | `.claude-plugin/marketplace.json` — каталог из одного плагина для `/plugin install` |

## Структура

```
Claudegram/
├── .claude-plugin/
│   └── plugin.json                  # манифест с userConfig (api_id/hash/phone/2fa)
├── .mcp.json                        # MCP stdio-сервер, env через ${user_config.*}
├── hooks/
│   ├── hooks.json                   # SessionStart auth-check, PreToolUse delete-guard
│   └── scripts/
│       ├── check-auth.sh
│       └── guard-delete.sh
├── skills/                          # каждая команда — отдельный каталог с SKILL.md
│   ├── telegram-workflow/SKILL.md   # фоновые правила (user-invocable: false)
│   ├── tg-channel-incoming/SKILL.md # обработка <channel source="claudegram"> тегов
│   ├── tg-digest/SKILL.md           # /claudegram:tg-digest [N]
│   ├── tg-search/SKILL.md           # /claudegram:tg-search <запрос> [@chat]
│   ├── tg-history/SKILL.md          # /claudegram:tg-history <@chat> [limit]
│   ├── tg-send/SKILL.md             # /claudegram:tg-send <@chat> <текст>  (disable-model-invocation)
│   └── tg-reply/SKILL.md            # /claudegram:tg-reply <@chat> <id> <текст>
├── bin/
│   └── claudegram-auth              # шелл-обёртка над server.auth
├── server/                          # Python MCP-сервер (FastMCP + Telethon)
│   ├── __init__.py
│   ├── config.py                    # plugin-mode + standalone-mode env loading
│   ├── auth.py                      # одноразовый интерактивный логин
│   ├── client.py                    # singleton TelegramClient
│   ├── formatters.py                # сериализация в JSON
│   ├── channel.py                   # channel-режим: push + permission relay
│   ├── main.py                      # FastMCP entry + custom stdio runner с experimental caps
│   └── tools/                       # 92 tools в 8 доменах с подпакетами
│       ├── __init__.py              # register_all(mcp) — диспатчит по доменам
│       ├── _common.py               # shared utils (ParseMode, normalize_chat, clamp, to_jsonable)
│       ├── identity/                # account, sessions
│       │   ├── account.py           # get_me, update_profile, set_online, update_username, get_full_user
│       │   └── sessions.py          # get_authorizations, terminate_authorization
│       ├── peers/                   # discovery + метаданные сущностей
│       │   ├── lookup.py            # resolve_username, get_chat_info, search_global, get_top_peers, get_input_peer
│       │   ├── users.py             # get_profile_photos, download_profile_photo, get_common_chats
│       │   └── contacts.py          # CRUD + block/unblock + import + get_blocked
│       ├── messaging/               # send/edit/history/pins/reactions
│       │   ├── messages.py          # send/edit/delete/forward
│       │   ├── history.py           # get_history (+filter_type), search_messages
│       │   ├── pins.py              # pin_message, unpin_message
│       │   └── reactions.py         # react_message
│       ├── dialogs/                 # список и состояния диалогов
│       │   ├── list_.py             # list_chats, get_drafts
│       │   ├── folders.py           # archive/unarchive/pin_dialog
│       │   └── notify.py            # mark_read, mute, unmute, delete_dialog
│       ├── chats/                   # управление группами/каналами
│       │   ├── create.py            # create_group, create_channel
│       │   ├── settings.py          # title/about/photo/forum_mode
│       │   ├── members.py           # participants, kick, ban, unban, restrict, promote, demote
│       │   ├── invites.py           # join, leave, export_invite
│       │   └── admin.py             # admin_log, stats
│       ├── media/                   # файлы и attachments
│       │   ├── files.py             # send_file, send_album
│       │   ├── download.py          # download_media, get_media_info
│       │   ├── attachments.py       # send_location, send_contact, send_dice
│       │   └── stickers.py          # все sticker-операции
│       ├── content/                 # контент-фичи
│       │   ├── polls.py             # send/vote/results
│       │   ├── stories.py           # all stories operations
│       │   └── forums.py            # forum-topics
│       └── advanced/
│           └── raw.py               # invoke_raw — ANY MTProto method
├── pyproject.toml + uv.lock         # uv-проект
├── .env.example                     # для standalone-режима
├── .gitignore                       # игнорит .env, *.session, .venv, кеши
└── README.md
```

## Стек

- Python 3.14, [uv](https://docs.astral.sh/uv/)
- [Telethon](https://docs.telethon.dev/) 1.43+ — MTProto-клиент
- [`mcp[cli]`](https://github.com/modelcontextprotocol/python-sdk) 1.x — официальный SDK MCP

## Установка

### 1. Получить API-креденшелы

1. Открой <https://my.telegram.org> → **API development tools**.
2. Создай приложение (любые `App title` / `Short name`).
3. Скопируй `api_id` и `api_hash`.

### 2. Установить зависимости (uv создаст `.venv/`)

```bash
cd ~/Desktop/Claudegram
uv sync
```

### 3. Подключить плагин в Claude Code

Самый быстрый способ для разработки — `--plugin-dir` (грузит как сессионный плагин,
без установки):

```bash
claude --plugin-dir ~/Desktop/Claudegram
```

Постоянная установка через локальный marketplace (`marketplace.json` уже включён
в `.claude-plugin/`):

```
/plugin marketplace add ~/Desktop/Claudegram
/plugin install claudegram@claudegram-local
```

`claudegram-local` — имя локального marketplace из `.claude-plugin/marketplace.json`.

При первом включении Claude Code откроет промпт и попросит ввести
`tg_api_id`, `tg_api_hash`, `tg_phone` (поля `userConfig` из манифеста).
Сенситивные значения уйдут в системный keychain, не в `settings.json`.

### 4. Авторизоваться (один раз)

⚠️ Важно: `bin/claudegram-auth` попадает в PATH **только Bash tool внутри
Claude Code**, не в обычный shell хоста (это ограничение Claude Code, см.
[plugins-reference](https://code.claude.com/docs/en/plugins-reference#file-locations-reference)).

Вариант **A** (рекомендуемый, из активной Claude-сессии):

```
! claudegram-auth
```

Префикс `!` запускает команду в shell сессии, и тогда `bin/claudegram-auth`
из плагина уже в PATH.

Вариант **B** (из обычного терминала, standalone):

```bash
cd ~/Desktop/Claudegram
uv run python -m server.auth
# или
uv run claudegram-auth     # после `uv sync` появляется console-script
```

В обоих случаях — введи код из Telegram. Файл сессии создастся:
- **Plugin-mode**: `~/.claude/plugins/data/claudegram-claudegram-local/claudegram.session` (переменная `${CLAUDE_PLUGIN_DATA}`) — не теряется при апдейте плагина.
- **Standalone**: в корне проекта `~/Desktop/Claudegram/claudegram.session`.

### 5. Проверить

```
/mcp                 # должен появиться сервер "claudegram"
/reload-plugins      # после правок без рестарта
/hooks               # увидишь SessionStart + PreToolUse гейт
```

## Использование

### Slash-skills (тип `/claudegram:<skill>`)

- `/claudegram:tg-digest [N]` — сводка непрочитанных по N чатам.
- `/claudegram:tg-search <запрос> [@chat]` — поиск.
- `/claudegram:tg-history <@chat> [N]` — последние N сообщений чата.
- `/claudegram:tg-send <@chat> <текст>` — отправка с подтверждением. Только пользователь вызывает (`disable-model-invocation: true`).
- `/claudegram:tg-reply <@chat> <id> <текст>` — ответ на конкретное сообщение. Только пользователь.

### Авто-активация

Skill `telegram-workflow` (`user-invocable: false`) подгружается, когда ты пишешь
"что у меня в Telegram?", "найди в чатах", "напиши Пете". Claude по описанию
выбирает правильный MCP-tool и следует safety-правилам из этого skill.

### Прямые MCP-инструменты (58 шт)

Полный namespace: `mcp__plugin_claudegram_claudegram__<tool>`. Wildcard для
permission-rule: `mcp__plugin_claudegram_claudegram__*`.

Полный каталог с описаниями и сигнатурами — в skill'е [`telegram-workflow/SKILL.md`](skills/telegram-workflow/SKILL.md).
Краткая сводка по категориям:

- **Account** (5): `get_me`, `get_authorizations`, `terminate_authorization`, `update_profile`, `set_online`
- **Messages** (11): `send_message`, `edit_message`, `delete_message`, `forward_message`, `get_history`, `search_messages`, `mark_read`, `pin_message`, `unpin_message`, `react_message`, `send_dice`
- **Dialogs** (7): `list_chats`, `get_drafts`, `archive_dialog`, `unarchive_dialog`, `delete_dialog`, `mute_dialog`, `unmute_dialog`
- **Users** (7): `get_chat_info`, `resolve_username`, `get_participants`, `get_profile_photos`, `block_user`, `unblock_user`, `get_common_chats`
- **Chats** (12): `create_group`, `create_channel`, `edit_chat_title`, `edit_chat_about`, `join_chat`, `leave_chat`, `kick_participant`, `ban_participant`, `unban_participant`, `promote_admin`, `demote_admin`, `get_admin_log`, `get_stats`
- **Media** (7): `download_media`, `download_profile_photo`, `send_file`, `send_album`, `send_location`, `send_contact`, `get_media_info`
- **Contacts** (4): `get_contacts`, `add_contact`, `delete_contact`, `search_global`
- **Polls** (2): `send_poll`, `vote_poll`
- **Raw API** (2): `invoke_raw`, `get_input_peer` — escape hatch для **любого** MTProto-метода через `telethon.tl.functions.<module>.<MethodNameRequest>`. Покрывает Stories, Payments, Stickers, Channels admin, Folders, Themes — всё, что не обёрнуто high-level API.

## Как работает безопасность

- `.env` и `*.session` в `.gitignore`.
- Sensitive userConfig (api_hash, phone, 2FA) уходят в системный keychain (или `~/.claude/.credentials.json`), не в `settings.json`.
- `*.session` лежит в `${CLAUDE_PLUGIN_DATA}` — не утекает с апдейтом, но даёт полный доступ к аккаунту, храни как пароль.
- `PreToolUse`-хук на `delete_message` принудительно спрашивает, если `revoke=true`.
- Skill `telegram-workflow` обязывает Claude получать явное подтверждение перед `send_message`/`mark_read`/`delete_message`.
- Telegram может посчитать активность подозрительной → возможна блокировка. Для экспериментов используй **отдельный** аккаунт.

## Standalone-режим (без плагина)

Можно запустить MCP-сервер вне Claude Code:

```bash
cp .env.example .env
$EDITOR .env       # заполни TG_API_ID/HASH/PHONE
uv run python -m server.auth        # логин, .session ляжет в корень
uv run python -m server.main        # MCP stdio-сервер
```

`server/config.py` сначала читает `TG_*` (или `.env`), затем —
`CLAUDE_PLUGIN_OPTION_TG_*`, которые экспортируются плагином. Один и тот же код
работает в обоих режимах.

## Расширение

- **Новый MCP-tool** → функция в `server/main.py` с `@mcp.tool()`. FastMCP сам сгенерирует JSON-схему по type-hints + docstring.
- **Новый skill** → каталог `skills/<name>/` с `SKILL.md`. Frontmatter: `name`, `description`, опционально `argument-hint`, `arguments`, `allowed-tools`, `disable-model-invocation`, `paths`, `model`, `effort`.
- **Новый hook** → редактируй `hooks/hooks.json`. Доступные события см. [hooks reference](https://code.claude.com/docs/en/hooks).
- **Бинарь** → положи в `bin/<name>` + chmod +x. Автоматически попадёт в PATH.

После любых изменений: `/reload-plugins` в Claude Code (рестарт не нужен).

## Channel-режим

[Channels](https://code.claude.com/docs/en/channels) (research preview Claude Code v2.1.80+) —
двусторонний bridge: входящие Telegram-сообщения **сами** появляются в активной
Claude-сессии как XML-теги, Claude отвечает обратно через `send_message`.

### Что под капотом

- В `.mcp.json` плагин выставляет `CLAUDEGRAM_CHANNEL_MODE=1` → `server/main.py`
  объявляет experimental capabilities `claude/channel` и `claude/channel/permission`
  через кастомный stdio-runner (FastMCP сам не умеет — обходим через `_mcp_server.create_initialization_options(experimental_capabilities=...)`).
- `server/channel.py` подписывается на Telethon `@client.on(events.NewMessage(incoming=True))`.
- Каждое входящее от ID из allowlist (`tg_allowed_sender_ids`) пушится как
  raw `JSONRPCNotification(method='notifications/claude/channel', ...)` напрямую
  через write_stream stdio-сессии.
- Тег у Claude выглядит так:

  ```xml
  <channel source="claudegram"
           chat_id="-1001234567890"
           message_id="42"
           sender_id="111222333"
           user="Pete">
  привет, как дела?
  </channel>
  ```

- Skill `tg-channel-incoming` (auto-active) объясняет Claude'у, что делать
  с такими тегами + правила безопасности (никакого автоответа без подтверждения).
- **Permission relay**: ответные сообщения вида `yes abcde` / `no abcde`
  (5 строчных букв без `l`, regex case-insensitive) парсятся как verdict и шлются
  обратно как `notifications/claude/channel/permission` — Claude Code применяет автоматически.

### Включение

Channel-режим **opt-in** через userConfig поле `enable_channel_mode`:

1. В `/plugin` интерфейсе или при первой установке выстави `enable_channel_mode = "1"`.
2. Перезапусти Claude Code с обоими флагами:

   ```bash
   claude \
     --dangerously-load-development-channels plugin:claudegram@claudegram-local \
     --channels plugin:claudegram@claudegram-local
   ```

   В research preview кастомные плагины **не входят** в Anthropic allowlist
   (`--dangerously-load-development-channels`), а `--channels` явно регистрирует
   listener — оба флага нужны.

Если `enable_channel_mode = "0"` (default) — сервер работает только как tools-MCP,
push'и не отсылаются, Telegram-rate-limit не тратится.

Удобно завести алиас в `~/.zshrc`:

```bash
alias claude-tg='claude --dangerously-load-development-channels plugin:claudegram@claudegram-local --channels plugin:claudegram@claudegram-local'
```

### Безопасность

| Слой | Защита |
|---|---|
| **Sender gate** | `parse_allowed_ids()` в `channel.py` пушит только от ID из `tg_allowed_sender_ids`. Пустой allowlist = только себе (свой `get_me().id`). |
| **Группы** | Гейтим по `event.sender_id`, **не** `chat_id` — иначе любой в allowlisted-группе мог бы инжектить промпты. |
| **Permission relay** | Декларируем `claude/channel/permission`. Анonymously пушнувший в обход allowlist'а не получит право жать `yes` — verdict тоже гейтится по sender. |
| **Skill `tg-channel-incoming`** | Обязывает Claude показывать draft и ждать "отправляй" перед `send_message`. Запрещает реагировать на prompt-injection из тела сообщения. |
| **Hook `guard-delete`** | `revoke=true` для удаления требует явного approval даже из channel-сценария. |

### Узнать свой sender_id для allowlist

После авторизации (`claudegram-auth`) — спроси у [@userinfobot](https://t.me/userinfobot)
или вызови в активной Claude-сессии `mcp__plugin_claudegram_claudegram__get_me`.

## Roadmap

- **Outbound permission_request handler** — Claude Code шлёт `notifications/claude/channel/permission_request` когда нужен approval; форвардить юзеру в Telegram. Сейчас inbound verdict работает, outbound forward — TODO (требует регистрации custom notification_handler в Server, не тривиально через FastMCP).
- **send media** (фото/документ/голосовое) — Telethon `send_file` уже умеет, обернуть в tool.
- **pin / unpin / mute / archive / set_typing** диалогов.
- **Stories** API (Telegram Stories через MTProto).
- **Monitor** на бэкап Saved Messages (`monitors/monitors.json`).
- **Submit** в Anthropic [official marketplace](https://claude.ai/settings/plugins/submit) — channel-плагины проходят security review, после чего работают без `--dangerously-load-development-channels`.
- **Marketplace на GitHub** + git-теги `claudegram--v0.1.0` для version-constraints.
