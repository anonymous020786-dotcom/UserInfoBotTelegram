import asyncio
from html import escape as escape_html
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
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
            f"• <b>Classification:</b> <code>{format_type}</code>",
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


# -------------------------------------------------------------
# 10. MTPROTO PROXY GENERATOR (/proxy)
# -------------------------------------------------------------
@router.message(Command("proxy", "proxies"))
async def handle_proxy_command(message: Message):
    """Provides verified MTProto & SOCKS5 proxy configurations to bypass censorship."""
    from core.network_tools import get_public_mtproto_proxies
    proxies = get_public_mtproto_proxies()

    lines = [
        "🛡️ <b>[TELEGRAM MTPROTO & SOCKS5 PROXY SUITE]</b>",
        "──────────────────────────────",
        "Use these verified proxy servers to bypass ISP blocks and network firewalls:\n"
    ]
    kb_rows = []
    for p in proxies:
        lines.append(f"🌐 <b>{p['name']}</b>")
        lines.append(f"   • Server: <code>{p['server']}</code> (Port: {p['port']})")
        lines.append(f"   • Protocol: MTProto Encrypted TLS\n")
        kb_rows.append([InlineKeyboardButton(text=f"⚡ Connect to {p['name']}", url=p['link'])])

    lines.append("<i>Click a button below to connect with 1 tap directly in Telegram:</i>")
    await message.reply("\n".join(lines), reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows), parse_mode="HTML")


# -------------------------------------------------------------
# 11. SSL CERTIFICATE INSPECTOR (/ssl <domain>)
# -------------------------------------------------------------
@router.message(Command("ssl", "cert"))
async def handle_ssl_command(message: Message):
    """Audits TLS/SSL certificate of any domain or web service."""
    from core.network_tools import check_ssl_certificate
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply("🔒 Usage: <code>/ssl &lt;domain_name&gt;</code>\n<i>Example:</i> <code>/ssl telegram.org</code>", parse_mode="HTML")
        return

    domain = parts[1].strip()
    status_msg = await message.reply(f"🔒 <i>Negotiating TLS handshake with {domain}:443...</i>", parse_mode="HTML")
    res = await check_ssl_certificate(domain)

    if not res.get("is_valid"):
        await status_msg.edit_text(f"❌ <b>SSL Handshake Failed:</b> <code>{res.get('error', 'Unknown error')}</code>", parse_mode="HTML")
        return

    days_str = f"<b>{res['days_remaining']} days remaining</b>" if res.get("days_remaining") is not None else "Unknown"
    text = [
        f"🔒 <b>[SSL/TLS CERTIFICATE AUDIT: {res['domain']}]</b>",
        "──────────────────────────────",
        f"• <b>Issuer CA:</b> <code>{res['issuer']}</code>",
        f"• <b>Valid Until:</b> <code>{res['expires_at']}</code>",
        f"• <b>Validity Window:</b> {days_str}",
        f"• <b>Alternative Names (SANs):</b> {res['sans_count']} domains covered",
        f"• <b>Sample SANs:</b> {', '.join(res.get('sans_sample', []))}",
        "──────────────────────────────",
        "✓ <b>Certificate Status:</b> <b>ACTIVE & SECURE</b>"
    ]
    await status_msg.edit_text("\n".join(text), parse_mode="HTML")


# -------------------------------------------------------------
# 12. WHOIS / RDAP REGISTRATION AUDITOR (/whois <domain>)
# -------------------------------------------------------------
@router.message(Command("whois", "rdap"))
async def handle_whois_command(message: Message):
    """Queries ICANN RDAP for authoritative domain registration records."""
    from core.network_tools import query_rdap_whois
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply("🌐 Usage: <code>/whois &lt;domain_name&gt;</code>\n<i>Example:</i> <code>/whois telegram.org</code>", parse_mode="HTML")
        return

    domain = parts[1].strip()
    status_msg = await message.reply(f"🌐 <i>Querying authoritative RDAP registry for {domain}...</i>", parse_mode="HTML")
    res = await query_rdap_whois(domain)

    if not res.get("success"):
        await status_msg.edit_text(f"❌ <b>RDAP Query Failed:</b> <code>{res.get('error', 'Lookup failed')}</code>", parse_mode="HTML")
        return

    text = [
        f"🌐 <b>[AUTHORITATIVE RDAP / WHOIS: {res['domain']}]</b>",
        "──────────────────────────────",
        f"• <b>Registrar:</b> <b>{res['registrar']}</b>",
        f"• <b>Registration Date:</b> <code>{res['created']}</code>",
        f"• <b>Expiration Date:</b> <code>{res['expires']}</code>",
        f"• <b>Last Updated:</b> <code>{res['last_changed']}</code>",
        f"• <b>Domain Status:</b> <code>{', '.join(res['status'][:3])}</code>",
        "──────────────────────────────",
        "✓ <b>Registry Data Source:</b> ICANN RDAP Framework"
    ]
    await status_msg.edit_text("\n".join(text), parse_mode="HTML")


# -------------------------------------------------------------
# 13. CRYPTOGRAPHIC HASH CALCULATOR (/hash <text>)
# -------------------------------------------------------------
@router.message(Command("hash", "checksum"))
async def handle_hash_command(message: Message):
    """Calculates MD5, SHA-1, and SHA-256 cryptographic hashes."""
    from core.network_tools import calculate_hashes
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply("🔑 Usage: <code>/hash &lt;text_or_payload&gt;</code>", parse_mode="HTML")
        return

    payload = parts[1].strip()
    res = calculate_hashes(payload)
    text = [
        "🔑 <b>[CRYPTOGRAPHIC HASH & CHECKSUM REPORT]</b>",
        "──────────────────────────────",
        f"• <b>Input Payload:</b> <code>{res['text']}</code> ({res['bytes_len']} bytes)",
        "──────────────────────────────",
        f"• <b>MD5:</b>\n<code>{res['md5']}</code>",
        f"• <b>SHA-1:</b>\n<code>{res['sha1']}</code>",
        f"• <b>SHA-256:</b>\n<code>{res['sha256']}</code>",
    ]
    await message.reply("\n".join(text), parse_mode="HTML")


# -------------------------------------------------------------
# 14. TELEGRAM DEEP START PARAM DECODER (/startparam <payload>)
# -------------------------------------------------------------
@router.message(Command("startparam", "decode"))
async def handle_startparam_command(message: Message):
    """Decodes Telegram deep link start parameters (?start=payload)."""
    from core.network_tools import decode_telegram_start_param
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply("🔍 Usage: <code>/startparam &lt;payload&gt;</code>\n<i>Example:</i> <code>/startparam dGVzdF9wYXlsb2Fk</code>", parse_mode="HTML")
        return

    raw_param = parts[1].strip()
    res = decode_telegram_start_param(raw_param)
    lines = [
        "🔍 <b>[TELEGRAM START PARAMETER FORENSICS]</b>",
        "──────────────────────────────",
        f"• <b>Raw Parameter:</b> <code>{res['raw_parameter']}</code>\n"
    ]
    if res["decodings"]:
        for d in res["decodings"]:
            lines.append(f"• <b>{d['format']}:</b>\n  <code>{d['value']}</code>\n")
    else:
        lines.append("• <i>No standard base64 or hex decoding pattern matched; payload appears plain or custom-encrypted.</i>")

    await message.reply("\n".join(lines), parse_mode="HTML")


# -------------------------------------------------------------
# 15. CHANNEL QUALITY & HEALTH AUDIT SCORE (/health @channel)
# -------------------------------------------------------------
@router.message(Command("health", "score"))
async def handle_channel_health(message: Message, bot: Bot):
    """Calculates comprehensive 100-point Channel Health & Quality Score."""
    from core.channel_intelligence import calculate_channel_health_score
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply("📈 Usage: <code>/health &lt;@channel_handle&gt;</code>\n<i>Example:</i> <code>/health @telegram</code>", parse_mode="HTML")
        return

    target = parts[1].strip().lstrip("@")
    status_msg = await message.reply(f"📈 <i>Auditing health metrics for @{target}...</i>", parse_mode="HTML")
    entity_data = await resolve_full_entity(target, bot=bot)

    if not entity_data:
        await status_msg.edit_text("❌ <b>Could not resolve channel.</b> Please verify the username.", parse_mode="HTML")
        return

    res = calculate_channel_health_score(entity_data)
    lines = [
        f"📈 <b>[CHANNEL HEALTH AUDIT: {escape_html(entity_data['title'])}]</b>",
        "──────────────────────────────",
        f"• <b>Quality Score:</b> <b>{res['score']} / 100</b>",
        f"• <b>Rating Tier:</b> 🏆 <b>{res['grade']}</b>",
        "──────────────────────────────",
        "📋 <b>SCORE BREAKDOWN:</b>"
    ]
    for b in res["breakdown"]:
        lines.append(f"• {b}")

    lines.extend([
        "──────────────────────────────",
        "<i>High quality scores correlate with authentic audiences, clear branding, and verified trust.</i>"
    ])
    await status_msg.edit_text("\n".join(lines), parse_mode="HTML")


# -------------------------------------------------------------
# 16. COUNTRY-SPECIFIC COMMUNITIES (/country <code_or_name>)
# -------------------------------------------------------------
@router.message(Command("country", "regional"))
async def handle_country_command(message: Message):
    """Lists popular national and regional communities."""
    from core.channel_intelligence import get_country_channels, COUNTRY_COMMUNITIES
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        avail_codes = ", ".join([f"<code>{k.upper()}</code>" for k in COUNTRY_COMMUNITIES.keys()])
        await message.reply(
            f"🌐 <b>REGIONAL CHAT EXPLORER:</b>\n"
            f"Send <code>/country &lt;code&gt;</code>\n"
            f"Available country codes: {avail_codes}\n"
            f"<i>Example:</i> <code>/country US</code> or <code>/country IN</code>",
            parse_mode="HTML"
        )
        return

    code = parts[1].strip().lower()
    cinfo = get_country_channels(code)
    if not cinfo:
        await message.reply(f"❌ Country code <code>{code.upper()}</code> not found in regional index. Available: US, UK, IN, DE, ES, FR, BR, AE.", parse_mode="HTML")
        return

    lines = [
        f"{cinfo['flag']} <b>[TOP COMMUNITIES: {cinfo['country'].upper()}]</b>",
        "──────────────────────────────",
        f"Curated leading national news & public communities:\n"
    ]
    kb_rows = []
    for ch in cinfo["channels"]:
        lines.append(f"• <b>@{ch}</b>")
        kb_rows.append([InlineKeyboardButton(text=f"📢 Open @{ch}", url=f"https://t.me/{ch}")])

    await message.reply("\n".join(lines), reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows), parse_mode="HTML")


# -------------------------------------------------------------
# 17. WATCHLIST / WATCHDOG MONITOR (/watch, /watchlist, /unwatch)
# -------------------------------------------------------------
@router.message(Command("watch"))
async def handle_watch_command(message: Message, bot: Bot):
    """Adds a target to personal watchdog monitoring list."""
    from database import add_to_watchlist
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply("👁️ Usage: <code>/watch &lt;@target&gt;</code>\n<i>Monitors target subscriber changes and rebranding.</i>", parse_mode="HTML")
        return

    target = parts[1].strip().lstrip("@")
    status_msg = await message.reply(f"👁️ <i>Resolving and registering @{target} to Watchdog...</i>", parse_mode="HTML")
    entity_data = await resolve_full_entity(target, bot=bot)

    if not entity_data:
        await status_msg.edit_text("❌ <b>Could not resolve target.</b> Please verify spelling.", parse_mode="HTML")
        return

    ok = await add_to_watchlist(
        user_id=message.from_user.id,
        target_identifier=target,
        target_type=entity_data.get("type", "entity"),
        target_title=entity_data.get("title", target),
        members_count=entity_data.get("members_count")
    )
    if ok:
        await status_msg.edit_text(
            f"👁️ <b>Watchdog Active:</b> Added <b>{escape_html(entity_data['title'])}</b> (@{target}) to your personal watchlist.\n"
            f"• <b>Type:</b> <code>{entity_data.get('type', 'entity')}</code>\n"
            f"• <b>Current Members:</b> <code>{entity_data.get('members_count', 'N/A')}</code>\n"
            f"• Use <code>/watchlist</code> to view all monitored targets.",
            parse_mode="HTML"
        )
    else:
        await status_msg.edit_text(f"⚠️ <b>@{target}</b> is already registered in your watchlist.", parse_mode="HTML")


@router.message(Command("watchlist", "watchdog"))
@router.callback_query(F.data == "nav_watchlist")
async def handle_watchlist_view(event: Message | CallbackQuery):
    """Displays user's active watchdog monitoring list."""
    from database import get_user_watchlist
    user_id = event.from_user.id
    items = await get_user_watchlist(user_id)

    if not items:
        text = (
            "👁️ <b>[YOUR WATCHDOG MONITORING LIST]</b>\n"
            "──────────────────────────────\n"
            "<i>You currently have no targets registered in your Watchdog.</i>\n\n"
            "To monitor a channel, group, or bot, send:\n"
            "<code>/watch &lt;@username&gt;</code>"
        )
        if isinstance(event, CallbackQuery):
            await event.message.answer(text, parse_mode="HTML")
            await event.answer()
        else:
            await event.answer(text, parse_mode="HTML")
        return

    lines = [
        "👁️ <b>[YOUR WATCHDOG MONITORING LIST]</b>",
        "──────────────────────────────",
        f"Tracking <b>{len(items)}</b> active entities for updates:\n"
    ]
    kb_rows = []
    for it in items:
        uname = it["target_identifier"]
        title = escape_html(it["target_title"] or uname)
        mcount = f"{it['last_members_count']:,} members" if it.get("last_members_count") else "Monitored"
        lines.append(f"• <b>{title}</b> (@{uname}) — <code>{mcount}</code>")
        kb_rows.append([
            InlineKeyboardButton(text=f"🔍 Check @{uname}", callback_data=f"query_chat_{uname}"),
            InlineKeyboardButton(text=f"❌ Unwatch", callback_data=f"unwatch_{uname}")
        ])

    kb_rows.append([InlineKeyboardButton(text="🏠 Home", callback_data="nav_home")])

    if isinstance(event, CallbackQuery):
        await event.message.edit_text("\n".join(lines), reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows), parse_mode="HTML")
        await event.answer()
    else:
        await event.answer("\n".join(lines), reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows), parse_mode="HTML")


@router.callback_query(F.data.startswith("unwatch_"))
async def handle_unwatch_callback(callback: CallbackQuery):
    """Removes a target from watchlist via inline button."""
    from database import remove_from_watchlist
    target = callback.data.split("unwatch_")[-1]
    await remove_from_watchlist(callback.from_user.id, target)
    await callback.answer(f"Removed @{target} from Watchdog.", show_alert=True)
    await handle_watchlist_view(callback)


@router.message(Command("unwatch"))
async def handle_unwatch_command(message: Message):
    """Removes a target from watchlist via command."""
    from database import remove_from_watchlist
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply("Usage: <code>/unwatch &lt;@target&gt;</code>", parse_mode="HTML")
        return

    target = parts[1].strip().lstrip("@")
    ok = await remove_from_watchlist(message.from_user.id, target)
    if ok:
        await message.reply(f"✓ Removed <b>@{target}</b> from your Watchdog.", parse_mode="HTML")
    else:
        await message.reply(f"Target <b>@{target}</b> was not found in your Watchdog.", parse_mode="HTML")


# -------------------------------------------------------------
# 18. DATA DUMP & EXPORT (/exportdata)
# -------------------------------------------------------------
@router.message(Command("exportdata", "dumpdata"))
async def handle_export_data(message: Message):
    """Compiles and exports all user search history, favorites, and watchlist into a downloadable JSON file."""
    import json
    from database import export_user_data_json
    from aiogram.types import BufferedInputFile
    status_msg = await message.reply("📦 <i>Compiling your complete activity and forensic history archive...</i>", parse_mode="HTML")

    dump = await export_user_data_json(message.from_user.id)
    json_bytes = json.dumps(dump, indent=2, ensure_ascii=False).encode("utf-8")

    file_doc = BufferedInputFile(
        file=json_bytes,
        filename=f"sentinel_archive_user_{message.from_user.id}.json"
    )
    await message.reply_document(
        document=file_doc,
        caption=(
            f"📦 <b>[SENTINEL USER ARCHIVE // JSON DUMP]</b>\n"
            f"──────────────────────────────\n"
            f"• <b>Total Searches:</b> <code>{dump['total_searches']}</code>\n"
            f"• <b>Total Bookmarks:</b> <code>{dump['total_favorites']}</code>\n"
            f"• <b>Watchdog Targets:</b> <code>{dump['total_watched']}</code>\n"
            f"• <i>Export generated securely in accordance with data sovereignty.</i>"
        ),
        parse_mode="HTML"
    )
    await status_msg.delete()

