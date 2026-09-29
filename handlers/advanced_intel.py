"""
Sentinel Advanced OSINT & Forensics Router.
Exposes deep analytical suites:
1. /botsafety - Bot Phishing & Security Vulnerability Scanner
2. /engagement (/velocity) - Channel Views-to-Subscriber Ratio & Zombie Detector
3. /linkaudit (/checklink) - Private Invite Hash & URL Redirection Forensics
4. /cloneradar - Impersonator & Lookalike Channel/Bot Radar
5. /groupaudit - Public Group Admin & Security Hygiene Auditor
6. /chanlang - Script & Regional Audience Classifier
7. /similar - Content & Taxonomy Community Recommendations
"""
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

from core.bot_safety_analyzer import audit_bot_safety
from core.channel_velocity import analyze_channel_velocity
from core.link_security import audit_telegram_link
from core.clone_radar import scan_clone_radar
from core.group_audit import audit_group_security
from core.language_detector import analyze_channel_language
from core.similar_engine import find_similar_communities
from ui.formatters import escape_html

router = Router(name="advanced_intel_router")


# ==============================================================================
# 1. BOT SAFETY & PHISHING SCANNER (/botsafety)
# ==============================================================================
@router.message(Command("botsafety", "safecheck", "auditbot"))
async def handle_bot_safety_command(message: Message):
    """Audits bot handle for impersonation, phishing phrases, and security rating."""
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply(
            "🛡️ <b>BOT SAFETY & PHISHING SCANNER USAGE:</b>\n"
            "──────────────────────────────\n"
            "Send <code>/botsafety &lt;@bot_username&gt;</code>\n"
            "<i>Example:</i> <code>/botsafety @BotFather</code> or <code>/botsafety @Wallet</code>\n\n"
            "• Scans for seed phrase/OTP harvesting patterns\n"
            "• Detects deceptive admin/support impersonation\n"
            "• Computes objective Bot Safety Score (0-100)",
            parse_mode="HTML"
        )
        return

    target = parts[1].strip()
    status_msg = await message.reply(f"🛡️ <i>Auditing bot security & phishing vectors for @{target.lstrip('@')}...</i>", parse_mode="HTML")

    res = await audit_bot_safety(target)
    if not res["found"]:
        await status_msg.edit_text(f"❌ <b>Error:</b> {res.get('error', 'Bot not found.')}", parse_mode="HTML")
        return

    verified_badge = " 🔷 [OFFICIALLY VERIFIED]" if res["is_verified"] else ""
    lines = [
        f"🛡️ <b>[BOT SECURITY FORENSICS: @{res['handle']}]</b>",
        "──────────────────────────────",
        f"• <b>Bot Title:</b> <b>{escape_html(res['title'])}</b>{verified_badge}",
        f"• <b>Security Score:</b> <b>{res['safety_score']} / 100</b>",
        f"• <b>Trust Verdict:</b> {res['badge']} <b>{res['verdict']}</b>",
        f"• <b>Threat Deduction:</b> <code>-{res['threat_points']} pts</code>",
        "──────────────────────────────"
    ]

    if res["triggers"]:
        lines.append("🚨 <b>DETECTED RISK TRIGGERS:</b>")
        for trig in res["triggers"]:
            lines.append(f"• <b>[{trig['type']}]:</b> <i>{trig['reason']}</i> (<code>{escape_html(trig['trigger'])}</code>)")
        lines.append("")
    else:
        lines.extend([
            "🔒 <b>ZERO PHISHING PATTERNS DETECTED:</b>",
            "• No credentials, OTP, or wallet seed harvesting phrases found.",
            ""
        ])

    lines.extend([
        "📋 <b>SECURITY ASSESSMENT:</b>",
        f"<i>{res['recommendation']}</i>"
    ])

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 Open Bot", url=f"https://t.me/{res['handle']}")],
        [InlineKeyboardButton(text="🔍 Deep OSINT Card", callback_data=f"query_chat_{res['handle']}")],
        [InlineKeyboardButton(text="🏠 Home Dashboard", callback_data="nav_home")]
    ])

    await status_msg.edit_text("\n".join(lines), reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data.startswith("run_botsafety_"))
async def handle_callback_botsafety(callback: CallbackQuery):
    """Interactive callback shortcut from bot search results."""
    uname = callback.data.replace("run_botsafety_", "").strip()
    fake_msg = callback.message
    fake_msg.text = f"/botsafety @{uname}"
    await callback.answer("Auditing bot safety...")
    await handle_bot_safety_command(fake_msg)


# ==============================================================================
# 2. CHANNEL ENGAGEMENT & VELOCITY FORENSICS (/engagement, /velocity)
# ==============================================================================
@router.message(Command("engagement", "velocity", "vsr", "reach"))
async def handle_channel_velocity_command(message: Message):
    """Calculates views-to-subscriber ratio, reach rate, and zombie channel detection."""
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply(
            "📈 <b>CHANNEL ENGAGEMENT & VELOCITY USAGE:</b>\n"
            "──────────────────────────────\n"
            "Send <code>/engagement &lt;@channel&gt;</code>\n"
            "<i>Example:</i> <code>/engagement @telegram</code> or <code>/velocity @durov</code>\n\n"
            "• Calculates Views-to-Subscriber Ratio (VSR%)\n"
            "• Measures Estimated Reach Rate (ERR%)\n"
            "• Detects Ghost/Zombie channels pumped with fake bots",
            parse_mode="HTML"
        )
        return

    target = parts[1].strip()
    status_msg = await message.reply(f"📈 <i>Auditing engagement velocity for @{target.lstrip('@')}...</i>", parse_mode="HTML")

    res = await analyze_channel_velocity(target)
    if not res["found"]:
        await status_msg.edit_text(f"❌ <b>Error:</b> {res.get('error', 'Channel not found.')}", parse_mode="HTML")
        return

    lines = [
        f"📈 <b>[ENGAGEMENT VELOCITY: @{res['handle']}]</b>",
        "──────────────────────────────",
        f"• <b>Target:</b> <b>{escape_html(res['title'])}</b>",
        f"• <b>Subscribers:</b> 👥 <b>{res['subscribers']:,}</b>",
        f"• <b>Average Post Views:</b> 👁️ <b>~{res['avg_post_views']:,}</b>",
        f"• <b>Views-to-Subs (VSR):</b> ⚡ <b>{res['vsr_percent']}%</b>",
        f"• <b>Estimated Reach Rate:</b> 📊 <b>{res['err_percent']}%</b>",
        f"• <b>Activity Tier:</b> <b>{res['status_tier']}</b>",
        f"• <b>Authenticity Grade:</b> 🏆 <b>Grade {res['activity_grade']}</b>",
        "──────────────────────────────",
        "📋 <b>FORENSIC FINDING:</b>",
        f"<i>{res['assessment']}</i>"
    ]

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Open Channel", url=f"https://t.me/{res['handle']}")],
        [InlineKeyboardButton(text="⚖️ Channel Health Audit", callback_data=f"tool_health")],
        [InlineKeyboardButton(text="🏠 Home Dashboard", callback_data="nav_home")]
    ])

    await status_msg.edit_text("\n".join(lines), reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data.startswith("run_velocity_"))
async def handle_callback_velocity(callback: CallbackQuery):
    """Interactive callback shortcut from channel search results."""
    uname = callback.data.replace("run_velocity_", "").strip()
    fake_msg = callback.message
    fake_msg.text = f"/engagement @{uname}"
    await callback.answer("Auditing engagement velocity...")
    await handle_channel_velocity_command(fake_msg)


# ==============================================================================
# 3. TELEGRAM LINK & PRIVATE INVITE SECURITY (/linkaudit, /checklink)
# ==============================================================================
@router.message(Command("linkaudit", "checklink", "invite"))
async def handle_link_audit_command(message: Message):
    """Inspects private join hashes, unmasks shorteners, and detects deceptive URLs."""
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply(
            "🔗 <b>TELEGRAM LINK & INVITE FORENSICS USAGE:</b>\n"
            "──────────────────────────────\n"
            "Send <code>/linkaudit &lt;link_or_invite&gt;</code>\n"
            "<i>Examples:</i>\n"
            "• <code>/linkaudit https://t.me/+AbCdEfGhIjKlMnOp</code> (Private Invite)\n"
            "• <code>/linkaudit https://bit.ly/example</code> (Unmask Shortener)\n"
            "• <code>/linkaudit http://suspicious-telegram-link.com</code>",
            parse_mode="HTML"
        )
        return

    raw_link = parts[1].strip()
    status_msg = await message.reply("🔗 <i>Analyzing link structure and tracing redirection hops...</i>", parse_mode="HTML")

    res = await audit_telegram_link(raw_link)

    if res["type"] == "telegram_invite":
        lines = [
            "🔐 <b>[TELEGRAM PRIVATE INVITE AUDIT]</b>",
            "──────────────────────────────",
            f"• <b>Invite Token Hash:</b> <code>{res['invite_hash']}</code>",
            f"• <b>Format Compliance:</b> {'✅ Valid Cryptographic Format' if res['is_valid_format'] else '⚠️ Irregular Hash'}",
            f"• <b>Resolved Chat Title:</b> <b>{escape_html(res['chat_title'])}</b>",
            f"• <b>Member Status:</b> 👥 <i>{res['chat_members']}</i>",
            f"• <b>Link Status:</b> <b>{res['verdict']}</b>",
            "──────────────────────────────",
            "💡 <b>Protocol Launch:</b>",
            f"Native Protocol: <code>{res['tg_protocol']}</code>"
        ]
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✈️ Join via tg:// Protocol", url=res["tg_protocol"])],
            [InlineKeyboardButton(text="🏠 Home Dashboard", callback_data="nav_home")]
        ])
    else:
        lines = [
            "🌐 <b>[WEB LINK REDIRECTION & PHISHING AUDIT]</b>",
            "──────────────────────────────",
            f"• <b>Original Link:</b> <code>{escape_html(res['original_url'])}</code>",
            f"• <b>Final Destination:</b> <code>{escape_html(res['final_url'])}</code>",
            f"• <b>Redirect Hops:</b> <b>{res['redirect_hops']}</b>",
            f"• <b>Shortener Detected:</b> {'⚠️ Yes (Unmasked)' if res['is_shortener'] else 'No'}",
            f"• <b>Threat Level:</b> <b>{res['threat_level']}</b> ({res['verdict']})",
            "──────────────────────────────"
        ]
        if res["phishing_triggers"]:
            lines.append("🚨 <b>SUSPICIOUS PHISHING INDICATORS:</b>")
            for trig in res["phishing_triggers"]:
                lines.append(f"• <i>{trig}</i>")
            lines.append("")

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Home Dashboard", callback_data="nav_home")]
        ])

    await status_msg.edit_text("\n".join(lines), reply_markup=kb, parse_mode="HTML")


# ==============================================================================
# 4. DUPLICATE & IMPERSONATOR CLONE RADAR (/cloneradar)
# ==============================================================================
@router.message(Command("cloneradar", "impostors", "fakefinder"))
async def handle_clone_radar_command(message: Message):
    """Scans for active typosquat channels and brand impersonators."""
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply(
            "📡 <b>IMPERSONATOR & CLONE RADAR USAGE:</b>\n"
            "──────────────────────────────\n"
            "Send <code>/cloneradar &lt;@channel_or_brand&gt;</code>\n"
            "<i>Example:</i> <code>/cloneradar @telegram</code> or <code>/cloneradar binance</code>\n\n"
            "• Generates 15+ high-risk impersonation handles\n"
            "• Checks live Telegram registrations for clones\n"
            "• Identifies fake copycat communities stealing users",
            parse_mode="HTML"
        )
        return

    target = parts[1].strip()
    status_msg = await message.reply(f"📡 <i>Scanning Telegram namespace for '@{target.lstrip('@')}' clones & typosquats...</i>", parse_mode="HTML")

    res = await scan_clone_radar(target)

    lines = [
        f"📡 <b>[CLONE RADAR: '@{escape_html(res['target'])}']</b>",
        "──────────────────────────────",
        f"• <b>Scanned Permutations:</b> <code>{res['scanned_permutations']}</code> handles",
        f"• <b>Detected Clone Candidates:</b> <b>{res['clones_detected_count']}</b>",
        "──────────────────────────────"
    ]

    kb_rows = []
    if res["clones"]:
        lines.append("⚠️ <b>LIVE CHANNELS MIMICKING TARGET:</b>\n")
        for idx, cl in enumerate(res["clones"][:6], 1):
            ver = " 🔷" if cl["is_verified"] else ""
            lines.append(f"<b>{idx}. {escape_html(cl['title'])}</b>{ver}")
            lines.append(f"   • Handle: @{cl['username']} (👥 {cl['members_count']:,} members)")
            lines.append(f"   • Threat Tier: <code>{cl['risk_tier']}</code>\n")
            kb_rows.append([InlineKeyboardButton(text=f"🔍 Inspect @{cl['username']}", callback_data=f"query_chat_{cl['username']}")])
    else:
        lines.append("✅ <b>CLEAN NAMESPACE:</b> No active unauthorized clones detected.")

    kb_rows.append([InlineKeyboardButton(text="🏠 Home Dashboard", callback_data="nav_home")])

    await status_msg.edit_text("\n".join(lines), reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows), parse_mode="HTML")


# ==============================================================================
# 5. PUBLIC GROUP SECURITY AUDITOR (/groupaudit)
# ==============================================================================
@router.message(Command("groupaudit", "grouphygiene", "supergroup"))
async def handle_group_audit_command(message: Message):
    """Evaluates public group security protections and administration hygiene."""
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply(
            "🛡️ <b>GROUP ADMIN & SECURITY AUDIT USAGE:</b>\n"
            "──────────────────────────────\n"
            "Send <code>/groupaudit &lt;@group_username&gt;</code>\n"
            "<i>Example:</i> <code>/groupaudit @developers</code>\n\n"
            "• Evaluates anti-scam admin disclaimers\n"
            "• Checks captcha gating & rules presence\n"
            "• Assigns Group Security Grade (A+ to F)",
            parse_mode="HTML"
        )
        return

    target = parts[1].strip()
    status_msg = await message.reply(f"🛡️ <i>Auditing security hygiene for group @{target.lstrip('@')}...</i>", parse_mode="HTML")

    res = await audit_group_security(target)
    if not res["found"]:
        await status_msg.edit_text(f"❌ <b>Error:</b> {res.get('error', 'Group not found.')}", parse_mode="HTML")
        return

    lines = [
        f"🛡️ <b>[GROUP SECURITY AUDIT: @{res['handle']}]</b>",
        "──────────────────────────────",
        f"• <b>Community:</b> <b>{escape_html(res['title'])}</b>",
        f"• <b>Members:</b> 👥 <b>{res['members']:,}</b>",
        f"• <b>Security Score:</b> <b>{res['security_score']} / 100</b>",
        f"• <b>Hygiene Grade:</b> 🏆 <b>Grade {res['grade']}</b> ({res['verdict']})",
        "──────────────────────────────",
        "📋 <b>DEFENSIVE CHECKLIST:</b>"
    ]

    for item in res["checklist"]:
        icon = "✅" if item["status"] == "PASS" else ("⚠️" if item["status"] == "WARN" else "ℹ️")
        lines.append(f"{icon} <b>{item['item']}:</b> {item['note']}")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Open Group", url=f"https://t.me/{res['handle']}")],
        [InlineKeyboardButton(text="🏠 Home Dashboard", callback_data="nav_home")]
    ])

    await status_msg.edit_text("\n".join(lines), reply_markup=kb, parse_mode="HTML")


# ==============================================================================
# 6. SCRIPT & REGIONAL AUDIENCE CLASSIFIER (/chanlang)
# ==============================================================================
@router.message(Command("chanlang", "channellang", "langdetect"))
async def handle_channel_lang_command(message: Message):
    """Analyzes Unicode scripts to determine primary language and regional audience."""
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply(
            "🌐 <b>CHANNEL REGIONAL AUDIENCE CLASSIFIER USAGE:</b>\n"
            "──────────────────────────────\n"
            "Send <code>/chanlang &lt;@channel&gt;</code>\n"
            "<i>Example:</i> <code>/chanlang @telegram</code>\n\n"
            "• Classifies scripts (Latin, Cyrillic, Arabic, Devanagari, CJK)\n"
            "• Identifies primary demographic region",
            parse_mode="HTML"
        )
        return

    target = parts[1].strip()
    status_msg = await message.reply(f"🌐 <i>Classifying linguistic composition for @{target.lstrip('@')}...</i>", parse_mode="HTML")

    res = await analyze_channel_language(target)
    if not res["found"]:
        await status_msg.edit_text(f"❌ <b>Error:</b> {res.get('error', 'Channel not found.')}", parse_mode="HTML")
        return

    lines = [
        f"🌐 <b>[REGIONAL AUDIENCE AUDIT: @{res['handle']}]</b>",
        "──────────────────────────────",
        f"• <b>Title:</b> <b>{escape_html(res['title'])}</b>",
        f"• <b>Primary Script:</b> <b>{res['primary_script']}</b>",
        f"• <b>Audience Region:</b> 📍 <b>{res['primary_region']}</b>",
        "──────────────────────────────",
        "📊 <b>SCRIPT COMPOSITION BREAKDOWN:</b>"
    ]

    for script, pct in res["percentages"].items():
        bar_len = int(pct / 10)
        bar = "█" * bar_len + "░" * (10 - bar_len)
        lines.append(f"• <b>{script}:</b> <code>[{bar}]</code> {pct}%")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Home Dashboard", callback_data="nav_home")]
    ])

    await status_msg.edit_text("\n".join(lines), reply_markup=kb, parse_mode="HTML")


# ==============================================================================
# 7. RELATED & SIMILAR COMMUNITY RECOMMENDATIONS (/similar)
# ==============================================================================
@router.message(Command("similar", "related", "recs"))
async def handle_similar_communities_command(message: Message):
    """Recommends related authentic channels and groups."""
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply(
            "💡 <b>SIMILAR COMMUNITY RECOMMENDER USAGE:</b>\n"
            "──────────────────────────────\n"
            "Send <code>/similar &lt;@channel_or_group&gt;</code>\n"
            "<i>Example:</i> <code>/similar @telegram</code> or <code>/similar @python</code>\n\n"
            "• Matches taxonomies and topics across 1,472 communities\n"
            "• Suggests authentic related channels and groups in the same domain",
            parse_mode="HTML"
        )
        return

    target = parts[1].strip()
    status_msg = await message.reply(f"💡 <i>Finding related communities for @{target.lstrip('@')}...</i>", parse_mode="HTML")

    res = await find_similar_communities(target, limit=6)

    lines = [
        f"💡 <b>[RELATED COMMUNITIES FOR: @{escape_html(res['target'])}]</b>",
        f"<i>Category: {res['category']}</i>",
        "──────────────────────────────"
    ]

    kb_rows = []
    for idx, it in enumerate(res["recommendations"], 1):
        uname = it.get("username", "")
        title = escape_html(it.get("title", it.get("name", uname)))
        cat = it.get("category", "General")
        desc = escape_html(it.get("description", it.get("desc", ""))[:70])

        lines.append(f"<b>{idx}. {title}</b> (@{uname})")
        lines.append(f"   • Category: <code>{cat}</code>")
        if desc:
            lines.append(f"   • Info: <i>{desc}...</i>")
        lines.append("")

        kb_rows.append([InlineKeyboardButton(text=f"🔍 Inspect {title[:20]}", callback_data=f"query_chat_{uname}")])

    kb_rows.append([InlineKeyboardButton(text="🏠 Home Dashboard", callback_data="nav_home")])

    await status_msg.edit_text("\n".join(lines), reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows), parse_mode="HTML")
