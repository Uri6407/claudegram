"""Сериализация Telethon-объектов в Pydantic-модели + JSON-friendly dict.

Возвращаем `dict[str, Any]`, чтобы не ломать существующие tools и тесты.
Pydantic-модели в `server/models.py` используются для structured output
в избранных tools и для документации.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from telethon.tl.custom.dialog import Dialog
from telethon.tl.custom.message import Message
from telethon.tl.types import Channel, Chat, User

from server.models import DialogBrief, DialogCompact, EntityBrief, MessageBrief


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


def entity_brief(entity: Any) -> dict[str, Any]:
    if isinstance(entity, User):
        return EntityBrief(
            type="user",
            id=entity.id,
            username=entity.username,
            first_name=entity.first_name,
            last_name=entity.last_name,
            phone=entity.phone,
            is_bot=entity.bot,
            is_self=getattr(entity, "is_self", False),
        ).model_dump(exclude_none=False)
    if isinstance(entity, Channel):
        return EntityBrief(
            type="channel" if entity.broadcast else "supergroup",
            id=entity.id,
            title=entity.title,
            username=entity.username,
            participants_count=getattr(entity, "participants_count", None),
        ).model_dump(exclude_none=False)
    if isinstance(entity, Chat):
        return EntityBrief(
            type="group",
            id=entity.id,
            title=entity.title,
            participants_count=getattr(entity, "participants_count", None),
        ).model_dump(exclude_none=False)
    return EntityBrief(type="unknown", id=getattr(entity, "id", None)).model_dump(
        exclude_none=False
    )


def dialog_brief(dialog: Dialog) -> dict[str, Any]:
    last = dialog.message
    return DialogBrief(
        id=dialog.id,
        peer_id=dialog.id,
        name=dialog.name,
        unread_count=dialog.unread_count,
        is_pinned=dialog.pinned,
        is_archived=getattr(dialog, "archived", False),
        entity=EntityBrief(**entity_brief(dialog.entity)),
        last_message=MessageBrief(**message_brief(last)) if last else None,
    ).model_dump(exclude_none=False)


def message_brief(msg: Message) -> dict[str, Any]:
    media_type: str | None = None
    if msg.photo:
        media_type = "photo"
    elif msg.video:
        media_type = "video"
    elif msg.voice:
        media_type = "voice"
    elif msg.audio:
        media_type = "audio"
    elif msg.document:
        media_type = "document"
    elif msg.sticker:
        media_type = "sticker"

    # Service-message action — для сервисных событий (joined, left, photo
    # changed, phone call, history clear, etc). Telethon кладёт это в msg.action
    # для MessageService; для обычных Message — None.
    action_type: str | None = None
    raw_action = getattr(msg, "action", None)
    if raw_action is not None:
        action_type = type(raw_action).__name__
    # Если text пустой и нет media, но есть action — текст-описание
    fallback_text = msg.message or ""
    if not fallback_text and action_type:
        fallback_text = f"[service: {action_type}]"

    return MessageBrief(
        id=msg.id,
        date=_iso(msg.date),
        text=fallback_text,
        sender_id=msg.sender_id,
        chat_id=msg.chat_id,
        reply_to_msg_id=msg.reply_to_msg_id,
        is_outgoing=msg.out,
        edited=_iso(msg.edit_date),
        views=getattr(msg, "views", None),
        forwards=getattr(msg, "forwards", None),
        media_type=media_type,
        has_media=bool(msg.media),
        action=action_type,
        silent=getattr(msg, "silent", None),
        pinned_in_chat=getattr(msg, "pinned", None),
        mentioned=getattr(msg, "mentioned", None),
    ).model_dump(exclude_none=False)


def dialog_compact(dialog: Dialog) -> dict[str, Any]:
    """Облегчённая форма для list-операций — 85% меньше payload.

    Не возвращает last_message, raw entity и full message_brief.
    """
    e = dialog.entity
    if isinstance(e, User):
        kind = "user"
        username = e.username
        is_bot = bool(e.bot)
        participants = None
    elif isinstance(e, Channel):
        kind = "channel" if e.broadcast else "supergroup"
        username = e.username
        is_bot = False
        participants = getattr(e, "participants_count", None)
    elif isinstance(e, Chat):
        kind = "group"
        username = None
        is_bot = False
        participants = getattr(e, "participants_count", None)
    else:
        kind = "unknown"
        username = None
        is_bot = False
        participants = None

    return DialogCompact(
        id=dialog.id,
        name=dialog.name or "",
        type=kind,
        username=username,
        is_pinned=dialog.pinned,
        is_archived=getattr(dialog, "archived", False),
        is_bot=is_bot,
        unread_count=dialog.unread_count,
        participants_count=participants,
    ).model_dump(exclude_none=False)
