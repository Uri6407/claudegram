"""Утилиты, общие для всех tool-модулей.

Этот модуль — единственная точка для shared helpers. Не зависит от других
tool-модулей и не импортирует Telethon, чтобы избежать циклов.
"""

from __future__ import annotations

from typing import Any, Literal

from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations
from pydantic import BaseModel, Field

ParseMode = Literal["markdown", "html", "none"]

# Annotations для подсказок клиенту (MCP 2025 spec).
# openWorldHint=True — все Telegram tools работают с внешним миром (не sandbox).
READ_ONLY = ToolAnnotations(
    readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=True
)
NON_DESTRUCTIVE = ToolAnnotations(
    readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=True
)
DESTRUCTIVE = ToolAnnotations(
    readOnlyHint=False, destructiveHint=True, idempotentHint=False, openWorldHint=True
)
IDEMPOTENT_WRITE = ToolAnnotations(
    readOnlyHint=False, destructiveHint=False, idempotentHint=True, openWorldHint=True
)


class ConfirmDestructive(BaseModel):
    """Схема elicit-запроса для деструктивных операций."""

    confirm: bool = Field(
        description="Подтвердить выполнение деструктивной операции (true/false)",
    )


async def confirm_or_abort(
    ctx: Context | None,
    *,
    action: str,
    target: str,
    extra: str = "",
) -> dict[str, Any] | None:
    """Запросить у клиента подтверждение через `ctx.elicit`.

    Возвращает dict с `ok=False` если юзер отказался / клиент не поддерживает
    elicitation; None — если подтверждено и можно продолжать.

    Если `ctx` is None (вызов вне MCP-контекста, например в тестах) — пропускает
    проверку и возвращает None, оставляя контроль на bash-хуки.
    """
    if ctx is None:
        return None
    msg = f"Подтвердить: {action} → {target}"
    if extra:
        msg += f"\n{extra}"
    try:
        await ctx.warning(f"destructive op pending: {action} on {target}")
        result = await ctx.elicit(message=msg, schema=ConfirmDestructive)
    except Exception:
        return None
    if getattr(result, "action", None) != "accept":
        return {
            "ok": False,
            "aborted": True,
            "reason": f"User declined elicitation ({getattr(result, 'action', '?')})",
        }
    data = getattr(result, "data", None)
    if data is None or not getattr(data, "confirm", False):
        return {"ok": False, "aborted": True, "reason": "User did not confirm"}
    return None


def parse_mode_arg(mode: ParseMode) -> str | None:
    """`'none'` → None для Telethon (plain text), иначе сам режим."""
    return None if mode == "none" else mode


def normalize_chat(chat_id: int | str | None) -> int | str | None:
    """Telethon принимает int (id), str (@username), или приглашение.
    Если пришла строка-число — конвертируем в int.
    None пропускаем (для глобального поиска и т.п.).
    """
    if chat_id is None:
        return None
    if isinstance(chat_id, str) and chat_id.lstrip("-").isdigit():
        return int(chat_id)
    return chat_id


def clamp(value: int, lo: int, hi: int) -> int:
    return max(lo, min(value, hi))


def to_jsonable(obj: Any) -> Any:
    """Безопасная JSON-сериализация Telethon-объектов через .to_dict().

    Используется в advanced/raw и peers/lookup для возврата произвольных
    Telethon-объектов как JSON-friendly dict'ов.
    """
    if hasattr(obj, "to_dict"):
        d = obj.to_dict()
        if isinstance(d, dict):
            return {k: to_jsonable(v) for k, v in d.items() if k != "_"}
        return d
    if isinstance(obj, list):
        return [to_jsonable(x) for x in obj]
    if isinstance(obj, dict):
        return {k: to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, str | int | float | bool | type(None)):
        return obj
    if isinstance(obj, bytes):
        return obj.hex()
    try:
        return str(obj)
    except Exception:
        return repr(obj)


