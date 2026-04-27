"""Raw API — escape hatch для любого Telegram MTProto-метода.

Telegram API содержит сотни методов, не все обёрнуты в Telethon high-level API.
Этот tool даёт доступ ко всему: указываешь полный путь к классу
(`telethon.tl.functions.<module>.<MethodNameRequest>`) и dict аргументов.

Полный список схемы Telegram API:
https://core.telegram.org/methods
https://docs.telethon.dev/en/stable/quick-references/objects-reference.html
"""

from __future__ import annotations

import importlib
import json
from typing import Any

from server.client import get_client
from server.tools._common import NON_DESTRUCTIVE, to_jsonable

# Backwards-compat alias для тестов и старых импортёров
_to_jsonable = to_jsonable


def register(mcp: Any) -> None:
    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def invoke_raw(
        method_path: str,
        kwargs_json: str = "{}",
    ) -> dict[str, Any]:
        """Вызвать произвольный Telegram MTProto-метод через Telethon.

        Args:
            method_path: полный python-путь, например
                'telethon.tl.functions.users.GetFullUserRequest'.
            kwargs_json: JSON-строка с kwargs для конструктора метода.

        ⚠️ Опасный tool — может изменить состояние аккаунта или вызвать flood-wait.
        Используй только когда нужного high-level метода нет.
        """
        client = await get_client()

        try:
            module_path, class_name = method_path.rsplit(".", 1)
            module = importlib.import_module(module_path)
            cls = getattr(module, class_name)
        except (ValueError, ImportError, AttributeError) as exc:
            return {"ok": False, "error": f"Не могу импортировать {method_path}: {exc}"}

        try:
            kwargs = json.loads(kwargs_json) if kwargs_json else {}
        except json.JSONDecodeError as exc:
            return {"ok": False, "error": f"Невалидный JSON в kwargs: {exc}"}

        if not isinstance(kwargs, dict):
            return {"ok": False, "error": "kwargs_json должен быть JSON object'ом"}

        try:
            request = cls(**kwargs)
        except TypeError as exc:
            return {"ok": False, "error": f"Не подходящие аргументы для {class_name}: {exc}"}

        try:
            result = await client(request)
        except Exception as exc:
            return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

        return {"ok": True, "result": to_jsonable(result)}
