"""Invites — join, leave, экспорт invite-link."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import Context
from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest
from telethon.tl.functions.messages import ExportChatInviteRequest

from server.client import get_client
from server.formatters import entity_brief
from server.tools._common import DESTRUCTIVE, NON_DESTRUCTIVE, confirm_or_abort, normalize_chat


def register(mcp: Any) -> None:
    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def join_chat(chat: int | str) -> dict[str, Any]:
        """Войти в публичный канал/группу (по @username или ссылке-приглашению)."""
        client = await get_client()
        peer = await client.get_input_entity(normalize_chat(chat))
        result = await client(JoinChannelRequest(channel=peer))
        chats = getattr(result, "chats", []) or []
        return {"ok": True, "chats": [entity_brief(c) for c in chats]}

    @mcp.tool(annotations=DESTRUCTIVE)
    async def leave_chat(chat: int | str, ctx: Context | None = None) -> dict[str, Any]:
        """Выйти из канала/супергруппы."""
        if (abort := await confirm_or_abort(ctx, action="leave_chat", target=str(chat))):
            return abort
        client = await get_client()
        peer = await client.get_input_entity(normalize_chat(chat))
        await client(LeaveChannelRequest(channel=peer))
        return {"ok": True}

    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def export_chat_invite(
        chat: int | str,
        expire_unix: int | None = None,
        usage_limit: int | None = None,
        request_needed: bool = False,
        title: str = "",
    ) -> dict[str, Any]:
        """Создать invite-ссылку на чат/канал.

        Args:
            expire_unix: до когда действует. None = бессрочно.
            usage_limit: на сколько использований.
            request_needed: True — кандидаты ждут approval.
            title: метка ссылки (для аудита в админке).
        """
        from datetime import datetime

        client = await get_client()
        peer = await client.get_input_entity(normalize_chat(chat))
        result = await client(
            ExportChatInviteRequest(
                peer=peer,
                expire_date=datetime.fromtimestamp(expire_unix) if expire_unix else None,
                usage_limit=usage_limit,
                request_needed=request_needed,
                title=title or None,
            )
        )
        return {
            "ok": True,
            "link": getattr(result, "link", None),
            "title": getattr(result, "title", None),
            "usage_limit": getattr(result, "usage_limit", None),
        }
