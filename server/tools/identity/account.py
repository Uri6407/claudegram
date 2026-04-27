"""Account — собственный профиль (me, имя, username, online status, full info)."""

from __future__ import annotations

from typing import Any

from telethon.tl.functions.account import (
    UpdateProfileRequest,
    UpdateStatusRequest,
    UpdateUsernameRequest,
)
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import InputUserSelf

from server.client import get_client
from server.formatters import entity_brief
from server.models import EntityBrief
from server.tools._common import NON_DESTRUCTIVE, READ_ONLY, normalize_chat


def register(mcp: Any) -> None:
    @mcp.tool(annotations=READ_ONLY)
    async def get_me() -> EntityBrief:
        """Информация о текущем авторизованном пользователе."""
        client = await get_client()
        me = await client.get_me()
        return EntityBrief(**entity_brief(me))

    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def update_profile(
        first_name: str | None = None,
        last_name: str | None = None,
        about: str | None = None,
    ) -> dict[str, Any]:
        """Изменить отображаемое имя/фамилию/био собственного профиля.

        None в поле = не менять. Пустая строка = очистить.
        """
        client = await get_client()
        user = await client(
            UpdateProfileRequest(
                first_name=first_name,
                last_name=last_name,
                about=about,
            )
        )
        return entity_brief(user)

    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def set_online(offline: bool = False) -> dict[str, Any]:
        """Установить online/offline статус.

        Args:
            offline: True — пометить аккаунт как offline (не показывать "online" зелёный кружок).
        """
        client = await get_client()
        ok = await client(UpdateStatusRequest(offline=offline))
        return {"ok": bool(ok)}

    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def update_username(username: str) -> dict[str, Any]:
        """Сменить @username аккаунта (пустая строка — снять username)."""
        client = await get_client()
        user = await client(UpdateUsernameRequest(username=username))
        return entity_brief(user)

    @mcp.tool(annotations=READ_ONLY)
    async def get_full_user(user: int | str | None = None) -> dict[str, Any]:
        """Расширенная инфа о пользователе (bio, общие чаты, premium, etc).

        Args:
            user: id/@username; None = я сам.
        """
        client = await get_client()
        if user is None:
            input_user = InputUserSelf()
        else:
            input_user = await client.get_input_entity(normalize_chat(user))
        result = await client(GetFullUserRequest(id=input_user))
        full = result.full_user
        users = {u.id: u for u in getattr(result, "users", [])}
        target = users.get(full.id, None) if hasattr(full, "id") else None
        out: dict[str, Any] = {
            "about": getattr(full, "about", None) or "",
            "common_chats_count": getattr(full, "common_chats_count", 0),
            "blocked": getattr(full, "blocked", False),
            "phone_calls_available": getattr(full, "phone_calls_available", False),
            "video_calls_available": getattr(full, "video_calls_available", False),
            "premium": getattr(full, "premium", False),
            "translations_disabled": getattr(full, "translations_disabled", False),
            "stories_pinned_available": getattr(full, "stories_pinned_available", False),
        }
        if target:
            out["entity"] = entity_brief(target)
        return out
