"""Payments — Telegram Stars баланс, транзакции, premium-промо."""

from __future__ import annotations

from typing import Any

from telethon.tl.functions.help import GetPremiumPromoRequest
from telethon.tl.functions.payments import (
    GetStarsStatusRequest,
    GetStarsTransactionsRequest,
)
from telethon.tl.types import InputPeerSelf

from server.client import get_client
from server.tools._common import READ_ONLY, clamp


def register(mcp: Any) -> None:
    @mcp.tool(annotations=READ_ONLY)
    async def get_stars_balance() -> dict[str, Any]:
        """Текущий баланс Telegram Stars (внутренняя валюта)."""
        client = await get_client()
        result = await client(GetStarsStatusRequest(peer=InputPeerSelf()))
        return {
            "balance": getattr(getattr(result, "balance", None), "amount", 0),
            "balance_nanos": getattr(getattr(result, "balance", None), "nanos", 0),
            "subscriptions_missing_balance": getattr(result, "subscriptions_missing_balance", 0),
        }

    @mcp.tool(annotations=READ_ONLY)
    async def get_stars_transactions(
        limit: int = 30,
        inbound: bool = False,
        outbound: bool = False,
        ascending: bool = False,
    ) -> list[dict[str, Any]]:
        """История Stars-транзакций (покупки/расходы).

        Args:
            inbound: только пополнения.
            outbound: только списания.
            ascending: True — старые первыми.
        """
        client = await get_client()
        result = await client(
            GetStarsTransactionsRequest(
                peer=InputPeerSelf(),
                offset="",
                limit=clamp(limit, 1, 100),
                inbound=inbound or None,
                outbound=outbound or None,
                ascending=ascending or None,
            )
        )
        return [
            {
                "id": t.id,
                "amount": getattr(getattr(t, "amount", None), "amount", 0),
                "date": t.date.isoformat() if getattr(t, "date", None) else None,
                "description": getattr(t, "description", None) or "",
                "refund": getattr(t, "refund", False),
            }
            for t in getattr(result, "history", [])
        ]

    @mcp.tool(annotations=READ_ONLY)
    async def get_premium_promo() -> dict[str, Any]:
        """Промо-материал Telegram Premium (фичи, цены)."""
        client = await get_client()
        result = await client(GetPremiumPromoRequest())
        return {
            "status_text": getattr(result, "status_text", "") or "",
            "video_sections": list(getattr(result, "video_sections", []) or []),
            "period_options_count": len(getattr(result, "period_options", []) or []),
        }
