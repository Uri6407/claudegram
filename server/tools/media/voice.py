"""Voice — голосовые/видео-кружки + транскрипция."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from telethon.tl.functions.messages import TranscribeAudioRequest

from server.client import get_client
from server.formatters import message_brief
from server.tools._common import NON_DESTRUCTIVE, READ_ONLY, normalize_chat


def register(mcp: Any) -> None:
    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def send_voice(
        chat: int | str,
        file_path: str,
        caption: str = "",
        duration_seconds: int | None = None,
        reply_to: int | None = None,
        silent: bool = False,
    ) -> dict[str, Any]:
        """Отправить голосовое сообщение (.ogg/.mp3 → opus voice note)."""
        from telethon.tl.types import DocumentAttributeAudio

        client = await get_client()
        path = Path(file_path).expanduser().resolve()
        if not path.exists():
            return {"ok": False, "reason": f"Файл не найден: {path}"}
        attrs: list[Any] = []
        if duration_seconds is not None:
            attrs.append(DocumentAttributeAudio(duration=duration_seconds, voice=True))
        msg = await client.send_file(
            normalize_chat(chat),
            str(path),
            caption=caption,
            voice_note=True,
            reply_to=reply_to,
            silent=silent,
            attributes=attrs or None,
        )
        return message_brief(msg)

    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def send_video_note(
        chat: int | str,
        file_path: str,
        duration_seconds: int | None = None,
        reply_to: int | None = None,
        silent: bool = False,
    ) -> dict[str, Any]:
        """Отправить video-кружок (.mp4 → круглое видео ≤60s, диаметр 384px)."""
        client = await get_client()
        path = Path(file_path).expanduser().resolve()
        if not path.exists():
            return {"ok": False, "reason": f"Файл не найден: {path}"}
        msg = await client.send_file(
            normalize_chat(chat),
            str(path),
            video_note=True,
            reply_to=reply_to,
            silent=silent,
        )
        return message_brief(msg)

    @mcp.tool(annotations=READ_ONLY)
    async def transcribe_audio(chat: int | str, message_id: int) -> dict[str, Any]:
        """Транскрибировать голосовое в текст (Telegram Premium фича).

        Возвращает текст или partial-транскрипцию + флаг pending.
        """
        client = await get_client()
        peer = await client.get_input_entity(normalize_chat(chat))
        result = await client(TranscribeAudioRequest(peer=peer, msg_id=message_id))
        return {
            "ok": True,
            "text": getattr(result, "text", "") or "",
            "pending": getattr(result, "pending", False),
            "transcription_id": getattr(result, "transcription_id", None),
        }
