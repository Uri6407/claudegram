"""Folders — архив, pin диалога."""

from __future__ import annotations

from typing import Any

from server.client import get_client
from server.tools._common import NON_DESTRUCTIVE, normalize_chat


def register(mcp: Any) -> None:
    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def archive_dialog(chat: int | str) -> dict[str, Any]:
        """Переместить диалог в архив (folder=1)."""
        client = await get_client()
        await client.edit_folder(normalize_chat(chat), folder=1)
        return {"ok": True, "folder": 1}

    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def unarchive_dialog(chat: int | str) -> dict[str, Any]:
        """Вернуть диалог из архива в основной список (folder=0)."""
        client = await get_client()
        await client.edit_folder(normalize_chat(chat), folder=0)
        return {"ok": True, "folder": 0}

    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def pin_dialog(chat: int | str, pinned: bool = True) -> dict[str, Any]:
        """Закрепить/открепить диалог в шапке списка."""
        from telethon.tl.functions.messages import ToggleDialogPinRequest
        from telethon.tl.types import InputDialogPeer

        client = await get_client()
        peer = await client.get_input_entity(normalize_chat(chat))
        await client(ToggleDialogPinRequest(peer=InputDialogPeer(peer=peer), pinned=pinned))
        return {"ok": True, "pinned": pinned}
