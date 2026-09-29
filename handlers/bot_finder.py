import asyncio
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

from core.bot_discovery import (
    search_real_bots,
    detect_bot_clones,
    get_random_bot,
    CURATED_BOTS,
    BOT_CATEGORIES
)
from core.telegram_discovery import fetch_real_telegram_preview
from ui.formatters import escape_html

router = Router(name="bot_finder_router")


@router.message(Command("findbot", "botfinder", "bots"))
@router.callback_query(F.data == "nav_bot_finder")
async def handle_bot_finder_menu(event: Message | CallbackQuery):
    """Entry point for the Advanced Telegram Bot Finder Suite."""
    text = (
        "🤖 <b>SENTINEL // TELEGRAM BOT FINDER ENGINE</b>\n"
        "──────────────────────────────\n"
        "Discover, audit, and benchmark Telegram bots across the global network:\n\n"
        "• <b>🔍 Real Bot Search:</b> <code>/findbot &lt;keyword&gt;</code> (AI, downloaders, tools)\n"
        "• <b>🛡️ Bot Squat & Clone Hunter:</b> <code>/botsquat &lt;brand&gt;</code> (detect fake bots)\n"
        "• <b>🎲 Bot Roulette:</b> <code>/randombot</code> (discover a top-rated utility bot)\n"
        "• <b>🏆 Curated Top Bots:</b> <code>/topbots</code> (categorized top bots catalog)\n\n"
        "👇 <i>Choose a category below or send a search query:</i>"
    )

    kb_rows = []
    keys = list(BOT_CATEGORIES.keys())
    for i in range(0, len(keys), 2):
        row = []
        k1 = keys[i]
        c1 = BOT_CATEGORIES[k1]
        row.append(InlineKeyboardButton(text=f"{c1['emoji']} {c1['name']}", callback_data=f"botcat_{k1}"))
        if i + 1 < len(keys):
            k2 = keys[i + 1]
            c2 = BOT_CATEGORIES[k2]
            row.append(InlineKeyboardButton(text=f"{c2['emoji']} {c2['name']}", callback_data=f"botcat_{k2}"))
        kb_rows.append(row)

    kb_rows.append([
        InlineKeyboardButton(text="🎲 Random Bot Roulette", callback_data="bot_roulette"),
        InlineKeyboardButton(text="🛡️ Phishing Squat Hunter", callback_data="bot_squat_prompt")
    ])
    kb_rows.append([InlineKeyboardButton(text="🏠 Home Dashboard", callback_data="nav_home")])

    kb = InlineKeyboardMarkup(inline_keyboard=kb_rows)

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        await event.answer()
    else:
        # Check if query was provided in /findbot <query>
        parts = event.text.split(maxsplit=1)
        if len(parts) > 1:
            await execute_bot_search(event, parts[1].strip())
            return
        await event.answer(text, reply_markup=kb, parse_mode="HTML")


async def execute_bot_search(message: Message, query: str):
    """Executes live bot search and displays matching candidates."""
    status_msg = await message.reply(f"🤖 <i>Searching global Telegram network for bots matching '{query}'...</i>", parse_mode="HTML")
    results = await search_real_bots(query, limit=6)

    if not results:
        await status_msg.edit_text(
            f"❌ <b>No bots found for:</b> <code>{query}</code>\n"
            "<i>Try searching by category such as 'ai', 'download', 'music', 'crypto', or 'security'.</i>",
            parse_mode="HTML"
        )
        return

    lines = [
        f"🤖 <b>[BOT SEARCH RESULTS: '{escape_html(query)}']</b>",
        "──────────────────────────────",
        f"Found <b>{len(results)}</b> verified and active bots:\n"
    ]

    kb_buttons = []
    for idx, b in enumerate(results, 1):
        uname = b.get("username", "Unknown")
        title = escape_html(b.get("title", uname))
        extra = b.get("extra", "")
        verified = " 🔷" if b.get("is_verified") else ""

        lines.append(f"<b>{idx}. {title}</b>{verified}")
        lines.append(f"   • Handle: @{uname}")
        if extra:
            lines.append(f"   • Extra: <i>{extra}</i>")
        lines.append("")

        kb_buttons.append([
            InlineKeyboardButton(text=f"🤖 Open @{uname}", url=f"https://t.me/{uname}"),
            InlineKeyboardButton(text=f"🔍 Inspect", callback_data=f"query_chat_{uname}")
        ])

    kb_buttons.append([InlineKeyboardButton(text="🔙 Back to Bot Finder", callback_data="nav_bot_finder")])

    await status_msg.edit_text(
        "\n".join(lines),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_buttons),
        parse_mode="HTML"
    )


@router.message(Command("botsquat", "botclones"))
async def handle_bot_squat(message: Message):
    """Detects active phishing and typo-squatting bot clones for a project or brand."""
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply(
            "🛡️ <b>BOT SQUAT & CLONE HUNTER USAGE:</b>\n"
            "Send <code>/botsquat &lt;brand_or_project&gt;</code>\n"
            "<i>Example:</i> <code>/botsquat telegram</code> or <code>/botsquat ton</code>\n"
            "<i>Generates common impersonation handles (_official_bot, _support_bot, _airdrop_bot) and detects active bots on Telegram.</i>",
            parse_mode="HTML"
        )
        return

    brand = parts[1].strip()
    status_msg = await message.reply(f"🛡️ <i>Scanning Telegram namespace for '@{brand}' bot permutations and clones...</i>", parse_mode="HTML")
    found = await detect_bot_clones(brand)

    if not found:
        await status_msg.edit_text(
            f"✅ <b>Clean Namespace:</b> No suspicious active bot clones detected for <code>{brand}</code>.",
            parse_mode="HTML"
        )
        return

    lines = [
        f"🛡️ <b>[BOT CLONE & SQUAT AUDIT: '{escape_html(brand)}']</b>",
        "──────────────────────────────",
        f"⚠️ Found <b>{len(found)}</b> active bot variations on Telegram:\n"
    ]

    for b in found:
        uname = b.get("username", "")
        title = escape_html(b.get("title", uname))
        is_ver = b.get("is_verified", False)
        status_tag = "🔷 Official / Verified" if is_ver else "⚠️ Unverified / Potential Impersonator"

        lines.append(f"• <b>@{uname}</b> ({title})")
        lines.append(f"  Status: <b>{status_tag}</b>")
        lines.append("")

    lines.append("<i>Always verify the official blue checkmark before authorizing bots or sending sensitive keys.</i>")
    await status_msg.edit_text("\n".join(lines), parse_mode="HTML")


@router.message(Command("randombot", "botroulette"))
@router.callback_query(F.data == "bot_roulette")
async def handle_random_bot(event: Message | CallbackQuery):
    """Picks a random curated bot."""
    b = get_random_bot()
    text = (
        "🎲 <b>[BOT ROULETTE // DISCOVERED BOT]</b>\n"
        "──────────────────────────────\n"
        f"🤖 <b>Name:</b> <b>{b['name']}</b>\n"
        f"🏷️ <b>Handle:</b> @{b['username']}\n"
        f"📂 <b>Category:</b> <code>{b['category']}</code>\n"
        f"📝 <b>About:</b> <i>{b['desc']}</i>\n"
        "──────────────────────────────\n"
        f"🔗 <a href=\"https://t.me/{b['username']}\">Launch Bot in Telegram</a>"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🚀 Open @{b['username']}", url=f"https://t.me/{b['username']}")],
        [
            InlineKeyboardButton(text="🎲 Roll Again", callback_data="bot_roulette"),
            InlineKeyboardButton(text="🔙 Bot Finder", callback_data="nav_bot_finder")
        ]
    ])

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        await event.answer()
    else:
        await event.answer(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data.startswith("botcat_"))
async def handle_bot_category(callback: CallbackQuery):
    """Displays bots in a specific category."""
    cat_key = callback.data.split("_")[1]
    cat_info = BOT_CATEGORIES.get(cat_key, {"name": cat_key.title(), "emoji": "🤖"})

    matches = [b for b in CURATED_BOTS if cat_key in b["category"].lower()]
    if not matches:
        matches = CURATED_BOTS[:4]

    lines = [
        f"{cat_info['emoji']} <b>[CURATED BOTS: {cat_info['name'].upper()}]</b>",
        "──────────────────────────────",
    ]

    kb_buttons = []
    for b in matches:
        lines.append(f"• <b>{b['name']}</b> (@{b['username']})")
        lines.append(f"  <i>{b['desc']}</i>\n")
        kb_buttons.append([InlineKeyboardButton(text=f"🤖 Launch @{b['username']}", url=f"https://t.me/{b['username']}")])

    kb_buttons.append([InlineKeyboardButton(text="🔙 Back to Categories", callback_data="nav_bot_finder")])

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_buttons),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "bot_squat_prompt")
async def prompt_squat(callback: CallbackQuery):
    await callback.message.answer(
        "🛡️ <b>BOT SQUAT HUNTER:</b>\n"
        "Send <code>/botsquat &lt;brand_name&gt;</code> to scan for impersonator bots!\n"
        "<i>Example:</i> <code>/botsquat binance</code>",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(Command("topbots"))
async def handle_top_bots(message: Message):
    """Displays top bots across all categories."""
    lines = [
        "🏆 <b>[TOP 10 CURATED TELEGRAM UTILITY BOTS]</b>",
        "──────────────────────────────"
    ]
    for idx, b in enumerate(CURATED_BOTS[:10], 1):
        lines.append(f"<b>{idx}. {b['name']}</b> (@{b['username']})")
        lines.append(f"   📂 <code>{b['category']}</code> — {b['desc']}\n")

    lines.append("<i>Use /findbot &lt;keyword&gt; to search for more specific bots!</i>")
    await message.reply("\n".join(lines), parse_mode="HTML")
