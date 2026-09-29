"""
Sentinel Channel Finder Handler.
Provides deep channel discovery, search operator filtering (min:, verified:),
interactive pagination (Prev/Next, Page X/Y), and CSV data export.
"""
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.filters import Command

from core.telegram_discovery import search_real_telegram_entities
from core.pagination_manager import (
    parse_search_operators,
    create_search_session,
    get_search_session,
    build_paginated_view,
    generate_search_csv
)
from ui.formatters import escape_html

router = Router(name="channel_finder_router")


@router.message(Command("channel", "findchannel", "c"))
async def handle_channel_search(message: Message, user_theme: str = "cyberpunk", user_lang: str = "en", bot: Bot = None):
    """Searches for real public Telegram channels matching keywords with pagination."""
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply(
            "📢 <b>CHANNEL FINDER USAGE:</b>\n"
            "──────────────────────────────\n"
            "Send <code>/channel &lt;keyword or name&gt; [filters]</code>\n\n"
            "<b>Search Examples:</b>\n"
            "• <code>/channel artificial intelligence</code>\n"
            "• <code>/channel python min:10k</code> (At least 10,000 members)\n"
            "• <code>/channel news verified:true</code> (Only verified channels)\n"
            "• <code>/channel crypto min:50k</code> (High-volume communities)",
            parse_mode="HTML"
        )
        return

    raw_query = parts[1].strip()
    clean_query, filters = parse_search_operators(raw_query)

    status_msg = await message.reply(f"📡 <i>Scanning Telegram global index for channels matching '{clean_query}'...</i>", parse_mode="HTML")

    try:
        raw_results = await search_real_telegram_entities(clean_query, limit=50, bot=bot)
        # Filter channels
        channel_results = [r for r in raw_results if r.get("type") in ["channel", "broadcast"]]
        if not channel_results and raw_results:
            channel_results = raw_results  # fallback

        # Apply search operator filters
        if filters.get("min_members"):
            min_m = filters["min_members"]
            channel_results = [r for r in channel_results if (r.get("members_count") or 0) >= min_m]

        if filters.get("verified_only"):
            channel_results = [r for r in channel_results if r.get("is_verified")]

        if not channel_results:
            await status_msg.edit_text(
                f"❌ No public channels found matching '<b>{escape_html(clean_query)}</b>' with given filters.\n"
                "<i>Try broader keywords or remove member thresholds.</i>",
                parse_mode="HTML"
            )
            return

        # Store in pagination session
        sess_id = create_search_session(
            results=channel_results,
            query=clean_query,
            entity_type="channel",
            per_page=5
        )

        text, kb = build_paginated_view(sess_id, page=1)
        await status_msg.delete()
        await message.reply(text, reply_markup=kb, parse_mode="HTML")

    except Exception as e:
        await status_msg.edit_text(f"❌ Error during channel search: {escape_html(str(e))}", parse_mode="HTML")


# ==============================================================================
# PAGINATION & SEARCH INTERACTIVE CALLBACKS
# ==============================================================================
@router.callback_query(F.data.startswith("page:"))
async def handle_pagination_page_flip(callback: CallbackQuery):
    """Handles Prev, Next, and direct page jumps."""
    parts = callback.data.split(":")
    if len(parts) < 3:
        await callback.answer()
        return

    sess_id = parts[1]
    page_num = int(parts[2])

    text, kb = build_paginated_view(sess_id, page=page_num)
    if not text:
        await callback.answer("⚠️ Search session expired. Please search again.", show_alert=True)
        return

    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        await callback.answer(f"Page {page_num}")
    except Exception:
        await callback.answer()


@router.callback_query(F.data.startswith("export_csv_"))
async def handle_export_search_csv(callback: CallbackQuery):
    """Generates downloadable CSV file of all discovered results in session."""
    sess_id = callback.data.replace("export_csv_", "").strip()
    csv_content = generate_search_csv(sess_id)

    if not csv_content:
        await callback.answer("⚠️ Session expired. Search again to export.", show_alert=True)
        return

    sess = get_search_session(sess_id)
    q_name = sess["query"].replace(" ", "_") if sess else "search"
    file_bytes = csv_content.encode("utf-8")
    doc = BufferedInputFile(file_bytes, filename=f"sentinel_{q_name}_results.csv")

    await callback.message.reply_document(
        document=doc,
        caption=f"📊 <b>Search Export: '{escape_html(sess['query'])}'</b>\n"
                f"Contains {len(sess['results'])} structured Telegram records (Title, Username, Members, Verification).",
        parse_mode="HTML"
    )
    await callback.answer("CSV Exported!")


@router.callback_query(F.data.startswith("toggle_ver_"))
async def handle_toggle_verified_filter(callback: CallbackQuery):
    """Toggles verified-only badge filter for active search session."""
    parts = callback.data.split(":")
    sess_id = parts[0].replace("toggle_ver_", "").strip()
    sess = get_search_session(sess_id)

    if not sess:
        await callback.answer("⚠️ Session expired.", show_alert=True)
        return

    sess["verified_only"] = not sess.get("verified_only", False)
    text, kb = build_paginated_view(sess_id, page=1)
    status_label = "Showing Verified Only 🔷" if sess["verified_only"] else "Showing All Results"

    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer(status_label)


@router.callback_query(F.data.startswith("page_reset:"))
async def handle_reset_filter(callback: CallbackQuery):
    """Resets filters when zero results are found."""
    sess_id = callback.data.split(":")[-1].strip()
    sess = get_search_session(sess_id)
    if not sess:
        await callback.answer("⚠️ Session expired.", show_alert=True)
        return

    sess["verified_only"] = False
    text, kb = build_paginated_view(sess_id, page=1)
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer("Filters reset!")
