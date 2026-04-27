"""MCP prompts — переиспользуемые шаблоны для типичных Telegram-задач.

Prompts в MCP — это slash-командные шаблоны, которые клиент показывает юзеру
в quick-picker. В отличие от tools они не вызываются моделью автоматически —
это явные точки входа в workflow.

Каждый prompt возвращает текст, который Claude должен выполнить, опираясь
на наши tools (`mcp__plugin_claudegram_claudegram__*`) и resources.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


def register(mcp: FastMCP) -> None:
    @mcp.prompt(
        title="Telegram: digest по непрочитанным",
        description="Сводка непрочитанных сообщений по всем чатам.",
    )
    def tg_digest(top_n: int = 10) -> str:
        return (
            f"Сделай краткий digest. Шаги:\n"
            f"1. Прочитай ресурс telegram://chats — выбери top {top_n} чатов с unread_count > 0.\n"
            f"2. Для каждого вызови get_history(chat=<id>, limit=unread_count).\n"
            f"3. Сгруппируй по приоритету: личные сообщения / упоминания / каналы.\n"
            f"4. Дай короткое summary каждого блока (одна-две фразы про suть).\n"
            f"5. НЕ зови mark_read."
        )

    @mcp.prompt(
        title="Telegram: поиск по чатам",
        description="Найти все упоминания темы во всех чатах или в одном.",
    )
    def tg_search(query: str, chat: str | None = None, limit: int = 30) -> str:
        scope = f"в чате {chat}" if chat else "глобально по всем чатам"
        return (
            f"Поиск '{query}' {scope}.\n"
            f"1. Если chat задан — search_messages(query='{query}', chat='{chat}', limit={limit}).\n"
            f"   Иначе — search_messages(query='{query}', limit={limit}) (глобально).\n"
            f"2. Сгруппируй результаты по чату.\n"
            f"3. Для топ-5 наиболее релевантных — покажи 1-2 строки контекста и ссылку telegram://msg/<chat>/<id>."
        )

    @mcp.prompt(
        title="Telegram: черновик ответа",
        description="Составить ответ на конкретное сообщение, дождаться подтверждения.",
    )
    def tg_draft_reply(chat: str, message_id: int, tone: str = "neutral") -> str:
        return (
            f"Помоги ответить в {chat} на сообщение {message_id} (тон: {tone}).\n"
            f"1. Прочитай ресурс telegram://msg/{chat}/{message_id} — увидишь контекст.\n"
            f"2. Прочитай telegram://chat/{chat}/history — пойми тон диалога.\n"
            f"3. Составь черновик в блоке кода.\n"
            f"4. Жди от меня 'отправляй'.\n"
            f"5. Только потом — send_message(chat='{chat}', text=<draft>, reply_to={message_id})."
        )

    @mcp.prompt(
        title="Telegram: summary треда",
        description="Резюме треда сообщений в чате (опираясь на reply-цепочку).",
    )
    def tg_summarize_thread(chat: str, root_message_id: int) -> str:
        return (
            f"Резюме треда вокруг сообщения {root_message_id} в {chat}.\n"
            f"1. get_history(chat='{chat}', reply_to={root_message_id}, limit=200) — все ответы треда.\n"
            f"2. get_history(chat='{chat}', ids=[{root_message_id}]) — корневое.\n"
            f"3. Хронологически объедини, сгруппируй по участникам.\n"
            f"4. Резюме 3-5 пунктов: тема, ключевые позиции, итог/решение."
        )

    @mcp.prompt(
        title="Telegram: weekly roundup",
        description="Сводка активности за последнюю неделю (по папке или всем диалогам).",
    )
    def tg_weekly_roundup(folder: str | None = None) -> str:
        scope = (
            f"папке '{folder}' (используй telegram://folders для resolve)"
            if folder
            else "всем диалогам (telegram://chats)"
        )
        return (
            f"Roundup за последние 7 дней по {scope}.\n"
            f"1. Получи список чатов из ресурса.\n"
            f"2. Для каждого — get_history(chat=<id>, limit=200) и отфильтруй по date >= now-7d.\n"
            f"3. Сгруппируй: новые контакты / горячие обсуждения / редкие, но важные.\n"
            f"4. Покажи 5-7 buллетов общим итогом + 3-5 конкретных action items, на которые стоит ответить."
        )

    @mcp.prompt(
        title="Telegram: триаж inbox",
        description="Сортировка непрочитанных по срочности.",
    )
    def tg_triage_inbox() -> str:
        return (
            "Триаж непрочитанных:\n"
            "1. telegram://chats → unread_count > 0.\n"
            "2. Для каждого — get_history(limit=unread_count).\n"
            "3. Классифицируй: 🔴 срочно (требует ответа сегодня), 🟡 информативно, 🟢 можно игнорить, "
            "📌 содержит action item.\n"
            "4. Покажи список с короткой причиной для каждого.\n"
            "5. На срочные — предложи готовый draft ответа (но НЕ отправляй сам)."
        )

    @mcp.prompt(
        title="Telegram: модерация чата",
        description="Аудит участников и активности группы (только для админов).",
    )
    def tg_moderate_chat(chat: str, days: int = 7) -> str:
        return (
            f"Аудит чата {chat} за последние {days} дней.\n"
            f"1. get_chat_info(chat='{chat}') — проверь, что я админ.\n"
            f"2. get_admin_log(chat='{chat}', limit=200) — действия админов.\n"
            f"3. get_participants(chat='{chat}', limit=200) — текущие участники.\n"
            f"4. get_history(chat='{chat}', limit=200) — последние сообщения.\n"
            f"5. Доклад: подозрительные паттерны (массовые join, спам-сигнатуры, флуд).\n"
            f"6. Никаких kick/ban/mute без явной моей команды."
        )
