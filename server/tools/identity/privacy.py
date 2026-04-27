"""Privacy — настройки видимости профиля (last seen, фото, звонки и т.д.)."""

from __future__ import annotations

from typing import Any

from telethon.tl.functions.account import GetPrivacyRequest, SetPrivacyRequest
from telethon.tl.types import (
    InputPrivacyKeyAbout,
    InputPrivacyKeyAddedByPhone,
    InputPrivacyKeyBirthday,
    InputPrivacyKeyChatInvite,
    InputPrivacyKeyForwards,
    InputPrivacyKeyPhoneCall,
    InputPrivacyKeyPhoneNumber,
    InputPrivacyKeyPhoneP2P,
    InputPrivacyKeyProfilePhoto,
    InputPrivacyKeyStatusTimestamp,
    InputPrivacyKeyVoiceMessages,
    InputPrivacyValueAllowAll,
    InputPrivacyValueAllowCloseFriends,
    InputPrivacyValueAllowContacts,
    InputPrivacyValueDisallowAll,
    InputPrivacyValueDisallowContacts,
)

from server.client import get_client
from server.tools._common import NON_DESTRUCTIVE, READ_ONLY

PRIVACY_KEYS = {
    "last_seen": InputPrivacyKeyStatusTimestamp,
    "profile_photo": InputPrivacyKeyProfilePhoto,
    "phone_call": InputPrivacyKeyPhoneCall,
    "phone_p2p": InputPrivacyKeyPhoneP2P,
    "phone_number": InputPrivacyKeyPhoneNumber,
    "added_by_phone": InputPrivacyKeyAddedByPhone,
    "forwards": InputPrivacyKeyForwards,
    "chat_invite": InputPrivacyKeyChatInvite,
    "voice_messages": InputPrivacyKeyVoiceMessages,
    "about": InputPrivacyKeyAbout,
    "birthday": InputPrivacyKeyBirthday,
}

PRIVACY_VALUES = {
    "everyone": InputPrivacyValueAllowAll,
    "contacts": InputPrivacyValueAllowContacts,
    "close_friends": InputPrivacyValueAllowCloseFriends,
    "nobody": InputPrivacyValueDisallowAll,
    "nobody_contacts": InputPrivacyValueDisallowContacts,
}


def register(mcp: Any) -> None:
    @mcp.tool(annotations=READ_ONLY)
    async def get_privacy(key: str) -> dict[str, Any]:
        """Получить текущие privacy-настройки для указанного ключа.

        Args:
            key: один из `last_seen`, `profile_photo`, `phone_call`, `phone_p2p`,
                `phone_number`, `added_by_phone`, `forwards`, `chat_invite`,
                `voice_messages`, `about`, `birthday`.
        """
        if key not in PRIVACY_KEYS:
            return {"ok": False, "error": f"unknown key: {key}", "valid_keys": list(PRIVACY_KEYS)}
        client = await get_client()
        result = await client(GetPrivacyRequest(key=PRIVACY_KEYS[key]()))
        rules = [type(r).__name__ for r in getattr(result, "rules", [])]
        return {"ok": True, "key": key, "rules": rules}

    @mcp.tool(annotations=NON_DESTRUCTIVE)
    async def set_privacy(key: str, value: str = "everyone") -> dict[str, Any]:
        """Установить privacy для указанного ключа.

        Args:
            key: см. get_privacy.
            value: 'everyone', 'contacts', 'close_friends', 'nobody', 'nobody_contacts'.
        """
        if key not in PRIVACY_KEYS:
            return {"ok": False, "error": f"unknown key: {key}"}
        if value not in PRIVACY_VALUES:
            return {"ok": False, "error": f"unknown value: {value}"}
        client = await get_client()
        result = await client(
            SetPrivacyRequest(key=PRIVACY_KEYS[key](), rules=[PRIVACY_VALUES[value]()])
        )
        rules = [type(r).__name__ for r in getattr(result, "rules", [])]
        return {"ok": True, "key": key, "value": value, "rules": rules}
