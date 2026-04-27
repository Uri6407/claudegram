"""Telethon TelegramClient — управляется lifespan'ом FastMCP.

`get_client()` остаётся как fallback для импортирующих модулей: возвращает
тот же singleton, который запускает lifespan. В тестах он подменяется
через `conftest.patch_get_client`.
"""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING

from telethon import TelegramClient

from server.config import Config

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

_client: TelegramClient | None = None
_lock = asyncio.Lock()


@dataclass(frozen=True)
class AppContext:
    """Состояние, доступное всем tools через `ctx.request_context.lifespan_context`."""

    client: TelegramClient | None
    config: Config


async def get_client() -> TelegramClient:
    """Singleton-доступ к Telethon-клиенту.

    Если lifespan уже запустился — возвращает закешированный инстанс мгновенно.
    Иначе (например, тесты или standalone-вне-MCP) — лениво коннектится.

    Важно: при ошибке аутентификации disconnect'имся перед raise, чтобы не
    держать session-lock и позволить пользователю запустить `claudegram-auth`
    в параллельном процессе.
    """
    global _client
    async with _lock:
        if _client is None:
            cfg = Config.load()
            client = TelegramClient(str(cfg.session_path), cfg.api_id, cfg.api_hash)
            await client.connect()
            try:
                authorized = await client.is_user_authorized()
            except Exception:
                with contextlib.suppress(Exception):
                    await client.disconnect()
                raise
            if not authorized:
                with contextlib.suppress(Exception):
                    await client.disconnect()
                raise RuntimeError(
                    "Telegram-сессия не авторизована. "
                    "Запусти `! claudegram-auth` один раз."
                )
            _client = client
        return _client


async def shutdown() -> None:
    """Закрыть текущий клиент. Идемпотентно."""
    global _client
    if _client is not None:
        try:
            await _client.disconnect()
        except Exception:
            pass
        _client = None


@asynccontextmanager
async def lifespan(_mcp: FastMCP) -> AsyncIterator[AppContext]:
    """FastMCP lifespan: warm-up через `get_client()` + чистый shutdown.

    Используем общий singleton — без второго TelegramClient на тот же session-файл.
    Если authorization не прошла — даём серверу подняться (tools-only), чтобы
    `health_check` мог сообщить об этом. `safe_tool` обернёт ошибки.
    """
    cfg = Config.load()
    try:
        client = await get_client()
        yield AppContext(client=client, config=cfg)
    except RuntimeError:
        # No-auth path: yield context без клиента, но логи будут видны.
        # tools, требующие client, сами упадут в safe_tool с понятным error.
        yield AppContext(client=None, config=cfg)  # type: ignore[arg-type]
    finally:
        await shutdown()
