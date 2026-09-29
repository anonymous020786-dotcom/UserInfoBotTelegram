import time
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from config import RATE_LIMIT_DELAY
from ui.locales import get_text


class ThrottlingMiddleware(BaseMiddleware):
    """
    Sliding window anti-flood middleware to protect bot from rapid spamming
    and prevent Telegram API 429 Too Many Requests errors.
    """
    def __init__(self, delay: float = RATE_LIMIT_DELAY):
        self.delay = delay
        self.last_seen: Dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user_id = None
        if isinstance(event, (Message, CallbackQuery)) and event.from_user:
            user_id = event.from_user.id

        if user_id:
            now = time.monotonic()
            last_time = self.last_seen.get(user_id, 0.0)

            if now - last_time < self.delay:
                # User is sending updates too quickly
                if isinstance(event, Message):
                    await event.reply("⏳ <i>Please wait a moment before sending another request...</i>", parse_mode="HTML")
                elif isinstance(event, CallbackQuery):
                    await event.answer("⏳ Please slow down!", show_alert=False)
                return

            self.last_seen[user_id] = now

        return await handler(event, data)
