"""Chats domain — управление группами/каналами."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


def register(mcp: FastMCP) -> None:
    from . import admin, create, invites, members, settings

    create.register(mcp)
    settings.register(mcp)
    members.register(mcp)
    invites.register(mcp)
    admin.register(mcp)
