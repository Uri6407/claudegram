"""Общие фикстуры для тестов Claudegram."""

from __future__ import annotations

import sys
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

# Гарантируем, что server/ импортируется
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[None]:
    """Чистим env перед каждым тестом, чтобы Config.load() не видел реальный .env."""
    for var in [
        "TG_API_ID",
        "TG_API_HASH",
        "TG_PHONE",
        "TG_SESSION_NAME",
        "TG_2FA_PASSWORD",
        "TG_ALLOWED_SENDER_IDS",
        "CLAUDEGRAM_DATA_DIR",
        "CLAUDEGRAM_CHANNEL_MODE",
        "CLAUDE_PLUGIN_DATA",
        "CLAUDE_PLUGIN_OPTION_TG_API_ID",
        "CLAUDE_PLUGIN_OPTION_TG_API_HASH",
        "CLAUDE_PLUGIN_OPTION_TG_PHONE",
        "CLAUDE_PLUGIN_OPTION_TG_SESSION_NAME",
        "CLAUDE_PLUGIN_OPTION_TG_2FA_PASSWORD",
        "CLAUDE_PLUGIN_OPTION_TG_ALLOWED_SENDER_IDS",
    ]:
        monkeypatch.delenv(var, raising=False)
    yield


@pytest.fixture
def valid_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Минимальный валидный конфиг + tmp data_dir."""
    monkeypatch.setenv("TG_API_ID", "12345")
    monkeypatch.setenv("TG_API_HASH", "abcdef0123456789abcdef0123456789")
    monkeypatch.setenv("TG_PHONE", "+19999999999")
    monkeypatch.setenv("CLAUDEGRAM_DATA_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture
def mock_client() -> MagicMock:
    """Фейковый Telethon TelegramClient — все методы AsyncMock."""
    client = MagicMock()
    client.get_me = AsyncMock()
    client.get_dialogs = AsyncMock(return_value=[])
    client.get_messages = AsyncMock(return_value=[])
    client.get_entity = AsyncMock()
    client.get_input_entity = AsyncMock()
    client.send_message = AsyncMock()
    client.edit_message = AsyncMock()
    client.delete_messages = AsyncMock(return_value=[])
    client.forward_messages = AsyncMock(return_value=[])
    client.send_read_acknowledge = AsyncMock(return_value=True)
    client.pin_message = AsyncMock()
    client.unpin_message = AsyncMock()
    client.get_drafts = AsyncMock(return_value=[])
    client.edit_folder = AsyncMock()
    client.delete_dialog = AsyncMock()
    client.get_participants = AsyncMock(return_value=[])
    client.get_profile_photos = AsyncMock(return_value=[])
    client.get_admin_log = AsyncMock(return_value=[])
    client.kick_participant = AsyncMock()
    client.send_file = AsyncMock()
    client.download_media = AsyncMock(return_value="/tmp/file.bin")
    client.download_profile_photo = AsyncMock(return_value="/tmp/photo.jpg")
    client.run_until_disconnected = AsyncMock()
    client.disconnect = AsyncMock()
    client.is_user_authorized = AsyncMock(return_value=True)
    client.connect = AsyncMock()
    # __call__ для invoke (raw_api)
    client.return_value = AsyncMock()
    return client


@pytest.fixture
def patch_get_client(monkeypatch: pytest.MonkeyPatch, mock_client: MagicMock) -> MagicMock:
    """Подменяет server.client.get_client глобально в server.* модулях."""

    async def _fake() -> MagicMock:
        return mock_client

    import server.client as client_mod

    monkeypatch.setattr(client_mod, "get_client", _fake)

    # Также подменяем в каждом tools-модуле, который импортирует get_client из server.client
    import server.channel as channel_mod

    monkeypatch.setattr(channel_mod, "get_client", _fake)

    for path in (
        "identity.account",
        "identity.sessions",
        "identity.privacy",
        "identity.security",
        "peers.lookup",
        "peers.users",
        "peers.contacts",
        "messaging.messages",
        "messaging.history",
        "messaging.pins",
        "messaging.reactions",
        "messaging.drafts",
        "messaging.scheduled",
        "messaging.typing",
        "dialogs.list_",
        "dialogs.folders",
        "dialogs.folders_custom",
        "dialogs.notify",
        "chats.create",
        "chats.settings",
        "chats.members",
        "chats.invites",
        "chats.admin",
        "media.files",
        "media.download",
        "media.attachments",
        "media.stickers",
        "media.voice",
        "content.polls",
        "content.stories",
        "content.forums",
        "content.payments",
        "interactions.bots",
        "advanced.raw",
        "advanced.health",
        "advanced.help_api",
        "advanced.sampling",
    ):
        try:
            mod = __import__(f"server.tools.{path}", fromlist=["get_client"])
            if hasattr(mod, "get_client"):
                monkeypatch.setattr(mod, "get_client", _fake)
        except ImportError:
            pass

    return mock_client
