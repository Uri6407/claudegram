"""Production middleware: error handling, latency logging, sanitization.

Все Telethon-исключения должны конвертироваться в graceful error-dict, а не
всплывать как stack-trace в Claude. FloodWait должен возвращать `retry_after`
секунд, чтобы Claude знал, сколько ждать.

Sensitive значения (api_hash, phone, 2FA password) никогда не должны попадать
в логи.
"""

from __future__ import annotations

import functools
import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any

logger = logging.getLogger("claudegram.tool")

SENSITIVE_KEYS = {
    "api_hash",
    "tg_api_hash",
    "TG_API_HASH",
    "tg_2fa_password",
    "TG_2FA_PASSWORD",
    "phone",
    "tg_phone",
    "TG_PHONE",
    "session",
    "password",
}


def sanitize(data: Any) -> Any:
    """Замаскировать sensitive ключи в dict для безопасного логирования."""
    if isinstance(data, dict):
        return {
            k: "***REDACTED***" if k in SENSITIVE_KEYS else sanitize(v) for k, v in data.items()
        }
    if isinstance(data, list):
        return [sanitize(x) for x in data]
    return data


def safe_tool(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
    """Decorator: оборачивает async tool-функцию в graceful error handling.

    - FloodWaitError → `{ok: False, retry_after: N, error: "FloodWait"}`
    - RPCError → `{ok: False, error: "<type>: <message>"}`
    - Любая Exception → `{ok: False, error: "<type>: <message>"}`
    - Логирует latency и success/error для observability.
    """

    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        from telethon.errors import FloodWaitError, RPCError

        start = time.monotonic()
        tool_name = func.__name__
        try:
            result = await func(*args, **kwargs)
            latency_ms = int((time.monotonic() - start) * 1000)
            logger.info("tool=%s status=ok latency_ms=%d", tool_name, latency_ms)
            return result
        except FloodWaitError as exc:
            latency_ms = int((time.monotonic() - start) * 1000)
            logger.warning(
                "tool=%s status=flood_wait seconds=%d latency_ms=%d",
                tool_name,
                exc.seconds,
                latency_ms,
            )
            return {
                "ok": False,
                "error": "FloodWaitError",
                "retry_after": exc.seconds,
                "message": (
                    f"Telegram требует подождать {exc.seconds} секунд. "
                    "Не ретрай раньше — иначе бан."
                ),
            }
        except RPCError as exc:
            latency_ms = int((time.monotonic() - start) * 1000)
            logger.warning(
                "tool=%s status=rpc_error code=%d latency_ms=%d msg=%s",
                tool_name,
                getattr(exc, "code", 0),
                latency_ms,
                exc.message,
            )
            return {
                "ok": False,
                "error": type(exc).__name__,
                "code": getattr(exc, "code", None),
                "message": exc.message,
            }
        except Exception as exc:
            latency_ms = int((time.monotonic() - start) * 1000)
            logger.exception("tool=%s status=exception latency_ms=%d", tool_name, latency_ms)
            return {
                "ok": False,
                "error": type(exc).__name__,
                "message": str(exc),
            }

    return wrapper
