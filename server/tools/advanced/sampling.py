"""Sampling — делегируем LLM-вызов обратно клиенту через MCP.

Тула получает `ctx`, собирает данные из Telegram, и просит клиент сделать
LLM-вызов через `ctx.session.create_message`. Никаких API-ключей на сервере
не нужно — клиент использует свою модель.

Полезно для: AI-summarize-chat, classify-unread, draft-from-context.
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import Context
from mcp.types import SamplingMessage, TextContent

from server.client import get_client
from server.formatters import message_brief
from server.tools._common import READ_ONLY, clamp, normalize_chat


def register(mcp: Any) -> None:
    @mcp.tool(annotations=READ_ONLY)
    async def summarize_chat(
        chat: int | str,
        limit: int = 100,
        instruction: str = "",
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        """Резюме последних N сообщений чата через LLM-вызов клиента.

        Args:
            chat: id или @username.
            limit: 1-200 сообщений.
            instruction: дополнительная инструкция для модели
                (например, "сделай маркированный список", "выдели action items").

        Если клиент не поддерживает sampling — возвращает сырые сообщения
        и просит юзера резюмировать самому.
        """
        # Предпочтительно читаем через ctx.read_resource (использует кэш клиента
        # + единая точка), фоллбэк на прямой client.get_messages.
        briefs: list[dict[str, Any]] = []
        target = clamp(limit, 1, 200)
        if ctx is not None:
            try:
                import json

                contents = await ctx.read_resource(f"telegram://chat/{chat}/history")
                for c in contents:
                    payload = getattr(c, "content", None) or getattr(c, "text", None)
                    if isinstance(payload, str):
                        briefs.extend(json.loads(payload))
                briefs = briefs[:target]
            except Exception:
                briefs = []
        if not briefs:
            client = await get_client()
            messages = await client.get_messages(normalize_chat(chat), limit=target)
            briefs = [message_brief(m) for m in messages]
        text_blob = "\n".join(
            f"[{b.get('date')}] {b.get('sender_id', '?')}: {b.get('text', '')}"
            for b in briefs
            if b.get("text")
        )

        if ctx is None:
            return {
                "ok": False,
                "reason": "Контекст недоступен — нечего делегировать клиенту",
                "raw_messages": briefs,
            }

        sys_prompt = (
            "Ты резюмируешь Telegram-переписку. Будь краток, выдели темы и решения."
        )
        if instruction:
            sys_prompt += f" Дополнительно: {instruction}"

        try:
            result = await ctx.session.create_message(
                messages=[
                    SamplingMessage(
                        role="user",
                        content=TextContent(type="text", text=text_blob[:50_000]),
                    )
                ],
                max_tokens=800,
                system_prompt=sys_prompt,
            )
        except Exception as exc:
            return {
                "ok": False,
                "reason": f"Sampling не поддержан клиентом: {exc}",
                "raw_messages": briefs,
            }

        out_text = ""
        content = getattr(result, "content", None)
        if content is not None:
            out_text = getattr(content, "text", "") or ""

        return {
            "ok": True,
            "summary": out_text,
            "model": getattr(result, "model", None),
            "stop_reason": getattr(result, "stopReason", None),
            "input_message_count": len(briefs),
        }
