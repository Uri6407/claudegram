"""List — list_chats, list_channels, list_groups, list_bots, dialog_stats, get_drafts."""

from __future__ import annotations

from typing import Any, Literal

from server.client import get_client
from server.formatters import dialog_brief, dialog_compact
from server.tools._common import READ_ONLY

DialogKind = Literal["channel", "supergroup", "group", "user", "bot", "all"]
ArchiveScope = Literal["main", "archive", "both"]
PinFilter = Literal["any", "pinned", "unpinned"]


async def _fetch_dialogs(
    *,
    limit: int,
    folder_mode: ArchiveScope,
    only_unread: bool = False,
    compact: bool = False,
) -> list[dict[str, Any]]:
    """Внутренний fetcher — нормализует логику folder/archived."""
    client = await get_client()
    if folder_mode == "main":
        dialogs = await client.get_dialogs(limit=limit, folder=0)
    elif folder_mode == "archive":
        dialogs = await client.get_dialogs(limit=limit, folder=1)
    else:  # both — берём всё через archived=True
        dialogs = await client.get_dialogs(limit=limit, archived=True)
    serializer = dialog_compact if compact else dialog_brief
    out = [serializer(d) for d in dialogs]
    if only_unread:
        out = [d for d in out if d["unread_count"] > 0]
    return out


def _filter_kind(dialogs: list[dict[str, Any]], kind: DialogKind) -> list[dict[str, Any]]:
    if kind == "all":
        return dialogs
    if kind == "bot":
        return [
            d
            for d in dialogs
            if d.get("is_bot") or d.get("entity", {}).get("is_bot")
        ]
    if kind == "user":
        # PM-юзеры (не боты)
        return [
            d
            for d in dialogs
            if (d.get("type") == "user" or d.get("entity", {}).get("type") == "user")
            and not (d.get("is_bot") or d.get("entity", {}).get("is_bot"))
        ]
    return [
        d
        for d in dialogs
        if (d.get("type") == kind or d.get("entity", {}).get("type") == kind)
    ]


def _filter_pinned(dialogs: list[dict[str, Any]], pin: PinFilter) -> list[dict[str, Any]]:
    if pin == "any":
        return dialogs
    if pin == "pinned":
        return [d for d in dialogs if d.get("is_pinned")]
    return [d for d in dialogs if not d.get("is_pinned")]


def _filter_participants(
    dialogs: list[dict[str, Any]],
    min_p: int | None,
    max_p: int | None,
) -> list[dict[str, Any]]:
    if min_p is None and max_p is None:
        return dialogs
    out = []
    for d in dialogs:
        p = d.get("participants_count") or d.get("entity", {}).get("participants_count")
        if p is None:
            continue
        if min_p is not None and p < min_p:
            continue
        if max_p is not None and p > max_p:
            continue
        out.append(d)
    return out


def register(mcp: Any) -> None:
    @mcp.tool(annotations=READ_ONLY)
    async def list_chats(
        limit: int = 50,
        archived: bool = False,
        only_unread: bool = False,
        ignore_pinned: bool = False,
        compact: bool = False,
    ) -> list[dict[str, Any]]:
        """Список всех диалогов (юзеры/боты/группы/каналы — без фильтра).

        Args:
            compact: True — облегчённая форма (id/name/type/is_pinned/unread/...) ~85% меньше payload.

        Для типизированных списков см. `list_channels`, `list_groups`, `list_bots`.
        """
        client = await get_client()
        folder = 1 if archived else 0
        dialogs = await client.get_dialogs(
            limit=limit,
            archived=archived,
            folder=folder,
            ignore_pinned=ignore_pinned,
        )
        serializer = dialog_compact if compact else dialog_brief
        result = [serializer(d) for d in dialogs]
        if only_unread:
            result = [d for d in result if d["unread_count"] > 0]
        return result

    @mcp.tool(annotations=READ_ONLY)
    async def list_channels(
        archived: ArchiveScope = "both",
        limit: int = 500,
        only_unread: bool = False,
        is_pinned: PinFilter = "any",
        min_participants: int | None = None,
        max_participants: int | None = None,
        compact: bool = True,
    ) -> list[dict[str, Any]]:
        """Только broadcast-каналы (без supergroup'ов).

        Args:
            archived: 'main' — основной список, 'archive' — только архив,
                'both' — всё. Default 'both' — включает архивные.
            limit: верхняя граница по сырому фетчу диалогов до фильтрации.
            only_unread: True — только с unread_count > 0.
            is_pinned: 'any' / 'pinned' / 'unpinned'.
            min_participants / max_participants: фильтр по подписчикам.
            compact: default True — payload в ~5x меньше.
        """
        all_dialogs = await _fetch_dialogs(
            limit=limit, folder_mode=archived, only_unread=only_unread, compact=compact
        )
        out = _filter_kind(all_dialogs, "channel")
        out = _filter_pinned(out, is_pinned)
        out = _filter_participants(out, min_participants, max_participants)
        return out

    @mcp.tool(annotations=READ_ONLY)
    async def list_groups(
        archived: ArchiveScope = "both",
        limit: int = 500,
        include_supergroups: bool = True,
        only_unread: bool = False,
        is_pinned: PinFilter = "any",
        min_participants: int | None = None,
        max_participants: int | None = None,
        compact: bool = True,
    ) -> list[dict[str, Any]]:
        """Группы и супергруппы.

        Args:
            include_supergroups: False — только old-style basic groups.
            is_pinned/min_participants/max_participants/compact — см. list_channels.
        """
        all_dialogs = await _fetch_dialogs(
            limit=limit, folder_mode=archived, only_unread=only_unread, compact=compact
        )
        if include_supergroups:
            out = [
                d
                for d in all_dialogs
                if (d.get("type") in ("group", "supergroup")
                    or d.get("entity", {}).get("type") in ("group", "supergroup"))
            ]
        else:
            out = _filter_kind(all_dialogs, "group")
        out = _filter_pinned(out, is_pinned)
        out = _filter_participants(out, min_participants, max_participants)
        return out

    @mcp.tool(annotations=READ_ONLY)
    async def list_bots(
        archived: ArchiveScope = "both",
        limit: int = 500,
        is_pinned: PinFilter = "any",
        compact: bool = True,
    ) -> list[dict[str, Any]]:
        """PM-боты в диалогах."""
        all_dialogs = await _fetch_dialogs(
            limit=limit, folder_mode=archived, compact=compact
        )
        out = _filter_kind(all_dialogs, "bot")
        return _filter_pinned(out, is_pinned)

    @mcp.tool(annotations=READ_ONLY)
    async def list_pm_users(
        archived: ArchiveScope = "both",
        limit: int = 500,
        is_pinned: PinFilter = "any",
        only_unread: bool = False,
        compact: bool = True,
    ) -> list[dict[str, Any]]:
        """Личные чаты с юзерами (без ботов)."""
        all_dialogs = await _fetch_dialogs(
            limit=limit, folder_mode=archived, only_unread=only_unread, compact=compact
        )
        out = _filter_kind(all_dialogs, "user")
        return _filter_pinned(out, is_pinned)

    @mcp.tool(annotations=READ_ONLY)
    async def dialog_stats() -> dict[str, int]:
        """Счётчики диалогов по типам — без payload, 1 запрос.

        Возвращает: total / pm_users / bots / channels / supergroups /
        basic_groups / archived / pinned / unread.
        """
        all_dialogs = await _fetch_dialogs(
            limit=2000, folder_mode="both", compact=True
        )
        stats: dict[str, int] = {
            "total": len(all_dialogs),
            "pm_users": 0,
            "bots": 0,
            "channels": 0,
            "supergroups": 0,
            "basic_groups": 0,
            "archived": 0,
            "pinned": 0,
            "unread": 0,
        }
        for d in all_dialogs:
            t = d.get("type")
            if d.get("is_bot"):
                stats["bots"] += 1
            elif t == "user":
                stats["pm_users"] += 1
            elif t == "channel":
                stats["channels"] += 1
            elif t == "supergroup":
                stats["supergroups"] += 1
            elif t == "group":
                stats["basic_groups"] += 1
            if d.get("is_archived"):
                stats["archived"] += 1
            if d.get("is_pinned"):
                stats["pinned"] += 1
            if d.get("unread_count", 0) > 0:
                stats["unread"] += 1
        return stats

    @mcp.tool(annotations=READ_ONLY)
    async def get_dialogs_by_ids(
        chat_ids: list[int],
        compact: bool = True,
    ) -> list[dict[str, Any]]:
        """Получить informация о N конкретных диалогах одним вызовом.

        Полезно для batch-проверки is_pinned/unread перед массовой операцией.
        """
        client = await get_client()
        out: list[dict[str, Any]] = []
        all_dialogs = await client.get_dialogs(limit=2000, archived=True)
        wanted = set(chat_ids)
        serializer = dialog_compact if compact else dialog_brief
        for d in all_dialogs:
            if d.id in wanted:
                out.append(serializer(d))
        return out

    @mcp.tool(annotations=READ_ONLY)
    async def get_drafts() -> list[dict[str, Any]]:
        """Список несохранённых черновиков по всем чатам."""
        client = await get_client()
        drafts = await client.get_drafts()
        return [
            {
                "entity_id": d.entity.id if d.entity else None,
                "text": d.text or "",
                "date": d.date.isoformat() if d.date else None,
                "raw_text": d.raw_text or "",
            }
            for d in drafts
        ]
