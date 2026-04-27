"""Тесты server/tools/advanced/raw.py — _to_jsonable + invoke_raw flow."""

from __future__ import annotations

from unittest.mock import MagicMock

from server.tools.advanced.raw import _to_jsonable


class TestToJsonable:
    def test_primitive(self) -> None:
        assert _to_jsonable(42) == 42
        assert _to_jsonable("x") == "x"
        assert _to_jsonable(True) is True
        assert _to_jsonable(None) is None
        assert _to_jsonable(3.14) == 3.14

    def test_bytes(self) -> None:
        assert _to_jsonable(b"\x01\x02") == "0102"

    def test_list(self) -> None:
        assert _to_jsonable([1, 2, "a"]) == [1, 2, "a"]

    def test_dict(self) -> None:
        assert _to_jsonable({"k": 1}) == {"k": 1}

    def test_telethon_to_dict(self) -> None:
        obj = MagicMock()
        obj.to_dict = MagicMock(return_value={"_": "Foo", "x": 1, "y": "z"})
        result = _to_jsonable(obj)
        assert result == {"x": 1, "y": "z"}  # _ stripped

    def test_unknown_falls_to_str(self) -> None:
        class Weird:
            def __str__(self) -> str:
                return "weird-instance"

        assert _to_jsonable(Weird()) == "weird-instance"
