"""Health — readiness/liveness probes для production-мониторинга."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from server.client import get_client
from server.config import Config
from server.models import HealthReport, ServerVersion
from server.tools._common import READ_ONLY


def _session_diagnostics() -> dict[str, Any]:
    """Где МЫ ищем сессию + существует ли файл (для отладки path mismatch)."""
    try:
        cfg = Config.load()
    except Exception as exc:
        return {"session_path": None, "session_exists": False, "data_dir": None, "_err": str(exc)}
    sp = Path(f"{cfg.session_path}.session")
    return {
        "session_path": str(sp),
        "session_exists": sp.exists(),
        "data_dir": str(cfg.data_dir),
    }


def register(mcp: Any) -> None:
    @mcp.tool(annotations=READ_ONLY)
    async def health_check(force_reconnect: bool = False) -> HealthReport:
        """Проверка работоспособности: соединение с Telegram, валидность сессии.

        Args:
            force_reconnect: True — сбросить singleton-клиент и переподключиться.
                Полезно после `claudegram-auth`, если сервер закэшировал старое
                no-auth состояние.

        Возвращает HealthReport со всеми полями даже при ошибке —
        включая session_path/session_exists/data_dir для диагностики
        path mismatch между CLI и MCP-сервером.
        """
        diag = _session_diagnostics()
        if force_reconnect:
            from server.client import shutdown

            await shutdown()

        start = time.monotonic()
        try:
            client = await get_client()
        except RuntimeError as exc:
            return HealthReport(
                ok=False,
                connected=False,
                authorized=False,
                message=str(exc),
                **diag,
            )
        except Exception as exc:
            return HealthReport(
                ok=False,
                connected=False,
                authorized=False,
                message=f"{type(exc).__name__}: {exc}",
                **diag,
            )

        try:
            connected = client.is_connected()
            if not connected:
                return HealthReport(ok=False, connected=False, authorized=False, **diag)
            authorized = await client.is_user_authorized()
            if not authorized:
                return HealthReport(
                    ok=False,
                    connected=True,
                    authorized=False,
                    message="Сессия не авторизована — запусти `! claudegram-auth`",
                    **diag,
                )
            me = await client.get_me()
            latency_ms = int((time.monotonic() - start) * 1000)
            return HealthReport(
                ok=True,
                connected=True,
                authorized=True,
                self_id=me.id,
                self_username=me.username,
                is_premium=getattr(me, "premium", False),
                telegram_latency_ms=latency_ms,
                **diag,
            )
        except Exception as exc:
            return HealthReport(
                ok=False,
                connected=False,
                authorized=False,
                message=f"{type(exc).__name__}: {exc}",
                **diag,
            )

    health_check.__claudegram_safe__ = True

    @mcp.tool(annotations=READ_ONLY)
    async def get_server_version() -> ServerVersion:
        """Версия Claudegram + Telethon + MCP SDK."""
        from importlib.metadata import version

        return ServerVersion(
            claudegram=version("claudegram"),
            telethon=version("telethon"),
            mcp=version("mcp"),
            python=__import__("sys").version.split()[0],
        )

    get_server_version.__claudegram_safe__ = True
