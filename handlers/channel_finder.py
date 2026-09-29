from aiogram import Router, F, Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

from core.telegram_discovery import search_real_telegram_entities, resolve_full_entity
from ui.formatters import format_channel_report
from ui.keyboards import channel_actions_keyboard
from database import is_favorite

router = Router(name="channel_finder_router")


@router.message(Command("channel", "findchannel", "c"))
async def handle_channel_search(message: Message, user_theme: str = "cyberpunk", user_lang: str = "en", bot: Bot = None):
    """Searches for real public Telegram channels matching keywords."""
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply(
            "📢 <b>CHANNEL FINDER USAGE:</b>\n"
            "Send <code>/channel &lt;keyword or name&gt;</code>\n"
            "<i>Example:</i> <code>/channel artificial intelligence</code> or <code>/channel python</code>",
            parse_mode="HTML"
        )
        return

    query = parts[1].strip()
    status_msg = await message.reply("📡 <i>Scanning Telegram global index for channels...</i>", parse_mode="HTML")

    results = await search_real_telegram_entities(query, limit=6, bot=bot)
    # Filter channels
    channel_results = [r for r in results if r.get("type") == "channel"]
    if not channel_results and results:
        channel_results = results  # fallback

    if not channel_results:
        await status_msg.edit_text(
            f"❌ No public channels found matching '<b>{query}</b>'. Try a broader keyword.",
            parse_mode="HTML"
        )
        return

    text_lines = [
        f"📢 <b>CHANNELS DISCOVERED FOR:</b> <code>{query}</code>",
        "──────────────────────────────"
    ]
    keyboard = []

    for idx, ch in enumerate(channel_results, 1):
        title = ch.get("title", "Untitled")
        uname = ch.get("username", "")
        members = ch.get("members_count")
        members_str = f"👥 {members:,}" if members else (ch.get("extra") or "")
        ver = " 🔷" if ch.get("is_verified") else ""

        text_lines.append(f"<b>{idx}.</b> <b>{title}</b>{ver} (@{uname})\n   └ {members_str}")
        keyboard.append([
            InlineKeyboardButton(text=f"🔍 Inspect {title[:20]}", callback_data=f"query_chat_{uname}")
        ])

    keyboard.append([InlineKeyboardButton(text="🏠 Home Menu", callback_data="nav_home")])
    await status_msg.delete()
    await message.reply(
        "\n".join(text_lines),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="HTML"
    )
