"""Batch-операции на списках chat_id — экономят 100+ MCP-вызовов.

Все ops идут sequentially server-side с обработкой FloodWait. По умолчанию
auto_floodwait_retry=True — внутренний sleep на retry_after, но не более
max_total_wait_seconds (default 600s). Возвращает структурированный
BatchOpResult с per-chat статусом.
"""

from __future__ import annotations

import asyncio
from typing import Any

from telethon.errors import FloodWaitError, RPCError
from telethon.tl.functions.channels import LeaveChannelRequest

from server.client import get_client
from server.tools._common import DESTRUCTIVE, confirm_or_abort, normalize_chat


async def _do_with_floodwait(
    coro_factory: Any,
    *,
    auto_retry: bool,
    max_total_wait: int,
) -> tuple[str, dict[str, Any]]:
    """Выполнить coro_factory(); при FloodWait — sleep и retry.

    Returns: ('ok'|'flood_skipped'|'error', detail_dict).
    """
    waited = 0
    while True:
        try:
            await coro_factory()
            return "ok", {"ok": True}
        except FloodWaitError as exc:
            if not auto_retry or waited + exc.seconds > max_total_wait:
                return "flood_skipped", {
                    "ok": False,
                    "error": "FloodWaitError",
                    "retry_after": exc.seconds,
                }
            await asyncio.sleep(exc.seconds + 1)
            waited += exc.seconds + 1
        except RPCError as exc:
            return "error", {
                "ok": False,
                "error": type(exc).__name__,
                "message": exc.message,
            }
        except Exception as exc:
            return "error", {
                "ok": False,
                "error": type(exc).__name__,
                "message": str(exc),
            }


def register(mcp: Any) -> None:
    @mcp.tool(annotations=DESTRUCTIVE)
    async def delete_dialogs(
        chat_ids: list[int | str],
        revoke: bool = False,
        auto_floodwait_retry: bool = True,
        max_total_wait_seconds: int = 600,
        ctx: Any = None,
    ) -> dict[str, Any]:
        """Удалить N диалогов одним MCP-вызовом.

        Для supergroups = leave + delete dialog. Для PM = clear history (revoke=False)
        или revoke=True (PM only — у собеседника тоже).

        Args:
            chat_ids: список int/str id диалогов.
            revoke: только для PM — удалить и у собеседника.
            auto_floodwait_retry: при FloodWait sleep'ить и продолжать.
            max_total_wait_seconds: верхний предел total sleep.
        """
        if (
            abort := await confirm_or_abort(
                ctx,
                action="delete_dialogs (batch)",
                target=f"{len(chat_ids)} диалогов",
                extra=f"revoke={revoke}",
            )
        ):
            return abort

        client = await get_client()
        results: list[dict[str, Any]] = []
        succeeded = failed = flood_waited = 0
        for cid in chat_ids:
            norm = normalize_chat(cid)
            status, detail = await _do_with_floodwait(
                lambda c=norm: client.delete_dialog(c, revoke=revoke),
                auto_retry=auto_floodwait_retry,
                max_total_wait=max_total_wait_seconds,
            )
            entry = {"chat_id": cid, **detail}
            results.append(entry)
            if status == "ok":
                succeeded += 1
            elif status == "flood_skipped":
                flood_waited += 1
            else:
                failed += 1
        return {
            "total": len(chat_ids),
            "succeeded": succeeded,
            "failed": failed,
            "flood_waited": flood_waited,
            "results": results,
        }

    @mcp.tool(annotations=DESTRUCTIVE)
    async def leave_chats(
        chat_ids: list[int | str],
        auto_floodwait_retry: bool = True,
        max_total_wait_seconds: int = 600,
        ctx: Any = None,
    ) -> dict[str, Any]:
        """Выйти из N каналов/супергрупп одним вызовом."""
        if (
            abort := await confirm_or_abort(
                ctx,
                action="leave_chats (batch)",
                target=f"{len(chat_ids)} каналов/групп",
            )
        ):
            return abort

        client = await get_client()
        results: list[dict[str, Any]] = []
        succeeded = failed = flood_waited = 0

        async def _leave_one(cid_norm: int | str) -> None:
            peer = await client.get_input_entity(cid_norm)
            await client(LeaveChannelRequest(channel=peer))

        for cid in chat_ids:
            norm = normalize_chat(cid)
            status, detail = await _do_with_floodwait(
                lambda c=norm: _leave_one(c),
                auto_retry=auto_floodwait_retry,
                max_total_wait=max_total_wait_seconds,
            )
            entry = {"chat_id": cid, **detail}
            results.append(entry)
            if status == "ok":
                succeeded += 1
            elif status == "flood_skipped":
                flood_waited += 1
            else:
                failed += 1
        return {
            "total": len(chat_ids),
            "succeeded": succeeded,
            "failed": failed,
            "flood_waited": flood_waited,
            "results": results,
        }

    @mcp.tool(annotations=DESTRUCTIVE)
    async def archive_dialogs(
        chat_ids: list[int | str],
        ctx: Any = None,
    ) -> dict[str, Any]:
        """Перенести N диалогов в архив."""
        client = await get_client()
        results: list[dict[str, Any]] = []
        succeeded = failed = 0
        for cid in chat_ids:
            try:
                await client.edit_folder(normalize_chat(cid), folder=1)
                results.append({"chat_id": cid, "ok": True})
                succeeded += 1
            except Exception as exc:
                results.append(
                    {"chat_id": cid, "ok": False, "error": f"{type(exc).__name__}: {exc}"}
                )
                failed += 1
        return {"total": len(chat_ids), "succeeded": succeeded, "failed": failed, "results": results}
