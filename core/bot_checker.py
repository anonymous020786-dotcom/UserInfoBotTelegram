import aiohttp
from typing import Dict, Any


async def check_bot_token(token: str) -> Dict[str, Any]:
    """
    Validates a Telegram Bot Token via official Bot API and extracts bot capabilities.
    """
    clean_token = token.strip()
    base_url = f"https://api.telegram.org/bot{clean_token}"

    timeout = aiohttp.ClientTimeout(total=8)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            # 1. Test getMe
            async with session.get(f"{base_url}/getMe") as resp:
                if resp.status != 200:
                    data = await resp.json()
                    return {
                        "is_valid": False,
                        "error": data.get("description", "Invalid bot token or unauthorized.")
                    }
                bot_info = (await resp.json()).get("result", {})

            # 2. Test getWebhookInfo
            webhook_info = {}
            try:
                async with session.get(f"{base_url}/getWebhookInfo") as resp:
                    if resp.status == 200:
                        webhook_info = (await resp.json()).get("result", {})
            except Exception:
                pass

            # 3. Test getMyCommands
            commands_info = []
            try:
                async with session.get(f"{base_url}/getMyCommands") as resp:
                    if resp.status == 200:
                        commands_info = (await resp.json()).get("result", [])
            except Exception:
                pass

            return {
                "is_valid": True,
                "bot_id": bot_info.get("id"),
                "first_name": bot_info.get("first_name"),
                "username": bot_info.get("username"),
                "can_join_groups": bot_info.get("can_join_groups", False),
                "can_read_all_group_messages": bot_info.get("can_read_all_group_messages", False),
                "supports_inline_queries": bot_info.get("supports_inline_queries", False),
                "can_connect_to_business": bot_info.get("can_connect_to_business", False),
                "webhook_url": webhook_info.get("url") or "None (Polling Mode)",
                "pending_updates": webhook_info.get("pending_update_count", 0),
                "last_error_message": webhook_info.get("last_error_message"),
                "command_count": len(commands_info)
            }
        except Exception as e:
            return {
                "is_valid": False,
                "error": f"Connection failed: {str(e)}"
            }
