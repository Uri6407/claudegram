"""Messaging domain — отправка, редактирование, история, закрепление, реакции."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


def register(mcp: FastMCP) -> None:
    from . import drafts, history, messages, pins, reactions, scheduled, typing

    messages.register(mcp)
    history.register(mcp)
    pins.register(mcp)
    reactions.register(mcp)
    drafts.register(mcp)
    scheduled.register(mcp)
    typing.register(mcp)
