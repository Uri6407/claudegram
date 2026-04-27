"""Notify — mute, mark_read, удаление диалога."""

from __future__ import annotations

from datetime import UTC
from typing import Any

from mcp.server.fastmcp import Context
from telethon.tl.functions.account import UpdateNotifySettingsRequest
from telethon.tl.types import InputNotifyPeer, InputPeerNotifySettings

from server.client import get_client
from server.tools._common import DESTRUCTIVE, NON_DESTRUCTIVE, confirm_or_abort, normalize_chat


def register(mcp: Any) -> None:
    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def mark_read(
        chat: int | str, max_id: int = 0, clear_mentions: bool = False
    ) -> dict[str, Any]:
        """Пометить сообщения чата прочитанными.

        Args:
            max_id: до какого id (0 — все).
            clear_mentions: ещё и сбросить @упоминания.
        """
        client = await get_client()
        ok = await client.send_read_acknowledge(
            normalize_chat(chat), max_id=max_id, clear_mentions=clear_mentions
        )
        return {"ok": bool(ok)}

    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def mute_dialog(
        chat: int | str,
        mute_until_unix: int | None = None,
        show_previews: bool = True,
        silent: bool = True,
        stories_muted: bool | None = None,
    ) -> dict[str, Any]:
        """Замьютить уведомления чата.

        Args:
            mute_until_unix: до какого UNIX timestamp (UTC). None = навсегда (2^31).
            show_previews: показывать текст превью в notification.
            silent: без звука уведомлений.
            stories_muted: True — также замьютить stories этого источника.
        """
        from datetime import datetime

        client = await get_client()
        peer = await client.get_input_entity(normalize_chat(chat))
        mute_until = (
            datetime.fromtimestamp(mute_until_unix, tz=UTC)
            if mute_until_unix
            else datetime.fromtimestamp(2**31 - 1, tz=UTC)
        )
        await client(
            UpdateNotifySettingsRequest(
                peer=InputNotifyPeer(peer=peer),
                settings=InputPeerNotifySettings(
                    show_previews=show_previews,
                    silent=silent,
                    mute_until=mute_until,
                    stories_muted=stories_muted,
                ),
            )
        )
        return {"ok": True, "muted_until_unix": int(mute_until.timestamp())}

    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def unmute_dialog(chat: int | str) -> dict[str, Any]:
        """Снять mute с чата (вернуть дефолтные настройки)."""
        client = await get_client()
        peer = await client.get_input_entity(normalize_chat(chat))
        await client(
            UpdateNotifySettingsRequest(
                peer=InputNotifyPeer(peer=peer),
                settings=InputPeerNotifySettings(mute_until=None),
            )
        )
        return {"ok": True}

    @mcp.tool(annotations=DESTRUCTIVE)
    async def delete_dialog(
        chat: int | str, revoke: bool = False, ctx: Context | None = None
    ) -> dict[str, Any]:
        """Покинуть чат/канал или удалить личный диалог.

        Args:
            revoke: True — удалить переписку и у собеседника (только PM).
        """
        extra = "revoke=True — удалит и у собеседника." if revoke else ""
        if (
            abort := await confirm_or_abort(
                ctx, action="delete_dialog", target=str(chat), extra=extra
            )
        ):
            return abort
        client = await get_client()
        await client.delete_dialog(normalize_chat(chat), revoke=revoke)
        return {"ok": True, "revoke": revoke}
