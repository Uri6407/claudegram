"""MCP completions — autocomplete для аргументов prompts/resources.

Подхватывается клиентом, когда юзер начинает вводить аргумент prompt'а или
URI-template-параметр resource'а. Например, при вводе chat в `tg_digest`
клиент покажет список реальных чатов.

Регистрируем один глобальный completion handler через `@mcp.completion()`,
который дискриминирует по `ref` + `argument.name`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from mcp.types import (
    Completion,
    CompletionArgument,
    CompletionContext,
    PromptReference,
    ResourceTemplateReference,
)

from server.client import get_client

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


_EMOJI_REACTIONS = [
    "👍", "👎", "❤", "🔥", "🥰", "👏", "😁", "🤔", "🤯", "😱",
    "🤬", "😢", "🎉", "🤩", "🤮", "💩", "🙏", "👌", "🕊", "🤡",
    "🥱", "🥴", "😍", "🐳", "❤‍🔥", "🌚", "🌭", "💯", "🤣", "⚡",
    "🍌", "🏆", "💔", "🤨", "😐", "🍓", "🍾", "💋", "🖕", "😈",
    "😴", "😭", "🤓", "👻", "👨‍💻", "👀", "🎃", "🙈", "😇", "😨",
]


async def _suggest_chats(prefix: str, limit: int = 25) -> list[str]:
    try:
        client = await get_client()
    except Exception:
        return []
    pfx = (prefix or "").lower().lstrip("@")
    out: list[str] = []
    async for d in client.iter_dialogs(limit=200):
        name = (d.name or "").lower()
        username = (getattr(d.entity, "username", None) or "").lower()
        if not pfx or pfx in name or pfx in username:
            label = f"@{d.entity.username}" if getattr(d.entity, "username", None) else str(d.id)
            out.append(label)
            if len(out) >= limit:
                break
    return out


async def _suggest_emoji(prefix: str) -> list[str]:
    return [e for e in _EMOJI_REACTIONS if not prefix or prefix in e][:25]


async def _suggest_folders(prefix: str) -> list[str]:
    from telethon.tl.functions.messages import GetDialogFiltersRequest

    try:
        client = await get_client()
        result = await client(GetDialogFiltersRequest())
    except Exception:
        return []
    filters = getattr(result, "filters", None) or result
    if not isinstance(filters, list):
        return []
    pfx = (prefix or "").lower()
    out: list[str] = []
    for f in filters:
        title = str(getattr(f, "title", "") or "")
        if not pfx or pfx in title.lower():
            out.append(title)
    return out[:25]


def register(mcp: FastMCP) -> None:
    @mcp.completion()
    async def handle_completion(
        ref: PromptReference | ResourceTemplateReference,
        argument: CompletionArgument,
        context: CompletionContext | None,
    ) -> Completion | None:
        name = argument.name
        value = argument.value or ""

        # URI templates: telegram://chat/{chat_id}, telegram://msg/{chat_id}/{message_id}
        if isinstance(ref, ResourceTemplateReference):
            if name == "chat_id":
                values = await _suggest_chats(value)
                return Completion(values=values, total=len(values), hasMore=False)
            return None

        # Prompts: tg_digest / tg_search / tg_draft_reply / tg_weekly_roundup / ...
        if isinstance(ref, PromptReference):
            if name == "chat":
                values = await _suggest_chats(value)
                return Completion(values=values, total=len(values), hasMore=False)
            if name == "folder":
                values = await _suggest_folders(value)
                return Completion(values=values, total=len(values), hasMore=False)
            if name == "tone":
                tones = ["neutral", "friendly", "formal", "concise", "apologetic", "enthusiastic"]
                values = [t for t in tones if not value or value.lower() in t]
                return Completion(values=values, total=len(values), hasMore=False)
            if name in {"emoji", "reaction"}:
                values = await _suggest_emoji(value)
                return Completion(values=values, total=len(values), hasMore=False)

        return None
