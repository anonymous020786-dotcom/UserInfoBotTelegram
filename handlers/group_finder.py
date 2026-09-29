"""
Sentinel Group Finder Handler.
Discovers active public groups & supergroups across global topics,
supports member count filters (min:), interactive pagination, and CSV data exports.
"""
from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.filters import Command

from core.telegram_discovery import search_real_telegram_entities
from core.pagination_manager import (
    parse_search_operators,
    create_search_session,
    build_paginated_view
)
from ui.formatters import escape_html

router = Router(name="group_finder_router")


@router.message(Command("group", "findgroup", "g"))
async def handle_group_search(message: Message, user_theme: str = "cyberpunk", user_lang: str = "en", bot: Bot = None):
    """Searches for real public Telegram groups/supergroups matching keywords with pagination."""
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply(
            "👥 <b>GROUP FINDER USAGE:</b>\n"
            "──────────────────────────────\n"
            "Send <code>/group &lt;topic or keyword&gt; [filters]</code>\n\n"
            "<b>Search Examples:</b>\n"
            "• <code>/group developers</code>\n"
            "• <code>/group crypto min:5k</code> (Groups with at least 5,000 members)\n"
            "• <code>/group gaming</code>\n"
            "• <code>/group start up community</code>",
            parse_mode="HTML"
        )
        return

    raw_query = parts[1].strip()
    clean_query, filters = parse_search_operators(raw_query)

    status_msg = await message.reply(f"📡 <i>Scanning Telegram index for active groups matching '{clean_query}'...</i>", parse_mode="HTML")

    try:
        raw_results = await search_real_telegram_entities(clean_query, limit=50, bot=bot)
        # Filter groups / supergroups
        group_results = [r for r in raw_results if r.get("type") in ["group", "supergroup"]]
        if not group_results and raw_results:
            group_results = raw_results  # fallback

        # Apply search filters
        if filters.get("min_members"):
            min_m = filters["min_members"]
            group_results = [r for r in group_results if (r.get("members_count") or 0) >= min_m]

        if filters.get("verified_only"):
            group_results = [r for r in group_results if r.get("is_verified")]

        if not group_results:
            await status_msg.edit_text(
                f"❌ No public communities found matching '<b>{escape_html(clean_query)}</b>' with given filters.\n"
                "<i>Try broader terms or lower member thresholds.</i>",
                parse_mode="HTML"
            )
            return

        # Store in pagination session
        sess_id = create_search_session(
            results=group_results,
            query=clean_query,
            entity_type="group",
            per_page=5
        )

        text, kb = build_paginated_view(sess_id, page=1)
        await status_msg.delete()
        await message.reply(text, reply_markup=kb, parse_mode="HTML")

    except Exception as e:
        await status_msg.edit_text(f"❌ Error during group search: {escape_html(str(e))}", parse_mode="HTML")
