## Что меняется

<!-- 1-3 коротких пункта -->

## Зачем

<!-- проблема / контекст / ссылка на issue -->

Closes #

## Тип изменения

- [ ] Bug fix
- [ ] Новый tool / skill / hook
- [ ] Refactor
- [ ] Документация
- [ ] CI / build / chore

## Чек-лист

- [ ] `uv run ruff check . && uv run ruff format --check .`
- [ ] `uv run mypy server tests` (или объяснил почему игнор)
- [ ] `uv run pytest`
- [ ] Обновлён `CHANGELOG.md` (если user-visible)
- [ ] Обновлены `plugin.json` / `marketplace.json` версии (если breaking)
- [ ] Если новый деструктивный tool — добавлен `PreToolUse` hook
- [ ] Не вставлял секреты (`api_hash`, `2fa_password`, содержимое `*.session`)

## Скриншоты / лог (опц.)
