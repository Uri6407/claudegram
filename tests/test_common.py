"""Тесты server/tools/_common.py — нормализация, clamp, parse_mode."""

from __future__ import annotations

from server.tools._common import clamp, normalize_chat, parse_mode_arg


class TestNormalizeChat:
    def test_int_id_passthrough(self) -> None:
        assert normalize_chat(12345) == 12345
        assert normalize_chat(-100123456789) == -100123456789

    def test_username_passthrough(self) -> None:
        assert normalize_chat("@username") == "@username"
        assert normalize_chat("username") == "username"

    def test_string_int_to_int(self) -> None:
        assert normalize_chat("12345") == 12345
        assert normalize_chat("-100123") == -100123

    def test_none_passthrough(self) -> None:
        assert normalize_chat(None) is None

    def test_invite_link_kept(self) -> None:
        assert normalize_chat("https://t.me/joinchat/abc") == "https://t.me/joinchat/abc"


class TestClamp:
    def test_within_range(self) -> None:
        assert clamp(50, 1, 200) == 50

    def test_below_lower(self) -> None:
        assert clamp(-5, 1, 200) == 1

    def test_above_upper(self) -> None:
        assert clamp(500, 1, 200) == 200

    def test_at_boundaries(self) -> None:
        assert clamp(1, 1, 200) == 1
        assert clamp(200, 1, 200) == 200


class TestParseModeArg:
    def test_none_returns_none(self) -> None:
        assert parse_mode_arg("none") is None

    def test_markdown(self) -> None:
        assert parse_mode_arg("markdown") == "markdown"

    def test_html(self) -> None:
        assert parse_mode_arg("html") == "html"
