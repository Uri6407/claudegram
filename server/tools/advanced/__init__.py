"""Advanced domain — escape hatches и низкоуровневое."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


def register(mcp: FastMCP) -> None:
    from . import health, help_api, raw, sampling

    raw.register(mcp)
    help_api.register(mcp)
    health.register(mcp)
    sampling.register(mcp)
