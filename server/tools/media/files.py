"""Files — отправка файлов, альбомов, voice/video notes."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from telethon.tl.types import DocumentAttributeFilename

from server.client import get_client
from server.formatters import message_brief
from server.tools._common import NON_DESTRUCTIVE, ParseMode, normalize_chat, parse_mode_arg


def register(mcp: Any) -> None:
    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def send_file(
        chat: int | str,
        file_path: str,
        caption: str = "",
        reply_to: int | None = None,
        silent: bool = False,
        force_document: bool = False,
        voice_note: bool = False,
        video_note: bool = False,
        parse_mode: ParseMode = "markdown",
        ttl_seconds: int | None = None,
        clear_draft: bool = False,
        supports_streaming: bool = False,
        custom_filename: str | None = None,
    ) -> dict[str, Any]:
        """Отправить файл. Telethon сам определит тип (фото/видео/документ).

        Args:
            file_path: путь к локальному файлу.
            caption: подпись (поддерживает форматирование, см. parse_mode).
            parse_mode: 'markdown', 'html' или 'none'.
            force_document: True — отправить как документ, не сжимать.
            voice_note: True — отправить голосовое (требует .ogg/.mp3).
            video_note: True — отправить video-кружок.
            ttl_seconds: self-destruct таймер (только для PM, 1-60 сек).
            clear_draft: очистить draft чата после отправки.
            supports_streaming: для видео — отметить как streamable.
            custom_filename: заменить имя файла при отправке.
        """
        client = await get_client()
        path = Path(file_path).expanduser().resolve()
        if not path.exists():
            return {"ok": False, "reason": f"Файл не найден: {path}"}
        attributes: list[Any] = []
        if custom_filename:
            attributes.append(DocumentAttributeFilename(file_name=custom_filename))
        msg = await client.send_file(
            normalize_chat(chat),
            str(path),
            caption=caption,
            reply_to=reply_to,
            silent=silent,
            force_document=force_document,
            voice_note=voice_note,
            video_note=video_note,
            parse_mode=parse_mode_arg(parse_mode),
            ttl=ttl_seconds,
            clear_draft=clear_draft,
            supports_streaming=supports_streaming,
            attributes=attributes if attributes else None,
        )
        return message_brief(msg)

    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def send_album(
        chat: int | str,
        file_paths: list[str],
        caption: str = "",
        reply_to: int | None = None,
        silent: bool = False,
    ) -> list[dict[str, Any]]:
        """Отправить альбом из 2-10 фото/видео одной группой.

        Caption ставится только на первое медиа альбома.
        """
        client = await get_client()
        paths = []
        for fp in file_paths:
            p = Path(fp).expanduser().resolve()
            if not p.exists():
                return [{"ok": False, "reason": f"Файл не найден: {p}"}]
            paths.append(str(p))
        msgs = await client.send_file(
            normalize_chat(chat),
            paths,
            caption=caption,
            reply_to=reply_to,
            silent=silent,
        )
        if not isinstance(msgs, list):
            msgs = [msgs]
        return [message_brief(m) for m in msgs]
