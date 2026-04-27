# Contributing to Claudegram

## Dev environment

```bash
git clone <repo>
cd Claudegram
uv sync --all-groups          # установит deps + ruff/mypy/pytest
cp .env.example .env          # для standalone-тестирования
uv run python -m server.auth  # одноразовый Telegram-логин
```

## Quality gates

Before opening a PR:

```bash
uv run ruff check server/ tests/      # должно быть "All checks passed!"
uv run ruff format server/ tests/     # auto-format
uv run mypy server/                   # пока не strict, но не должно ломаться
uv run pytest tests/ --cov            # все тесты passing, coverage ≥ 40%
```

CI workflow (`.github/workflows/ci.yml`) запускает то же самое на каждый PR.

## Adding a new tool

1. Найди правильный домен:

   | Если tool про… | Домен |
   |---|---|
   | мой собственный аккаунт / профиль / сессии | `identity/` |
   | поиск или метаданные сущностей | `peers/` |
   | отправку/чтение сообщений в чате | `messaging/` |
   | список диалогов или их состояния | `dialogs/` |
   | управление группой/каналом (admin) | `chats/` |
   | файлы / медиа / стикеры / голосовые | `media/` |
   | контентные фичи (polls/stories/forums/payments) | `content/` |
   | inline-боты / callbacks / games | `interactions/` |
   | escape hatch / низкоуровневое | `advanced/` |

2. Найди подходящий подмодуль или создай новый `<domain>/<name>.py`.

3. Если новый файл — добавь его в `<domain>/__init__.py:register()`.

4. Сигнатура tool:

   ```python
   from server.client import get_client
   from server.middleware import safe_tool
   from server.tools._common import normalize_chat

   @mcp.tool()
   @safe_tool                                    # ← обязательно для production
   async def my_tool(chat: int | str) -> dict[str, Any]:
       """Краткое описание (Claude видит как description).

       Args:
           chat: id или @username.
       """
       client = await get_client()
       # ...
       return {"ok": True}
   ```

5. Сверь сигнатуру вызываемого Telethon-метода:

   ```bash
   uv run python -c "
   import inspect
   from telethon.tl.functions.<module> import <Method>Request
   print(inspect.signature(<Method>Request.__init__))
   "
   ```

6. Если tool **деструктивный** — добавь имя в `hooks/hooks.json` под
   `guard-destructive` или `guard-confirm` matcher.

7. Напиши тест в `tests/test_<domain>_<module>.py` или расширь
   `tests/test_main_registration.py:test_required_tools_present.expected`.

## Adding a new domain

1. `mkdir server/tools/<new_domain>/`
2. Создать `__init__.py` с `register(mcp)` и подмодулями
3. Добавить `<new_domain>.register(mcp)` в `server/tools/__init__.py:register_all`

## Commits

Conventional Commits style:
```
feat(content/payments): add gift_premium tool
fix(messaging/messages): correct parse_mode default
docs(SECURITY): document hook coverage
test(channel): cover MessageEdited handler
```

## Telegram API breaking changes

Telegram периодически меняет MTProto schema (новые поля, deprecate'ы).
Если PR падает на CI с `TypeError: unexpected keyword argument` — это
означает, что Telethon обновился и параметры тула расходятся со схемой.

Подход: всегда сверять через `inspect.signature()` Telethon-класса, как
в чек-листе пункта 5 выше. См. `CHANGELOG.md` "Sync с Telethon" entries.

## Release process

1. Bump version в `pyproject.toml` и `.claude-plugin/plugin.json` (один и тот же)
2. Добавить запись в `CHANGELOG.md` под `## [X.Y.Z]`
3. `git tag claudegram--vX.Y.Z`
4. `git push --tags` → GitHub Action `release.yml` создаст релиз

## Code style

- Никаких комментариев, дублирующих код. Только когда _почему_ не очевидно.
- Type-hints везде, даже в private.
- `from __future__ import annotations` в каждом модуле (для PEP 563).
- Async всегда, даже для оборачиваемых sync-вызовов.
- Имена tools: `snake_case`, существительное-глагол (`send_message`, `get_history`).
- Имена файлов: `snake_case.py`.
- Имена доменов/подмодулей: `snake_case` без подчёркивания префиксом
  (исключение: `_common.py` — приватный shared util).
