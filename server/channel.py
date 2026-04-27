"""Channel-режим для Claudegram.

Реализует контракт `claude/channel` (см. docs/en/channels-reference):
- объявляет experimental-capability при init MCP-сессии
- слушает Telegram events: NewMessage / MessageEdited / MessageDeleted / ChatAction
- пушит каждое в активную Claude-сессию как
  `notifications/claude/channel` (превращается в `<channel source="claudegram" ...>` тег)
  с meta.event_type для различения
- парсит ответные сообщения вида `yes <id>` / `no <id>` и шлёт
  `notifications/claude/channel/permission` верд­икт (permission relay)

Sender allowlist обязателен: пушим только от ID, перечисленных в
`tg_allowed_sender_ids` userConfig. В групповых чатах гейтим по
`event.sender_id`, не `chat_id`, чтобы участник allowlisted-группы не мог
инжектить промпты от чужого имени.

Активируется через env `CLAUDEGRAM_CHANNEL_MODE=1` (выставляется в .mcp.json
для plugin-режима). В standalone — выключено по умолчанию.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
from typing import Any

from mcp.shared.message import SessionMessage
from mcp.types import JSONRPCMessage, JSONRPCNotification
from telethon import events

from server.client import get_client

logger = logging.getLogger("claudegram.channel")

PERMISSION_RE = re.compile(r"^\s*(y|yes|n|no)\s+([a-km-z]{5})\s*$", re.IGNORECASE)


def parse_allowed_ids(raw: str | None) -> set[int]:
    """Распарсить allowlist из CSV-строки в set int'ов."""
    if not raw:
        return set()
    out: set[int] = set()
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if chunk.lstrip("-").isdigit():
            out.add(int(chunk))
    return out


async def _send_raw_notification(write_stream: Any, method: str, params: dict[str, Any]) -> None:
    """Запушить raw JSON-RPC notification в активную MCP-сессию."""
    notification = JSONRPCNotification(jsonrpc="2.0", method=method, params=params)
    msg = SessionMessage(message=JSONRPCMessage(notification))
    await write_stream.send(msg)


async def push_resource_updated(write_stream: Any, uri: str) -> None:
    """Сообщить клиенту, что resource по URI устарел и его надо перечитать."""
    await _send_raw_notification(
        write_stream, "notifications/resources/updated", {"uri": uri}
    )


async def push_resource_list_changed(write_stream: Any) -> None:
    """Список resources изменился (новый/удалённый чат)."""
    await _send_raw_notification(
        write_stream, "notifications/resources/list_changed", {}
    )


async def _push_event(
    write_stream: Any,
    *,
    event_type: str,
    content: str,
    extra_meta: dict[str, str] | None = None,
) -> None:
    """Универсальный push любого Telegram-события в Claude как `<channel>` тег."""
    meta: dict[str, str] = {"event_type": event_type}
    if extra_meta:
        meta.update(extra_meta)
    await _send_raw_notification(
        write_stream,
        "notifications/claude/channel",
        {"content": content, "meta": meta},
    )


async def push_message(
    write_stream: Any,
    *,
    content: str,
    chat_id: int,
    message_id: int,
    sender_id: int,
    user: str,
) -> None:
    """Push нового сообщения как `<channel source="claudegram" event_type="message" ...>текст</channel>`."""
    await _push_event(
        write_stream,
        event_type="message",
        content=content,
        extra_meta={
            "chat_id": str(chat_id),
            "message_id": str(message_id),
            "sender_id": str(sender_id),
            "user": user,
        },
    )


async def push_edit(
    write_stream: Any,
    *,
    content: str,
    chat_id: int,
    message_id: int,
    sender_id: int,
) -> None:
    """Push редакции сообщения."""
    await _push_event(
        write_stream,
        event_type="message_edited",
        content=content,
        extra_meta={
            "chat_id": str(chat_id),
            "message_id": str(message_id),
            "sender_id": str(sender_id),
        },
    )


async def push_delete(
    write_stream: Any,
    *,
    chat_id: int | None,
    deleted_ids: list[int],
) -> None:
    """Push удаления сообщения(й)."""
    await _push_event(
        write_stream,
        event_type="message_deleted",
        content=f"Удалены сообщения: {deleted_ids}",
        extra_meta={
            "chat_id": str(chat_id) if chat_id else "",
            "deleted_count": str(len(deleted_ids)),
        },
    )


async def push_chat_action(
    write_stream: Any,
    *,
    description: str,
    chat_id: int,
    action_type: str,
    user_id: int | None = None,
) -> None:
    """Push админских действий: join/leave/title-change/photo-change."""
    extra: dict[str, str] = {
        "chat_id": str(chat_id),
        "action": action_type,
    }
    if user_id is not None:
        extra["user_id"] = str(user_id)
    await _push_event(
        write_stream,
        event_type="chat_action",
        content=description,
        extra_meta=extra,
    )


async def push_permission_verdict(write_stream: Any, *, request_id: str, behavior: str) -> None:
    """Отправить permission verdict обратно в Claude Code."""
    await _send_raw_notification(
        write_stream,
        "notifications/claude/channel/permission",
        {"request_id": request_id, "behavior": behavior},
    )


def _media_label(message: Any) -> str:
    """Семантический label для сообщений без текста (только медиа)."""
    if message.photo:
        return "photo"
    if message.video:
        return "video"
    if message.voice:
        return "voice message"
    if message.audio:
        return "audio"
    if message.document:
        return "document"
    if message.sticker:
        return "sticker"
    return "attachment"


async def run_listener(write_stream: Any, allowed_ids: set[int]) -> None:
    """Подписаться на входящие Telegram-события и форвардить в Claude.

    Запускается как background-task параллельно с MCP message loop.
    Telethon-клиент уже соединён через `get_client()`.

    Слушает события:
    - NewMessage(incoming=True) — новые сообщения от allowed senders
    - MessageEdited — редакции от allowed senders
    - MessageDeleted — удаления (chat-level, не sender-gated)
    - ChatAction — join/leave/title-change

    Перед регистрацией handler'а ждём короткий warm-up, чтобы MCP-сессия
    успела пройти initialize handshake — иначе наш первый push может
    нарушить протокол (notification до initialize-response).
    """
    # Warm-up: ждём, пока Claude Code пришлёт InitializeRequest и сервер ответит.
    await asyncio.sleep(2)

    client = await get_client()
    me = await client.get_me()
    self_id = me.id

    # Если allowlist пуст — разрешить только себе (Saved Messages / тесты).
    effective_allowed = allowed_ids or {self_id}

    logger.info(
        "channel listener started; allowed sender_ids=%s",
        sorted(effective_allowed),
    )

    @client.on(events.NewMessage(incoming=True))
    async def on_new_message(event):  # type: ignore[no-untyped-def]
        try:
            sender_id = event.sender_id
            if sender_id is None or sender_id not in effective_allowed:
                return

            text = (event.message.message or "").strip()

            # Permission verdict?
            m = PERMISSION_RE.match(text)
            if m:
                behavior = "allow" if m.group(1).lower().startswith("y") else "deny"
                await push_permission_verdict(
                    write_stream,
                    request_id=m.group(2).lower(),
                    behavior=behavior,
                )
                return

            content = text or f"[{_media_label(event.message)}]"
            sender = await event.get_sender()
            user_label = (
                getattr(sender, "first_name", None)
                or getattr(sender, "title", None)
                or getattr(sender, "username", None)
                or "?"
            )
            await push_message(
                write_stream,
                content=content,
                chat_id=event.chat_id,
                message_id=event.message.id,
                sender_id=sender_id,
                user=user_label,
            )
            # Invalidate history-resource для этого чата + общий список диалогов
            await push_resource_updated(
                write_stream, f"telegram://chat/{event.chat_id}/history"
            )
            await push_resource_updated(write_stream, "telegram://chats")
        except Exception:
            logger.exception("on_new_message failed")

    @client.on(events.MessageEdited(incoming=True))
    async def on_message_edited(event):  # type: ignore[no-untyped-def]
        try:
            sender_id = event.sender_id
            if sender_id is None or sender_id not in effective_allowed:
                return
            text = (event.message.message or "").strip()
            await push_edit(
                write_stream,
                content=text or f"[{_media_label(event.message)}]",
                chat_id=event.chat_id,
                message_id=event.message.id,
                sender_id=sender_id,
            )
        except Exception:
            logger.exception("on_message_edited failed")

    @client.on(events.MessageDeleted)
    async def on_message_deleted(event):  # type: ignore[no-untyped-def]
        try:
            await push_delete(
                write_stream,
                chat_id=event.chat_id,
                deleted_ids=list(event.deleted_ids or []),
            )
        except Exception:
            logger.exception("on_message_deleted failed")

    @client.on(events.ChatAction)
    async def on_chat_action(event):  # type: ignore[no-untyped-def]
        try:
            description = "chat action"
            action_type = "unknown"
            list_changed = False
            if event.user_joined or event.user_added:
                action_type = "user_joined" if event.user_joined else "user_added"
                description = f"User joined chat {event.chat_id}"
                list_changed = True
            elif event.user_left or event.user_kicked:
                action_type = "user_left" if event.user_left else "user_kicked"
                description = f"User left/kicked from chat {event.chat_id}"
                list_changed = True
            elif event.new_title:
                action_type = "title_changed"
                description = f"Chat title changed to: {event.new_title}"
            elif event.new_photo:
                action_type = "photo_changed"
                description = "Chat photo changed"
            elif event.new_pin:
                action_type = "message_pinned"
                description = "Message pinned"
            else:
                return  # не пушим неизвестные actions

            await push_chat_action(
                write_stream,
                description=description,
                chat_id=event.chat_id,
                action_type=action_type,
                user_id=getattr(event, "user_id", None),
            )
            if list_changed:
                await push_resource_list_changed(write_stream)
        except Exception:
            logger.exception("on_chat_action failed")

    # Telethon уже коннекчен; ждём вечно. На отмену task'а корректно выйдем.
    try:
        await client.run_until_disconnected()
    except asyncio.CancelledError:
        pass


def channel_mode_enabled() -> bool:
    """True если плагин запущен с CLAUDEGRAM_CHANNEL_MODE=1."""
    return os.environ.get("CLAUDEGRAM_CHANNEL_MODE", "").strip() in ("1", "true", "True")


def get_allowed_ids() -> set[int]:
    """Прочитать allowlist из env (plugin или standalone)."""
    raw = (
        os.environ.get("TG_ALLOWED_SENDER_IDS")
        or os.environ.get("CLAUDE_PLUGIN_OPTION_TG_ALLOWED_SENDER_IDS")
        or ""
    )
    return parse_allowed_ids(raw)


CHANNEL_INSTRUCTIONS = (
    "Telegram-события приходят как "
    '<channel source="claudegram" event_type="message|message_edited|message_deleted|chat_action" ...>текст</channel>. '
    "Чтобы ответить, вызови mcp__plugin_claudegram_claudegram__send_message, "
    "передав chat_id из тега в параметр `chat`. "
    "Чтобы reply'нуть на конкретное сообщение — добавь reply_to=message_id из тега. "
    "Перед send_message всегда показывай мне финальный текст и жди явного 'отправляй'. "
    "На message_edited/message_deleted/chat_action не реагируй автоматически — это контекст."
)
