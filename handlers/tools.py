import asyncio
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command

from ui.keyboards import tools_menu_keyboard
from ui.formatters import (
    format_post_report,
    format_fragment_report,
    format_comparison_report,
    format_domain_ip_report,
    format_phone_report,
    format_id_forensics_report,
)
from core.bot_checker import check_bot_token
from core.dc_resolver import DC_DATA
from core.osint_analyzer import analyze_text_osint, validate_telegram_username
from core.qr_generator import generate_styled_qr
from core.post_analyzer import fetch_real_telegram_post
from core.fragment_scraper import scrape_fragment_username
from core.domain_ip_analyzer import resolve_domain_or_ip
from core.phone_analyzer import analyze_phone_number
from core.id_forensics import analyze_telegram_id, analyze_bot_token_forensics
from core.telegram_discovery import fetch_real_telegram_preview, resolve_full_entity

router = Router(name="tools_router")


@router.message(Command("tools"))
@router.callback_query(F.data == "nav_tools")
async def handle_tools_menu(event: Message | CallbackQuery, user_lang: str = "en"):
    """Displays the comprehensive OSINT and developer utility suite."""
    text = (
        "🛠️ <b>SENTINEL // OSINT & DEVELOPER SUITE</b>\n"
        "──────────────────────────────\n"
        "Advanced diagnostic and OSINT utilities for Telegram analysts:\n\n"
        "• <b>📊 Post Forensics:</b> Live view count, engagement %, media & timestamps\n"
        "• <b>⚖️ Channel Comparator:</b> Side-by-side metric comparison for 2 channels\n"
        "• <b>💎 Fragment NFT Live:</b> Real auction bids, valuation in TON, and owners\n"
        "• <b>🌐 Domain & IP OSINT:</b> Asynchronous DNS, geolocation, ISP & ASN lookup\n"
        "• <b>📱 Phone Number OSINT:</b> E.164 parser, flag, country & TON +888 detector\n"
        "• <b>🔢 64-bit ID Forensics:</b> Epoch mathematics, bit-depth & architecture\n"
        "• <b>🤖 Bot Token Checker:</b> Validate token, getWebhookInfo, and permissions\n"
        "• <b>🎨 Sticker Forensics:</b> Extract sticker pack size, type & emojis\n"
        "• <b>🌐 DC Architecture Map:</b> Telegram global routing & primary nodes\n"
        "• <b>🛡️ Scam & Phishing Auditor:</b> Heuristic threat scoring on text\n\n"
        "👇 <i>Select a tool below or use the commands: /post, /compare, /fragment, /domain, /phone, /idmath, /token, /sticker</i>"
    )
    kb = tools_menu_keyboard(user_lang)
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        await event.answer()
    else:
        await event.answer(text, reply_markup=kb, parse_mode="HTML")


# -------------------------------------------------------------
# 1. CHANNEL POST FORENSICS (/post <link>)
# -------------------------------------------------------------
@router.message(Command("post"))
async def handle_post_command(message: Message):
    """Scrapes 100% real live data for any Telegram channel post."""
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply(
            "📊 <b>POST FORENSICS USAGE:</b>\n"
            "Send <code>/post &lt;channel_post_url&gt;</code>\n"
            "<i>Example:</i> <code>/post https://t.me/telegram/248</code>\n"
            "<i>Extracts real views, published date, media type, and calculates engagement rate.</i>",
            parse_mode="HTML"
        )
        return

    post_url = parts[1].strip()
    status_msg = await message.reply("⚙️ <i>Fetching live post metrics directly from Telegram servers...</i>", parse_mode="HTML")
    post_data = await fetch_real_telegram_post(post_url)

    if not post_data:
        await status_msg.edit_text("❌ <b>Could not retrieve post.</b> Verify the channel is public and link format is valid (e.g. <code>https://t.me/channel/123</code>).", parse_mode="HTML")
        return

    # Fetch channel total subscribers to compute real engagement %
    channel_preview = await fetch_real_telegram_preview(post_data["channel_handle"])
    channel_members = channel_preview.get("members_count") if channel_preview else None

    report = format_post_report(post_data, channel_members=channel_members)
    await status_msg.edit_text(report, parse_mode="HTML", disable_web_page_preview=True)


# -------------------------------------------------------------
# 2. CHANNEL COMPARATOR (/compare @ch1 @ch2)
# -------------------------------------------------------------
@router.message(Command("compare"))
async def handle_compare_command(message: Message, bot: Bot):
    """Compares two Telegram channels or groups side-by-side."""
    parts = message.text.split()
    if len(parts) < 3:
        await message.reply(
            "⚖️ <b>CHANNEL COMPARATOR USAGE:</b>\n"
            "Send <code>/compare &lt;@target1&gt; &lt;@target2&gt;</code>\n"
            "<i>Example:</i> <code>/compare @telegram @durov</code>",
            parse_mode="HTML"
        )
        return

    t1, t2 = parts[1].strip().lstrip("@"), parts[2].strip().lstrip("@")
    status_msg = await message.reply(f"⚖️ <i>Comparing @{t1} vs @{t2} in real-time...</i>", parse_mode="HTML")

    e1, e2 = await asyncio.gather(
        resolve_full_entity(t1, bot=bot),
        resolve_full_entity(t2, bot=bot),
        return_exceptions=True
    )

    if not isinstance(e1, dict) or not isinstance(e2, dict):
        await status_msg.edit_text("❌ <b>Comparison failed.</b> One or both entities could not be resolved on Telegram.", parse_mode="HTML")
        return

    rep = format_comparison_report(e1, e2)
    await status_msg.edit_text(rep, parse_mode="HTML")


# -------------------------------------------------------------
# 3. FRAGMENT.COM LIVE SCRAPER (/fragment <handle>)
# -------------------------------------------------------------
@router.message(Command("fragment", "nft"))
@router.callback_query(F.data == "tool_fragment")
async def handle_fragment_check(event: Message | CallbackQuery):
    """Scrapes live data directly from Fragment.com."""
    if isinstance(event, CallbackQuery):
        await event.message.answer(
            "💎 <b>FRAGMENT NFT LIVE SCRAPER:</b>\n"
            "Send <code>/fragment &lt;username or 888 number&gt;</code>\n"
            "<i>Example:</i> <code>/fragment crypto</code> or <code>/fragment 8880123</code>\n"
            "<i>Scrapes real status, current bids, price in TON, and auction timer.</i>",
            parse_mode="HTML"
        )
        await event.answer()
        return

    parts = event.text.split(maxsplit=1)
    if len(parts) < 2:
        await event.reply("Usage: <code>/fragment &lt;username&gt;</code>", parse_mode="HTML")
        return

    username = parts[1].strip().lstrip("@")
    status_msg = await event.reply(f"💎 <i>Querying Fragment.com blockchain marketplace for @{username}...</i>", parse_mode="HTML")
    frag_data = await scrape_fragment_username(username)
    report = format_fragment_report(frag_data)
    await status_msg.edit_text(report, parse_mode="HTML", disable_web_page_preview=True)


# -------------------------------------------------------------
# 4. DOMAIN & IP OSINT (/domain <domain> or /ip <address>)
# -------------------------------------------------------------
@router.message(Command("domain", "ip", "dns"))
@router.callback_query(F.data == "tool_domain_ip")
async def handle_domain_ip_command(event: Message | CallbackQuery):
    """Resolves DNS, queries IP Geolocation, ASN, and scans phishing risk."""
    if isinstance(event, CallbackQuery):
        await event.message.answer(
            "🌐 <b>DOMAIN & IP OSINT USAGE:</b>\n"
            "Send <code>/domain &lt;domain_or_url&gt;</code> or <code>/ip &lt;ip_address&gt;</code>\n"
            "<i>Example:</i> <code>/domain telegram.org</code> or <code>/ip 149.154.167.99</code>",
            parse_mode="HTML"
        )
        await event.answer()
        return

    parts = event.text.split(maxsplit=1)
    if len(parts) < 2:
        await event.reply("Usage: <code>/domain &lt;example.com&gt;</code> or <code>/ip &lt;1.1.1.1&gt;</code>", parse_mode="HTML")
        return

    target = parts[1].strip()
    status_msg = await event.reply("🌐 <i>Resolving DNS & routing infrastructure...</i>", parse_mode="HTML")
    res = await resolve_domain_or_ip(target)
    report = format_domain_ip_report(res)
    await status_msg.edit_text(report, parse_mode="HTML")


# -------------------------------------------------------------
# 5. PHONE NUMBER OSINT (/phone <number>)
# -------------------------------------------------------------
@router.message(Command("phone"))
@router.callback_query(F.data == "tool_phone_osint")
async def handle_phone_command(event: Message | CallbackQuery):
    """Analyzes international phone number, detects country and Fragment +888 NFT."""
    if isinstance(event, CallbackQuery):
        await event.message.answer(
            "📱 <b>PHONE NUMBER OSINT USAGE:</b>\n"
            "Send <code>/phone &lt;number_with_country_code&gt;</code>\n"
            "<i>Example:</i> <code>/phone +12025550143</code> or <code>/phone +88801234567</code>",
            parse_mode="HTML"
        )
        await event.answer()
        return

    parts = event.text.split(maxsplit=1)
    if len(parts) < 2:
        await event.reply("Usage: <code>/phone &lt;number_with_country_code&gt;</code>", parse_mode="HTML")
        return

    phone = parts[1].strip()
    res = analyze_phone_number(phone)
    report = format_phone_report(res)
    await event.reply(report, parse_mode="HTML", disable_web_page_preview=True)


# -------------------------------------------------------------
# 6. 64-BIT ID FORENSICS (/idmath <id>)
# -------------------------------------------------------------
@router.message(Command("idmath", "epoch"))
@router.callback_query(F.data == "tool_idmath")
async def handle_idmath_command(event: Message | CallbackQuery):
    """Performs 64-bit ID mathematics, architecture, and epoch breakdown."""
    if isinstance(event, CallbackQuery):
        await event.message.answer(
            "🔢 <b>64-BIT ID FORENSICS USAGE:</b>\n"
            "Send <code>/idmath &lt;numeric_telegram_id&gt;</code>\n"
            "<i>Example:</i> <code>/idmath 7500000000</code> or <code>/idmath -1001234567890</code>",
            parse_mode="HTML"
        )
        await event.answer()
        return

    parts = event.text.split(maxsplit=1)
    if len(parts) < 2:
        await event.reply("Usage: <code>/idmath &lt;numeric_id&gt;</code>", parse_mode="HTML")
        return

    raw_id = parts[1].strip()
    res = analyze_telegram_id(raw_id)
    if "error" in res:
        await event.reply(f"❌ {res['error']}", parse_mode="HTML")
        return

    report = format_id_forensics_report(res)
    await event.reply(report, parse_mode="HTML")


# -------------------------------------------------------------
# 7. STICKER PACK FORENSICS (/sticker <pack_name>)
# -------------------------------------------------------------
@router.message(Command("sticker", "stickers"))
@router.callback_query(F.data == "tool_sticker")
async def handle_sticker_command(event: Message | CallbackQuery, bot: Bot):
    """Inspects official Telegram sticker packs."""
    if isinstance(event, CallbackQuery):
        await event.message.answer(
            "🎨 <b>STICKER FORENSICS USAGE:</b>\n"
            "Send <code>/sticker &lt;pack_name or link&gt;</code>\n"
            "<i>Example:</i> <code>/sticker TelegramFlies</code> or send <code>/sticker https://t.me/addstickers/TelegramFlies</code>",
            parse_mode="HTML"
        )
        await event.answer()
        return

    parts = event.text.split(maxsplit=1)
    if len(parts) < 2:
        await event.reply("Usage: <code>/sticker &lt;pack_name_or_link&gt;</code>", parse_mode="HTML")
        return

    target = parts[1].strip()
    if "addstickers/" in target:
        target = target.split("addstickers/")[-1].split("?")[0].strip("/")

    try:
        set_info = await bot.get_sticker_set(name=target)
        stickers_count = len(set_info.stickers)
        sample_emojis = " ".join([s.emoji for s in set_info.stickers[:8] if s.emoji])
        format_type = getattr(set_info, "sticker_type", "Regular")
        is_anim = getattr(set_info.stickers[0], "is_animated", False) if set_info.stickers else False
        is_vid = getattr(set_info.stickers[0], "is_video", False) if set_info.stickers else False

        st_type = "🎬 Video (WebM)" if is_vid else ("✨ Animated (TGS/Lottie)" if is_anim else "🖼️ Static (WebP)")

        text = [
            f"🎨 <b>[STICKER PACK FORENSICS: {set_info.title}]</b>",
            "──────────────────────────────",
            f"• <b>Short Name:</b> <code>{set_info.name}</code>",
            f"• <b>Sticker Format:</b> <b>{st_type}</b>",
            f"• <b>Total Stickers:</b> <code>{stickers_count}</code>",
            f"• <b>Sample Emojis:</b> {sample_emojis or 'None'}",
            "──────────────────────────────",
            f"🔗 <b>INSTALL PROTOCOL:</b> <a href=\"tg://addstickers?set={set_info.name}\">Install in Telegram</a> | <a href=\"https://t.me/addstickers/{set_info.name}\">Web Link</a>"
        ]
        await event.reply("\n".join(text), parse_mode="HTML")
    except Exception as e:
        await event.reply(f"❌ <b>Sticker Set Error:</b> <code>{e}</code>\n<i>Verify the pack name is correct.</i>", parse_mode="HTML")


@router.message(F.sticker)
async def handle_incoming_sticker(message: Message, bot: Bot):
    """Directly inspects any sent sticker and its parent sticker set."""
    stk = message.sticker
    set_name = stk.set_name
    w, h = stk.width, stk.height
    is_anim = stk.is_animated
    is_vid = stk.is_video
    fmt = "🎬 Video (WebM)" if is_vid else ("✨ Animated (TGS/Lottie)" if is_anim else "🖼️ Static (WebP)")

    lines = [
        "🎨 <b>[STICKER INSPECTION REPORT]</b>",
        "──────────────────────────────",
        f"• <b>Associated Emoji:</b> {stk.emoji or 'None'}",
        f"• <b>Format:</b> <b>{fmt}</b>",
        f"• <b>Dimensions:</b> <code>{w}x{h} px</code>",
        f"• <b>File ID:</b> <code>{stk.file_id[:30]}...</code>",
    ]

    if set_name:
        lines.append(f"• <b>Parent Pack:</b> <code>{set_name}</code>")
        try:
            set_info = await bot.get_sticker_set(name=set_name)
            lines.extend([
                f"• <b>Pack Title:</b> <b>{set_info.title}</b>",
                f"• <b>Total Stickers in Pack:</b> <code>{len(set_info.stickers)}</code>",
                "──────────────────────────────",
                f"🔗 <b>INSTALL PROTOCOL:</b> <a href=\"tg://addstickers?set={set_name}\">Install in Telegram</a>"
            ])
        except Exception:
            lines.append(f"🔗 <b>INSTALL PROTOCOL:</b> <a href=\"tg://addstickers?set={set_name}\">Install in Telegram</a>")
    else:
        lines.append("• <i>This sticker is standalone or from a custom collection.</i>")

    await message.reply("\n".join(lines), parse_mode="HTML")



# -------------------------------------------------------------
# 8. BOT TOKEN CHECKER (/token <bot_token>)
# -------------------------------------------------------------
@router.message(Command("token", "checkbot"))
async def handle_token_check(message: Message):
    """Validates Telegram Bot Token, decodes embedded Bot ID, and queries getWebhookInfo."""
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply(
            "🤖 <b>BOT TOKEN CHECKER USAGE:</b>\n"
            "Send <code>/token &lt;bot_token&gt;</code>\n"
            "<i>Performs offline Bot ID decoding, age estimation, and Bot API webhook health checks.</i>",
            parse_mode="HTML"
        )
        return

    token = parts[1].strip()
    status_msg = await message.reply("⚙️ <i>Authenticating token against Telegram Bot API...</i>", parse_mode="HTML")

    # Offline token forensics
    token_forensics = analyze_bot_token_forensics(token)
    res = await check_bot_token(token)

    if not res.get("is_valid"):
        err = res.get("error", "Invalid token")
        if token_forensics.get("is_valid_format"):
            bot_id = token_forensics["bot_id"]
            id_data = token_forensics["id_forensics"]
            await status_msg.edit_text(
                f"❌ <b>Bot API Authentication Failed:</b>\n<code>{err}</code>\n\n"
                f"🔍 <b>Offline Forensic Token Extraction:</b>\n"
                f"• <b>Extracted Bot ID:</b> <code>{bot_id}</code>\n"
                f"• <b>Estimated Bot Creation:</b> {id_data['estimated_registration']} ({id_data['relative_age']})\n"
                f"• <i>The token format is valid, but Telegram's server revoked or rejected it.</i>",
                parse_mode="HTML"
            )
        else:
            await status_msg.edit_text(f"❌ <b>Token Check Failed:</b>\n<code>{err}</code>", parse_mode="HTML")
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


# -------------------------------------------------------------
# 9. EXISTING UTILITIES (DC MAP, QR, AUDIT, DEEPLINKS)
# -------------------------------------------------------------
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


# Callbacks for tools menu
@router.callback_query(F.data == "tool_post_forensics")
async def prompt_post_forensics(callback: CallbackQuery):
    await callback.message.answer(
        "📊 <b>POST FORENSICS & ENGAGEMENT:</b>\n"
        "Send <code>/post &lt;channel_post_url&gt;</code>\n"
        "<i>Example:</i> <code>/post https://t.me/telegram/248</code>",
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "tool_compare")
async def prompt_compare(callback: CallbackQuery):
    await callback.message.answer(
        "⚖️ <b>CHANNEL COMPARATOR:</b>\n"
        "Send <code>/compare &lt;@channel1&gt; &lt;@channel2&gt;</code>\n"
        "<i>Example:</i> <code>/compare @telegram @durov</code>",
        parse_mode="HTML"
    )
    await callback.answer()


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
        "• <b>Apply Language Pack:</b> <code>tg://setlanguage?lang=&lt;LANG&gt;</code>\n"
        "• <b>Resolve Phone Number:</b> <code>tg://resolve?phone=&lt;PHONE_NUMBER&gt;</code>\n"
        "• <b>Add Sticker Set:</b> <code>tg://addstickers?set=&lt;PACK_NAME&gt;</code>"
    )
    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()
