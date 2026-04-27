"""Messages — send, edit, delete, forward."""

from __future__ import annotations

from datetime import UTC
from typing import Any

from mcp.server.fastmcp import Context

from server.client import get_client
from server.formatters import message_brief
from server.tools._common import (
    DESTRUCTIVE,
    NON_DESTRUCTIVE,
    ParseMode,
    confirm_or_abort,
    normalize_chat,
    parse_mode_arg,
)


def register(mcp: Any) -> None:
    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def send_message(
        chat: int | str,
        text: str,
        reply_to: int | None = None,
        silent: bool = False,
        parse_mode: ParseMode = "markdown",
        link_preview: bool = True,
        schedule_unix: int | None = None,
        comment_to: int | None = None,
        clear_draft: bool = False,
    ) -> dict[str, Any]:
        """Отправить текстовое сообщение.

        Args:
            chat: id или @username получателя.
            text: текст сообщения.
            reply_to: id сообщения, на которое отвечаем.
            silent: без звука уведомления.
            parse_mode: 'markdown', 'html' или 'none' для plain-text.
            link_preview: показывать превью первой ссылки.
            schedule_unix: если задан — отправить отложенно на UNIX-таймстамп (UTC).
            comment_to: id поста в канале — отправить как комментарий
                (требует у канала включённой обсуждаемой группы).
            clear_draft: очистить draft чата после отправки.
        """
        from datetime import datetime

        client = await get_client()
        schedule = datetime.fromtimestamp(schedule_unix, tz=UTC) if schedule_unix else None
        msg = await client.send_message(
            normalize_chat(chat),
            text,
            reply_to=reply_to,
            silent=silent,
            parse_mode=parse_mode_arg(parse_mode),
            link_preview=link_preview,
            schedule=schedule,
            comment_to=comment_to,
            clear_draft=clear_draft,
        )
        return message_brief(msg)

    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def edit_message(
        chat: int | str,
        message_id: int,
        text: str,
        parse_mode: ParseMode = "markdown",
        link_preview: bool = True,
    ) -> dict[str, Any]:
        """Отредактировать своё сообщение."""
        client = await get_client()
        msg = await client.edit_message(
            normalize_chat(chat),
            message_id,
            text,
            parse_mode=parse_mode_arg(parse_mode),
            link_preview=link_preview,
        )
        return message_brief(msg)

    @mcp.tool(annotations=DESTRUCTIVE)
    async def delete_message(
        chat: int | str,
        message_ids: list[int],
        revoke: bool = False,
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        """Удалить сообщения. По умолчанию — только у себя.

        Args:
            revoke: True — у всех (необратимо). При revoke=True вызывает elicit
                для подтверждения и параллельно срабатывает PreToolUse hook.
        """
        if revoke and (
            abort := await confirm_or_abort(
                ctx,
                action="delete_message(revoke=True)",
                target=f"{chat}: {message_ids}",
                extra="Удаление у всех необратимо.",
            )
        ):
            return abort
        client = await get_client()
        affected = await client.delete_messages(normalize_chat(chat), message_ids, revoke=revoke)
        return {"deleted_count": sum(getattr(a, "pts_count", 0) for a in affected)}

    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def forward_message(
        from_chat: int | str,
        message_ids: list[int],
        to_chat: int | str,
        silent: bool = False,
        drop_author: bool = False,
    ) -> list[dict[str, Any]]:
        """Переслать сообщения из одного чата в другой."""
        client = await get_client()
        forwarded = await client.forward_messages(
            normalize_chat(to_chat),
            message_ids,
            normalize_chat(from_chat),
            silent=silent,
            drop_author=drop_author,
        )
        if forwarded is None:
            return []
        if not isinstance(forwarded, list):
            forwarded = [forwarded]
        return [message_brief(m) for m in forwarded if m is not None]
