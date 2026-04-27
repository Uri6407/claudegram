# Changelog

Все значимые изменения проекта документируются в этом файле.

Формат [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
проект следует [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Git-теги в формате `claudegram--v<version>` для resolution в плагин-marketplace.

## [1.1.0] — 2026-04-26 — Deep MCP/Claude Code Integration

### Added (MCP feature coverage)
- **Lifespan + AppContext** через `@asynccontextmanager` в `server/client.py` —
  переиспользует `get_client()` singleton, нет дубль-коннекта к session.
- **Pydantic-модели** в `server/models.py`: `EntityBrief`, `MessageBrief`,
  `DialogBrief`, `HealthReport`, `ServerVersion` — structured output
  для всех 121 tools.
- **Resources**: `telegram://{me,chats,chats/archived,contacts,drafts,blocked,
  folders,stories/feed,files/recent}` (9 static).
- **Resource templates**: `chat/{id}`, `chat/{id}/history`, `chat/{id}/pinned`,
  `chat/{id}/photos`, `chat/{id}/common`, `msg/{chat}/{id}`,
  `chat/{id}/topic/{topic_id}/history` (7 templates).
- **Prompts** (7): `tg_digest`, `tg_search`, `tg_draft_reply`,
  `tg_summarize_thread`, `tg_weekly_roundup`, `tg_triage_inbox`, `tg_moderate_chat`.
- **Completion handler** в `server/completions.py` — autocomplete для
  chat / chat_id / folder / tone / emoji через Telethon dialog cache.
- **Sampling tool** `summarize_chat` через `ctx.session.create_message`.
- **Tool annotations** (MCP 2025): 121/121 размечены — 48 READ_ONLY,
  15 DESTRUCTIVE, 58 NON_DESTRUCTIVE.
- **`ctx.report_progress`** в `get_history`, `search_messages`, `get_admin_log`,
  `get_participants`, `download_media`.
- **`ctx.elicit`** для destructive: `delete_message(revoke=True)`, `kick_participant`,
  `ban_participant`, `leave_chat`, `delete_dialog` + `ctx.warning` логи.
- **`ResourceLink` в `get_history_with_links`** — гибридный возврат
  `list[TextContent | ResourceLink]` с URI на каждое сообщение.
- **`ImageContent`** в `download_profile_photo(inline=True)` — base64 inline до 1 MB.
- **`set_typing`** tool — Telethon `client.action()` для индикатора печати.
- **`send_resource_updated` + `send_resource_list_changed`** из channel listener
  при NewMessage / ChatAction.
- **`NotificationOptions(prompts_changed, resources_changed, tools_changed)`** —
  все три capability декларируем для full subscription.
- **Experimental capability `claude/channel/permission_request`** — outbound
  permission relay явно объявлен.

### Added (Claude Code feature coverage)
- **`commands/`**: `auth.md`, `health.md`, `dev.md` — slash-commands помимо skills.
- **Hooks**: `SessionEnd` (лог сессии), `PreCompact` (reminder про drafts),
  + расширенный `PreToolUse` matcher (11 destructive + 7 confirm-required).
- **Plugin manifest 2.0**: `displayName`, `homepage`, `repository`, `bugs`,
  `permissions` (35 read-only tools pre-approved → юзер не апрувит каждый раз).
- **`commands/dev.md`** + console-script `claudegram-dev` →
  `uv run claudegram-dev` поднимает MCP Inspector.

### Changed
- **Версия** `1.0.0` → `1.1.0`.
- `pyproject.toml description` обновлён под новые числа.
- `permission_relay.py` / `main.py`: убран Python-2-стиль `except A, B:` →
  `except (A, B):`.
- Tests: проверка `≥120 tools`, `≥9 resources`, `≥6 templates`, `≥7 prompts`,
  `outputSchema present everywhere`, annotation present.

### Tools count
- **121** (с +3 за итерацию: `get_history_with_links`, `set_typing`, `summarize_chat`).

## [1.0.0] — 2026-04-26 — Production Release 🎉

### Added (production hardening)
- **`server/middleware.py`** с `safe_tool` декоратором: graceful обработка
  `FloodWaitError` (возвращает `retry_after`), `RPCError` (с code/message),
  любых Exception. Тула возвращает dict вместо raise.
- **Latency logging**: каждый tool-call логирует `tool=<name> status=<ok|error> latency_ms=<N>` через стандартный `logging`.
- **Sensitive sanitization**: `middleware.sanitize()` маскирует `api_hash`,
  `phone`, `2fa_password`, `session` ключи в логах.
- **Health probe** в `advanced/health.py` — 2 tools:
  - `health_check` — `connected` / `authorized` / `self_id` / `telegram_latency_ms`
  - `get_server_version` — версии claudegram/telethon/mcp/python
- **Расширенные hooks** в `hooks/hooks.json`:
  - `guard-destructive` для 11 операций: ban, kick, terminate_authorization,
    leave_chat, delete_dialog, delete_forum_topic, delete_stories, delete_scheduled,
    demote_admin, block_user (+ delete_message с revoke)
  - `guard-confirm` для 7 операций: invoke_raw, set_privacy, update_username,
    edit_chat_{title,about,photo}, toggle_forum_mode
- **`SECURITY.md`** — threat model, secrets handling, hook coverage, рекомендации
- **`CONTRIBUTING.md`** — dev environment, quality gates, конвенции для
  добавления tools/доменов, release process

### Tools added (24 → итого 118)
- **identity/privacy**: `get_privacy`, `set_privacy` (11 keys × 5 visibility levels)
- **identity/security**: `get_password_info`
- **messaging/drafts**: `save_draft`, `clear_draft`
- **messaging/scheduled**: `get_scheduled_messages`, `send_scheduled_now`, `delete_scheduled`
- **media/voice**: `send_voice`, `send_video_note`, `transcribe_audio`
- **content/payments**: `get_stars_balance`, `get_stars_transactions`, `get_premium_promo`
- **dialogs/folders_custom**: `get_dialog_filters`, `create_dialog_filter`, `delete_dialog_filter`
- **interactions/bots** (новый домен): `inline_query`, `start_bot`, `click_inline_button`
- **advanced/help_api**: `get_telegram_config`, `get_app_config`, `get_nearest_dc`, `get_countries_list`
- **advanced/health**: `health_check`, `get_server_version`

### Changed
- **Версия** `0.2.0` → `1.0.0` (production-ready)
- `pyproject.toml description` обновлён: 118 tools / 9 доменов
- `plugin.json description` обновлён аналогично

### Architecture
- **9 доменов** (с +1 новый `interactions/`): identity, peers, messaging, dialogs, chats, media, content, **interactions**, advanced
- **24 подмодуля** (с +9 новых)
- **118 tools** (с +26 за итерацию)

## [0.2.0] — 2026-04-26

### Changed (architecture)
- **Реорганизация** `server/tools/` из 11 плоских модулей в **8 доменов с подпакетами**:
  `identity/`, `peers/`, `messaging/`, `dialogs/`, `chats/`, `media/`, `content/`, `advanced/`.
- **10+ misplaced tools** переехали в семантически правильные модули:
  - `get_chat_info`, `resolve_username`, `search_global`, `get_top_peers` → `peers/lookup`
  - `block_user`/`unblock_user` → `peers/contacts` (MTProto namespace)
  - `download_profile_photo`, `get_profile_photos` → `peers/users`
  - `mark_read`, `delete_dialog` → `dialogs/notify`
  - `send_dice`, `send_location`, `send_contact` → `media/attachments`
  - `pin_message`/`unpin_message` → `messaging/pins`
  - `react_message` → `messaging/reactions`
  - `toggle_forum_mode` → `chats/settings` (был дубликат, удалён)
- `_to_jsonable` вынесен в `tools/_common.to_jsonable` (избежание cross-domain зависимости).
- `media/files.py` использует типизированный `ParseMode` Literal вместо сырого str.
- `tests/test_main_registration.py` `expected` расширен: 60+ tools против 38 (было).

### Planned
- Multi-account support (несколько `*.session` файлов)
- Schedule-интеграция с `/schedule` skill
- AI-augmented features (`summarize_chat`, `extract_action_items`)
- Web UI для конфигурации (`uv run claudegram-config`)
- Encryption-at-rest для session файлов

## [0.2.0] — 2026-04-26

### Added
- **71 MCP tools** (с 12) разбитых по 11 категориям в `server/tools/`:
  - `account.py` (5): `get_me`, `get_authorizations`, `terminate_authorization`, `update_profile`, `set_online`
  - `messages.py` (11): + `pin_message`, `unpin_message`, `react_message`, `send_dice`, расширенные `send_message`/`get_history`/`search_messages`
  - `dialogs.py` (7): + `get_drafts`, `archive_dialog`, `unarchive_dialog`, `mute_dialog`, `unmute_dialog`
  - `users.py` (7): + `get_participants`, `get_profile_photos`, `block_user`, `unblock_user`, `get_common_chats`
  - `chats.py` (12): `create_group`, `create_channel`, `edit_chat_title/about`, `join_chat`, `leave_chat`, `kick/ban/unban`, `promote_admin`, `demote_admin`, `get_admin_log`, `get_stats`
  - `media.py` (7): + `download_profile_photo`, `send_file`, `send_album`, `send_location`, `send_contact`, `get_media_info`, `forward_message`
  - `contacts.py` (4): `get_contacts`, `add_contact`, `delete_contact`, `search_global`
  - `polls.py` (2): `send_poll`, `vote_poll`
  - `stickers.py` (2): `get_installed_stickers`, `get_sticker_set`
  - `forums.py` (5): `get_forum_topics`, `create_forum_topic`, `edit_forum_topic`, `pin_forum_topic`, `delete_forum_topic`
  - `stories.py` (6): `get_all_stories`, `get_peer_stories`, `get_pinned_stories`, `get_stories_by_id`, `mark_stories_read`, `delete_stories`
  - `raw_api.py` (2): `invoke_raw`, `get_input_peer` — escape hatch для **любого** MTProto-метода
- **Channel mode** (research preview Claude Code v2.1.80+):
  - Push входящих Telegram-сообщений в активную сессию как `<channel source="claudegram" event_type="...">` теги
  - 4 типа событий: `message`, `message_edited`, `message_deleted`, `chat_action`
  - Sender allowlist через `tg_allowed_sender_ids` (gate by `event.sender_id` для безопасности групп)
  - Outbound permission relay: forward `permission_request` от Claude Code в Telegram + parse `yes/no <id>` verdict
  - `enable_channel_mode` opt-in через userConfig
- **Plugin infrastructure**:
  - `.claude-plugin/marketplace.json` — single-plugin local marketplace
  - `.claude-plugin/plugin.json` с `userConfig` (sensitive → keychain)
  - `.mcp.json` с `${user_config.*}` substitution + `${CLAUDE_PLUGIN_DATA}` для session
  - `hooks/hooks.json` — `SessionStart` auth-check, `PreToolUse` гейт на `delete_message(revoke=true)`
  - `bin/claudegram-auth` — обёртка одноразового логина
  - 7 skills (5 user-invokable + 2 background auto-active)
- **Dev infrastructure**:
  - `pyproject.toml` с `[project.scripts]` (`claudegram`, `claudegram-auth`)
  - Ruff lint + format конфиг
  - Mypy strict-leaning конфиг
  - Pytest с asyncio-mode=auto
  - 90 unit-тестов с покрытием 49%+
  - GitHub Actions CI: lint + format + mypy + tests + manifest validation
  - GitHub Actions release workflow на git tag `claudegram--v*`
  - `CHANGELOG.md`
- **Logging**: стандартный `logging` с `CLAUDEGRAM_LOG_LEVEL` env var

### Changed
- Версия `0.1.0` → `0.2.0`
- Архитектура: монолитный `main.py` → модульная `server/tools/{account,messages,dialogs,users,chats,media,contacts,polls,stickers,forums,stories,raw_api}.py` с `register_all(mcp)` dispatcher'ом
- `delete_message` дефолт `revoke=True` → `revoke=False` (безопаснее)
- `download_media` дефолт `/tmp` → `tempfile.gettempdir()` (кросс-платформа)
- `send_message`/`edit_message` получили `parse_mode: 'markdown'|'html'|'none'`
- `get_history` получил `from_user`, `min_id`, `reverse` параметры
- `mark_read` получил `clear_mentions`
- `dialog_brief` дополнен `peer_id` (для семантической ясности)
- `print(file=sys.stderr)` → `logger.info/warning/exception`
- README расширен секцией про channel mode

### Fixed
- B1: race condition между listener'ом и MCP initialize handshake → `await asyncio.sleep(2)` warm-up
- B2: silent failure listener'а при no-auth → pre-flight `get_client()` + понятное warning в stderr
- B3: bash-синтаксис `${limit:-30}` в skill `tg-history` → естественный язык
- B4: README врал про `claudegram-auth` в обычном PATH (только Bash tool в Claude Code)
- I1: пустой content для медиа без подписи → `_media_label()` fallback `[photo]`/`[voice message]`/etc
- `forward_message` upon None-return на service messages → гард + фильтр

### Security
- Sensitive `userConfig` поля (api_hash, phone, 2FA) → системный keychain, не `settings.json`
- Channel sender gate по `sender_id`, не `chat_id` (защита от prompt injection в групповых чатах)
- Permission relay декларируется только при наличии sender allowlist'а
- Skill `tg-channel-incoming` обязывает Claude игнорировать prompt-injection из тела сообщений

## [0.1.0] — 2026-04-26

### Added
- Минимальный MCP-сервер на FastMCP + Telethon с 12 базовыми tools
- Plugin manifest, marketplace.json, .mcp.json
- README с инструкциями установки
