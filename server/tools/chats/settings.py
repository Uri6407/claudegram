"""Settings — название/описание/фото чата + forum-режим."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from telethon.tl.functions.channels import (
    EditPhotoRequest,
    EditTitleRequest,
    ToggleForumRequest,
)
from telethon.tl.functions.messages import EditChatAboutRequest
from telethon.tl.types import InputChatUploadedPhoto

from server.client import get_client
from server.tools._common import NON_DESTRUCTIVE, normalize_chat


def register(mcp: Any) -> None:
    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def edit_chat_title(chat: int | str, title: str) -> dict[str, Any]:
        """Переименовать чат/канал."""
        client = await get_client()
        peer = await client.get_input_entity(normalize_chat(chat))
        await client(EditTitleRequest(channel=peer, title=title))
        return {"ok": True, "title": title}

    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def edit_chat_about(chat: int | str, about: str) -> dict[str, Any]:
        """Установить описание чата (about/bio)."""
        client = await get_client()
        await client(EditChatAboutRequest(peer=normalize_chat(chat), about=about))
        return {"ok": True, "about": about}

    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def edit_chat_photo(chat: int | str, file_path: str) -> dict[str, Any]:
        """Установить аватарку чата/канала из файла."""
        client = await get_client()
        path = Path(file_path).expanduser().resolve()
        if not path.exists():
            return {"ok": False, "reason": f"Файл не найден: {path}"}
        uploaded = await client.upload_file(str(path))
        peer = await client.get_input_entity(normalize_chat(chat))
        await client(EditPhotoRequest(channel=peer, photo=InputChatUploadedPhoto(file=uploaded)))
        return {"ok": True}

    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def toggle_forum_mode(
        chat: int | str,
        enabled: bool = True,
        tabs: bool = False,
    ) -> dict[str, Any]:
        """Включить/выключить forum-режим (темы) в супергруппе.

        Требует ≥200 участников. После включения супергруппа становится "форумом".
        """
        client = await get_client()
        peer = await client.get_input_entity(normalize_chat(chat))
        await client(ToggleForumRequest(channel=peer, enabled=enabled, tabs=tabs))
        return {"ok": True, "enabled": enabled}
