"""Scheduled — операции с отложенными сообщениями."""

from __future__ import annotations

from typing import Any

from telethon.tl.functions.messages import (
    DeleteScheduledMessagesRequest,
    GetScheduledHistoryRequest,
    SendScheduledMessagesRequest,
)

from server.client import get_client
from server.formatters import message_brief
from server.tools._common import DESTRUCTIVE, NON_DESTRUCTIVE, READ_ONLY, normalize_chat


def register(mcp: Any) -> None:
    @mcp.tool(annotations=READ_ONLY)
    async def get_scheduled_messages(chat: int | str) -> list[dict[str, Any]]:
        """Список отложенных сообщений в чате (которые ещё не отправлены)."""
        client = await get_client()
        peer = await client.get_input_entity(normalize_chat(chat))
        result = await client(GetScheduledHistoryRequest(peer=peer, hash=0))
        messages = getattr(result, "messages", []) or []
        return [message_brief(m) for m in messages]

    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def send_scheduled_now(
        chat: int | str,
        message_ids: list[int],
    ) -> list[dict[str, Any]]:
        """Принудительно отправить отложенные сообщения сейчас."""
        client = await get_client()
        peer = await client.get_input_entity(normalize_chat(chat))
        result = await client(SendScheduledMessagesRequest(peer=peer, id=message_ids))
        msgs = [u for u in getattr(result, "updates", []) if hasattr(u, "message")]
        return [{"update_type": type(u).__name__} for u in msgs]

    @mcp.tool(annotations=DESTRUCTIVE)
    async def delete_scheduled(
        chat: int | str,
        message_ids: list[int],
    ) -> dict[str, Any]:
        """Удалить отложенные сообщения (до их отправки)."""
        client = await get_client()
        peer = await client.get_input_entity(normalize_chat(chat))
        await client(DeleteScheduledMessagesRequest(peer=peer, id=message_ids))
        return {"ok": True, "deleted_ids": message_ids}
