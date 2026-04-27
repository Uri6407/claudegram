"""Create — создание групп и каналов."""

from __future__ import annotations

from typing import Any

from telethon.tl.functions.channels import CreateChannelRequest
from telethon.tl.functions.messages import CreateChatRequest

from server.client import get_client
from server.formatters import entity_brief
from server.tools._common import NON_DESTRUCTIVE, normalize_chat


def register(mcp: Any) -> None:
    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def create_group(
        title: str,
        users: list[int | str],
    ) -> dict[str, Any]:
        """Создать обычную группу с указанными участниками."""
        client = await get_client()
        peers = [await client.get_input_entity(normalize_chat(u)) for u in users]
        result = await client(CreateChatRequest(users=peers, title=title))
        chats = getattr(result, "chats", []) or []
        return {"ok": True, "chats": [entity_brief(c) for c in chats]}

    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def create_channel(
        title: str,
        about: str = "",
        broadcast: bool = False,
        megagroup: bool = True,
    ) -> dict[str, Any]:
        """Создать канал (broadcast=True) или супергруппу (megagroup=True).

        Args:
            broadcast: True — broadcast-канал (только админы пишут).
            megagroup: True — супергруппа.
        """
        client = await get_client()
        result = await client(
            CreateChannelRequest(
                title=title,
                about=about,
                broadcast=broadcast,
                megagroup=megagroup,
            )
        )
        chats = getattr(result, "chats", []) or []
        return {"ok": True, "chats": [entity_brief(c) for c in chats]}
