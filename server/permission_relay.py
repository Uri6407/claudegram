"""Outbound permission_request handler.

Claude Code посылает в `read_stream` notifications вида
`notifications/claude/channel/permission_request` когда нужен approval
на tool. SDK не знает этот метод и дропает на парсинге.

Решение: перехватываем read_stream через tee — async-task читает оригинал,
peek'ает на target-method, пересылает в Telegram, всё остальное прозрачно
отдаёт MCP-серверу через proxy-стрим.

Verdict (`yes/no <id>`) приходит обратно через Telegram — обрабатывается
в `channel.run_listener` и отправляется как `notifications/claude/channel/permission`.
"""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import anyio

logger = logging.getLogger("claudegram.permission_relay")


def _peek_method(message: Any) -> str | None:
    """Извлечь method из SessionMessage, если он есть. None для requests/responses."""
    try:
        inner = message.message  # JSONRPCMessage
        # JSONRPCMessage = RootModel[Union[Request, Notification, Response, Error]]
        root = getattr(inner, "root", inner)
        return getattr(root, "method", None)
    except (AttributeError, TypeError):
        return None


def _peek_params(message: Any) -> dict[str, Any] | None:
    try:
        inner = message.message
        root = getattr(inner, "root", inner)
        params = getattr(root, "params", None)
        if params is None:
            return None
        if hasattr(params, "model_dump"):
            return params.model_dump()
        if isinstance(params, dict):
            return params
        return json.loads(json.dumps(params, default=str))
    except (AttributeError, TypeError, ValueError):
        return None


@asynccontextmanager
async def relay_read_stream(
    original_read: Any,
    on_permission_request: Any,
) -> AsyncIterator[Any]:
    """Wrap read_stream так, чтобы permission_request шёл в callback,
    а остальные сообщения — прозрачно дальше серверу.

    Args:
        original_read: оригинальный MemoryObjectReceiveStream от stdio_server.
        on_permission_request: async callable(params: dict) — что делать с прошением.

    Yields:
        proxy_read — MemoryObjectReceiveStream, который можно отдать `_mcp_server.run()`.
    """
    proxy_send, proxy_read = anyio.create_memory_object_stream[Any](max_buffer_size=100)

    async def _pump() -> None:
        try:
            async for message in original_read:
                # Если это исключение от stdio_server — прокидываем
                if isinstance(message, Exception):
                    await proxy_send.send(message)
                    continue
                method = _peek_method(message)
                if method == "notifications/claude/channel/permission_request":
                    params = _peek_params(message) or {}
                    try:
                        await on_permission_request(params)
                    except Exception:
                        logger.exception("permission_request handler failed")
                    # НЕ пробрасываем дальше — SDK не умеет такое
                    continue
                await proxy_send.send(message)
        except anyio.EndOfStream:
            pass
        except Exception:
            logger.exception("relay read pump crashed")
        finally:
            await proxy_send.aclose()

    async with anyio.create_task_group() as tg:
        tg.start_soon(_pump)
        try:
            yield proxy_read
        finally:
            tg.cancel_scope.cancel()


async def forward_permission_to_telegram(
    client: Any,
    chat_id: int,
    params: dict[str, Any],
) -> None:
    """Отправить permission_request как Telegram-сообщение в указанный чат.

    Юзер ответит `yes <id>` или `no <id>` — channel.run_listener распознает
    регексом и пушнёт verdict обратно.
    """
    request_id = params.get("request_id", "?????")
    tool_name = params.get("tool_name", "?")
    description = params.get("description", "")
    input_preview = params.get("input_preview", "")

    text = f"🔐 Claude хочет вызвать `{tool_name}`\n\n{description}\n"
    if input_preview:
        # Обрезаем превью и оборачиваем в кодовый блок
        snippet = input_preview[:300]
        text += f"\n```\n{snippet}\n```\n"
    text += f"\nОтветь:\n  `yes {request_id}` — разрешить\n  `no {request_id}` — запретить"

    await client.send_message(chat_id, text, parse_mode="markdown")
