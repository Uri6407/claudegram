"""MCP resources — read-only данные Telegram-аккаунта по URI.

Resources отличаются от tools тем, что:
- Кэшируемы клиентом (не вызывают side-effects)
- Могут отображаться в UI клиента списком/деревом
- Поддерживают URI templates для параметризации

URI namespace:
- telegram://me — мой профиль
- telegram://chats — список диалогов (top 50, без архива)
- telegram://chats/archived — архивированные
- telegram://contacts — записная книжка
- telegram://drafts — несохранённые черновики
- telegram://blocked — список заблокированных юзеров
- telegram://folders — кастомные папки/фильтры диалогов
- telegram://stories/feed — лента сторис
- telegram://files/recent — недавно отправленные файлы
- telegram://chat/{id} — get_chat_info по id или @username
- telegram://chat/{id}/history — последние 50 сообщений
- telegram://chat/{id}/pinned — закреплённые сообщения чата
- telegram://chat/{id}/photos — аватарки entity
- telegram://chat/{id}/common — общие чаты с юзером
- telegram://msg/{chat}/{id} — конкретное сообщение полностью
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from server.client import get_client
from server.formatters import dialog_brief, entity_brief, message_brief
from server.tools._common import normalize_chat

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


def _dump(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, default=str, indent=2)


def register(mcp: FastMCP) -> None:
    @mcp.resource("telegram://me", mime_type="application/json")
    async def me_resource() -> str:
        """Мой профиль (id, username, имя, premium-статус)."""
        client = await get_client()
        me = await client.get_me()
        return _dump(entity_brief(me))

    @mcp.resource("telegram://chats", mime_type="application/json")
    async def chats_resource() -> str:
        """Топ 50 диалогов (без архива)."""
        client = await get_client()
        dialogs = await client.get_dialogs(limit=50, archived=False)
        return _dump([dialog_brief(d) for d in dialogs])

    @mcp.resource("telegram://chats/archived", mime_type="application/json")
    async def chats_archived_resource() -> str:
        """Архивированные диалоги."""
        client = await get_client()
        dialogs = await client.get_dialogs(limit=100, archived=True, folder=1)
        return _dump([dialog_brief(d) for d in dialogs])

    @mcp.resource("telegram://contacts", mime_type="application/json")
    async def contacts_resource() -> str:
        """Записная книжка контактов."""
        from telethon.tl.functions.contacts import GetContactsRequest

        client = await get_client()
        result = await client(GetContactsRequest(hash=0))
        return _dump([entity_brief(u) for u in result.users])

    @mcp.resource("telegram://drafts", mime_type="application/json")
    async def drafts_resource() -> str:
        """Несохранённые черновики по всем чатам."""
        client = await get_client()
        drafts = await client.get_drafts()
        return _dump(
            [
                {
                    "entity_id": d.entity.id if d.entity else None,
                    "text": d.text or "",
                    "date": d.date.isoformat() if d.date else None,
                }
                for d in drafts
            ]
        )

    @mcp.resource("telegram://blocked", mime_type="application/json")
    async def blocked_resource() -> str:
        """Заблокированные юзеры (основной blocklist)."""
        from telethon.tl.functions.contacts import GetBlockedRequest

        client = await get_client()
        result = await client(GetBlockedRequest(offset=0, limit=100, my_stories_from=False))
        return _dump([entity_brief(u) for u in getattr(result, "users", [])])

    @mcp.resource("telegram://folders", mime_type="application/json")
    async def folders_resource() -> str:
        """Кастомные папки диалогов (DialogFilters)."""
        from telethon.tl.functions.messages import GetDialogFiltersRequest

        client = await get_client()
        result = await client(GetDialogFiltersRequest())
        filters = getattr(result, "filters", []) or result
        return _dump(
            [
                {
                    "id": getattr(f, "id", None),
                    "title": str(getattr(f, "title", "") or ""),
                    "emoticon": getattr(f, "emoticon", None),
                    "type": type(f).__name__,
                }
                for f in (filters if isinstance(filters, list) else [])
            ]
        )

    @mcp.resource("telegram://stories/feed", mime_type="application/json")
    async def stories_feed_resource() -> str:
        """Лента сторис от подписок."""
        from telethon.tl.functions.stories import GetAllStoriesRequest

        client = await get_client()
        try:
            result = await client(GetAllStoriesRequest())
        except Exception as exc:
            return _dump({"ok": False, "error": str(exc)})
        return _dump(
            {
                "count": getattr(result, "count", 0),
                "peer_stories": [
                    {
                        "peer_id": getattr(p, "peer", None).__class__.__name__
                        if getattr(p, "peer", None)
                        else None,
                        "max_read_id": getattr(p, "max_read_id", None),
                        "stories_count": len(getattr(p, "stories", []) or []),
                    }
                    for p in (getattr(result, "peer_stories", []) or [])
                ],
            }
        )

    @mcp.resource("telegram://files/recent", mime_type="application/json")
    async def recent_files_resource() -> str:
        """Недавно отправленные/полученные файлы."""
        from telethon.tl.functions.messages import GetRecentLocationsRequest

        client = await get_client()
        try:
            me = await client.get_me()
            result = await client(GetRecentLocationsRequest(peer=me, limit=50, hash=0))
        except Exception as exc:
            return _dump({"ok": False, "error": str(exc)})
        return _dump(
            [message_brief(m) for m in getattr(result, "messages", []) or []]
        )

    @mcp.resource("telegram://chat/{chat_id}", mime_type="application/json")
    async def chat_info_resource(chat_id: str) -> str:
        """Метаданные чата/юзера/канала по id или @username."""
        client = await get_client()
        entity = await client.get_entity(normalize_chat(chat_id))
        return _dump(entity_brief(entity))

    @mcp.resource("telegram://chat/{chat_id}/history", mime_type="application/json")
    async def chat_history_resource(chat_id: str) -> str:
        """Последние 50 сообщений чата (read-only снапшот)."""
        client = await get_client()
        messages = await client.get_messages(normalize_chat(chat_id), limit=50)
        return _dump([message_brief(m) for m in messages])

    @mcp.resource("telegram://chat/{chat_id}/pinned", mime_type="application/json")
    async def chat_pinned_resource(chat_id: str) -> str:
        """Закреплённые сообщения чата."""
        from telethon.tl.types import InputMessagesFilterPinned

        client = await get_client()
        messages = await client.get_messages(
            normalize_chat(chat_id), filter=InputMessagesFilterPinned(), limit=50
        )
        return _dump([message_brief(m) for m in messages])

    @mcp.resource("telegram://chat/{chat_id}/photos", mime_type="application/json")
    async def chat_photos_resource(chat_id: str) -> str:
        """Аватарки entity (метаданные, не файлы)."""
        client = await get_client()
        photos = await client.get_profile_photos(normalize_chat(chat_id), limit=20)
        return _dump(
            [
                {
                    "id": getattr(p, "id", None),
                    "date": p.date.isoformat() if getattr(p, "date", None) else None,
                    "has_video": bool(getattr(p, "video_sizes", None)),
                }
                for p in photos
            ]
        )

    @mcp.resource("telegram://chat/{chat_id}/common", mime_type="application/json")
    async def chat_common_resource(chat_id: str) -> str:
        """Общие чаты с юзером."""
        from telethon.tl.functions.messages import GetCommonChatsRequest

        client = await get_client()
        peer = await client.get_input_entity(normalize_chat(chat_id))
        result = await client(GetCommonChatsRequest(user_id=peer, max_id=0, limit=100))
        return _dump([entity_brief(c) for c in getattr(result, "chats", []) or []])

    @mcp.resource("telegram://msg/{chat_id}/{message_id}", mime_type="application/json")
    async def message_resource(chat_id: str, message_id: str) -> str:
        """Конкретное сообщение целиком."""
        client = await get_client()
        msg = await client.get_messages(normalize_chat(chat_id), ids=int(message_id))
        if msg is None:
            return _dump({"ok": False, "reason": "сообщение не найдено"})
        if isinstance(msg, list):
            msg = msg[0] if msg else None
        return _dump(message_brief(msg)) if msg else _dump({"ok": False})

    @mcp.resource(
        "telegram://chat/{chat_id}/topic/{topic_id}/history",
        mime_type="application/json",
    )
    async def topic_history_resource(chat_id: str, topic_id: str) -> str:
        """Последние 50 сообщений топика форума."""
        client = await get_client()
        messages = await client.get_messages(
            normalize_chat(chat_id), reply_to=int(topic_id), limit=50
        )
        return _dump([message_brief(m) for m in messages])
