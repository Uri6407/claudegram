"""Drafts — сохранение/очистка черновиков на стороне сервера."""

from __future__ import annotations

from typing import Any

from telethon.tl.functions.messages import SaveDraftRequest

from server.client import get_client
from server.tools._common import DESTRUCTIVE, NON_DESTRUCTIVE, ParseMode, normalize_chat


def register(mcp: Any) -> None:
    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def save_draft(
        chat: int | str,
        text: str,
        reply_to: int | None = None,
        parse_mode: ParseMode = "markdown",
        link_preview: bool = True,
    ) -> dict[str, Any]:
        """Сохранить серверный draft в чате (синхронизируется на все устройства).

        Args:
            text: текст; пустая строка очищает draft.
            parse_mode: подсказка клиенту, как парсить при отправке
                (фактическое форматирование происходит в момент отправки сообщения).
        """
        client = await get_client()
        peer = await client.get_input_entity(normalize_chat(chat))
        ok = await client(
            SaveDraftRequest(
                peer=peer,
                message=text,
                reply_to_msg_id=reply_to,
                no_webpage=not link_preview,
            )
        )
        return {"ok": bool(ok), "parse_mode": parse_mode}

    @mcp.tool(annotations=DESTRUCTIVE)
    async def clear_draft(chat: int | str) -> dict[str, Any]:
        """Очистить draft в чате (синхронизация на все устройства)."""
        client = await get_client()
        peer = await client.get_input_entity(normalize_chat(chat))
        ok = await client(SaveDraftRequest(peer=peer, message=""))
        return {"ok": bool(ok)}
