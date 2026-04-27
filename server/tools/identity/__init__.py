"""Identity domain — кто я и как меня видят."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


def register(mcp: FastMCP) -> None:
    from . import account, auth, privacy, security, sessions

    account.register(mcp)
    sessions.register(mcp)
    privacy.register(mcp)
    security.register(mcp)
    auth.register(mcp)
