"""Smoke-тест: все tools/resources/prompts регистрируются и валидны."""

from __future__ import annotations

import json

import pytest


@pytest.mark.asyncio
async def test_all_tools_have_valid_schemas() -> None:
    from server.main import mcp

    tools = await mcp.list_tools()
    assert len(tools) >= 120, f"ожидаем ≥120 tools, получили {len(tools)}"

    for t in tools:
        try:
            json.dumps(t.inputSchema)
        except (TypeError, ValueError) as exc:
            pytest.fail(f"tool {t.name}: невалидная JSON-схема — {exc}")

        assert t.name, "tool без name"
        assert t.description, f"tool {t.name} без description"
        assert isinstance(t.inputSchema, dict), f"{t.name}: inputSchema не dict"
        # Все tools должны иметь annotations (READ_ONLY/NON_DESTRUCTIVE/DESTRUCTIVE)
        assert t.annotations is not None, f"{t.name}: нет annotations"


@pytest.mark.asyncio
async def test_resources_and_prompts_registered() -> None:
    from server.main import mcp

    resources = await mcp.list_resources()
    templates = await mcp.list_resource_templates()
    prompts = await mcp.list_prompts()

    assert len(resources) >= 9, f"ожидаем ≥9 static resources, получили {len(resources)}"
    assert len(templates) >= 6, f"ожидаем ≥6 templates, получили {len(templates)}"
    assert len(prompts) >= 7, f"ожидаем ≥7 prompts, получили {len(prompts)}"


@pytest.mark.asyncio
async def test_structured_output_present() -> None:
    """Все tools имеют outputSchema (FastMCP автогенерация)."""
    from server.main import mcp

    tools = await mcp.list_tools()
    without_schema = [t.name for t in tools if not t.outputSchema]
    assert not without_schema, f"tools без outputSchema: {without_schema}"


@pytest.mark.asyncio
async def test_required_tools_present() -> None:
    """Smoke: ключевые tools каждого домена на месте."""
    from server.main import mcp

    tools = {t.name for t in await mcp.list_tools()}
    expected = {
        # identity/account
        "get_me",
        "update_profile",
        "set_online",
        "update_username",
        "get_full_user",
        # identity/sessions
        "get_authorizations",
        "terminate_authorization",
        # peers/lookup
        "resolve_username",
        "get_chat_info",
        "search_global",
        "get_top_peers",
        "get_input_peer",
        # peers/users
        "get_profile_photos",
        "download_profile_photo",
        "get_common_chats",
        # peers/contacts
        "get_contacts",
        "add_contact",
        "delete_contact",
        "import_contacts",
        "block_user",
        "unblock_user",
        "get_blocked",
        # messaging/messages
        "send_message",
        "edit_message",
        "delete_message",
        "forward_message",
        # messaging/history
        "get_history",
        "get_history_with_links",
        "search_messages",
        # messaging/typing
        "set_typing",
        # messaging/pins
        "pin_message",
        "unpin_message",
        # messaging/reactions
        "react_message",
        # dialogs
        "list_chats",
        "get_drafts",
        "archive_dialog",
        "unarchive_dialog",
        "pin_dialog",
        "mark_read",
        "mute_dialog",
        "unmute_dialog",
        "delete_dialog",
        # chats
        "create_group",
        "create_channel",
        "edit_chat_title",
        "edit_chat_about",
        "edit_chat_photo",
        "toggle_forum_mode",
        "get_participants",
        "kick_participant",
        "ban_participant",
        "unban_participant",
        "restrict_participant",
        "promote_admin",
        "demote_admin",
        "join_chat",
        "leave_chat",
        "export_chat_invite",
        "get_admin_log",
        "get_stats",
        # media
        "send_file",
        "send_album",
        "download_media",
        "get_media_info",
        "send_location",
        "send_contact",
        "send_dice",
        "get_installed_stickers",
        "get_sticker_set",
        "install_sticker_set",
        "uninstall_sticker_set",
        "search_sticker_sets",
        "send_sticker_by_id",
        # content
        "send_poll",
        "vote_poll",
        "get_poll_results",
        "get_all_stories",
        "get_peer_stories",
        "send_story",
        "get_forum_topics",
        "create_forum_topic",
        "edit_forum_topic",
        "delete_forum_topic",
        # advanced
        "invoke_raw",
        "health_check",
        "get_server_version",
        "summarize_chat",
    }
    missing = expected - tools
    assert not missing, f"отсутствуют tools: {sorted(missing)}"


@pytest.mark.asyncio
async def test_dangerous_tools_have_safety_hint() -> None:
    """delete_message default revoke=False — критическая защита."""
    from server.main import mcp

    tools = {t.name: t for t in await mcp.list_tools()}
    delete = tools["delete_message"]
    schema = delete.inputSchema
    # Параметр revoke есть и default=false
    assert "revoke" in schema["properties"]
    assert schema["properties"]["revoke"].get("default") is False
