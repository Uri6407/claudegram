"""Claudegram MCP-сервер.

Запуск:
    uv run python -m server.main
    uv run claudegram

Использует stdio-транспорт MCP. Регистрируется в Claude Code через .mcp.json.

Поддерживает два режима:
- **Tools-only** (по умолчанию): 58+ типизированных tool'ов через FastMCP,
  разбитых по категориям в server/tools/.
- **Channel mode** (`CLAUDEGRAM_CHANNEL_MODE=1` + `enable_channel_mode=1` в userConfig):
  дополнительно объявляет `claude/channel` capability + permission relay,
  пушит входящие Telegram-сообщения в активную Claude-сессию,
  форвардит permission-prompts юзеру в Telegram.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.server.lowlevel.server import NotificationOptions
from mcp.server.stdio import stdio_server

from server import channel as channel_mod
from server import completions as completions_mod
from server import permission_relay
from server import prompts as prompts_mod
from server import resources as resources_mod
from server.client import get_client, lifespan
from server.client import shutdown as shutdown_client
from server.middleware import safe_tool
from server.tools import register_all

logging.basicConfig(
    level=os.environ.get("CLAUDEGRAM_LOG_LEVEL", "INFO"),
    format="[%(asctime)s] [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("claudegram")

mcp = FastMCP(
    "claudegram",
    instructions=channel_mod.CHANNEL_INSTRUCTIONS,
    lifespan=lifespan,
)


def _wrap_all_tools_with_safe_tool() -> None:
    """Оборачиваем все зарегистрированные tools в `safe_tool` middleware.

    Делаем после `register_all`, потому что декоратор `@safe_tool` иначе
    надо было бы добавлять руками в каждом из 25+ модулей. Идемпотентно:
    `safe_tool` устанавливает атрибут `__claudegram_safe__`, второй проход
    пропускает уже обёрнутые.
    """
    manager = mcp._tool_manager
    for _name, tool in list(manager._tools.items()):
        fn = tool.fn
        if getattr(fn, "__claudegram_safe__", False):
            continue
        wrapped = safe_tool(fn)
        wrapped.__claudegram_safe__ = True  # type: ignore[attr-defined]
        tool.fn = wrapped


# Регистрируем все tools из server/tools/* (9 доменов, 121 tools),
# resources (read-only снапшоты), prompts (slash-шаблоны) и completion handler.
register_all(mcp)
resources_mod.register(mcp)
prompts_mod.register(mcp)
completions_mod.register(mcp)
_wrap_all_tools_with_safe_tool()


async def _run_async() -> None:
    """Кастомный stdio-runner: оборачиваем MCP-сервер, чтобы:

    1. Объявить experimental capabilities (`claude/channel`,
       `claude/channel/permission`) — FastMCP сам этого не умеет.
    2. Запараллелить background Telethon-listener, который пушит входящие
       сообщения в Claude через тот же write_stream.
    3. Перехватывать `permission_request` от Claude Code и форвардить
       юзеру в Telegram (outbound permission relay).
    """
    channel_on = channel_mod.channel_mode_enabled()
    allowed_ids = channel_mod.get_allowed_ids() if channel_on else set()

    experimental: dict[str, dict[str, Any]] = {}
    if channel_on:
        experimental["claude/channel"] = {}
        experimental["claude/channel/permission"] = {}
        # Outbound permission relay: явно декларируем, что сервер
        # принимает permission_request от Claude Code и форвардит юзеру в Telegram.
        experimental["claude/channel/permission_request"] = {}

    async with stdio_server() as (read_stream, write_stream):
        listener_task: asyncio.Task[None] | None = None
        client = None
        if channel_on:
            try:
                client = await get_client()
                logger.info("channel mode ON; starting Telegram listener…")
                listener_task = asyncio.create_task(
                    channel_mod.run_listener(write_stream, allowed_ids)
                )
            except RuntimeError as exc:
                logger.warning(
                    "channel mode requested but disabled: %s. Tools-only mode будет работать. "
                    "Запусти `claudegram-auth` и перезапусти Claude Code.",
                    exc,
                )

        async def _on_perm_request(params: dict[str, Any]) -> None:
            """Forward permission_request → Telegram (если канал активен)."""
            if client is None:
                return
            try:
                target_chat: int
                if allowed_ids:
                    target_chat = next(iter(allowed_ids))
                else:
                    me = await client.get_me()
                    target_chat = me.id
                await permission_relay.forward_permission_to_telegram(client, target_chat, params)
            except Exception:
                logger.exception("forward_permission_to_telegram failed")

        init_opts = mcp._mcp_server.create_initialization_options(
            notification_options=NotificationOptions(
                prompts_changed=True,
                resources_changed=True,
                tools_changed=True,
            ),
            experimental_capabilities=experimental,
        )

        try:
            if channel_on and client is not None:
                async with permission_relay.relay_read_stream(
                    read_stream, _on_perm_request
                ) as proxied:
                    await mcp._mcp_server.run(proxied, write_stream, init_opts)
            else:
                await mcp._mcp_server.run(read_stream, write_stream, init_opts)
        finally:
            if listener_task and not listener_task.done():
                listener_task.cancel()
                try:
                    await listener_task
                except (asyncio.CancelledError, Exception):
                    logger.debug("listener task ended", exc_info=True)
            await shutdown_client()


def run() -> None:
    asyncio.run(_run_async())


if __name__ == "__main__":
    run()
