"""Users — операции специфичные для пользователей (фото, общие чаты, full info)."""

from __future__ import annotations

import io
import tempfile
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import Image

from server.client import get_client
from server.formatters import entity_brief
from server.tools._common import NON_DESTRUCTIVE, READ_ONLY, clamp, normalize_chat


def register(mcp: Any) -> None:
    @mcp.tool(annotations=READ_ONLY)
    async def get_profile_photos(
        chat: int | str,
        limit: int = 10,
        offset: int = 0,
        max_id: int = 0,
    ) -> list[dict[str, Any]]:
        """Список фото профиля юзера/группы/канала (метаданные, без скачивания).

        Args:
            offset: пропустить N фото с начала.
            max_id: вернуть фото старше указанного id.
        """
        client = await get_client()
        photos = await client.get_profile_photos(
            normalize_chat(chat), limit=clamp(limit, 1, 100), offset=offset, max_id=max_id
        )
        return [
            {
                "id": p.id,
                "date": p.date.isoformat() if p.date else None,
                "has_video": getattr(p, "has_video", False),
            }
            for p in photos
        ]

    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def download_profile_photo(
        chat: int | str,
        download_dir: str | None = None,
        download_big: bool = True,
        inline: bool = False,
    ) -> dict[str, Any]:
        """Скачать аватарку юзера/чата на диск или inline (base64 в ответе).

        Args:
            download_big: True — большая (640x640); False — маленькая (160x160).
            inline: True — вернуть фото как ImageContent inline (≤ 1 MB),
                False — записать в файл и вернуть путь.
        """
        client = await get_client()
        if inline:
            buf = io.BytesIO()
            result = await client.download_profile_photo(
                normalize_chat(chat), file=buf, download_big=download_big
            )
            if result is None:
                return {"ok": False, "reason": "Нет фото профиля"}
            data = buf.getvalue()
            if len(data) > 1_048_576:
                return {
                    "ok": False,
                    "reason": f"inline слишком большой ({len(data)} байт). Используй inline=False.",
                }
            return {
                "ok": True,
                "image": Image(data=data, format="jpeg"),
                "size_bytes": len(data),
            }
        out_dir = (
            Path(download_dir).expanduser().resolve()
            if download_dir
            else Path(tempfile.gettempdir())
        )
        out_dir.mkdir(parents=True, exist_ok=True)
        path = await client.download_profile_photo(
            normalize_chat(chat), file=str(out_dir), download_big=download_big
        )
        if path is None:
            return {"ok": False, "reason": "Нет фото профиля"}
        return {"ok": True, "path": str(path)}

    @mcp.tool(annotations=READ_ONLY)
    async def get_common_chats(user: int | str, limit: int = 50) -> list[dict[str, Any]]:
        """Общие чаты с указанным юзером."""
        from telethon.tl.functions.messages import GetCommonChatsRequest

        client = await get_client()
        peer = await client.get_input_entity(normalize_chat(user))
        result = await client(
            GetCommonChatsRequest(user_id=peer, max_id=0, limit=clamp(limit, 1, 100))
        )
        return [entity_brief(c) for c in result.chats]
