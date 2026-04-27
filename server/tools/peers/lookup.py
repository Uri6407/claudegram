"""Lookup — поиск и resolve любых сущностей (universal entity discovery)."""

from __future__ import annotations

from typing import Any

from telethon.tl.functions.contacts import (
    GetTopPeersRequest,
    SearchRequest,
)

from server.client import get_client
from server.formatters import entity_brief
from server.models import EntityBrief
from server.tools._common import READ_ONLY, clamp, normalize_chat, to_jsonable


def register(mcp: Any) -> None:
    @mcp.tool(annotations=READ_ONLY)
    async def get_chat_info(chat: int | str) -> EntityBrief:
        """Подробная инфа о любом entity: пользователе/чате/канале/боте."""
        client = await get_client()
        entity = await client.get_entity(normalize_chat(chat))
        return EntityBrief(**entity_brief(entity))

    @mcp.tool(annotations=READ_ONLY)
    async def resolve_username(username: str) -> EntityBrief:
        """Найти entity по @username и вернуть инфу + id."""
        client = await get_client()
        entity = await client.get_entity(username)
        return EntityBrief(**entity_brief(entity))

    @mcp.tool(annotations=READ_ONLY)
    async def search_global(query: str, limit: int = 20) -> list[dict[str, Any]]:
        """Глобальный поиск по юзерам/чатам/каналам по имени или @username."""
        client = await get_client()
        result = await client(SearchRequest(q=query, limit=clamp(limit, 1, 100)))
        out: list[dict[str, Any]] = []
        for u in getattr(result, "users", []) or []:
            out.append({**entity_brief(u), "match_kind": "user"})
        for c in getattr(result, "chats", []) or []:
            out.append({**entity_brief(c), "match_kind": "chat"})
        return out

    @mcp.tool(annotations=READ_ONLY)
    async def get_top_peers(
        category: str = "correspondents",
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Топ часто-используемых контактов в указанной категории.

        Args:
            category: 'correspondents' (личные чаты), 'bots_pm', 'bots_inline',
                'phone_calls', 'forward_users', 'forward_chats', 'groups', 'channels',
                'bots_app'.
        """
        flags = {
            "correspondents",
            "bots_pm",
            "bots_inline",
            "phone_calls",
            "forward_users",
            "forward_chats",
            "groups",
            "channels",
            "bots_app",
        }
        if category not in flags:
            return [{"ok": False, "error": f"unknown category: {category}"}]
        client = await get_client()
        kwargs: dict[str, Any] = {"offset": 0, "limit": clamp(limit, 1, 100), "hash": 0}
        kwargs[category] = True
        result = await client(GetTopPeersRequest(**kwargs))
        return [entity_brief(u) for u in getattr(result, "users", [])] + [
            entity_brief(c) for c in getattr(result, "chats", [])
        ]

    @mcp.tool(annotations=READ_ONLY)
    async def get_input_peer(chat: int | str) -> dict[str, Any]:
        """Получить InputPeer для чата (нужен для raw API вызовов).

        Возвращает dict с _, который можно положить в kwargs_json для invoke_raw.
        """
        client = await get_client()
        peer = await client.get_input_entity(normalize_chat(chat))
        return to_jsonable(peer)
