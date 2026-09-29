from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command

from ui.keyboards import tools_menu_keyboard
from core.bot_checker import check_bot_token
from core.dc_resolver import DC_DATA
from core.osint_analyzer import analyze_text_osint, validate_telegram_username
from core.qr_generator import generate_styled_qr

router = Router(name="tools_router")


@router.message(Command("tools"))
@router.callback_query(F.data == "nav_tools")
async def handle_tools_menu(event: Message | CallbackQuery, user_lang: str = "en"):
    """Displays the OSINT and developer utility suite."""
    text = (
        "🛠️ <b>SENTINEL // OSINT & DEVELOPER SUITE</b>\n"
        "──────────────────────────────\n"
        "Advanced diagnostic and OSINT utilities for Telegram analysts:\n\n"
        "• <b>🤖 Bot Token Checker:</b> Validate bot tokens, webhooks, and permissions\n"
        "• <b>🌐 DC Map:</b> Telegram global infrastructure and Data Center nodes\n"
        "• <b>💎 Fragment NFT:</b> Check username auction and collectible status\n"
        "• <b>🔗 Deep Links Suite:</b> Synthesize direct application protocol links\n"
        "• <b>🏁 QR Generator:</b> Generate styled Telegram QR codes\n"
        "• <b>🛡️ Scam Auditor:</b> Scan text for phishing and investment scam triggers\n\n"
        "👇 <i>Select an option below or use /token, /fragment, /qr, /audit:</i>"
    )
    kb = tools_menu_keyboard(user_lang)
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        await event.answer()
    else:
        await event.answer(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data == "tool_dc_map")
@router.message(Command("dc", "datacenters"))
async def handle_dc_map(event: Message | CallbackQuery):
    """Displays the Telegram Data Center architecture map."""
    lines = [
        "🌐 <b>TELEGRAM CORE DATA CENTERS (DC) MAP</b>",
        "──────────────────────────────",
        "Telegram routes traffic across 5 primary global clusters:",
        ""
    ]
    for dc_id, d in DC_DATA.items():
        lines.extend([
            f"{d['flag']} <b>DC{dc_id} — {d['name']}</b>",
            f"   • <b>Location:</b> {d['location']}",
            f"   • <b>Primary IP Node:</b> <code>{d['ip']}</code>",
            f"   • <b>Region:</b> {d['region']}",
            ""
        ])

    lines.append("<i>Note: DC allocation is determined upon registration and avatar hosting.</i>")
    text = "\n".join(lines)
    if isinstance(event, CallbackQuery):
        await event.message.answer(text, parse_mode="HTML")
        await event.answer()
    else:
        await event.answer(text, parse_mode="HTML")


@router.message(Command("token", "checkbot"))
async def handle_token_check(message: Message):
    """Validates Telegram Bot Token and queries getWebhookInfo & getMe."""
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply(
            "🤖 <b>BOT TOKEN CHECKER USAGE:</b>\n"
            "Send <code>/token &lt;bot_token&gt;</code>\n"
            "<i>Tests authentication, webhook status, pending updates, and permissions.</i>",
            parse_mode="HTML"
        )
        return

    token = parts[1].strip()
    status_msg = await message.reply("⚙️ <i>Authenticating token against Telegram Bot API...</i>", parse_mode="HTML")
    res = await check_bot_token(token)

    if not res.get("is_valid"):
        await status_msg.edit_text(
            f"❌ <b>Token Check Failed:</b>\n<code>{res.get('error', 'Invalid token')}</code>",
            parse_mode="HTML"
        )
        return

    text = [
        "🤖 <b>[BOT TOKEN AUDIT REPORT]</b>",
        "──────────────────────────────",
        f"• <b>Bot ID:</b> <code>{res['bot_id']}</code>",
        f"• <b>Name:</b> {res['first_name']}",
        f"• <b>Username:</b> @{res['username']}",
        f"• <b>Join Groups Allowed:</b> {'✅ Yes' if res['can_join_groups'] else '❌ No'}",
        f"• <b>Read Group Messages:</b> {'✅ Yes' if res['can_read_all_group_messages'] else '❌ Privacy Mode Enabled'}",
        f"• <b>Inline Queries Supported:</b> {'✅ Yes' if res['supports_inline_queries'] else '❌ No'}",
        f"• <b>Business Bot Support:</b> {'✅ Yes' if res['can_connect_to_business'] else '❌ No'}",
        "──────────────────────────────",
        "🌐 <b>WEBHOOK STATUS:</b>",
        f"• <b>Webhook URL:</b> <code>{res['webhook_url']}</code>",
        f"• <b>Pending Updates:</b> <code>{res['pending_updates']}</code>",
    ]
    if res.get("last_error_message"):
        text.append(f"• <b>Last Error:</b> ⚠️ <code>{res['last_error_message']}</code>")

    await status_msg.edit_text("\n".join(text), parse_mode="HTML")


@router.message(Command("fragment", "nft"))
@router.callback_query(F.data == "tool_fragment")
async def handle_fragment_check(event: Message | CallbackQuery):
    """Checks Fragment NFT market link and collectible format."""
    if isinstance(event, CallbackQuery):
        await event.message.answer(
            "💎 <b>FRAGMENT NFT CHECKER:</b>\n"
            "Send <code>/fragment &lt;username or anonymous number&gt;</code>\n"
            "<i>Example:</i> <code>/fragment auto</code> or <code>/fragment 8880123</code>",
            parse_mode="HTML"
        )
        await event.answer()
        return

    parts = event.text.split(maxsplit=1)
    if len(parts) < 2:
        await event.reply("Usage: <code>/fragment &lt;username&gt;</code>", parse_mode="HTML")
        return

    username = parts[1].strip().lstrip("@")
    val = validate_telegram_username(username)
    text = (
        f"💎 <b>FRAGMENT MARKETPLACE AUDIT: @{username}</b>\n"
        "──────────────────────────────\n"
        f"• <b>Valid Handle Format:</b> {'✅ Valid' if val['is_valid_format'] else '❌ Invalid'}\n"
        f"• <b>Length:</b> {val['length']} characters\n"
        f"• <b>Fragment Candidate:</b> {'⭐ High probability collectible' if val['is_fragment_candidate'] else 'Standard handle'}\n"
        f"• <b>Market Link:</b> <a href=\"{val['fragment_url']}\">Open on Fragment.com</a>"
    )
    await event.reply(text, parse_mode="HTML", disable_web_page_preview=True)


@router.message(Command("qr"))
async def handle_qr_command(message: Message):
    """Generates custom Telegram-themed QR code for any text or link."""
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply("🏁 Usage: <code>/qr &lt;text or link&gt;</code>", parse_mode="HTML")
        return

    text = parts[1].strip()
    qr_path = generate_styled_qr(text, filename_prefix="user_custom")
    await message.reply_photo(
        photo=FSInputFile(str(qr_path)),
        caption=f"🏁 <b>Styled QR Code for:</b>\n<code>{text[:100]}</code>",
        parse_mode="HTML"
    )


@router.message(Command("audit"))
async def handle_audit_command(message: Message):
    """Scans text for phishing, scam keywords, and suspicious links."""
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply("🛡️ Usage: <code>/audit &lt;suspicious text or bio&gt;</code>", parse_mode="HTML")
        return

    text = parts[1].strip()
    res = analyze_text_osint(text)
    report = [
        "🛡️ <b>[OSINT TEXT & PHISHING AUDIT]</b>",
        "──────────────────────────────",
        f"• <b>Risk Rating:</b> <b>{res['risk_rating']}</b>",
        f"• <b>Threat Score:</b> <code>{res['risk_score']}/100</code>",
        f"• <b>Detected Script:</b> <code>{res['language_script']}</code>",
        f"• <b>Extracted Links:</b> {', '.join(res['links']) or 'None'}",
        f"• <b>Extracted Emails:</b> {', '.join(res['emails']) or 'None'}",
        f"• <b>Extracted Mentions:</b> {', '.join(res['mentions']) or 'None'}",
    ]
    if res['risk_triggers']:
        report.append(f"⚠️ <b>Detected Triggers:</b> {', '.join(res['risk_triggers'])}")

    await message.reply("\n".join(report), parse_mode="HTML")


@router.callback_query(F.data == "tool_bot_check")
async def prompt_bot_check(callback: CallbackQuery):
    await callback.message.answer("🤖 Send <code>/token &lt;bot_token&gt;</code> to check bot info & webhook!", parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "tool_custom_qr")
async def prompt_custom_qr(callback: CallbackQuery):
    await callback.message.answer("🏁 Send <code>/qr &lt;url or text&gt;</code> to render a custom QR code!", parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "tool_scam_audit")
async def prompt_scam_audit(callback: CallbackQuery):
    await callback.message.answer("🛡️ Send <code>/audit &lt;text&gt;</code> to analyze scam/phishing triggers!", parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "tool_deeplinks")
async def show_deeplinks_guide(callback: CallbackQuery):
    text = (
        "🔗 <b>TELEGRAM DEEP PROTOCOL LINKS SUITE</b>\n"
        "──────────────────────────────\n"
        "• <b>Direct User Protocol:</b> <code>tg://user?id=&lt;USER_ID&gt;</code>\n"
        "• <b>Direct Chat Resolution:</b> <code>tg://resolve?domain=&lt;USERNAME&gt;</code>\n"
        "• <b>Direct Message Share:</b> <code>tg://msg_url?url=&lt;URL&gt;&amp;text=&lt;TEXT&gt;</code>\n"
        "• <b>Add Proxy Protocol:</b> <code>tg://proxy?server=&lt;IP&gt;&amp;port=&lt;PORT&gt;&amp;secret=&lt;SECRET&gt;</code>\n"
        "• <b>Apply Language Pack:</b> <code>tg://setlanguage?lang=&lt;LANG&gt;</code>"
    )
    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()
