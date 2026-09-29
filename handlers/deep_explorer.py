"""
Sentinel Multi-Vector Explorer & Deep Search Handler.
Provides /explore interactive dashboard and /deepsearch cross-ecosystem intelligence.
"""
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

from core.deep_explorer import execute_deep_search, get_explorer_categories
from core.pagination_manager import create_search_session, build_paginated_view
from core.directory_data import get_curated_communities
from ui.formatters import escape_html

router = Router(name="deep_explorer_router")


# ==============================================================================
# 1. EXPLORER CONSOLE (/explore)
# ==============================================================================
@router.message(Command("explore", "discover"))
@router.callback_query(F.data == "nav_explorer")
async def handle_explorer_console(event: Message | CallbackQuery):
    """Entry point for the Multi-Vector Community Explorer Console."""
    stats = get_explorer_categories()

    text = (
        "🧭 <b>SENTINEL // TELEGRAM COMMUNITY EXPLORER</b>\n"
        "──────────────────────────────\n"
        "Explore <b>1,472+</b> verified communities, channels, groups, and AI bots:\n\n"
        f"• 📢 <b>Broadcast Channels:</b> <code>{stats['channels_count']}</code> curated\n"
        f"• 👥 <b>Discussion Groups:</b> <code>{stats['groups_count']}</code> communities\n"
        f"• 🤖 <b>Automated Bots:</b> <code>{stats['bots_count']}</code> utilities\n"
        f"• 📂 <b>Taxonomy Categories:</b> <code>{stats['total_categories']}</code> vertical domains\n\n"
        "👇 <i>Choose an exploration sector or filter below:</i>"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👑 Mega Channels (>100k)", callback_data="exp_filter:mega"),
            InlineKeyboardButton(text="🔷 Verified Ecosystem", callback_data="exp_filter:verified")
        ],
        [
            InlineKeyboardButton(text="🤖 AI & Language Bots", callback_data="exp_filter:ai"),
            InlineKeyboardButton(text="💎 Crypto & TON Collectibles", callback_data="exp_filter:crypto")
        ],
        [
            InlineKeyboardButton(text="💻 Programming & Dev", callback_data="exp_filter:tech"),
            InlineKeyboardButton(text="🌍 Global News & Alerts", callback_data="exp_filter:news")
        ],
        [
            InlineKeyboardButton(text="📂 Browse All 32 Topics", callback_data="nav_directory"),
            InlineKeyboardButton(text="🎲 Random Roulette", callback_data="bot_roulette")
        ],
        [
            InlineKeyboardButton(text="🏠 Home Dashboard", callback_data="nav_home")
        ]
    ])

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        await event.answer()
    else:
        await event.reply(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data.startswith("exp_filter:"))
async def handle_explorer_preset(callback: CallbackQuery):
    """Launches instant paginated search for an explorer preset."""
    preset = callback.data.split(":")[-1]
    all_comms = get_curated_communities()

    if preset == "mega":
        items = [c for c in all_comms if (c.get("members_count") or 0) >= 100_000]
        label = "Mega Communities (>100k)"
    elif preset == "verified":
        items = [c for c in all_comms if c.get("is_verified")]
        label = "Verified Telegram Channels & Bots"
    elif preset == "ai":
        items = [c for c in all_comms if "ai" in c.get("category", "").lower() or "ai" in c.get("title", "").lower()]
        label = "AI & Machine Learning Communities"
    elif preset == "crypto":
        items = [c for c in all_comms if "crypto" in c.get("category", "").lower()]
        label = "Crypto & Web3 Channels"
    elif preset == "tech":
        items = [c for c in all_comms if "tech" in c.get("category", "").lower() or "programming" in c.get("category", "").lower()]
        label = "Tech & Developer Hubs"
    elif preset == "news":
        items = [c for c in all_comms if "news" in c.get("category", "").lower()]
        label = "Global News Networks"
    else:
        items = all_comms[:30]
        label = "Curated Selection"

    if not items:
        items = all_comms[:25]

    sess_id = create_search_session(
        results=items,
        query=label,
        entity_type="global",
        per_page=5
    )

    text, kb = build_paginated_view(sess_id, page=1)
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer(label)


# ==============================================================================
# 2. DEEP CROSS-VECTOR SEARCH (/deepsearch)
# ==============================================================================
@router.message(Command("deepsearch", "ds", "recon"))
async def handle_deep_search_command(message: Message, bot: Bot):
    """Executes multi-vector reconnaissance across channels, groups, bots, and Fragment NFTs."""
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply(
            "🔬 <b>DEEP RECON SEARCH USAGE:</b>\n"
            "──────────────────────────────\n"
            "Send <code>/deepsearch &lt;target_keyword&gt;</code>\n"
            "<i>Example:</i> <code>/deepsearch ai</code> or <code>/deepsearch ton</code>\n\n"
            "• Simultaneously queries Channels, Groups & Supergroups\n"
            "• Discovers verified utility & AI Bots\n"
            "• Scrapes Fragment TON NFT Collectibles\n"
            "• Cross-references 1,472 curated topics",
            parse_mode="HTML"
        )
        return

    query = parts[1].strip()
    status_msg = await message.reply(f"🔬 <i>Initiating multi-vector deep search for '{query}' across Telegram & Fragment...</i>", parse_mode="HTML")

    try:
        res = await execute_deep_search(query, bot=bot)

        total_found = res["total_found"]
        chans = res["channels"]
        groups = res["groups"]
        bots = res["bots"]
        frag = res["fragment"]

        lines = [
            f"🔬 <b>[DEEP RECON REPORT: '{escape_html(query)}']</b>",
            "──────────────────────────────",
            f"• <b>Total Discovered Assets:</b> <b>{total_found}</b>",
            f"• 📢 <b>Broadcast Channels:</b> <code>{len(chans)}</code> candidates",
            f"• 👥 <b>Discussion Groups:</b> <code>{len(groups)}</code> communities",
            f"• 🤖 <b>Automated Bots:</b> <code>{len(bots)}</code> utilities",
        ]

        if frag and frag.get("status"):
            lines.append(f"• 💎 <b>Fragment NFT @{query}:</b> <b>{frag['status']}</b> (Valuation: {frag.get('price_ton', 'N/A')} TON)")

        lines.extend([
            "──────────────────────────────",
            "📊 <b>TOP RECONNAISSANCE ASSETS:</b>"
        ])

        top_candidates = []
        if chans:
            top_candidates.append(f"📢 <b>Channel:</b> <b>{escape_html(chans[0]['title'])}</b> (@{chans[0]['username']})")
        if groups:
            top_candidates.append(f"👥 <b>Group:</b> <b>{escape_html(groups[0]['title'])}</b> (@{groups[0]['username']})")
        if bots:
            top_candidates.append(f"🤖 <b>Bot:</b> <b>{escape_html(bots[0]['title'])}</b> (@{bots[0]['username']})")

        lines.extend(top_candidates)
        lines.append("\n<i>Tap below to open full paginated views for each ecosystem:</i>")

        # Session for all combined assets
        all_combined = chans + groups + bots
        combined_sess = create_search_session(
            results=all_combined,
            query=f"Deep: {query}",
            entity_type="global",
            per_page=5
        )

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text=f"📢 View All Channels ({len(chans)})", callback_data=f"ds_view:channel:{combined_sess}"),
                InlineKeyboardButton(text=f"👥 View All Groups ({len(groups)})", callback_data=f"ds_view:group:{combined_sess}")
            ],
            [
                InlineKeyboardButton(text=f"🤖 View All Bots ({len(bots)})", callback_data=f"ds_view:bot:{combined_sess}"),
                InlineKeyboardButton(text=f"🌐 Browse Combined ({len(all_combined)})", callback_data=f"page:{combined_sess}:1")
            ],
            [
                InlineKeyboardButton(text="📥 Export Full CSV", callback_data=f"export_csv_{combined_sess}"),
                InlineKeyboardButton(text="🏠 Home Dashboard", callback_data="nav_home")
            ]
        ])

        await status_msg.edit_text("\n".join(lines), reply_markup=kb, parse_mode="HTML")

    except Exception as e:
        await status_msg.edit_text(f"❌ Error during deep search: {escape_html(str(e))}", parse_mode="HTML")


@router.callback_query(F.data.startswith("ds_view:"))
async def handle_deep_search_type_slice(callback: CallbackQuery):
    """Filters combined deep search session by entity type."""
    parts = callback.data.split(":")
    slice_type = parts[1]
    sess_id = parts[2]

    sess = get_search_session(sess_id)
    if not sess:
        await callback.answer("⚠️ Session expired.", show_alert=True)
        return

    sess["type_filter"] = slice_type
    sess["entity_type"] = slice_type
    text, kb = build_paginated_view(sess_id, page=1)
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer(f"Filtered by {slice_type.title()}s")
