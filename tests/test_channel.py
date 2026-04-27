"""Тесты server/channel.py — permission regex, allowlist parsing, env toggles, media label."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from server import channel


class TestPermissionRegex:
    @pytest.mark.parametrize(
        "text,expected",
        [
            ("y abcde", ("y", "abcde")),
            ("yes abcde", ("yes", "abcde")),
            ("YES abcde", ("YES", "abcde")),
            ("n fghij", ("n", "fghij")),
            ("no qrstu", ("no", "qrstu")),
            ("  yes  abcde  ", ("yes", "abcde")),
            ("Y mnopq", ("Y", "mnopq")),
        ],
    )
    def test_matches_valid(self, text: str, expected: tuple[str, str]) -> None:
        m = channel.PERMISSION_RE.match(text)
        assert m is not None
        assert m.group(1) == expected[0]
        assert m.group(2) == expected[1]

    @pytest.mark.parametrize(
        "text",
        [
            "yes abcle",  # содержит запрещённую l
            "yes abcle ",  # та же причина
            "maybe abcde",  # не verdict-keyword
            "yes abc",  # 3 буквы
            "yes abcdef",  # 6 букв
            "yes abcd1",  # цифра
            "yes abcLe",  # содержит l даже в смешанном регистре
            "yesabcde",  # без пробела
            "привет abcde",  # cyrillic
            "",
            "yes",
            "abcde",
        ],
    )
    def test_rejects_invalid(self, text: str) -> None:
        assert channel.PERMISSION_RE.match(text) is None


class TestParseAllowedIds:
    def test_empty(self) -> None:
        assert channel.parse_allowed_ids(None) == set()
        assert channel.parse_allowed_ids("") == set()

    def test_single_id(self) -> None:
        assert channel.parse_allowed_ids("12345") == {12345}

    def test_multiple_ids(self) -> None:
        assert channel.parse_allowed_ids("111, 222, 333") == {111, 222, 333}

    def test_negative_ids(self) -> None:
        assert channel.parse_allowed_ids("-100123, 456") == {-100123, 456}

    def test_garbage_filtered(self) -> None:
        assert channel.parse_allowed_ids("abc, 42, xyz, 7") == {42, 7}

    def test_whitespace_handled(self) -> None:
        assert channel.parse_allowed_ids("  1  ,2,  3  ") == {1, 2, 3}


class TestChannelModeEnabled:
    def test_default_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("CLAUDEGRAM_CHANNEL_MODE", raising=False)
        assert channel.channel_mode_enabled() is False

    @pytest.mark.parametrize("val", ["1", "true", "True"])
    def test_truthy(self, monkeypatch: pytest.MonkeyPatch, val: str) -> None:
        monkeypatch.setenv("CLAUDEGRAM_CHANNEL_MODE", val)
        assert channel.channel_mode_enabled() is True

    @pytest.mark.parametrize("val", ["0", "false", "False", "no", "TRUE"])
    def test_falsy(self, monkeypatch: pytest.MonkeyPatch, val: str) -> None:
        monkeypatch.setenv("CLAUDEGRAM_CHANNEL_MODE", val)
        assert channel.channel_mode_enabled() is False


class TestGetAllowedIds:
    def test_from_TG_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TG_ALLOWED_SENDER_IDS", "1,2,3")
        assert channel.get_allowed_ids() == {1, 2, 3}

    def test_from_plugin_option(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_TG_ALLOWED_SENDER_IDS", "10,20")
        assert channel.get_allowed_ids() == {10, 20}

    def test_TG_var_wins(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TG_ALLOWED_SENDER_IDS", "1")
        monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_TG_ALLOWED_SENDER_IDS", "999")
        assert channel.get_allowed_ids() == {1}


class TestMediaLabel:
    @pytest.mark.parametrize(
        "field,expected",
        [
            ("photo", "photo"),
            ("video", "video"),
            ("voice", "voice message"),
            ("audio", "audio"),
            ("document", "document"),
            ("sticker", "sticker"),
        ],
    )
    def test_known_types(self, field: str, expected: str) -> None:
        msg = MagicMock()
        for f in ("photo", "video", "voice", "audio", "document", "sticker"):
            setattr(msg, f, f == field)
        assert channel._media_label(msg) == expected

    def test_unknown_falls_back(self) -> None:
        msg = MagicMock()
        for f in ("photo", "video", "voice", "audio", "document", "sticker"):
            setattr(msg, f, False)
        assert channel._media_label(msg) == "attachment"


class TestChannelInstructions:
    def test_mentions_chat_id(self) -> None:
        assert "chat_id" in channel.CHANNEL_INSTRUCTIONS

    def test_mentions_send_message_tool(self) -> None:
        assert "send_message" in channel.CHANNEL_INSTRUCTIONS

    def test_safety_clause(self) -> None:
        assert "отправляй" in channel.CHANNEL_INSTRUCTIONS.lower()
