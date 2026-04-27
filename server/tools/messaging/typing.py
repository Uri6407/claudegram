"""Typing — отправка статуса 'печатает...' / 'записывает голосовое'."""

from __future__ import annotations

from typing import Any, Literal

from server.client import get_client
from server.tools._common import NON_DESTRUCTIVE, normalize_chat

ActionKind = Literal[
    "typing",
    "contact",
    "game",
    "location",
    "sticker",
    "record-audio",
    "record-round",
    "record-video",
    "audio",
    "round",
    "video",
    "photo",
    "document",
    "cancel",
]


def register(mcp: Any) -> None:
    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def set_typing(
        chat: int | str,
        action: ActionKind = "typing",
        delay_seconds: float = 0.0,
    ) -> dict[str, Any]:
        """Послать сигнал активности в чат (печатает / записывает / отправляет).

        Args:
            chat: id или @username чата.
            action: тип активности — `typing` для текста, `record-audio` перед
                голосовым, `cancel` чтобы снять текущий статус и т.д.
            delay_seconds: на сколько секунд держать статус (0 — мгновенный сигнал).
        """
        client = await get_client()
        peer = await client.get_input_entity(normalize_chat(chat))
        if delay_seconds > 0:
            async with client.action(peer, action):
                import asyncio

                await asyncio.sleep(min(delay_seconds, 30.0))
        else:
            await client.action(peer, action).set()
        return {"ok": True, "action": action}
