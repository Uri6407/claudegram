"""Тесты `server/prompts.py` — все 7 шаблонов."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_prompts_registered_with_descriptions() -> None:
    from server.main import mcp

    prompts = await mcp.list_prompts()
    names = {p.name for p in prompts}
    expected = {
        "tg_digest",
        "tg_search",
        "tg_draft_reply",
        "tg_summarize_thread",
        "tg_weekly_roundup",
        "tg_triage_inbox",
        "tg_moderate_chat",
    }
    assert expected <= names, f"missing: {expected - names}"
    for p in prompts:
        assert p.description, f"{p.name} без description"


@pytest.mark.asyncio
async def test_tg_digest_renders() -> None:
    from server.main import mcp

    result = await mcp.get_prompt("tg_digest", {"top_n": "5"})
    assert result.messages
    text = result.messages[0].content.text
    assert "5" in text
    assert "list_chats" in text or "telegram://chats" in text


@pytest.mark.asyncio
async def test_tg_search_with_chat() -> None:
    from server.main import mcp

    result = await mcp.get_prompt("tg_search", {"query": "deploy", "chat": "@team"})
    text = result.messages[0].content.text
    assert "deploy" in text
    assert "@team" in text


@pytest.mark.asyncio
async def test_tg_search_global() -> None:
    from server.main import mcp

    result = await mcp.get_prompt("tg_search", {"query": "release"})
    text = result.messages[0].content.text
    assert "release" in text
    assert "глобально" in text or "global" in text.lower()
