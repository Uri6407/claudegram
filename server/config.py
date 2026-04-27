"""Загрузка конфига.

Поддерживаются два режима:

1. **Plugin mode** — Claude Code запускает MCP-сервер с подставленными
   `${user_config.*}` в env (а также `CLAUDE_PLUGIN_OPTION_TG_API_ID` и т.д.,
   которые экспортируются автоматически в дочерние процессы плагина).
   Session-файл живёт в `CLAUDEGRAM_DATA_DIR` (= `${CLAUDE_PLUGIN_DATA}`),
   чтобы переживать апдейты плагина.

2. **Standalone mode** — `uv run python -m server.main` вне плагина.
   Конфиг берётся из `.env` рядом с `pyproject.toml`. Session-файл
   ложится в корень проекта.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def _env(*names: str) -> str:
    """Вернуть первое непустое значение из списка имён переменных."""
    for n in names:
        v = os.environ.get(n, "").strip()
        if v:
            return v
    return ""


@dataclass(frozen=True)
class Config:
    api_id: int
    api_hash: str
    phone: str
    session_name: str
    session_path: Path
    twofa_password: str | None
    data_dir: Path

    @classmethod
    def load(cls) -> Config:
        api_id_raw = _env("TG_API_ID", "CLAUDE_PLUGIN_OPTION_TG_API_ID")
        api_hash = _env("TG_API_HASH", "CLAUDE_PLUGIN_OPTION_TG_API_HASH")
        phone = _env("TG_PHONE", "CLAUDE_PLUGIN_OPTION_TG_PHONE")
        # Telethon сам добавляет суффикс `.session`. Если юзер ввёл имя
        # с расширением (например "claudegram.session"), отрезаем —
        # иначе файл создастся как `claudegram.session.session` и оба
        # клиента (CLI auth и MCP server) разъедутся по разным путям.
        raw_session_name = (
            _env("TG_SESSION_NAME", "CLAUDE_PLUGIN_OPTION_TG_SESSION_NAME") or "claudegram"
        )
        session_name = raw_session_name.removesuffix(".session") or "claudegram"
        twofa = _env("TG_2FA_PASSWORD", "CLAUDE_PLUGIN_OPTION_TG_2FA_PASSWORD") or None

        data_dir_raw = _env("CLAUDEGRAM_DATA_DIR", "CLAUDE_PLUGIN_DATA")
        data_dir = Path(data_dir_raw).expanduser() if data_dir_raw else PROJECT_ROOT
        data_dir.mkdir(parents=True, exist_ok=True)

        missing = [
            k
            for k, v in {
                "TG_API_ID": api_id_raw,
                "TG_API_HASH": api_hash,
                "TG_PHONE": phone,
            }.items()
            if not v
        ]
        if missing:
            raise RuntimeError(
                f"Не заданы значения: {', '.join(missing)}. "
                "В режиме плагина — настрой через `/plugin` (поля userConfig). "
                "В standalone — заполни .env по образцу .env.example."
            )

        try:
            api_id = int(api_id_raw)
        except ValueError as exc:
            raise RuntimeError("TG_API_ID должен быть числом") from exc

        return cls(
            api_id=api_id,
            api_hash=api_hash,
            phone=phone,
            session_name=session_name,
            session_path=data_dir / session_name,
            twofa_password=twofa,
            data_dir=data_dir,
        )
