"""Help API — общая инфа Telegram (config, country list, app config)."""

from __future__ import annotations

from typing import Any

from telethon.tl.functions.help import (
    GetAppConfigRequest,
    GetConfigRequest,
    GetCountriesListRequest,
    GetNearestDcRequest,
)

from server.client import get_client
from server.tools._common import READ_ONLY, to_jsonable


def register(mcp: Any) -> None:
    @mcp.tool(annotations=READ_ONLY)
    async def get_telegram_config() -> dict[str, Any]:
        """Базовый конфиг Telegram-сети (DC, лимиты файлов, edit_time_limit и т.д.)."""
        client = await get_client()
        cfg = await client(GetConfigRequest())
        return {
            "this_dc": getattr(cfg, "this_dc", None),
            "edit_time_limit": getattr(cfg, "edit_time_limit", None),
            "revoke_time_limit": getattr(cfg, "revoke_time_limit", None),
            "revoke_pm_time_limit": getattr(cfg, "revoke_pm_time_limit", None),
            "forwarded_count_max": getattr(cfg, "forwarded_count_max", None),
            "saved_gifs_limit": getattr(cfg, "saved_gifs_limit", None),
            "stickers_recent_limit": getattr(cfg, "stickers_recent_limit", None),
            "channels_read_media_period": getattr(cfg, "channels_read_media_period", None),
            "online_update_period_ms": getattr(cfg, "online_update_period_ms", None),
            "offline_blur_timeout_ms": getattr(cfg, "offline_blur_timeout_ms", None),
            "test_mode": getattr(cfg, "test_mode", None),
        }

    @mcp.tool(annotations=READ_ONLY)
    async def get_app_config() -> dict[str, Any]:
        """Конфигурация клиента (флаги фич, premium-лимиты, gifts и т.д.).

        Возвращает raw config JSON — много ключей, нужно искать по имени.
        """
        client = await get_client()
        result = await client(GetAppConfigRequest(hash=0))
        return to_jsonable(result)

    @mcp.tool(annotations=READ_ONLY)
    async def get_nearest_dc() -> dict[str, Any]:
        """Ближайший Telegram DC по geo (используется для оптимизации)."""
        client = await get_client()
        dc = await client(GetNearestDcRequest())
        return {
            "country": getattr(dc, "country", None),
            "this_dc": getattr(dc, "this_dc", None),
            "nearest_dc": getattr(dc, "nearest_dc", None),
        }

    @mcp.tool(annotations=READ_ONLY)
    async def get_countries_list(lang_code: str = "en") -> list[dict[str, Any]]:
        """Список всех стран с phone-кодами (для интерфейса добавления контактов).

        Args:
            lang_code: 'en', 'ru', etc. — язык названий.
        """
        client = await get_client()
        result = await client(GetCountriesListRequest(lang_code=lang_code, hash=0))
        countries = getattr(result, "countries", []) or []
        out = []
        for c in countries[:50]:  # ограничиваем размер ответа
            out.append(
                {
                    "iso2": c.iso2,
                    "default_name": c.default_name,
                    "name": getattr(c, "name", None) or c.default_name,
                    "country_codes": [
                        {"code": cc.country_code, "prefixes": list(cc.prefixes or [])}
                        for cc in (c.country_codes or [])
                    ],
                    "hidden": getattr(c, "hidden", False),
                }
            )
        return out
