"""Media domain — файлы, attachments, стикеры."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


def register(mcp: FastMCP) -> None:
    from . import attachments, download, files, stickers, voice

    files.register(mcp)
    download.register(mcp)
    attachments.register(mcp)
    voice.register(mcp)
    stickers.register(mcp)
