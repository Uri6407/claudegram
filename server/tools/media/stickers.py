"""Stickers — установленные наборы, поиск, install/uninstall, отправка."""

from __future__ import annotations

from typing import Any

from telethon.tl.functions.messages import (
    GetAllStickersRequest,
    GetStickerSetRequest,
    InstallStickerSetRequest,
    SearchStickerSetsRequest,
    UninstallStickerSetRequest,
)
from telethon.tl.types import InputStickerSetShortName

from server.client import get_client
from server.formatters import message_brief
from server.tools._common import NON_DESTRUCTIVE, READ_ONLY, normalize_chat


def register(mcp: Any) -> None:
    @mcp.tool(annotations=READ_ONLY)
    async def get_installed_stickers() -> list[dict[str, Any]]:
        """Список установленных стикерсетов."""
        client = await get_client()
        result = await client(GetAllStickersRequest(hash=0))
        sets = getattr(result, "sets", []) or []
        return [
            {
                "id": s.id,
                "access_hash": str(s.access_hash),
                "title": s.title,
                "short_name": s.short_name,
                "count": s.count,
                "animated": getattr(s, "animated", False),
                "videos": getattr(s, "videos", False),
                "emojis": getattr(s, "emojis", False),
            }
            for s in sets
        ]

    @mcp.tool(annotations=READ_ONLY)
    async def get_sticker_set(short_name: str) -> dict[str, Any]:
        """Получить стикерсет по short_name (например 'AnimatedEmojies').

        Возвращает метаданные сета + список первых 10 стикеров (id + emoji).
        """
        client = await get_client()
        try:
            result = await client(
                GetStickerSetRequest(
                    stickerset=InputStickerSetShortName(short_name=short_name),
                    hash=0,
                )
            )
        except Exception as exc:
            return {"ok": False, "error": str(exc)}
        s = result.set
        documents = getattr(result, "documents", [])[:10]
        packs = getattr(result, "packs", [])
        emoji_by_doc: dict[int, str] = {}
        for pack in packs:
            for doc_id in pack.documents:
                emoji_by_doc.setdefault(doc_id, pack.emoticon)
        return {
            "ok": True,
            "set": {
                "id": s.id,
                "access_hash": str(s.access_hash),
                "title": s.title,
                "short_name": s.short_name,
                "count": s.count,
            },
            "preview": [
                {"document_id": str(d.id), "emoji": emoji_by_doc.get(d.id, "")} for d in documents
            ],
        }

    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def install_sticker_set(
        short_name: str,
        archived: bool = False,
    ) -> dict[str, Any]:
        """Установить стикерсет аккаунту.

        Args:
            archived: True — добавить в архивированные (не показывать активно).
        """
        client = await get_client()
        try:
            await client(
                InstallStickerSetRequest(
                    stickerset=InputStickerSetShortName(short_name=short_name),
                    archived=archived,
                )
            )
        except Exception as exc:
            return {"ok": False, "error": str(exc)}
        return {"ok": True, "short_name": short_name}

    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def uninstall_sticker_set(short_name: str) -> dict[str, Any]:
        """Удалить стикерсет из аккаунта."""
        client = await get_client()
        try:
            await client(
                UninstallStickerSetRequest(
                    stickerset=InputStickerSetShortName(short_name=short_name)
                )
            )
        except Exception as exc:
            return {"ok": False, "error": str(exc)}
        return {"ok": True, "short_name": short_name}

    @mcp.tool(annotations=READ_ONLY)
    async def search_sticker_sets(
        query: str, exclude_featured: bool = False
    ) -> list[dict[str, Any]]:
        """Поиск стикерсетов по имени (Telegram-каталог).

        Args:
            exclude_featured: исключить из выдачи featured-наборы.
        """
        client = await get_client()
        result = await client(
            SearchStickerSetsRequest(q=query, hash=0, exclude_featured=exclude_featured)
        )
        sets = getattr(result, "sets", []) or []
        return [
            {
                "id": s.set.id if hasattr(s, "set") else s.id,
                "title": (s.set.title if hasattr(s, "set") else s.title),
                "short_name": (s.set.short_name if hasattr(s, "set") else s.short_name),
                "count": (s.set.count if hasattr(s, "set") else s.count),
            }
            for s in sets
        ]

    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def send_sticker_by_id(
        chat: int | str,
        document_id: int,
        access_hash: int,
        sticker_set_short_name: str,
        reply_to: int | None = None,
        silent: bool = False,
    ) -> dict[str, Any]:
        """Отправить стикер по document_id (получи через get_sticker_set).

        Args:
            document_id: id стикер-документа.
            access_hash: access_hash набора (поле `set.access_hash`).
            sticker_set_short_name: short_name набора-источника.
        """
        from telethon.tl.types import InputDocument

        client = await get_client()
        # Сначала получим polnoye stickerset чтобы достать file_reference
        ss = await client(
            GetStickerSetRequest(
                stickerset=InputStickerSetShortName(short_name=sticker_set_short_name),
                hash=0,
            )
        )
        target_doc = next((d for d in getattr(ss, "documents", []) if d.id == document_id), None)
        if target_doc is None:
            return {"ok": False, "reason": f"document_id {document_id} нет в наборе"}
        sticker = InputDocument(
            id=target_doc.id,
            access_hash=target_doc.access_hash,
            file_reference=target_doc.file_reference,
        )
        msg = await client.send_file(
            normalize_chat(chat), sticker, reply_to=reply_to, silent=silent
        )
        return message_brief(msg)
