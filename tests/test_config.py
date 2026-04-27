"""Тесты server/config.py — env loading в обоих режимах."""

from __future__ import annotations

from pathlib import Path

import pytest
from server.config import Config


class TestStandaloneMode:
    def test_loads_valid(self, valid_env: Path) -> None:
        cfg = Config.load()
        assert cfg.api_id == 12345
        assert cfg.api_hash == "abcdef0123456789abcdef0123456789"
        assert cfg.phone == "+19999999999"
        assert cfg.session_name == "claudegram"
        assert cfg.session_path == valid_env / "claudegram"
        assert cfg.data_dir == valid_env

    def test_missing_required_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TG_API_HASH", "x")
        monkeypatch.setenv("TG_PHONE", "+1")
        # TG_API_ID отсутствует
        with pytest.raises(RuntimeError, match="TG_API_ID"):
            Config.load()

    def test_invalid_api_id_raises(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        monkeypatch.setenv("TG_API_ID", "not-a-number")
        monkeypatch.setenv("TG_API_HASH", "x")
        monkeypatch.setenv("TG_PHONE", "+1")
        monkeypatch.setenv("CLAUDEGRAM_DATA_DIR", str(tmp_path))
        with pytest.raises(RuntimeError, match="должен быть числом"):
            Config.load()


class TestPluginMode:
    def test_falls_back_to_plugin_option_vars(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_TG_API_ID", "999")
        monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_TG_API_HASH", "h")
        monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_TG_PHONE", "+1")
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
        cfg = Config.load()
        assert cfg.api_id == 999
        assert cfg.data_dir == tmp_path

    def test_TG_vars_win_over_plugin_option(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setenv("TG_API_ID", "111")
        monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_TG_API_ID", "222")
        monkeypatch.setenv("TG_API_HASH", "x")
        monkeypatch.setenv("TG_PHONE", "+1")
        monkeypatch.setenv("CLAUDEGRAM_DATA_DIR", str(tmp_path))
        cfg = Config.load()
        assert cfg.api_id == 111

    def test_data_dir_created_if_missing(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        target = tmp_path / "deep" / "nested"
        monkeypatch.setenv("TG_API_ID", "1")
        monkeypatch.setenv("TG_API_HASH", "x")
        monkeypatch.setenv("TG_PHONE", "+1")
        monkeypatch.setenv("CLAUDEGRAM_DATA_DIR", str(target))
        Config.load()
        assert target.exists()


class TestSessionName:
    def test_default(self, valid_env: Path) -> None:
        cfg = Config.load()
        assert cfg.session_name == "claudegram"

    def test_custom(self, monkeypatch: pytest.MonkeyPatch, valid_env: Path) -> None:
        monkeypatch.setenv("TG_SESSION_NAME", "my-session")
        cfg = Config.load()
        assert cfg.session_name == "my-session"
        assert cfg.session_path == valid_env / "my-session"


class TestTwoFA:
    def test_none_by_default(self, valid_env: Path) -> None:
        cfg = Config.load()
        assert cfg.twofa_password is None

    def test_set(self, monkeypatch: pytest.MonkeyPatch, valid_env: Path) -> None:
        monkeypatch.setenv("TG_2FA_PASSWORD", "secret")
        cfg = Config.load()
        assert cfg.twofa_password == "secret"
