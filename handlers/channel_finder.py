"""
Sentinel Channel Finder Handler.
Provides deep channel discovery, search operator filtering (min:, verified:, sort:),
interactive multi-mode sorting (members, A-Z, verified), size bracket filters,
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
    build_filter_controls_view,
    generate_search_csv
)
from ui.formatters import escape_html

router = Router(name="channel_finder_router")


@router.message(Command("channel", "findchannel", "c"))
async def handle_channel_search(message: Message, user_theme: str = "cyberpunk", user_lang: str = "en", bot: Bot = None):
    """Searches for real public Telegram channels matching keywords with pagination & sorting."""
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply(
            "📢 <b>CHANNEL FINDER & ADVANCED SEARCH USAGE:</b>\n"
            "──────────────────────────────\n"
            "Send <code>/channel &lt;keyword or name&gt; [filters]</code>\n\n"
            "<b>Search Examples:</b>\n"
            "• <code>/channel artificial intelligence</code>\n"
            "• <code>/channel python min:10k sort:subs</code> (Top Python communities)\n"
            "• <code>/channel news verified:true</code> (Only verified news outlets)\n"
            "• <code>/channel crypto sort:alpha</code> (Alphabetical listing)",
            parse_mode="HTML"
        )
        return

    raw_query = parts[1].strip()
    clean_query, filters = parse_search_operators(raw_query)

    status_msg = await message.reply(f"📡 <i>Scanning Telegram global index for channels matching '{clean_query}'...</i>", parse_mode="HTML")

    try:
        raw_results = await search_real_telegram_entities(clean_query, limit=60, bot=bot)
        # Filter channels
        channel_results = [r for r in raw_results if r.get("type") in ["channel", "broadcast"]]
        if not channel_results and raw_results:
            channel_results = raw_results  # fallback

        if not channel_results:
            await status_msg.edit_text(
                f"❌ No public channels found matching '<b>{escape_html(clean_query)}</b>'.\n"
                "<i>Try broader keywords or search with /explore.</i>",
                parse_mode="HTML"
            )
            return

        # Store in pagination session with initial filters
        sess_id = create_search_session(
            results=channel_results,
            query=clean_query,
            entity_type="channel",
            per_page=5,
            initial_filters=filters
        )

        text, kb = build_paginated_view(sess_id, page=1)
        await status_msg.delete()
        await message.reply(text, reply_markup=kb, parse_mode="HTML")

    except Exception as e:
        await status_msg.edit_text(f"❌ Error during channel search: {escape_html(str(e))}", parse_mode="HTML")


# ==============================================================================
# PAGINATION, SORTING & FILTER INTERACTIVE CALLBACKS
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


@router.callback_query(F.data.startswith("open_filters:"))
async def handle_open_filter_controls(callback: CallbackQuery):
    """Opens the interactive Filter & Sorting Control Center."""
    parts = callback.data.split(":")
    sess_id = parts[1]
    ret_page = int(parts[2]) if len(parts) > 2 else 1

    text, kb = build_filter_controls_view(sess_id, return_page=ret_page)
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("set_sort:"))
async def handle_set_sort_option(callback: CallbackQuery):
    """Updates sorting order in active search session."""
    parts = callback.data.split(":")
    sess_id = parts[1]
    new_sort = parts[2]

    sess = get_search_session(sess_id)
    if not sess:
        await callback.answer("⚠️ Session expired.", show_alert=True)
        return

    sess["sort_by"] = new_sort
    text, kb = build_filter_controls_view(sess_id)
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer("Sorting updated!")


@router.callback_query(F.data.startswith("set_size:"))
async def handle_set_size_tier(callback: CallbackQuery):
    """Updates audience size bracket filter."""
    parts = callback.data.split(":")
    sess_id = parts[1]
    new_size = parts[2]

    sess = get_search_session(sess_id)
    if not sess:
        await callback.answer("⚠️ Session expired.", show_alert=True)
        return

    sess["size_tier"] = "all" if sess.get("size_tier") == new_size else new_size
    text, kb = build_filter_controls_view(sess_id)
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer("Size filter updated!")


@router.callback_query(F.data.startswith("set_type:"))
async def handle_set_type_filter(callback: CallbackQuery):
    """Updates entity type filter (channel/group/bot)."""
    parts = callback.data.split(":")
    sess_id = parts[1]
    new_type = parts[2]

    sess = get_search_session(sess_id)
    if not sess:
        await callback.answer("⚠️ Session expired.", show_alert=True)
        return

    sess["type_filter"] = "all" if sess.get("type_filter") == new_type else new_type
    text, kb = build_filter_controls_view(sess_id)
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer("Type filter updated!")


@router.callback_query(F.data.startswith("toggle_ver_btn:"))
async def handle_toggle_ver_button(callback: CallbackQuery):
    """Toggles verified-only badge in filter controls."""
    sess_id = callback.data.split(":")[-1].strip()
    sess = get_search_session(sess_id)
    if not sess:
        await callback.answer("⚠️ Session expired.", show_alert=True)
        return

    sess["verified_only"] = not sess.get("verified_only", False)
    text, kb = build_filter_controls_view(sess_id)
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer("Verified filter toggled!")


@router.callback_query(F.data.startswith("filter_reset:"))
async def handle_reset_all_filters(callback: CallbackQuery):
    """Resets all filters and sorting to defaults."""
    sess_id = callback.data.split(":")[-1].strip()
    sess = get_search_session(sess_id)
    if not sess:
        await callback.answer("⚠️ Session expired.", show_alert=True)
        return

    sess["sort_by"] = "relevance"
    sess["size_tier"] = "all"
    sess["type_filter"] = "all"
    sess["verified_only"] = False

    text, kb = build_paginated_view(sess_id, page=1)
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer("All filters reset!")


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
