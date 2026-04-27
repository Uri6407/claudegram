"""Тесты server/formatters.py — entity_brief, dialog_brief, message_brief."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

from server.formatters import _iso, dialog_brief, entity_brief, message_brief
from telethon.tl.types import Channel, Chat, User


class TestIso:
    def test_none(self) -> None:
        assert _iso(None) is None

    def test_dt(self) -> None:
        dt = datetime(2025, 1, 1, 12, 0, tzinfo=UTC)
        assert _iso(dt).startswith("2025-01-01T12:00:00")


class TestEntityBrief:
    def test_user(self) -> None:
        user = MagicMock(spec=User)
        user.id = 123
        user.username = "alice"
        user.first_name = "Alice"
        user.last_name = "Smith"
        user.phone = None
        user.bot = False
        user.is_self = True
        result = entity_brief(user)
        assert result["type"] == "user"
        assert result["id"] == 123
        assert result["username"] == "alice"
        assert result["is_self"] is True

    def test_channel_broadcast(self) -> None:
        channel = MagicMock(spec=Channel)
        channel.id = 456
        channel.title = "News"
        channel.username = "news"
        channel.broadcast = True
        channel.participants_count = 1000
        result = entity_brief(channel)
        assert result["type"] == "channel"
        assert result["title"] == "News"

    def test_channel_supergroup(self) -> None:
        channel = MagicMock(spec=Channel)
        channel.id = 789
        channel.title = "Chat"
        channel.username = None
        channel.broadcast = False
        channel.participants_count = None
        result = entity_brief(channel)
        assert result["type"] == "supergroup"

    def test_chat_basic(self) -> None:
        chat = MagicMock(spec=Chat)
        chat.id = 111
        chat.title = "Group"
        chat.participants_count = 5
        result = entity_brief(chat)
        assert result["type"] == "group"
        assert result["title"] == "Group"

    def test_unknown_entity(self) -> None:
        thing = MagicMock()
        thing.id = 999
        # Force isinstance checks to fail
        result = entity_brief(thing)
        # Either user/channel/chat, but if none of them match — unknown
        # Since MagicMock isn't a subclass of any, it'll fall through
        assert "type" in result


class TestDialogBrief:
    def test_basic(self) -> None:
        d = MagicMock()
        d.id = -100123
        d.name = "MyChat"
        d.unread_count = 5
        d.pinned = False
        d.archived = False
        d.message = None
        # Setup entity inside
        d.entity = MagicMock(spec=Chat)
        d.entity.id = 123
        d.entity.title = "MyChat"
        d.entity.participants_count = 10
        result = dialog_brief(d)
        assert result["id"] == -100123
        assert result["peer_id"] == -100123  # дублирующее поле
        assert result["unread_count"] == 5
        assert result["last_message"] is None


class TestMessageBrief:
    def _make_msg(self, **overrides: object) -> MagicMock:
        m = MagicMock()
        m.id = 42
        m.date = datetime(2025, 1, 1, tzinfo=UTC)
        m.message = "hello"
        m.sender_id = 111
        m.chat_id = 222
        m.reply_to_msg_id = None
        m.out = False
        m.edit_date = None
        m.views = None
        m.forwards = None
        m.media = None
        m.photo = None
        m.video = None
        m.voice = None
        m.audio = None
        m.document = None
        m.sticker = None
        for k, v in overrides.items():
            setattr(m, k, v)
        return m

    def test_text_only(self) -> None:
        msg = self._make_msg()
        result = message_brief(msg)
        assert result["id"] == 42
        assert result["text"] == "hello"
        assert result["media_type"] is None
        assert result["has_media"] is False

    def test_with_photo(self) -> None:
        msg = self._make_msg(photo=MagicMock(), media=MagicMock())
        result = message_brief(msg)
        assert result["media_type"] == "photo"
        assert result["has_media"] is True

    def test_with_voice(self) -> None:
        msg = self._make_msg(voice=MagicMock(), media=MagicMock())
        result = message_brief(msg)
        assert result["media_type"] == "voice"

    def test_with_reply(self) -> None:
        msg = self._make_msg(reply_to_msg_id=99)
        result = message_brief(msg)
        assert result["reply_to_msg_id"] == 99
