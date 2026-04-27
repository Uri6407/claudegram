"""Contacts — записная книжка + блок-листы."""

from __future__ import annotations

from typing import Any

from telethon.tl.functions.contacts import (
    AddContactRequest,
    BlockRequest,
    DeleteContactsRequest,
    GetBlockedRequest,
    GetContactsRequest,
    ImportContactsRequest,
    UnblockRequest,
)
from telethon.tl.types import InputPhoneContact

from server.client import get_client
from server.formatters import entity_brief
from server.tools._common import DESTRUCTIVE, NON_DESTRUCTIVE, READ_ONLY, clamp, normalize_chat


def register(mcp: Any) -> None:
    @mcp.tool(annotations=READ_ONLY)
    async def get_contacts() -> list[dict[str, Any]]:
        """Список всех контактов аккаунта."""
        client = await get_client()
        result = await client(GetContactsRequest(hash=0))
        return [entity_brief(u) for u in result.users]

    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def add_contact(
        user: int | str,
        first_name: str,
        last_name: str = "",
        phone: str = "",
        add_phone_privacy_exception: bool = False,
    ) -> dict[str, Any]:
        """Добавить пользователя в контакты.

        Args:
            user: id или @username существующего юзера.
            phone: опционально (можно пустое).
            add_phone_privacy_exception: разрешить юзеру видеть твой номер.
        """
        client = await get_client()
        peer = await client.get_input_entity(normalize_chat(user))
        result = await client(
            AddContactRequest(
                id=peer,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                add_phone_privacy_exception=add_phone_privacy_exception,
            )
        )
        users = getattr(result, "users", [])
        return {"ok": True, "users": [entity_brief(u) for u in users]}

    @mcp.tool(annotations=DESTRUCTIVE)
    async def delete_contact(user: int | str) -> dict[str, Any]:
        """Удалить пользователя из контактов."""
        client = await get_client()
        peer = await client.get_input_entity(normalize_chat(user))
        result = await client(DeleteContactsRequest(id=[peer]))
        return {"ok": True, "users_count": len(getattr(result, "users", []))}

    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def import_contacts(
        contacts: list[dict[str, str]],
    ) -> list[dict[str, Any]]:
        """Массовый импорт контактов по номерам телефона (без знания Telegram-ID).

        Args:
            contacts: список dict'ов с ключами `phone`, `first_name`, `last_name`.
        """
        client = await get_client()
        input_contacts = [
            InputPhoneContact(
                client_id=i,
                phone=c["phone"],
                first_name=c.get("first_name", ""),
                last_name=c.get("last_name", ""),
            )
            for i, c in enumerate(contacts)
        ]
        result = await client(ImportContactsRequest(contacts=input_contacts))
        return [entity_brief(u) for u in getattr(result, "users", [])]

    @mcp.tool(annotations=DESTRUCTIVE)
    async def block_user(
        user: int | str,
        my_stories_from: bool = False,
    ) -> dict[str, Any]:
        """Заблокировать пользователя — он не сможет писать.

        Args:
            my_stories_from: True — добавить только в story-blocklist.
        """
        client = await get_client()
        peer = await client.get_input_entity(normalize_chat(user))
        ok = await client(BlockRequest(id=peer, my_stories_from=my_stories_from))
        return {"ok": bool(ok), "my_stories_from": my_stories_from}

    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def unblock_user(
        user: int | str,
        my_stories_from: bool = False,
    ) -> dict[str, Any]:
        """Разблокировать пользователя."""
        client = await get_client()
        peer = await client.get_input_entity(normalize_chat(user))
        ok = await client(UnblockRequest(id=peer, my_stories_from=my_stories_from))
        return {"ok": bool(ok)}

    @mcp.tool(annotations=READ_ONLY)
    async def get_blocked(
        offset: int = 0,
        limit: int = 100,
        my_stories_from: bool = False,
    ) -> list[dict[str, Any]]:
        """Список заблокированных юзеров.

        Args:
            my_stories_from: True — story-blocklist; False — основной.
        """
        client = await get_client()
        result = await client(
            GetBlockedRequest(
                offset=offset, limit=clamp(limit, 1, 100), my_stories_from=my_stories_from
            )
        )
        return [entity_brief(u) for u in getattr(result, "users", [])]
