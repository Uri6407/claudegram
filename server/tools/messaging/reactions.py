"""Reactions — эмодзи-реакции на сообщения."""

from __future__ import annotations

from typing import Any

from telethon.tl.functions.messages import SendReactionRequest
from telethon.tl.types import ReactionEmoji

from server.client import get_client
from server.tools._common import NON_DESTRUCTIVE, normalize_chat


def register(mcp: Any) -> None:
    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def react_message(
        chat: int | str,
        message_id: int,
        emoji: str,
        big: bool = False,
        add_to_recent: bool = False,
    ) -> dict[str, Any]:
        """Поставить реакцию-эмодзи на сообщение.

        Args:
            emoji: 1 эмодзи (👍, ❤️, 🔥). Пустая строка — снять все реакции.
            big: показать с анимацией "большой реакции".
            add_to_recent: добавить эмодзи в "недавно использованные".
        """
        client = await get_client()
        reaction = [ReactionEmoji(emoticon=emoji)] if emoji else []
        await client(
            SendReactionRequest(
                peer=await client.get_input_entity(normalize_chat(chat)),
                msg_id=message_id,
                reaction=reaction,
                big=big,
                add_to_recent=add_to_recent,
            )
        )
        return {"ok": True, "emoji": emoji or "(cleared)"}
