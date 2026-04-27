"""Forums — темы (topics) в супергруппах с включённым forum-режимом."""

from __future__ import annotations

import secrets
from typing import Any

from telethon.tl.functions.messages import (
    CreateForumTopicRequest,
    DeleteTopicHistoryRequest,
    EditForumTopicRequest,
    GetForumTopicsByIDRequest,
    GetForumTopicsRequest,
    ReorderPinnedForumTopicsRequest,
    UpdatePinnedForumTopicRequest,
)

from server.client import get_client
from server.tools._common import DESTRUCTIVE, NON_DESTRUCTIVE, READ_ONLY, clamp, normalize_chat


def register(mcp: Any) -> None:
    @mcp.tool(annotations=READ_ONLY)
    async def get_forum_topics(
        chat: int | str,
        limit: int = 50,
        search: str = "",
        offset_id: int = 0,
        offset_topic: int = 0,
    ) -> list[dict[str, Any]]:
        """Список тем в forum-супергруппе.

        Args:
            limit: 1-100.
            search: фильтр по названию темы.
            offset_id / offset_topic: пагинация.
        """
        client = await get_client()
        peer = await client.get_input_entity(normalize_chat(chat))
        result = await client(
            GetForumTopicsRequest(
                peer=peer,
                offset_date=None,
                offset_id=offset_id,
                offset_topic=offset_topic,
                limit=clamp(limit, 1, 100),
                q=search or None,
            )
        )
        return [
            {
                "id": t.id,
                "title": t.title,
                "icon_color": getattr(t, "icon_color", None),
                "icon_emoji_id": str(getattr(t, "icon_emoji_id", "") or ""),
                "top_message": t.top_message,
                "unread_count": t.unread_count,
                "unread_mentions_count": t.unread_mentions_count,
                "from_id": getattr(getattr(t, "from_id", None), "user_id", None),
                "closed": getattr(t, "closed", False),
                "hidden": getattr(t, "hidden", False),
                "pinned": getattr(t, "pinned", False),
            }
            for t in (result.topics or [])
        ]

    @mcp.tool(annotations=READ_ONLY)
    async def get_forum_topics_by_id(
        chat: int | str,
        topic_ids: list[int],
    ) -> list[dict[str, Any]]:
        """Получить конкретные темы по их id."""
        client = await get_client()
        peer = await client.get_input_entity(normalize_chat(chat))
        result = await client(GetForumTopicsByIDRequest(peer=peer, topics=topic_ids))
        return [
            {
                "id": t.id,
                "title": t.title,
                "top_message": t.top_message,
                "unread_count": t.unread_count,
                "closed": getattr(t, "closed", False),
                "hidden": getattr(t, "hidden", False),
            }
            for t in (result.topics or [])
        ]

    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def create_forum_topic(
        chat: int | str,
        title: str,
        icon_color: int | None = None,
        icon_emoji_id: int | None = None,
    ) -> dict[str, Any]:
        """Создать новую тему в forum-супергруппе.

        Args:
            icon_color: hex int цвета иконки (опционально, для дефолтных эмодзи).
            icon_emoji_id: id custom-emoji для иконки.
        """
        client = await get_client()
        peer = await client.get_input_entity(normalize_chat(chat))
        await client(
            CreateForumTopicRequest(
                peer=peer,
                title=title,
                icon_color=icon_color,
                icon_emoji_id=icon_emoji_id,
                random_id=secrets.randbits(63),
            )
        )
        return {"ok": True, "title": title}

    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def edit_forum_topic(
        chat: int | str,
        topic_id: int,
        title: str | None = None,
        icon_emoji_id: int | None = None,
        closed: bool | None = None,
        hidden: bool | None = None,
    ) -> dict[str, Any]:
        """Редактировать тему: переименовать, закрыть, скрыть.

        Args:
            hidden: только для General-темы (id=1) — спрятать из шапки.
        """
        client = await get_client()
        peer = await client.get_input_entity(normalize_chat(chat))
        await client(
            EditForumTopicRequest(
                peer=peer,
                topic_id=topic_id,
                title=title,
                icon_emoji_id=icon_emoji_id,
                closed=closed,
                hidden=hidden,
            )
        )
        return {"ok": True, "topic_id": topic_id}

    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def pin_forum_topic(
        chat: int | str,
        topic_id: int,
        pinned: bool = True,
    ) -> dict[str, Any]:
        """Закрепить/открепить тему в шапке."""
        client = await get_client()
        peer = await client.get_input_entity(normalize_chat(chat))
        await client(
            UpdatePinnedForumTopicRequest(
                peer=peer,
                topic_id=topic_id,
                pinned=pinned,
            )
        )
        return {"ok": True, "pinned": pinned}

    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def reorder_pinned_forum_topics(
        chat: int | str,
        topic_ids_in_order: list[int],
        force: bool = False,
    ) -> dict[str, Any]:
        """Переставить порядок закреплённых тем.

        Args:
            topic_ids_in_order: id тем в нужном порядке.
            force: True — снять pin с тем, не указанных в списке.
        """
        client = await get_client()
        peer = await client.get_input_entity(normalize_chat(chat))
        await client(
            ReorderPinnedForumTopicsRequest(peer=peer, order=topic_ids_in_order, force=force)
        )
        return {"ok": True}

    @mcp.tool(annotations=DESTRUCTIVE)
    async def delete_forum_topic(chat: int | str, topic_id: int) -> dict[str, Any]:
        """Удалить тему вместе со всеми сообщениями."""
        client = await get_client()
        peer = await client.get_input_entity(normalize_chat(chat))
        await client(DeleteTopicHistoryRequest(peer=peer, top_msg_id=topic_id))
        return {"ok": True}
