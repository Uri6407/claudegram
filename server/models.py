"""Pydantic-модели для типизированных tools и structured output.

FastMCP по этим моделям генерирует `outputSchema` и складывает результат
в `structuredContent` ответа `tools/call`. Клиент получает type-safe данные.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

EntityType = Literal["user", "channel", "supergroup", "group", "unknown"]


class EntityBrief(BaseModel):
    type: EntityType
    id: int | None
    title: str | None = None
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    is_bot: bool | None = None
    is_self: bool | None = None
    participants_count: int | None = None


class MessageBrief(BaseModel):
    id: int
    date: str | None = None
    text: str = ""
    sender_id: int | None = None
    chat_id: int | None = None
    reply_to_msg_id: int | None = None
    is_outgoing: bool = False
    edited: str | None = None
    views: int | None = None
    forwards: int | None = None
    media_type: str | None = None
    has_media: bool = False
    # Service-message action type (например 'MessageActionPhoneCall',
    # 'MessageActionChatJoinedByLink', 'MessageActionHistoryClear').
    # Заполняется только для сервисных сообщений; для обычных = None.
    action: str | None = None
    silent: bool | None = None
    pinned_in_chat: bool | None = None
    mentioned: bool | None = None


class DialogBrief(BaseModel):
    id: int
    peer_id: int
    name: str
    unread_count: int
    is_pinned: bool
    is_archived: bool
    entity: EntityBrief
    last_message: MessageBrief | None = None


class DialogCompact(BaseModel):
    """Облегчённая форма для list-операций — 85% меньше payload."""

    id: int
    name: str
    type: EntityType
    username: str | None = None
    is_pinned: bool = False
    is_archived: bool = False
    is_bot: bool = False
    unread_count: int = 0
    participants_count: int | None = None


class DialogStats(BaseModel):
    """Счётчики диалогов по типам — без payload."""

    total: int
    pm_users: int
    bots: int
    channels: int
    supergroups: int
    basic_groups: int
    archived: int
    pinned: int
    unread: int


class BatchOpResult(BaseModel):
    """Результат batch-операции по списку chat_id."""

    total: int
    succeeded: int
    failed: int
    flood_waited: int
    results: list[dict] = []


class HealthReport(BaseModel):
    ok: bool
    connected: bool
    authorized: bool
    self_id: int | None = None
    self_username: str | None = None
    is_premium: bool = False
    telegram_latency_ms: int | None = None
    message: str | None = None
    # Диагностика — где сервер ищет session
    session_path: str | None = None
    session_exists: bool | None = None
    data_dir: str | None = None


class ServerVersion(BaseModel):
    claudegram: str = Field(description="Версия плагина")
    telethon: str
    mcp: str
    python: str
