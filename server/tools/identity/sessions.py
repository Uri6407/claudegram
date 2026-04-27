"""Sessions — управление активными авторизациями (другие устройства/клиенты)."""

from __future__ import annotations

from typing import Any

from telethon.tl.functions.account import (
    GetAuthorizationsRequest,
    ResetAuthorizationRequest,
)

from server.client import get_client
from server.tools._common import DESTRUCTIVE, READ_ONLY


def register(mcp: Any) -> None:
    @mcp.tool(annotations=READ_ONLY)
    async def get_authorizations() -> list[dict[str, Any]]:
        """Список активных сессий аккаунта (другие устройства/клиенты).

        Полезно для аудита: "кто сейчас залогинен в мой аккаунт".
        """
        client = await get_client()
        result = await client(GetAuthorizationsRequest())
        return [
            {
                "hash": str(a.hash),
                "device_model": a.device_model,
                "platform": a.platform,
                "system_version": a.system_version,
                "app_name": a.app_name,
                "app_version": a.app_version,
                "date_created": a.date_created.isoformat() if a.date_created else None,
                "date_active": a.date_active.isoformat() if a.date_active else None,
                "ip": a.ip,
                "country": a.country,
                "region": a.region,
                "current": a.current,
                "official_app": a.official_app,
                "password_pending": a.password_pending,
            }
            for a in result.authorizations
        ]

    @mcp.tool(annotations=DESTRUCTIVE)
    async def terminate_authorization(hash_str: str) -> dict[str, Any]:
        """Завершить чужую активную сессию по `hash` из get_authorizations.

        Свою (current=true) сессию через этот метод завершить нельзя.
        """
        client = await get_client()
        try:
            hash_int = int(hash_str)
        except ValueError as exc:
            raise RuntimeError("hash должен быть числовой строкой") from exc
        ok = await client(ResetAuthorizationRequest(hash=hash_int))
        return {"ok": bool(ok)}
