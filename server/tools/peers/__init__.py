"""Peers domain — discovery и метаданные сущностей (users/chats/channels)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


def register(mcp: FastMCP) -> None:
    from . import contacts, lookup, users

    lookup.register(mcp)
    users.register(mcp)
    contacts.register(mcp)
