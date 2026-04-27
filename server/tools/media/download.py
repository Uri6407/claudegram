"""Download — скачивание медиа из сообщений + получение метаданных."""

from __future__ import annotations

import io
import tempfile
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import Context, Image
from mcp.server.fastmcp.utilities.types import Audio

from server.client import get_client
from server.tools._common import NON_DESTRUCTIVE, READ_ONLY, normalize_chat

INLINE_LIMIT_BYTES = 1_048_576  # 1 MB


async def _validate_against_roots(ctx: Context | None, target: Path) -> Path:
    """Если клиент объявил roots — проверить, что target внутри хотя бы одного.

    Возвращает sanitized Path или сам target. Не падает: в худшем случае
    оставляет дефолтный path. Roots — best-effort security helper.
    """
    if ctx is None:
        return target
    try:
        roots = await ctx.session.list_roots()
    except Exception:
        return target
    root_paths: list[Path] = []
    for r in getattr(roots, "roots", []) or []:
        uri = str(getattr(r, "uri", "") or "")
        if uri.startswith("file://"):
            root_paths.append(Path(uri.removeprefix("file://")).resolve())
    if not root_paths:
        return target
    target_resolved = target.resolve()
    for rp in root_paths:
        try:
            target_resolved.relative_to(rp)
            return target_resolved
        except ValueError:
            continue
    # Падать в первый из roots — безопаснее, чем писать вне.
    return root_paths[0]


def register(mcp: Any) -> None:
    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def download_media(
        chat: int | str,
        message_id: int,
        download_dir: str | None = None,
        thumb_index: int | None = None,
        inline: bool = False,
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        """Скачать медиа из сообщения.

        Args:
            download_dir: куда писать (если roots заявлены — путь валидируется).
            thumb_index: если задан — скачать только превью указанного индекса.
            inline: True — вернуть Image/Audio inline (≤1 MB) вместо файла.
        """
        client = await get_client()
        msg = await client.get_messages(normalize_chat(chat), ids=message_id)
        if msg is None or not msg.media:
            return {"ok": False, "reason": "В сообщении нет медиа"}

        # Inline — байты прямо в ответ как ImageContent / AudioContent
        if inline:
            buf = io.BytesIO()
            result = await client.download_media(msg, file=buf, thumb=thumb_index)
            if result is None:
                return {"ok": False, "reason": "Не удалось скачать"}
            data = buf.getvalue()
            if len(data) > INLINE_LIMIT_BYTES:
                return {
                    "ok": False,
                    "reason": (
                        f"Файл слишком большой для inline ({len(data)} байт > "
                        f"{INLINE_LIMIT_BYTES}). Используй inline=False."
                    ),
                }
            if msg.photo:
                return {"ok": True, "image": Image(data=data, format="jpeg"), "size": len(data)}
            if msg.voice or msg.audio:
                fmt = "ogg" if msg.voice else "mpeg"
                return {"ok": True, "audio": Audio(data=data, format=fmt), "size": len(data)}
            return {"ok": False, "reason": "inline поддерживается только для photo/voice/audio"}

        # File mode — пишем на диск; валидация по roots если есть
        out_dir = (
            Path(download_dir).expanduser().resolve()
            if download_dir
            else Path(tempfile.gettempdir())
        )
        out_dir = await _validate_against_roots(ctx, out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        progress_callback = None
        if ctx is not None:

            async def _on_progress(received: int, total: int) -> None:
                await ctx.report_progress(
                    progress=float(received),
                    total=float(total) if total else None,
                    message=f"скачано {received}/{total or '?'} байт",
                )

            progress_callback = _on_progress

        path = await client.download_media(
            msg, file=str(out_dir), thumb=thumb_index, progress_callback=progress_callback
        )
        return {"ok": True, "path": str(path)}

    @mcp.tool(annotations=READ_ONLY)
    async def get_media_info(chat: int | str, message_id: int) -> dict[str, Any]:
        """Метаданные медиа в сообщении (тип, размер, mime, dimensions, duration)."""
        client = await get_client()
        msg = await client.get_messages(normalize_chat(chat), ids=message_id)
        if msg is None or not msg.media:
            return {"ok": False, "reason": "Нет медиа"}
        info: dict[str, Any] = {"ok": True, "type": type(msg.media).__name__}
        if msg.document:
            info["mime_type"] = msg.document.mime_type
            info["size"] = msg.document.size
            for attr in msg.document.attributes:
                info[type(attr).__name__] = {k: v for k, v in attr.to_dict().items() if k != "_"}
        if msg.photo:
            info["photo_id"] = msg.photo.id
            info["sizes"] = [
                {"w": s.w, "h": s.h, "type": s.type}
                for s in (msg.photo.sizes or [])
                if hasattr(s, "w")
            ]
        return info
