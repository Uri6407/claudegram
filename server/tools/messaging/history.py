"""History — get_history, search_messages."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import Context
from mcp.types import ResourceLink, TextContent
from pydantic import AnyUrl

from server.client import get_client
from server.formatters import message_brief
from server.tools._common import READ_ONLY, clamp, normalize_chat


def register(mcp: Any) -> None:
    @mcp.tool(annotations=READ_ONLY)
    async def get_history(
        chat: int | str,
        limit: int = 50,
        offset_id: int = 0,
        min_id: int = 0,
        max_id: int = 0,
        from_user: int | str | None = None,
        reverse: bool = False,
        ids: list[int] | None = None,
        reply_to: int | None = None,
        filter_type: str | None = None,
        scheduled: bool = False,
        ctx: Context | None = None,
    ) -> list[dict[str, Any]]:
        """Сообщения чата (новые → старые по умолчанию).

        Args:
            limit: 1-200.
            offset_id: вернуть старше указанного id (пагинация).
            min_id / max_id: границы id.
            from_user: id/@username — фильтровать по отправителю.
            reverse: True — от старых к новым.
            ids: получить конкретные сообщения по id (без пагинации).
            reply_to: показать сообщения треда/комментариев под этим id.
            filter_type: media-фильтр: `photo`, `video`, `document`, `voice`,
                `music`, `gif`, `url`, `chat_photo`, `phone_call`, `roundvideo`, `mymentions`.
            scheduled: показать запланированные (а не уже отправленные) сообщения.
        """
        from telethon.tl import types as tg_types

        filter_map = {
            "photo": tg_types.InputMessagesFilterPhotos,
            "video": tg_types.InputMessagesFilterVideo,
            "document": tg_types.InputMessagesFilterDocument,
            "voice": tg_types.InputMessagesFilterVoice,
            "music": tg_types.InputMessagesFilterMusic,
            "gif": tg_types.InputMessagesFilterGif,
            "url": tg_types.InputMessagesFilterUrl,
            "chat_photo": tg_types.InputMessagesFilterChatPhotos,
            "phone_call": tg_types.InputMessagesFilterPhoneCalls,
            "roundvideo": tg_types.InputMessagesFilterRoundVideo,
            "mymentions": tg_types.InputMessagesFilterMyMentions,
        }
        msg_filter = (
            filter_map[filter_type]() if filter_type and filter_type in filter_map else None
        )

        client = await get_client()
        target_total = clamp(limit, 1, 200)

        if ids is not None:
            messages = await client.get_messages(normalize_chat(chat), ids=ids)
            return [message_brief(m) for m in (messages if isinstance(messages, list) else [messages]) if m]

        out: list[dict[str, Any]] = []
        async for msg in client.iter_messages(
            normalize_chat(chat),
            limit=target_total,
            offset_id=offset_id,
            min_id=min_id,
            max_id=max_id,
            from_user=normalize_chat(from_user) if from_user else None,
            reverse=reverse,
            reply_to=reply_to,
            filter=msg_filter,
            scheduled=scheduled,
        ):
            out.append(message_brief(msg))
            if ctx is not None and len(out) % 25 == 0:
                await ctx.report_progress(
                    progress=float(len(out)),
                    total=float(target_total),
                    message=f"Получено {len(out)}/{target_total} сообщений",
                )
        if ctx is not None:
            await ctx.report_progress(
                progress=float(len(out)), total=float(target_total), message="готово"
            )
        return out

    @mcp.tool(annotations=READ_ONLY)
    async def get_history_with_links(
        chat: int | str,
        limit: int = 50,
        ctx: Context | None = None,
    ) -> list[TextContent | ResourceLink]:
        """Гибрид: компактные text-блоки + ResourceLink на каждое сообщение.

        Клиент видит дешёвый список и может догрузить полное сообщение
        через `telegram://msg/{chat_id}/{message_id}` ресурс.
        """
        client = await get_client()
        target = clamp(limit, 1, 200)
        chat_norm = normalize_chat(chat)
        blocks: list[TextContent | ResourceLink] = []
        async for msg in client.iter_messages(chat_norm, limit=target):
            brief = message_brief(msg)
            preview = (brief["text"] or f"[{brief.get('media_type') or 'media'}]")[:120]
            chat_id = brief["chat_id"]
            msg_id = brief["id"]
            blocks.append(
                TextContent(
                    type="text",
                    text=f"#{msg_id} [{brief['date']}] {brief.get('sender_id')}: {preview}",
                )
            )
            blocks.append(
                ResourceLink(
                    type="resource_link",
                    uri=AnyUrl(f"telegram://msg/{chat_id}/{msg_id}"),
                    name=f"msg-{msg_id}",
                    description=f"Полный JSON сообщения {msg_id} из чата {chat_id}",
                    mimeType="application/json",
                )
            )
            if ctx is not None and (len(blocks) // 2) % 25 == 0:
                await ctx.report_progress(
                    progress=float(len(blocks) // 2),
                    total=float(target),
                    message=f"получено {len(blocks) // 2}/{target}",
                )
        return blocks

    @mcp.tool(annotations=READ_ONLY)
    async def search_messages(
        query: str,
        chat: int | str | None = None,
        limit: int = 50,
        from_user: int | str | None = None,
        ctx: Context | None = None,
    ) -> list[dict[str, Any]]:
        """Поиск сообщений по тексту глобально или в чате."""
        client = await get_client()
        target_total = clamp(limit, 1, 200)
        out: list[dict[str, Any]] = []
        async for msg in client.iter_messages(
            normalize_chat(chat),
            search=query,
            limit=target_total,
            from_user=normalize_chat(from_user) if from_user else None,
        ):
            out.append(message_brief(msg))
            if ctx is not None and len(out) % 20 == 0:
                await ctx.report_progress(
                    progress=float(len(out)),
                    total=float(target_total),
                    message=f"найдено {len(out)} совпадений",
                )
        return out
