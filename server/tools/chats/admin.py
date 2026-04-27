"""Admin — журнал действий админов + статистика канала."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import Context

from server.client import get_client
from server.tools._common import READ_ONLY, clamp, normalize_chat


def register(mcp: Any) -> None:
    @mcp.tool(annotations=READ_ONLY)
    async def get_admin_log(
        chat: int | str,
        limit: int = 50,
        search: str = "",
        ctx: Context | None = None,
    ) -> list[dict[str, Any]]:
        """Журнал действий админов в супергруппе/канале."""
        client = await get_client()
        target = clamp(limit, 1, 200)
        out: list[dict[str, Any]] = []
        async for e in client.iter_admin_log(
            normalize_chat(chat), limit=target, search=search or None
        ):
            out.append(
                {
                    "id": e.id,
                    "date": e.date.isoformat() if e.date else None,
                    "user_id": e.user_id,
                    "action": type(e.action).__name__ if e.action else None,
                }
            )
            if ctx is not None and len(out) % 25 == 0:
                await ctx.report_progress(
                    progress=float(len(out)),
                    total=float(target),
                    message=f"записей {len(out)}/{target}",
                )
        return out

    @mcp.tool(annotations=READ_ONLY)
    async def get_stats(chat: int | str) -> dict[str, Any]:
        """Статистика канала/супергруппы (только если ты админ)."""
        client = await get_client()
        try:
            stats = await client.get_stats(normalize_chat(chat))
        except Exception as exc:
            return {"ok": False, "error": str(exc)}
        return {
            "ok": True,
            "type": type(stats).__name__,
            "period": getattr(getattr(stats, "period", None), "min_date", None),
        }
