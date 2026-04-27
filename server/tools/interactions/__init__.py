"""Interactions domain — bots inline, callback queries, games."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


def register(mcp: FastMCP) -> None:
    from . import bots

    bots.register(mcp)
