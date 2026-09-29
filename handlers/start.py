from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command

from ui.keyboards import main_menu_keyboard
from ui.locales import get_text
from config import BOT_NAME, BOT_VERSION

router = Router(name="start_router")


@router.message(CommandStart())
async def handle_start(message: Message, user_lang: str = "en"):
    """Handles the /start command and renders the main dashboard."""
    welcome_text = (
        f"{get_text('welcome_title', user_lang)}\n"
        f"──────────────────────────────\n"
        f"{get_text('welcome_body', user_lang)}"
    )
    await message.answer(
        text=welcome_text,
        reply_markup=main_menu_keyboard(user_lang),
        parse_mode="HTML",
        disable_web_page_preview=True
    )


@router.callback_query(F.data == "nav_home")
async def handle_nav_home(callback: CallbackQuery, user_lang: str = "en"):
    """Returns to the primary dashboard menu."""
    welcome_text = (
        f"{get_text('welcome_title', user_lang)}\n"
        f"──────────────────────────────\n"
        f"{get_text('welcome_body', user_lang)}"
    )
    await callback.message.edit_text(
        text=welcome_text,
        reply_markup=main_menu_keyboard(user_lang),
        parse_mode="HTML",
        disable_web_page_preview=True
    )
    await callback.answer()


@router.message(Command("help"))
@router.callback_query(F.data == "nav_help")
async def handle_help(event: Message | CallbackQuery, user_lang: str = "en"):
    """Displays comprehensive interactive user guide."""
    help_text = (
        "📖 <b>SENTINEL OPERATOR MANUAL & GUIDE</b>\n"
        "──────────────────────────────\n"
        "<b>1. User & Account Intelligence:</b>\n"
        "• Send <code>@username</code> or <code>123456789</code>\n"
        "• Forward any message from any user to inspect hidden headers\n"
        "• Send any contact card to inspect identity\n\n"
        "<b>2. Channels & Communities Discovery:</b>\n"
        "• Send <code>/channel &lt;name/keyword&gt;</code> to discover public channels\n"
        "• Send <code>/group &lt;name/keyword&gt;</code> to find active supergroups\n"
        "• Browse <code>/directory</code> to explore 12 curated topics with pagination\n\n"
        "<b>3. Forensic Exports:</b>\n"
        "• Click <b>🪪 Generate ID Card</b> to export a high-res graphic PNG\n"
        "• Click <b>📄 Export PDF Dossier</b> for an OSINT PDF report\n"
        "• Click <b>🏁 QR Code</b> for a custom Telegram QR\n"
        "• Click <b>📇 Export VCard</b> to save to contacts\n\n"
        "<b>4. Inline Query Mode:</b>\n"
        "• In any chat, type: <code>@YourBot &lt;handle&gt;</code> for instant lookups!"
    )
    reply_markup = main_menu_keyboard(user_lang)

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(help_text, reply_markup=reply_markup, parse_mode="HTML")
        await event.answer()
    else:
        await event.answer(help_text, reply_markup=reply_markup, parse_mode="HTML")


@router.message(Command("features"))
@router.callback_query(F.data == "nav_features")
async def handle_features(event: Message | CallbackQuery, user_lang: str = "en"):
    """Displays complete 47+ features audit breakdown."""
    features_text = (
        "📋 <b>SENTINEL // 50+ FUNCTIONAL FEATURES CATALOG</b>\n"
        "──────────────────────────────\n"
        "<b>1. USER FORENSICS (1-12):</b>\n"
        "✓ Username Lookup • ID Lookup • Forward Header Inspector\n"
        "✓ Data Center (DC1-DC5) • Account Age & Epoch Regression\n"
        "✓ Premium Status • Scam/Fake Flag • Bot Capabilities Check\n"
        "✓ Verified Badge • Profile Avatar Downloader • Photos Count\n"
        "✓ Identity & Alias Change Tracker (SQLite)\n\n"
        "<b>2. CHANNEL & GROUP DISCOVERY (13-26):</b>\n"
        "✓ Channel Live Stats • Group Member Counter • Invite Link Analyzer\n"
        "✓ Live Telegram Keyword Search Engine • Forum Topic Inspector\n"
        "✓ Slowmode Interval • Permissions Matrix • Linked Chat Finder\n"
        "✓ Admin Team Inspector • Fragment Collectible Inspector\n"
        "✓ Post Link Synthesizer • Platform Restriction Auditor\n\n"
        "<b>3. OSINT, SECURITY & UTILITIES (27-38):</b>\n"
        "✓ Permanent tg:// Link • Deep Protocol Links • Graphic ID Card (PNG)\n"
        "✓ Styled QR Codes • OSINT PDF Dossier (ReportLab) • Raw JSON Dumper\n"
        "✓ Phone VCard (.vcf) • Bio Link & Email Extractor • Script Detector\n"
        "✓ Phishing/Scam Risk Auditor • Bot Token Validator • Webhook Inspector\n\n"
        "<b>4. DIRECTORY & PERSONALIZATION (39-50+):</b>\n"
        "✓ 12-Category Directory • Interactive Pagination • Community Roulette\n"
        "✓ User Submissions & Admin Queue • Bookmarks/Favorites System\n"
        "✓ Search History with 1-Click Re-Query • 3 Visual Themes\n"
        "✓ 5 Languages (EN, ES, HI, RU, AR) • Anti-Flood Rate Limiting\n"
        "✓ Global Admin Broadcast • Live System Analytics • Inline Mode"
    )
    reply_markup = main_menu_keyboard(user_lang)

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(features_text, reply_markup=reply_markup, parse_mode="HTML")
        await event.answer()
    else:
        await event.answer(features_text, reply_markup=reply_markup, parse_mode="HTML")


@router.callback_query(F.data == "nav_user_lookup")
async def nav_user_prompt(callback: CallbackQuery):
    await callback.message.answer(
        "👤 <b>USER LOOKUP:</b>\n"
        "Send any Telegram <code>@username</code> or numeric <code>User ID</code> (e.g. <code>777000</code>), or forward a message here!",
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "nav_channel_finder")
async def nav_channel_prompt(callback: CallbackQuery):
    await callback.message.answer(
        "📢 <b>CHANNEL FINDER:</b>\n"
        "Send <code>/channel &lt;keyword or handle&gt;</code> to discover public channels in real-time!",
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "nav_group_finder")
async def nav_group_prompt(callback: CallbackQuery):
    await callback.message.answer(
        "👥 <b>GROUP FINDER:</b>\n"
        "Send <code>/group &lt;keyword or handle&gt;</code> to discover active public supergroups in real-time!",
        parse_mode="HTML"
    )
    await callback.answer()
