"""Каталог MCP-tools, организованный по доменам Telegram API.

Структура:
- identity/      — собственный аккаунт, профиль, сессии, privacy, security (2FA)
- peers/         — discovery и метаданные сущностей (lookup, users, contacts)
- messaging/     — отправка, история, pins, реакции, drafts, scheduled
- dialogs/       — список диалогов и их состояния (folders, custom-folders, notify)
- chats/         — управление группами/каналами (create, settings, members, invites, admin)
- media/         — файлы, attachments, voice notes, стикеры
- content/       — polls, stories, forum-topics, payments (Stars/Premium)
- interactions/  — bots inline, start_bot, callback-кнопки, games
- advanced/      — raw API escape hatch + help (config, country list)

Каждый домен — пакет с `register(mcp)` функцией, которая подключает свои подмодули.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


def register_all(mcp: FastMCP) -> None:
    """Подключить все домены tools к серверу."""
    from . import (
        advanced,
        chats,
        content,
        dialogs,
        identity,
        interactions,
        media,
        messaging,
        peers,
    )

    identity.register(mcp)
    peers.register(mcp)
    messaging.register(mcp)
    dialogs.register(mcp)
    chats.register(mcp)
    media.register(mcp)
    content.register(mcp)
    interactions.register(mcp)
    advanced.register(mcp)
