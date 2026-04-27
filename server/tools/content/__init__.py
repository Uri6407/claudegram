"""Content domain — polls, stories, forum-topics."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


def register(mcp: FastMCP) -> None:
    from . import forums, payments, polls, stories

    polls.register(mcp)
    stories.register(mcp)
    forums.register(mcp)
    payments.register(mcp)
