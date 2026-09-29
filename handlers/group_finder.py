from aiogram import Router, F, Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

from core.telegram_discovery import search_real_telegram_entities
from ui.formatters import format_group_report
from ui.keyboards import group_actions_keyboard
from database import is_favorite

router = Router(name="group_finder_router")


@router.message(Command("group", "findgroup", "g"))
async def handle_group_search(message: Message, user_theme: str = "cyberpunk", user_lang: str = "en", bot: Bot = None):
    """Searches for real public Telegram groups/supergroups matching keywords."""
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply(
            "👥 <b>GROUP FINDER USAGE:</b>\n"
            "Send <code>/group &lt;topic or keyword&gt;</code>\n"
            "<i>Example:</i> <code>/group developers</code> or <code>/group crypto community</code>",
            parse_mode="HTML"
        )
        return

    query = parts[1].strip()
    status_msg = await message.reply("📡 <i>Scanning Telegram index for active groups...</i>", parse_mode="HTML")

    results = await search_real_telegram_entities(query, limit=6, bot=bot)
    group_results = [r for r in results if r.get("type") in ["group", "supergroup"]]
    if not group_results and results:
        group_results = results

    if not group_results:
        await status_msg.edit_text(
            f"❌ No public communities found matching '<b>{query}</b>'. Try broader terms.",
            parse_mode="HTML"
        )
        return

    text_lines = [
        f"👥 <b>GROUPS DISCOVERED FOR:</b> <code>{query}</code>",
        "──────────────────────────────"
    ]
    keyboard = []

    for idx, grp in enumerate(group_results, 1):
        title = grp.get("title", "Community")
        uname = grp.get("username", "")
        members = grp.get("members_count")
        members_str = f"👥 {members:,} members" if members else (grp.get("extra") or "")

        text_lines.append(f"<b>{idx}.</b> <b>{title}</b> (@{uname})\n   └ {members_str}")
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
