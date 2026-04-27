"""Тесты `server/resources.py` — все resources зарегистрированы."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_static_resources_registered() -> None:
    from server.main import mcp

    resources = await mcp.list_resources()
    uris = {str(r.uri) for r in resources}
    expected = {
        "telegram://me",
        "telegram://chats",
        "telegram://chats/archived",
        "telegram://contacts",
        "telegram://drafts",
        "telegram://blocked",
        "telegram://folders",
        "telegram://stories/feed",
        "telegram://files/recent",
    }
    assert expected <= uris, f"missing: {expected - uris}"


@pytest.mark.asyncio
async def test_resource_templates_registered() -> None:
    from server.main import mcp

    templates = await mcp.list_resource_templates()
    template_uris = {t.uriTemplate for t in templates}
    expected = {
        "telegram://chat/{chat_id}",
        "telegram://chat/{chat_id}/history",
        "telegram://chat/{chat_id}/pinned",
        "telegram://chat/{chat_id}/photos",
        "telegram://chat/{chat_id}/common",
        "telegram://msg/{chat_id}/{message_id}",
        "telegram://chat/{chat_id}/topic/{topic_id}/history",
    }
    assert expected <= template_uris, f"missing: {expected - template_uris}"


@pytest.mark.asyncio
async def test_all_resources_have_mime_type() -> None:
    from server.main import mcp

    resources = await mcp.list_resources()
    for r in resources:
        assert r.mimeType, f"{r.uri} без mimeType"
