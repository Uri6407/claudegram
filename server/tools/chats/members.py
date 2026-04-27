"""Members — участники, kick, ban, restrict, promote/demote."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import Context
from telethon.tl.functions.channels import (
    EditAdminRequest,
    EditBannedRequest,
)
from telethon.tl.types import (
    ChannelParticipantsAdmins,
    ChannelParticipantsBanned,
    ChannelParticipantsBots,
    ChannelParticipantsKicked,
    ChannelParticipantsRecent,
    ChatAdminRights,
    ChatBannedRights,
)

from server.client import get_client
from server.formatters import entity_brief
from server.tools._common import (
    DESTRUCTIVE,
    NON_DESTRUCTIVE,
    READ_ONLY,
    clamp,
    confirm_or_abort,
    normalize_chat,
)


def register(mcp: Any) -> None:
    @mcp.tool(annotations=READ_ONLY)
    async def get_participants(
        chat: int | str,
        limit: int = 100,
        search: str = "",
        filter_admin: bool = False,
        filter_kicked: bool = False,
        filter_banned: bool = False,
        filter_bots: bool = False,
        filter_recent: bool = False,
        aggressive: bool = False,
        ctx: Context | None = None,
    ) -> list[dict[str, Any]]:
        """Список участников группы/канала.

        Args:
            limit: 1-200.
            filter_admin/kicked/banned/bots/recent: показать только эту категорию.
            aggressive: для каналов с >200 участников — итерировать через
                индексные search-страницы (медленнее, но даёт больше).
        """
        client = await get_client()
        target = clamp(limit, 1, 200)
        kwargs: dict[str, Any] = {"limit": target, "aggressive": aggressive}
        if search:
            kwargs["search"] = search
        if filter_admin:
            kwargs["filter"] = ChannelParticipantsAdmins()
        elif filter_kicked:
            kwargs["filter"] = ChannelParticipantsKicked(search)
        elif filter_banned:
            kwargs["filter"] = ChannelParticipantsBanned(search)
        elif filter_bots:
            kwargs["filter"] = ChannelParticipantsBots()
        elif filter_recent:
            kwargs["filter"] = ChannelParticipantsRecent()

        out: list[dict[str, Any]] = []
        async for p in client.iter_participants(normalize_chat(chat), **kwargs):
            out.append(entity_brief(p))
            if ctx is not None and len(out) % 50 == 0:
                await ctx.report_progress(
                    progress=float(len(out)),
                    total=float(target),
                    message=f"участников {len(out)}/{target}",
                )
        return out

    @mcp.tool(annotations=DESTRUCTIVE)
    async def kick_participant(
        chat: int | str, user: int | str, ctx: Context | None = None
    ) -> dict[str, Any]:
        """Кикнуть участника из чата (он сможет вернуться)."""
        if (abort := await confirm_or_abort(ctx, action="kick", target=f"{user} from {chat}")):
            return abort
        client = await get_client()
        await client.kick_participant(normalize_chat(chat), normalize_chat(user))
        return {"ok": True}

    @mcp.tool(annotations=DESTRUCTIVE)
    async def ban_participant(
        chat: int | str, user: int | str, ctx: Context | None = None
    ) -> dict[str, Any]:
        """Забанить участника навсегда — он не сможет вернуться."""
        if (
            abort := await confirm_or_abort(
                ctx,
                action="ban (permanent)",
                target=f"{user} from {chat}",
                extra="Юзер не сможет вернуться без явного unban.",
            )
        ):
            return abort
        client = await get_client()
        chat_peer = await client.get_input_entity(normalize_chat(chat))
        user_peer = await client.get_input_entity(normalize_chat(user))
        await client(
            EditBannedRequest(
                channel=chat_peer,
                participant=user_peer,
                banned_rights=ChatBannedRights(until_date=None, view_messages=True),
            )
        )
        return {"ok": True}

    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def unban_participant(chat: int | str, user: int | str) -> dict[str, Any]:
        """Снять бан с участника."""
        client = await get_client()
        chat_peer = await client.get_input_entity(normalize_chat(chat))
        user_peer = await client.get_input_entity(normalize_chat(user))
        await client(
            EditBannedRequest(
                channel=chat_peer,
                participant=user_peer,
                banned_rights=ChatBannedRights(until_date=None),
            )
        )
        return {"ok": True}

    @mcp.tool(annotations=DESTRUCTIVE)
    async def restrict_participant(
        chat: int | str,
        user: int | str,
        until_unix: int | None = None,
        send_messages: bool = False,
        send_media: bool = False,
        send_stickers: bool = False,
        send_gifs: bool = False,
        send_polls: bool = False,
        embed_links: bool = False,
        invite_users: bool = False,
        pin_messages: bool = False,
        change_info: bool = False,
    ) -> dict[str, Any]:
        """Ограничить права участника супергруппы (read-only mute и т.п.).

        В ChatBannedRights каждый bool=True означает ЗАПРЕТ соответствующего действия.
        send_*=False → разрешено отправлять (стандартный участник).
        send_*=True → запрещено (mute).

        Args:
            until_unix: до какого UNIX timestamp; None = навсегда.
        """
        from datetime import datetime

        client = await get_client()
        chat_peer = await client.get_input_entity(normalize_chat(chat))
        user_peer = await client.get_input_entity(normalize_chat(user))
        until_date = datetime.fromtimestamp(until_unix) if until_unix else None
        await client(
            EditBannedRequest(
                channel=chat_peer,
                participant=user_peer,
                banned_rights=ChatBannedRights(
                    until_date=until_date,
                    send_messages=send_messages,
                    send_media=send_media,
                    send_stickers=send_stickers,
                    send_gifs=send_gifs,
                    send_polls=send_polls,
                    embed_links=embed_links,
                    invite_users=invite_users,
                    pin_messages=pin_messages,
                    change_info=change_info,
                ),
            )
        )
        return {"ok": True}

    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def promote_admin(
        chat: int | str,
        user: int | str,
        rank: str = "",
        change_info: bool = True,
        post_messages: bool = True,
        edit_messages: bool = True,
        delete_messages: bool = True,
        ban_users: bool = True,
        invite_users: bool = True,
        pin_messages: bool = True,
        add_admins: bool = False,
        anonymous: bool = False,
        manage_call: bool = False,
        manage_topics: bool = False,
        post_stories: bool = False,
        edit_stories: bool = False,
        delete_stories: bool = False,
        manage_direct_messages: bool = False,
    ) -> dict[str, Any]:
        """Назначить участника администратором с заданными правами."""
        client = await get_client()
        chat_peer = await client.get_input_entity(normalize_chat(chat))
        user_peer = await client.get_input_entity(normalize_chat(user))
        rights = ChatAdminRights(
            change_info=change_info,
            post_messages=post_messages,
            edit_messages=edit_messages,
            delete_messages=delete_messages,
            ban_users=ban_users,
            invite_users=invite_users,
            pin_messages=pin_messages,
            add_admins=add_admins,
            anonymous=anonymous,
            manage_call=manage_call,
            manage_topics=manage_topics,
            post_stories=post_stories,
            edit_stories=edit_stories,
            delete_stories=delete_stories,
            manage_direct_messages=manage_direct_messages,
        )
        await client(
            EditAdminRequest(
                channel=chat_peer,
                user_id=user_peer,
                admin_rights=rights,
                rank=rank,
            )
        )
        return {"ok": True, "rank": rank}

    @mcp.tool(annotations=DESTRUCTIVE)
    async def demote_admin(chat: int | str, user: int | str) -> dict[str, Any]:
        """Снять права админа (все флаги в False)."""
        client = await get_client()
        chat_peer = await client.get_input_entity(normalize_chat(chat))
        user_peer = await client.get_input_entity(normalize_chat(user))
        await client(
            EditAdminRequest(
                channel=chat_peer,
                user_id=user_peer,
                admin_rights=ChatAdminRights(),
                rank="",
            )
        )
        return {"ok": True}
