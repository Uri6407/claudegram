"""Custom Dialog Folders (DialogFilter) — пользовательские папки чатов."""

from __future__ import annotations

from typing import Any

from telethon.tl.functions.messages import (
    GetDialogFiltersRequest,
    UpdateDialogFilterRequest,
)
from telethon.tl.types import DialogFilter

from server.client import get_client
from server.tools._common import DESTRUCTIVE, NON_DESTRUCTIVE, READ_ONLY, normalize_chat


def register(mcp: Any) -> None:
    @mcp.tool(annotations=READ_ONLY)
    async def get_dialog_filters() -> list[dict[str, Any]]:
        """Список кастомных папок диалогов (Folders в UI Telegram)."""
        client = await get_client()
        result = await client(GetDialogFiltersRequest())
        filters = getattr(result, "filters", []) or []
        out: list[dict[str, Any]] = []
        for f in filters:
            out.append(
                {
                    "id": getattr(f, "id", None),
                    "title": getattr(f, "title", None)
                    if isinstance(getattr(f, "title", None), str)
                    else (getattr(getattr(f, "title", None), "text", "") or ""),
                    "emoticon": getattr(f, "emoticon", None) or "",
                    "include_count": len(getattr(f, "include_peers", []) or []),
                    "exclude_count": len(getattr(f, "exclude_peers", []) or []),
                    "pinned_count": len(getattr(f, "pinned_peers", []) or []),
                    "contacts": getattr(f, "contacts", False),
                    "non_contacts": getattr(f, "non_contacts", False),
                    "groups": getattr(f, "groups", False),
                    "broadcasts": getattr(f, "broadcasts", False),
                    "bots": getattr(f, "bots", False),
                    "exclude_muted": getattr(f, "exclude_muted", False),
                    "exclude_read": getattr(f, "exclude_read", False),
                    "exclude_archived": getattr(f, "exclude_archived", False),
                }
            )
        return out

    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def create_dialog_filter(
        filter_id: int,
        title: str,
        included_chats: list[int | str],
        emoticon: str = "",
        contacts: bool = False,
        non_contacts: bool = False,
        groups: bool = False,
        broadcasts: bool = False,
        bots: bool = False,
        exclude_muted: bool = False,
        exclude_read: bool = False,
        exclude_archived: bool = False,
    ) -> dict[str, Any]:
        """Создать/обновить кастомную папку диалогов.

        Args:
            filter_id: уникальный id папки (2-255). 1 — резерв All.
            title: название (отображается в табе).
            emoticon: эмодзи иконки.
            included_chats: список id/@username включённых чатов.
            contacts/non_contacts/groups/broadcasts/bots: автоматически
                включать чаты этой категории.
            exclude_muted/read/archived: исключать соответствующие.
        """
        from telethon.tl.types import TextWithEntities

        client = await get_client()
        included_peers = [await client.get_input_entity(normalize_chat(c)) for c in included_chats]
        flt = DialogFilter(
            id=filter_id,
            title=TextWithEntities(text=title, entities=[]),
            pinned_peers=[],
            include_peers=included_peers,
            exclude_peers=[],
            emoticon=emoticon or None,
            contacts=contacts,
            non_contacts=non_contacts,
            groups=groups,
            broadcasts=broadcasts,
            bots=bots,
            exclude_muted=exclude_muted,
            exclude_read=exclude_read,
            exclude_archived=exclude_archived,
        )
        await client(UpdateDialogFilterRequest(id=filter_id, filter=flt))
        return {"ok": True, "filter_id": filter_id, "title": title}

    @mcp.tool(annotations=DESTRUCTIVE)
    async def delete_dialog_filter(filter_id: int) -> dict[str, Any]:
        """Удалить кастомную папку диалогов."""
        client = await get_client()
        await client(UpdateDialogFilterRequest(id=filter_id, filter=None))
        return {"ok": True, "deleted_id": filter_id}
