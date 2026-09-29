import re
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from core.telegram_discovery import resolve_full_entity
from ui.formatters import format_user_report, format_channel_report, format_group_report
from ui.keyboards import user_actions_keyboard, channel_actions_keyboard, group_actions_keyboard
from database import record_search, log_identity, is_favorite

router = Router(name="user_info_router")


@router.message(Command("id"))
async def handle_my_id(message: Message, user_theme: str = "cyberpunk", user_lang: str = "en", bot: Bot = None):
    """Returns the caller's own Telegram ID and comprehensive profile card."""
    user = message.from_user
    data = await resolve_full_entity(str(user.id), bot=bot)
    if not data:
        await message.reply(f"🆔 <b>Your Telegram ID:</b> <code>{user.id}</code>", parse_mode="HTML")
        return

    fav = await is_favorite(user.id, data["id"])
    report = format_user_report(data, theme=user_theme)
    kb = user_actions_keyboard(data["id"], data["username"], is_fav=fav, lang=user_lang)
    await message.reply(report, reply_markup=kb, parse_mode="HTML")


@router.message(Command("info"))
async def handle_info_command(message: Message, user_theme: str = "cyberpunk", user_lang: str = "en", bot: Bot = None):
    """Processes /info <username or id> or replied message."""
    target = None
    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        target = args[1].strip()
    elif message.reply_to_message and message.reply_to_message.from_user:
        target = str(message.reply_to_message.from_user.id)
    else:
        target = str(message.from_user.id)

    await process_entity_lookup(message, target, user_theme, user_lang, bot)


@router.message(F.contact)
async def handle_contact_lookup(message: Message, user_theme: str = "cyberpunk", user_lang: str = "en", bot: Bot = None):
    """Extracts Telegram ID from sent contact card and looks up live data."""
    contact = message.contact
    if contact.user_id:
        await process_entity_lookup(message, str(contact.user_id), user_theme, user_lang, bot)
    else:
        await message.reply(
            f"📇 <b>Contact Card Received:</b>\n"
            f"• <b>Name:</b> {contact.first_name} {contact.last_name or ''}\n"
            f"• <b>Phone:</b> <code>{contact.phone_number}</code>\n"
            f"• <i>No direct Telegram User ID linked to this card.</i>",
            parse_mode="HTML"
        )


@router.message(F.text & ~F.text.startswith("/"))
async def handle_plain_text_lookup(message: Message, user_theme: str = "cyberpunk", user_lang: str = "en", bot: Bot = None):
    """
    Catches usernames (@handle), links (t.me/handle), or numeric IDs sent directly in chat.
    """
    text = message.text.strip()
    # Check if text looks like a handle, link, or ID
    is_handle = text.startswith("@") or "t.me/" in text
    is_num_id = text.lstrip("-").isdigit() and len(text) >= 5
    is_single_word = re.match(r'^[a-zA-Z0-9_]{3,32}$', text)

    # 1. Automatic Channel Post Forensics (e.g. https://t.me/telegram/248)
    if re.search(r'(?:t\.me\/(?:s\/)?|telegram\.me\/)[a-zA-Z0-9_]{3,32}\/\d+', text):
        from core.post_analyzer import fetch_real_telegram_post
        from ui.formatters import format_post_report
        from core.telegram_discovery import fetch_real_telegram_preview
        status_msg = await message.reply("📊 <i>Analyzing live channel post metrics...</i>", parse_mode="HTML")
        pdata = await fetch_real_telegram_post(text)
        if pdata:
            cprev = await fetch_real_telegram_preview(pdata["channel_handle"])
            cmem = cprev.get("members_count") if cprev else None
            rep = format_post_report(pdata, channel_members=cmem)
            await status_msg.edit_text(rep, parse_mode="HTML", disable_web_page_preview=True)
            return

    # 2. Automatic International Phone OSINT (+123456789 or +888...)
    clean_digits = re.sub(r'[^\d]', '', text)
    if (text.startswith("+") or text.startswith("00")) and 7 <= len(clean_digits) <= 15:
        from core.phone_analyzer import analyze_phone_number
        from ui.formatters import format_phone_report
        res = analyze_phone_number(text)
        rep = format_phone_report(res)
        await message.reply(rep, parse_mode="HTML", disable_web_page_preview=True)
        return

    if not (is_handle or is_num_id or is_single_word):
        return  # Ignore casual chatter

    await process_entity_lookup(message, text, user_theme, user_lang, bot)



async def process_entity_lookup(message: Message, identifier: str, user_theme: str, user_lang: str, bot: Bot):
    """Performs deep live entity inspection and presents corresponding UI card."""
    status_msg = await message.reply("🔍 <i>Querying live Telegram servers...</i>", parse_mode="HTML")
    
    data = await resolve_full_entity(identifier, bot=bot)
    if not data:
        await status_msg.edit_text(
            f"❌ <b>Entity not found:</b> <code>{identifier}</code>\n"
            "<i>Could not resolve entity via Telegram Bot API or public web index. Please verify spelling.</i>",
            parse_mode="HTML"
        )
        return

    entity_id = data["id"]
    fav = await is_favorite(message.from_user.id, entity_id)

    # Log to SQLite history & identity tracker
    await record_search(
        user_id=message.from_user.id,
        target_id=entity_id,
        target_username=data.get("username"),
        target_type=data.get("type", "user"),
        target_title=data.get("title", "")
    )
    await log_identity(
        target_id=entity_id,
        username=data.get("username"),
        first_name=data.get("first_name"),
        last_name=data.get("last_name")
    )

    # Render appropriate card according to entity type
    if data["type"] == "channel":
        report = format_channel_report(data, theme=user_theme)
        kb = channel_actions_keyboard(entity_id, data.get("username"), is_fav=fav, lang=user_lang, linked_chat_id=data.get("linked_chat_id"))
    elif data["type"] in ["group", "supergroup"]:
        report = format_group_report(data, theme=user_theme)
        kb = group_actions_keyboard(entity_id, data.get("username"), is_fav=fav, lang=user_lang)
    else:
        report = format_user_report(data, theme=user_theme)
        kb = user_actions_keyboard(entity_id, data.get("username"), is_fav=fav, lang=user_lang)

    await status_msg.delete()
    await message.reply(report, reply_markup=kb, parse_mode="HTML", disable_web_page_preview=True)


@router.callback_query(F.data.startswith("query_chat_"))
async def handle_callback_query_chat(callback: CallbackQuery, user_theme: str = "cyberpunk", user_lang: str = "en", bot: Bot = None):
    """Handles 1-click re-query buttons from history, bookmarks, or directory."""
    target = callback.data.replace("query_chat_", "")
    await callback.answer("Fetching live data...")
    data = await resolve_full_entity(target, bot=bot)
    if not data:
        await callback.message.answer(f"❌ Could not resolve {target}")
        return

    entity_id = data["id"]
    fav = await is_favorite(callback.from_user.id, entity_id)

    if data["type"] == "channel":
        report = format_channel_report(data, theme=user_theme)
        kb = channel_actions_keyboard(entity_id, data.get("username"), is_fav=fav, lang=user_lang, linked_chat_id=data.get("linked_chat_id"))
    elif data["type"] in ["group", "supergroup"]:
        report = format_group_report(data, theme=user_theme)
        kb = group_actions_keyboard(entity_id, data.get("username"), is_fav=fav, lang=user_lang)
    else:
        report = format_user_report(data, theme=user_theme)
        kb = user_actions_keyboard(entity_id, data.get("username"), is_fav=fav, lang=user_lang)

    await callback.message.answer(report, reply_markup=kb, parse_mode="HTML", disable_web_page_preview=True)
