import asyncio
import logging
from typing import Optional, Dict, Any
from telethon import TelegramClient
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.types import User, Channel, Chat

from config import API_ID, API_HASH, BOT_TOKEN, SESSION_STRING

logger = logging.getLogger(__name__)

_telethon_client: Optional[TelegramClient] = None


async def get_telethon_client() -> Optional[TelegramClient]:
    """
    Initializes or returns existing Telethon MTProto client if credentials are configured.
    """
    global _telethon_client
    if _telethon_client and _telethon_client.is_connected():
        return _telethon_client

    if not API_ID or not API_HASH:
        return None

    try:
        session_name = "data/sentinel_mtproto"
        client = TelegramClient(session_name, API_ID, API_HASH)
        
        if SESSION_STRING:
            await client.start(session=SESSION_STRING)
        elif BOT_TOKEN:
            await client.start(bot_token=BOT_TOKEN)
        else:
            return None

        _telethon_client = client
        logger.info("MTProto Telethon client connected successfully.")
        return _telethon_client
    except Exception as e:
        logger.warning(f"Could not connect MTProto Telethon engine: {e}")
        return None


async def deep_mtproto_lookup(identifier: str) -> Optional[Dict[str, Any]]:
    """
    Performs deep MTProto lookup using Telethon if client is active.
    """
    client = await get_telethon_client()
    if not client:
        return None

    try:
        entity = await client.get_entity(identifier)
        if isinstance(entity, User):
            try:
                full = await client(GetFullUserRequest(entity))
                about = full.full_user.about
            except Exception:
                about = None

            return {
                "source": "MTProto",
                "id": entity.id,
                "first_name": entity.first_name,
                "last_name": entity.last_name,
                "username": entity.username,
                "phone": entity.phone if hasattr(entity, 'phone') else None,
                "is_bot": entity.bot,
                "is_verified": entity.verified,
                "is_restricted": entity.restricted,
                "is_scam": entity.scam,
                "is_fake": entity.fake,
                "is_premium": getattr(entity, 'premium', False),
                "bio": about,
                "dc_id": getattr(entity.photo, 'dc_id', None) if entity.photo else None
            }

        elif isinstance(entity, (Channel, Chat)):
            try:
                full_channel = await client(GetFullChannelRequest(entity))
                about = full_channel.full_chat.about
                participants_count = full_channel.full_chat.participants_count
                linked_chat_id = full_channel.full_chat.linked_chat_id
            except Exception:
                about = getattr(entity, 'title', '')
                participants_count = None
                linked_chat_id = None

            return {
                "source": "MTProto",
                "id": entity.id,
                "title": entity.title,
                "username": getattr(entity, 'username', None),
                "is_broadcast": getattr(entity, 'broadcast', False),
                "is_megagroup": getattr(entity, 'megagroup', False),
                "is_verified": entity.verified,
                "is_scam": entity.scam,
                "is_fake": entity.fake,
                "members_count": participants_count,
                "bio": about,
                "linked_chat_id": linked_chat_id,
                "dc_id": getattr(entity.photo, 'dc_id', None) if entity.photo else None
            }
    except Exception as e:
        logger.debug(f"MTProto lookup failed for {identifier}: {e}")
        return None
