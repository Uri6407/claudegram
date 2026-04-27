"""Polls — создание, голосование, результаты."""

from __future__ import annotations

from typing import Any

from telethon.tl.functions.messages import GetPollResultsRequest, SendVoteRequest
from telethon.tl.types import (
    InputMediaPoll,
    Poll,
    PollAnswer,
    TextWithEntities,
)

from server.client import get_client
from server.formatters import message_brief
from server.tools._common import NON_DESTRUCTIVE, READ_ONLY, normalize_chat


def _twe(text: str) -> TextWithEntities:
    """Wrapper для нового MTProto-формата TextWithEntities."""
    return TextWithEntities(text=text, entities=[])


def register(mcp: Any) -> None:
    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def send_poll(
        chat: int | str,
        question: str,
        options: list[str],
        anonymous: bool = True,
        multiple_choice: bool = False,
        quiz: bool = False,
        correct_option_index: int | None = None,
        explanation: str = "",
        close_period_seconds: int | None = None,
        close_unix: int | None = None,
        revoting_disabled: bool = False,
        shuffle_answers: bool = False,
        silent: bool = False,
    ) -> dict[str, Any]:
        """Создать и отправить опрос.

        Args:
            options: 2-10 вариантов ответа.
            anonymous: голоса без видимости кто как голосовал.
            multiple_choice: можно выбрать несколько вариантов.
            quiz: режим викторины (один правильный ответ + объяснение).
            correct_option_index: индекс правильного варианта (для quiz=True).
            explanation: пояснение, показываемое после голосования (quiz).
            close_period_seconds: автозакрытие через N секунд (5-600 на момент API layer 215).
            close_unix: автозакрытие на UNIX-таймстамп.
            revoting_disabled: True — нельзя сменить голос (для викторин).
            shuffle_answers: True — порядок вариантов рандомизируется на каждом устройстве.
        """
        if not 2 <= len(options) <= 10:
            return {"ok": False, "reason": "Нужно 2-10 вариантов"}
        from datetime import datetime

        client = await get_client()
        answers = [PollAnswer(text=_twe(opt), option=bytes([i])) for i, opt in enumerate(options)]
        poll = Poll(
            id=0,
            question=_twe(question),
            answers=answers,
            hash=0,
            public_voters=not anonymous,
            multiple_choice=multiple_choice,
            quiz=quiz,
            close_period=close_period_seconds,
            close_date=datetime.fromtimestamp(close_unix) if close_unix else None,
            revoting_disabled=revoting_disabled,
            shuffle_answers=shuffle_answers,
        )
        # correct_answers — bytes список, по одному на правильный вариант (для quiz max 1)
        correct_answers = (
            [bytes([correct_option_index])] if quiz and correct_option_index is not None else None
        )
        media = InputMediaPoll(
            poll=poll,
            correct_answers=correct_answers,
            solution=explanation if (quiz and explanation) else None,
            solution_entities=[] if (quiz and explanation) else None,
        )
        msg = await client.send_file(normalize_chat(chat), media, silent=silent)
        return message_brief(msg)

    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def vote_poll(
        chat: int | str,
        message_id: int,
        option_indices: list[int],
    ) -> dict[str, Any]:
        """Проголосовать в poll.

        Args:
            option_indices: 0-based индексы выбранных вариантов
                (один — для обычного, несколько — для multiple_choice).
        """
        client = await get_client()
        peer = await client.get_input_entity(normalize_chat(chat))
        await client(
            SendVoteRequest(
                peer=peer,
                msg_id=message_id,
                options=[bytes([i]) for i in option_indices],
            )
        )
        return {"ok": True, "voted": option_indices}

    @mcp.tool(annotations=READ_ONLY)
    async def get_poll_results(chat: int | str, message_id: int) -> dict[str, Any]:
        """Текущие результаты опроса (количество голосов на вариант)."""
        client = await get_client()
        peer = await client.get_input_entity(normalize_chat(chat))
        result = await client(GetPollResultsRequest(peer=peer, msg_id=message_id))
        # Достаём poll-update внутри обновлений
        results: list[dict[str, Any]] = []
        for upd in getattr(result, "updates", []):
            poll_results = getattr(upd, "results", None)
            if poll_results is None:
                continue
            for r in getattr(poll_results, "results", []) or []:
                results.append(
                    {
                        "option_byte": r.option.hex(),
                        "voters": r.voters,
                        "chosen": getattr(r, "chosen", False),
                        "correct": getattr(r, "correct", False),
                    }
                )
        return {"ok": True, "results": results}
