"""Dialogs domain — список диалогов и их состояния."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


def register(mcp: FastMCP) -> None:
    from . import batch, folders, folders_custom, list_, notify

    list_.register(mcp)
    folders.register(mcp)
    folders_custom.register(mcp)
    notify.register(mcp)
    batch.register(mcp)
