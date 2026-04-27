"""Attachments — interactive media: location, contact, dice."""

from __future__ import annotations

from typing import Any

from telethon.tl.types import (
    InputGeoPoint,
    InputMediaContact,
    InputMediaDice,
    InputMediaGeoLive,
    InputMediaGeoPoint,
)

from server.client import get_client
from server.formatters import message_brief
from server.tools._common import NON_DESTRUCTIVE, normalize_chat


def register(mcp: Any) -> None:
    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def send_location(
        chat: int | str,
        latitude: float,
        longitude: float,
        live_period: int | None = None,
        silent: bool = False,
    ) -> dict[str, Any]:
        """Отправить геолокацию.

        Args:
            live_period: если задан (60-86400) — отправить как live-локацию.
        """
        client = await get_client()
        geo = InputGeoPoint(lat=latitude, long=longitude)
        media = (
            InputMediaGeoLive(geo_point=geo, period=live_period)
            if live_period
            else InputMediaGeoPoint(geo_point=geo)
        )
        msg = await client.send_file(normalize_chat(chat), media, silent=silent)
        return message_brief(msg)

    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def send_contact(
        chat: int | str,
        phone: str,
        first_name: str,
        last_name: str = "",
        silent: bool = False,
    ) -> dict[str, Any]:
        """Отправить визитку контакта."""
        client = await get_client()
        media = InputMediaContact(
            phone_number=phone,
            first_name=first_name,
            last_name=last_name,
            vcard="",
        )
        msg = await client.send_file(normalize_chat(chat), media, silent=silent)
        return message_brief(msg)

    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def send_dice(
        chat: int | str,
        emoji: str = "🎲",
        silent: bool = False,
    ) -> dict[str, Any]:
        """Отправить интерактивный «кубик».

        Args:
            emoji: 🎲 (кубик), 🎯 (дартс), 🏀 (баскетбол), ⚽ (футбол),
                🎰 (слот), 🎳 (боулинг). Telegram пришлёт случайный результат.
        """
        client = await get_client()
        msg = await client.send_file(
            normalize_chat(chat),
            InputMediaDice(emoticon=emoji),
            silent=silent,
        )
        return message_brief(msg)
