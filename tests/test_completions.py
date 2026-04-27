"""Тесты `server/completions.py` — emoji/folder/tone autocomplete."""

from __future__ import annotations

import pytest
from server.completions import _suggest_emoji


@pytest.mark.asyncio
async def test_suggest_emoji_no_prefix() -> None:
    out = await _suggest_emoji("")
    assert len(out) == 25
    assert "👍" in out
    assert "🔥" in out


@pytest.mark.asyncio
async def test_suggest_emoji_filtered() -> None:
    out = await _suggest_emoji("❤")
    assert "❤" in out
    # все возвращённые должны содержать prefix
    assert all("❤" in e for e in out)
