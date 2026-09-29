import datetime
from aiogram import Router, F, Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from ui.formatters import format_forward_report
from ui.keyboards import user_actions_keyboard
from core.telegram_discovery import resolve_full_entity
from database import is_favorite

router = Router(name="forward_inspector_router")


@router.message(F.forward_origin | F.forward_date | F.forward_from | F.forward_from_chat)
async def handle_forwarded_message(message: Message, user_theme: str = "cyberpunk", user_lang: str = "en", bot: Bot = None):
    """
    Forensic inspector for forwarded messages: extracts hidden sender, original date,
    message ID, and chat origin.
    """
    origin = message.forward_origin
    sender_id = None
    sender_name = None
    sender_username = None
    chat_id = None
    chat_title = None
    msg_id = None
    origin_type = "legacy_forward"
    date_str = "Unknown"

    if origin:
        origin_type = origin.type  # 'user', 'hidden_user', 'chat', 'channel'
        dt = datetime.datetime.fromtimestamp(origin.date.timestamp() if hasattr(origin.date, 'timestamp') else origin.date)
        date_str = dt.strftime("%Y-%m-%d %H:%M:%S UTC")

        if origin.type == "user":
            u = origin.sender_user
            sender_id = u.id
            sender_name = f"{u.first_name} {u.last_name or ''}".strip()
            sender_username = u.username
        elif origin.type == "hidden_user":
            sender_name = origin.sender_user_name
        elif origin.type == "chat":
            c = origin.sender_chat
            chat_id = c.id
            chat_title = c.title
        elif origin.type == "channel":
            c = origin.chat
            chat_id = c.id
            chat_title = c.title
            msg_id = getattr(origin, "message_id", None)

    else:
        # Legacy Bot API fallback
        if message.forward_date:
            date_str = message.forward_date.strftime("%Y-%m-%d %H:%M:%S UTC")
        if message.forward_from:
            u = message.forward_from
            sender_id = u.id
            sender_name = f"{u.first_name} {u.last_name or ''}".strip()
            sender_username = u.username
            origin_type = "user"
        elif message.forward_from_chat:
            c = message.forward_from_chat
            chat_id = c.id
            chat_title = c.title
            msg_id = message.forward_from_message_id
            origin_type = c.type
        elif message.forward_sender_name:
            sender_name = message.forward_sender_name
            origin_type = "hidden_user"

    data = {
        "origin_type": origin_type,
        "date_str": date_str,
        "sender_id": sender_id,
        "sender_name": sender_name,
        "sender_username": sender_username,
        "chat_id": chat_id,
        "chat_title": chat_title,
        "message_id": msg_id
    }

    report = format_forward_report(data)

    buttons = []
    if sender_id:
        buttons.append([
            InlineKeyboardButton(text="🔍 Deep Inspect User", callback_data=f"query_chat_{sender_id}"),
            InlineKeyboardButton(text="🪪 Generate ID Card", callback_data=f"exp_card_{sender_id}")
        ])
    elif chat_id:
        buttons.append([
            InlineKeyboardButton(text="🔍 Deep Inspect Origin Chat", callback_data=f"query_chat_{chat_id}")
        ])

    buttons.append([InlineKeyboardButton(text="🏠 Home Menu", callback_data="nav_home")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await message.reply(report, reply_markup=kb, parse_mode="HTML")
