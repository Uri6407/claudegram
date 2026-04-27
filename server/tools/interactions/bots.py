"""Bots — inline-запросы к ботам, start_bot, callback-кнопки."""

from __future__ import annotations

from typing import Any

from telethon.tl.functions.messages import StartBotRequest

from server.client import get_client
from server.tools._common import NON_DESTRUCTIVE, clamp, normalize_chat


def register(mcp: Any) -> None:
    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def inline_query(
        bot: int | str,
        query: str,
        offset: str = "",
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Сделать inline-запрос к боту (как `@bot query` в любом чате).

        Возвращает список результатов, которые бот хочет показать.
        """
        client = await get_client()
        # Telethon umеет inline_query as a high-level метод:
        results = await client.inline_query(
            normalize_chat(bot),
            query,
            offset=offset,
        )
        out: list[dict[str, Any]] = []
        for r in results[: clamp(limit, 1, 100)]:
            out.append(
                {
                    "id": getattr(r.result, "id", None),
                    "type": type(r.result).__name__,
                    "title": getattr(r.result, "title", None) or "",
                    "description": getattr(r.result, "description", None) or "",
                    "url": getattr(r.result, "url", None),
                }
            )
        return out

    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def start_bot(
        bot: int | str,
        chat: int | str | None = None,
        start_param: str = "",
    ) -> dict[str, Any]:
        """Запустить бота (отправить /start) с deep-link параметром.

        Args:
            bot: id/@username бота.
            chat: куда добавлять бота. None = личный чат с ботом.
            start_param: deep-link payload (часть после `?start=`).
        """
        client = await get_client()
        bot_peer = await client.get_input_entity(normalize_chat(bot))
        chat_peer = await client.get_input_entity(normalize_chat(chat)) if chat else bot_peer
        result = await client(
            StartBotRequest(bot=bot_peer, peer=chat_peer, start_param=start_param)
        )
        msgs = [u for u in getattr(result, "updates", []) if hasattr(u, "message")]
        return {"ok": True, "updates": [type(u).__name__ for u in msgs]}

    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def click_inline_button(
        chat: int | str,
        message_id: int,
        button_text: str | None = None,
        button_index: int | None = None,
    ) -> dict[str, Any]:
        """Нажать inline-кнопку под сообщением бота.

        Args:
            button_text: текст кнопки (точное совпадение).
            button_index: альтернатива — flat-индекс кнопки (через все ряды).
                Передай либо `button_text`, либо `button_index`.
        """
        client = await get_client()
        msg = await client.get_messages(normalize_chat(chat), ids=message_id)
        if msg is None:
            return {"ok": False, "reason": "Сообщение не найдено"}
        try:
            if button_text is not None:
                result = await msg.click(text=button_text)
            elif button_index is not None:
                result = await msg.click(button_index)
            else:
                return {"ok": False, "reason": "Нужен button_text или button_index"}
        except Exception as exc:
            return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
        return {
            "ok": True,
            "result_type": type(result).__name__ if result else None,
            "message_id": getattr(result, "message_id", None),
        }
