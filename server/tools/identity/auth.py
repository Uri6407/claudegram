"""Auth — интерактивный двухшаговый логин в Telegram через MCP-tools.

Реализует тот же flow, что `claudegram-auth`, но без необходимости в реальном
терминале: Claude вызывает `auth_request_code` → юзер передаёт SMS-код →
Claude вызывает `auth_submit_code(code)`. Если включён 2FA — повторно с
`password_2fa`. После успеха singleton MCP-клиент сбрасывается, чтобы все
другие tools подхватили свежую сессию.
"""

from __future__ import annotations

from typing import Any

from telethon import TelegramClient
from telethon.errors import (
    PhoneCodeExpiredError,
    PhoneCodeInvalidError,
    SessionPasswordNeededError,
)

from server.client import shutdown as shutdown_client
from server.config import Config
from server.tools._common import NON_DESTRUCTIVE

# Хранит in-flight TelegramClient между request_code и submit_code.
# Обнуляется после успешного логина или явного `auth_cancel`.
_auth_state: dict[str, Any] = {}


async def _release_in_flight() -> None:
    """Disconnect и убрать незавершённый auth-client."""
    client = _auth_state.pop("client", None)
    _auth_state.pop("phone_code_hash", None)
    if client is not None:
        try:
            await client.disconnect()
        except Exception:
            pass


def register(mcp: Any) -> None:
    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def auth_request_code() -> dict[str, Any]:
        """Шаг 1: запросить SMS-код у Telegram. Очищает предыдущий auth-state.

        Возвращает:
            ok: True если код отправлен
            code_sent: True
            phone: куда отправлен (масковано последние 4 цифры)
            already_authorized: True если сессия уже валидна (код не нужен)
        """
        cfg = Config.load()
        # Освободить старый MCP-singleton-клиент чтобы не было session-lock
        await shutdown_client()
        await _release_in_flight()

        client = TelegramClient(str(cfg.session_path), cfg.api_id, cfg.api_hash)
        await client.connect()
        try:
            if await client.is_user_authorized():
                me = await client.get_me()
                await client.disconnect()
                return {
                    "ok": True,
                    "already_authorized": True,
                    "self_id": me.id,
                    "username": me.username,
                    "first_name": me.first_name,
                }
            sent = await client.send_code_request(cfg.phone)
        except Exception as exc:
            try:
                await client.disconnect()
            except Exception:
                pass
            return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

        _auth_state["client"] = client
        _auth_state["phone_code_hash"] = sent.phone_code_hash
        masked = (
            f"{cfg.phone[:-4]}{'*' * 4}" if len(cfg.phone) > 4 else "***"
        )
        return {
            "ok": True,
            "code_sent": True,
            "phone": masked,
            "message": (
                "Telegram отправил код. Прочитай его и передай в "
                "auth_submit_code(code='12345')."
            ),
        }

    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def auth_submit_code(
        code: str,
        password_2fa: str = "",
    ) -> dict[str, Any]:
        """Шаг 2: отправить код (и опц. пароль 2FA).

        Args:
            code: 5-значный SMS-код из Telegram.
            password_2fa: пароль cloud-2FA если включён. Если опущен и 2FA
                требуется — вернётся ошибка с просьбой повторить.
        """
        if "client" not in _auth_state:
            return {
                "ok": False,
                "error": "Сначала вызови auth_request_code, потом передай код сюда.",
            }
        client: TelegramClient = _auth_state["client"]
        phone_code_hash: str = _auth_state["phone_code_hash"]
        cfg = Config.load()

        try:
            await client.sign_in(
                phone=cfg.phone,
                code=code,
                phone_code_hash=phone_code_hash,
            )
        except (PhoneCodeInvalidError, PhoneCodeExpiredError) as exc:
            return {
                "ok": False,
                "error": f"{type(exc).__name__}: {exc}",
                "hint": "Запроси новый код через auth_request_code.",
            }
        except SessionPasswordNeededError:
            if not password_2fa:
                return {
                    "ok": False,
                    "needs_2fa": True,
                    "error": (
                        "Cloud-2FA включён. Повтори вызов с "
                        "password_2fa='<твой пароль>'."
                    ),
                }
            try:
                await client.sign_in(password=password_2fa)
            except Exception as exc:
                return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
        except Exception as exc:
            return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

        try:
            me = await client.get_me()
        except Exception as exc:
            await _release_in_flight()
            return {"ok": False, "error": f"get_me failed: {exc}"}

        # Закрываем auth-client; следующий get_client() сделает свежий с той же session.
        await _release_in_flight()
        await shutdown_client()

        return {
            "ok": True,
            "authorized": True,
            "self_id": me.id,
            "username": me.username,
            "first_name": me.first_name,
            "session_path": f"{cfg.session_path}.session",
            "message": "Готово. Вызови health_check чтобы убедиться.",
        }

    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def auth_cancel() -> dict[str, Any]:
        """Отменить незавершённый auth-flow (если запросил код, но не ввёл)."""
        had = "client" in _auth_state
        await _release_in_flight()
        return {"ok": True, "cancelled": had}
