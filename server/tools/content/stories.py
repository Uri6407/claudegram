"""Stories — Telegram Stories (24-часовые посты с фото/видео)."""

from __future__ import annotations

from typing import Any

from telethon.tl.functions.stories import (
    DeleteStoriesRequest,
    GetAllStoriesRequest,
    GetPeerStoriesRequest,
    GetPinnedStoriesRequest,
    GetStoriesArchiveRequest,
    GetStoriesByIDRequest,
    GetStoryViewsListRequest,
    ReadStoriesRequest,
    SendStoryRequest,
    TogglePinnedRequest,
)

from server.client import get_client
from server.tools._common import DESTRUCTIVE, NON_DESTRUCTIVE, READ_ONLY, clamp, normalize_chat


def _story_brief(s: Any) -> dict[str, Any]:
    return {
        "id": s.id,
        "date": s.date.isoformat() if s.date else None,
        "expire_date": s.expire_date.isoformat() if s.expire_date else None,
        "caption": getattr(s, "caption", None) or "",
        "pinned": getattr(s, "pinned", False),
        "public": getattr(s, "public", False),
        "close_friends": getattr(s, "close_friends", False),
        "views": getattr(getattr(s, "views", None), "views_count", None),
        "media_type": type(s.media).__name__ if getattr(s, "media", None) else None,
    }


def register(mcp: Any) -> None:
    @mcp.tool(annotations=READ_ONLY)
    async def get_all_stories() -> list[dict[str, Any]]:
        """Все доступные истории из ленты (по подпискам)."""
        client = await get_client()
        result = await client(GetAllStoriesRequest(next=False, hidden=False))
        out: list[dict[str, Any]] = []
        for ps in getattr(result, "peer_stories", []):
            peer_id = getattr(getattr(ps, "peer", None), "user_id", None) or getattr(
                getattr(ps, "peer", None), "channel_id", None
            )
            for s in getattr(ps, "stories", []):
                item = _story_brief(s)
                item["peer_id"] = peer_id
                out.append(item)
        return out

    @mcp.tool(annotations=READ_ONLY)
    async def get_peer_stories(peer: int | str) -> list[dict[str, Any]]:
        """Активные истории конкретного юзера/канала."""
        client = await get_client()
        input_peer = await client.get_input_entity(normalize_chat(peer))
        result = await client(GetPeerStoriesRequest(peer=input_peer))
        stories = getattr(getattr(result, "stories", None), "stories", []) or []
        return [_story_brief(s) for s in stories]

    @mcp.tool(annotations=READ_ONLY)
    async def get_pinned_stories(
        peer: int | str,
        offset_id: int = 0,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Закреплённые (сохранённые в профиле) истории юзера."""
        client = await get_client()
        input_peer = await client.get_input_entity(normalize_chat(peer))
        result = await client(
            GetPinnedStoriesRequest(
                peer=input_peer, offset_id=offset_id, limit=clamp(limit, 1, 100)
            )
        )
        return [_story_brief(s) for s in (result.stories or [])]

    @mcp.tool(annotations=READ_ONLY)
    async def get_stories_by_id(
        peer: int | str,
        story_ids: list[int],
    ) -> list[dict[str, Any]]:
        """Получить конкретные истории по их id."""
        client = await get_client()
        input_peer = await client.get_input_entity(normalize_chat(peer))
        result = await client(GetStoriesByIDRequest(peer=input_peer, id=story_ids))
        return [_story_brief(s) for s in (result.stories or [])]

    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def mark_stories_read(
        peer: int | str,
        max_story_id: int,
    ) -> dict[str, Any]:
        """Пометить истории прочитанными до указанного id."""
        client = await get_client()
        input_peer = await client.get_input_entity(normalize_chat(peer))
        result = await client(ReadStoriesRequest(peer=input_peer, max_id=max_story_id))
        return {"ok": True, "read_count": len(result) if hasattr(result, "__len__") else None}

    @mcp.tool(annotations=DESTRUCTIVE)
    async def delete_stories(story_ids: list[int]) -> dict[str, Any]:
        """Удалить свои истории."""
        from telethon.tl.types import InputPeerSelf

        client = await get_client()
        deleted = await client(DeleteStoriesRequest(peer=InputPeerSelf(), id=story_ids))
        return {"ok": True, "deleted": list(deleted)}

    @mcp.tool(annotations=READ_ONLY)
    async def get_stories_archive(
        offset_id: int = 0,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Архив моих историй (истёкшие, но не удалённые)."""
        from telethon.tl.types import InputPeerSelf

        client = await get_client()
        result = await client(
            GetStoriesArchiveRequest(
                peer=InputPeerSelf(), offset_id=offset_id, limit=clamp(limit, 1, 100)
            )
        )
        return [_story_brief(s) for s in (result.stories or [])]

    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def toggle_pinned_stories(
        story_ids: list[int],
        pinned: bool = True,
    ) -> dict[str, Any]:
        """Закрепить/открепить мои stories в профиле (доступно бессрочно)."""
        from telethon.tl.types import InputPeerSelf

        client = await get_client()
        result = await client(
            TogglePinnedRequest(peer=InputPeerSelf(), id=story_ids, pinned=pinned)
        )
        return {"ok": True, "ids": list(result), "pinned": pinned}

    @mcp.tool(annotations=READ_ONLY)
    async def get_story_views(
        story_id: int,
        limit: int = 50,
        just_contacts: bool = False,
        reactions_first: bool = False,
    ) -> dict[str, Any]:
        """Кто посмотрел мою story.

        Args:
            just_contacts: только контакты (не все 1000+ зрителей).
            reactions_first: сначала те, кто оставил реакцию.
        """
        from telethon.tl.types import InputPeerSelf

        client = await get_client()
        result = await client(
            GetStoryViewsListRequest(
                peer=InputPeerSelf(),
                id=story_id,
                offset="",
                limit=clamp(limit, 1, 100),
                just_contacts=just_contacts,
                reactions_first=reactions_first,
            )
        )
        from server.formatters import entity_brief

        return {
            "ok": True,
            "views_count": result.count,
            "viewers": [entity_brief(u) for u in getattr(result, "users", [])],
        }

    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def send_story(
        media_path: str,
        caption: str = "",
        period_seconds: int = 86400,
        privacy: str = "everyone",
        pinned: bool = False,
        noforwards: bool = False,
    ) -> dict[str, Any]:
        """Опубликовать новую story с фото/видео.

        Args:
            media_path: путь к фото или видео.
            caption: подпись.
            period_seconds: время жизни (6/12/24/48 часов = 21600/43200/86400/172800).
            privacy: 'everyone' / 'contacts' / 'close_friends' / 'self' (никто кроме меня).
            pinned: True — сразу закрепить в профиле бессрочно.
            noforwards: запретить forward.
        """
        import secrets as _secrets
        from pathlib import Path

        from telethon.tl.types import (
            InputMediaUploadedDocument,
            InputMediaUploadedPhoto,
            InputPeerSelf,
            InputPrivacyValueAllowAll,
            InputPrivacyValueAllowCloseFriends,
            InputPrivacyValueAllowContacts,
            InputPrivacyValueDisallowAll,
        )

        client = await get_client()
        path = Path(media_path).expanduser().resolve()
        if not path.exists():
            return {"ok": False, "reason": f"Файл не найден: {path}"}

        uploaded = await client.upload_file(str(path))
        suffix = path.suffix.lower()
        if suffix in (".jpg", ".jpeg", ".png", ".webp"):
            media = InputMediaUploadedPhoto(file=uploaded)
        else:
            media = InputMediaUploadedDocument(
                file=uploaded,
                mime_type="video/mp4" if suffix in (".mp4", ".mov") else "application/octet-stream",
                attributes=[],
            )

        privacy_map = {
            "everyone": [InputPrivacyValueAllowAll()],
            "contacts": [InputPrivacyValueAllowContacts()],
            "close_friends": [InputPrivacyValueAllowCloseFriends()],
            "self": [InputPrivacyValueDisallowAll()],
        }
        privacy_rules = privacy_map.get(privacy, [InputPrivacyValueAllowAll()])

        result = await client(
            SendStoryRequest(
                peer=InputPeerSelf(),
                media=media,
                privacy_rules=privacy_rules,
                pinned=pinned,
                noforwards=noforwards,
                caption=caption or None,
                entities=[] if caption else None,
                random_id=_secrets.randbits(63),
                period=period_seconds,
            )
        )
        return {"ok": True, "result": type(result).__name__}
