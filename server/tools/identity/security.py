"""Security — 2FA password info."""

from __future__ import annotations

from typing import Any

from telethon.tl.functions.account import GetPasswordRequest

from server.client import get_client
from server.tools._common import READ_ONLY


def register(mcp: Any) -> None:
    @mcp.tool(annotations=READ_ONLY)
    async def get_password_info() -> dict[str, Any]:
        """Информация о настроенном 2FA-пароле (включён ли, hint, recovery email).

        НЕ возвращает сам пароль — только метаданные.
        """
        client = await get_client()
        result = await client(GetPasswordRequest())
        return {
            "has_password": getattr(result, "has_password", False),
            "has_recovery": getattr(result, "has_recovery", False),
            "has_secure_values": getattr(result, "has_secure_values", False),
            "hint": getattr(result, "hint", None) or "",
            "email_unconfirmed_pattern": getattr(result, "email_unconfirmed_pattern", None) or "",
            "pending_reset_unix": (
                int(result.pending_reset_date.timestamp())
                if getattr(result, "pending_reset_date", None)
                else None
            ),
        }
