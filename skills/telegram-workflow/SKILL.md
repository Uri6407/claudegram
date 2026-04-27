---
name: telegram-workflow
description: Правила и контекст работы с личным Telegram-аккаунтом пользователя через MCP-сервер claudegram. Загружается, когда пользователь просит читать чаты, искать сообщения, отвечать кому-то в Telegram, делать сводку непрочитанных, управлять диалогами, создавать чаты/каналы, модерировать группу, скачивать медиа, управлять контактами, или вообще обращается к Telegram-аккаунту.
when_to_use: "Активируется на: 'что у меня в Telegram', 'найди в чатах', 'напиши/отправь в тг', 'удали сообщение', 'забань', 'создай группу/канал', 'переименуй чат', 'кикни', 'admin', 'статистика канала', 'опрос', 'голосуй', 'скачай вложение', 'контакты'."
disable-user-invocation: true
---

# Работа с Telegram через claudegram

MCP-сервер `claudegram` даёт доступ к **личному аккаунту** пользователя
через MTProto (не бот). 58 типизированных tools, разбитых по категориям.

## Базовые принципы безопасности

1. **Никогда не отправляй сообщения без явного подтверждения.** Намерение «составить черновик» ≠ намерение отправить. Покажи проект текста и жди слов вроде «отправь / шли / да».
2. **`delete_message(revoke=True)` — необратимо.** Дефолт `False` (только у себя). Hook `guard-delete` требует подтверждения. Не передавай `True` без явного запроса юзера.
3. **Не помечай прочитанным автоматически.** `mark_read` — только по явной просьбе. Иначе пользователь потеряет визуальные индикаторы непрочитанного.
4. **Деструктивные операции на чатах**: `kick_participant`, `ban_participant`, `delete_dialog`, `leave_chat`, `terminate_authorization`, `block_user` — **всегда** показывай action + entity и жди "да".
5. **Markdown в `send_message`/`edit_message`.** Если в тексте есть `*`, `_`, `[`, `]`, `~`, `\``, и это **не** разметка — передай `parse_mode="none"`, иначе Telegram упадёт с ParseMode-error.
6. **Сессия — это пароль.** Файл `*.session` в `${CLAUDE_PLUGIN_DATA}` даёт полный доступ к аккаунту. Никогда не предлагай пересылать его, копировать в чат, коммитить.
7. **`invoke_raw`** — крайний инструмент. Используй только если нет high-level tool. Можешь случайно изменить состояние аккаунта или нарваться на flood-wait.

## Каталог инструментов

Все имена под префиксом `mcp__plugin_claudegram_claudegram__`. Сгруппированы по модулям.

### Identity / Account (`server/tools/identity/account.py`)
| Tool | Назначение |
|---|---|
| `get_me` | Кто я залогинен |
| `get_authorizations` | Список активных сессий аккаунта (другие устройства) |
| `terminate_authorization` | Завершить чужую сессию (по `hash`) |
| `update_profile` | Изменить имя/фамилию/био |
| `set_online` | Online/offline статус |

### Messaging (`server/tools/messaging/{messages,history,pins,reactions}.py`)
| Tool | Назначение |
|---|---|
| `send_message` | Отправить (parse_mode, reply_to, silent, link_preview, schedule_unix) |
| `edit_message` | Отредактировать своё |
| `delete_message` | Удалить (revoke=False default) |
| `forward_message` | Переслать (silent, drop_author) |
| `get_history` | Последние N (offset_id, min_id, from_user, reverse) |
| `search_messages` | Поиск по тексту (chat, from_user) |
| `mark_read` | Прочитано (max_id, clear_mentions) |
| `pin_message` | Закрепить (notify, pm_oneside) |
| `unpin_message` | Открепить одно или все |
| `react_message` | Поставить эмодзи-реакцию (`""` чтобы снять) |
| `send_dice` | 🎲/🎯/🏀/⚽/🎰/🎳 |

### Dialogs (`server/tools/dialogs/{list_,folders,notify}.py`)
| Tool | Назначение |
|---|---|
| `list_chats` | Список диалогов (archived, only_unread, ignore_pinned) |
| `get_drafts` | Несохранённые черновики |
| `archive_dialog` / `unarchive_dialog` | Архив |
| `delete_dialog` | Покинуть/удалить |
| `mute_dialog` / `unmute_dialog` | Уведомления |

### Peers (`server/tools/peers/{lookup,users,contacts}.py`)
| Tool | Назначение |
|---|---|
| `get_chat_info` | Метаданные entity |
| `resolve_username` | `@username` → entity + id |
| `get_participants` | Участники (search, filter_admin/kicked/banned) |
| `get_profile_photos` | Метаданные аватарок |
| `block_user` / `unblock_user` | (Раз)блокировать |
| `get_common_chats` | Общие чаты с юзером |

### Chats (`server/tools/chats/{create,settings,members,invites,admin}.py`)
| Tool | Назначение |
|---|---|
| `create_group` | Обычная группа с участниками |
| `create_channel` | Канал (broadcast=True) или супергруппа (megagroup=True) |
| `edit_chat_title` | Переименовать |
| `edit_chat_about` | Описание |
| `join_chat` / `leave_chat` | Войти / выйти |
| `kick_participant` | Кик (можно вернуться) |
| `ban_participant` / `unban_participant` | Бан навсегда |
| `promote_admin` (с правами) / `demote_admin` | Админ |
| `get_admin_log` | Журнал действий админов |
| `get_stats` | Статистика канала (только админу) |

### Media (`server/tools/media/{files,download,attachments,stickers}.py`)
| Tool | Назначение |
|---|---|
| `download_media` | Скачать вложение из сообщения |
| `download_profile_photo` | Скачать аватарку |
| `send_file` | Отправить файл (force_document, voice_note, video_note) |
| `send_album` | 2-10 фото/видео одной группой |
| `send_location` | Координаты (live_period для live-локации) |
| `send_contact` | Визитка |
| `get_media_info` | Метаданные медиа без скачивания |

### Contacts (`server/tools/peers/contacts.py`)
| Tool | Назначение |
|---|---|
| `get_contacts` | Все контакты |
| `add_contact` | Добавить (с phone_privacy_exception) |
| `delete_contact` | Удалить |
| `search_global` | Глобальный поиск юзеров/чатов/каналов |

### Content / Polls (`server/tools/content/polls.py`)
| Tool | Назначение |
|---|---|
| `send_poll` | Опрос (anonymous, multiple_choice, quiz + correct_option_index) |
| `vote_poll` | Проголосовать (option_indices) |

### Advanced / Raw API (`server/tools/advanced/raw.py`)
| Tool | Назначение |
|---|---|
| `invoke_raw` | Вызов любого MTProto-метода через `telethon.tl.functions.<...>` |
| `get_input_peer` | Получить InputPeer для использования в `invoke_raw` |

## Идентификация чатов

- Параметр `chat` принимает: целочисленный `id` (напр. `-1001234567890`),
  `@username`, или просто `username` без `@`.
- Если пользователь говорит «напиши Пете» — сначала найди Петю через
  `search_global` или `resolve_username`. Не угадывай id.
- Перед действиями над незнакомым чатом покажи `get_chat_info` —
  пусть пользователь подтвердит, что это правильный собеседник.
- В групповых чатах для `forward_message`/`pin_message` используй полный
  signed id (`-100<chan_id>` для супергрупп). `dialog_brief.peer_id`
  возвращает уже правильный формат.

## Типичные сценарии

**«Что пропустил?»** → `list_chats(only_unread=true)` → для каждого
`get_history(limit=unread_count)` → сгруппированная сводка. Не зови `mark_read`.

**«Найди про X»** → если упомянут чат — `resolve_username` → `search_messages(query, chat)`. Иначе глобальный поиск или `search_global`.

**«Ответь Y кому-то»** → найди чат → составь черновик → покажи + получатель → жди «отправляй» → `send_message(reply_to=...)` если ответ на конкретное сообщение.

**«Скачай это видео»** → `get_history` найди message_id → `get_media_info` для проверки → `download_media(chat, message_id, download_dir)`.

**«Создай группу с Васей и Петей»** → `resolve_username` для каждого → собери список id → `create_group(title, users)` → жди подтверждения title'а перед созданием.

**«Кто админы канала?»** → `get_participants(chat, filter_admin=True)`.

**«Замьють чат до утра»** → `mute_dialog(chat, mute_until_unix=<завтра 9:00 UTC>)`. Перед — спроси подтверждение времени.

**«Переименуй чат в …»** → `get_chat_info` показать текущее название → `edit_chat_title(chat, new_title)` после подтверждения.

**«Лайкни последнее»** → `get_history(chat, limit=1)` → `react_message(chat, message_id, emoji='👍')`.

**«Отправь голосовое»** → `send_file(chat, '/path/to/voice.ogg', voice_note=True)`. Если файл не .ogg — сначала convert через ffmpeg (предложи команду юзеру).

**«Сделай опрос: «Куда обедать?» с вариантами «Sushi/Pizza/Burger»»** → `send_poll(chat, question, options, anonymous=True)` после подтверждения.

**«Что в админ-логе?»** → `get_admin_log(chat, limit=50)`.

## Пагинация и лимиты

- `get_history` / `search_messages` / `get_participants` / `get_admin_log`: `limit` обычно 1-200. Для больших объёмов — несколько вызовов с `offset_id` (для сообщений) или продвигайся по страницам.
- Не запрашивай больше, чем нужно — каждый вызов = запрос к Telegram под лимитом FloodWait.

## Ошибки

- **«Telegram-сессия не авторизована»** → `claudegram-auth` (через `! claudegram-auth` в Claude или `uv run claudegram-auth` в shell).
- **`FloodWaitError: A wait of N seconds is required`** → подожди ровно N секунд (Telethon бросит `FloodWaitError`), не ретрай в цикле.
- **`UsernameNotOccupiedError`** → нет такого `@username`. Перепроверь.
- **`ChatAdminRequiredError`** → нужны права админа для операции (`get_stats`, `kick`, `promote` и т.п.).
- **`UserNotParticipantError`** → юзер не в этом чате (для `kick`/`promote`).
- **`MessageNotModifiedError`** при `edit_message` → новый текст идентичен старому.

## Channel-режим

Если плагин запущен с `enable_channel_mode=1` и `--channels`, входящие
сообщения от allowlist'ed юзеров приходят в сессию как `<channel source="claudegram">`
теги. См. отдельный skill `tg-channel-incoming` для правил их обработки.
