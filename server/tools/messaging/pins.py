"""Pins — закрепление/открепление сообщений в чате."""

from __future__ import annotations

from typing import Any

from telethon.tl.functions.messages import UnpinAllMessagesRequest

from server.client import get_client
from server.tools._common import NON_DESTRUCTIVE, normalize_chat


def register(mcp: Any) -> None:
    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def pin_message(
        chat: int | str,
        message_id: int,
        notify: bool = True,
        pm_oneside: bool = False,
    ) -> dict[str, Any]:
        """Закрепить сообщение в чате.

        Args:
            notify: True — отправить уведомление участникам о новом pin.
            pm_oneside: только в PM — закрепить только у себя, не у собеседника.
        """
        client = await get_client()
        await client.pin_message(
            normalize_chat(chat), message_id, notify=notify, pm_oneside=pm_oneside
        )
        return {"ok": True, "pinned_id": message_id}

    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def unpin_message(
        chat: int | str,
        message_id: int | None = None,
    ) -> dict[str, Any]:
        """Открепить одно сообщение или все pinned в чате.

        Args:
            message_id: если задан — открепить конкретное; None — открепить все.
        """
        client = await get_client()
        if message_id is None:
            await client(UnpinAllMessagesRequest(peer=normalize_chat(chat)))
            return {"ok": True, "unpinned": "all"}
        await client.unpin_message(normalize_chat(chat), message_id)
        return {"ok": True, "unpinned_id": message_id}
