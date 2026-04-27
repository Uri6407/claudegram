"""Одноразовый интерактивный логин в Telegram.

Запуск:
    uv run python -m server.auth

Скрипт запросит код из Telegram (и пароль 2FA, если включён),
после чего создаст файл сессии. Дальше MCP-сервер сможет
работать без интерактива.
"""

from __future__ import annotations

import asyncio

from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

from server.config import Config


async def main() -> None:
    cfg = Config.load()
    client = TelegramClient(str(cfg.session_path), cfg.api_id, cfg.api_hash)

    await client.connect()
    if await client.is_user_authorized():
        me = await client.get_me()
        print(f"Уже авторизован как {me.first_name} (@{me.username}) id={me.id}")
        await client.disconnect()
        return

    print(f"Отправляю код на {cfg.phone}…")
    sent = await client.send_code_request(cfg.phone)
    code = input("Код из Telegram: ").strip()
    try:
        await client.sign_in(phone=cfg.phone, code=code, phone_code_hash=sent.phone_code_hash)
    except SessionPasswordNeededError:
        password = cfg.twofa_password or input("Пароль 2FA: ").strip()
        await client.sign_in(password=password)

    me = await client.get_me()
    print(f"Готово. Залогинен как {me.first_name} (@{me.username}) id={me.id}")
    print(f"Session-файл: {cfg.session_path}.session")
    await client.disconnect()


def cli() -> None:
    """Entry point для `claudegram-auth` console-script."""
    asyncio.run(main())


if __name__ == "__main__":
    cli()
