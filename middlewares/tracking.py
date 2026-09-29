from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from database import get_or_create_user, increment_user_query


class UserTrackingMiddleware(BaseMiddleware):
    """
    Middleware to ensure every user is recorded in SQLite database,
    fetch their preferences (language, theme), and track query statistics.
    """
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user = None
        if isinstance(event, (Message, CallbackQuery)) and event.from_user:
            user = event.from_user

        if user:
            db_user = await get_or_create_user(
                user_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            # Inject language and theme into handler data context
            data["user_lang"] = db_user.get("language", "en")
            data["user_theme"] = db_user.get("theme", "cyberpunk")
            data["db_user"] = db_user

            if isinstance(event, Message) and event.text and not event.text.startswith("/start"):
                await increment_user_query(user.id)

        return await handler(event, data)
