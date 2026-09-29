import html
from typing import Dict, Any, Optional


def escape_html(text: Optional[str]) -> str:
    """Escapes HTML special characters safely."""
    if not text:
        return ""
    return html.escape(str(text))


def format_user_report(data: Dict[str, Any], theme: str = "cyberpunk") -> str:
    """Renders user OSINT report according to selected visual theme."""
    uid = data["id"]
    first_name = escape_html(data.get("first_name", ""))
    last_name = escape_html(data.get("last_name", ""))
    full_name = f"{first_name} {last_name}".strip()
    username = data.get("username")
    uname_str = f"@{username}" if username else "<i>No public username</i>"
    is_bot = data.get("is_bot", False)
    is_premium = data.get("is_premium", False)
    is_verified = data.get("is_verified", False)
    is_scam = data.get("is_scam", False)
    is_fake = data.get("is_fake", False)
    dc_info = data.get("dc_info", {})
    reg_info = data.get("reg_info", {})
    bio = escape_html(data.get("bio", ""))
    osint_analysis = data.get("osint_analysis", {})

    status_badges = []
    if is_bot:
        status_badges.append("🤖 <b>BOT</b>")
    if is_verified:
        status_badges.append("🔷 <b>VERIFIED</b>")
    if is_premium:
        status_badges.append("⭐ <b>PREMIUM</b>")
    if is_scam:
        status_badges.append("🚨 <b>SCAM ALERT</b>")
    if is_fake:
        status_badges.append("⚠️ <b>FAKE</b>")
    if not is_scam and not is_fake:
        status_badges.append("🛡️ <b>CLEAN</b>")

    badges_str = " | ".join(status_badges)

    if theme == "minimalist":
        text = [
            f"👤 <b>{full_name}</b> ({uname_str})",
            f"• <b>ID:</b> <code>{uid}</code>",
            f"• <b>Type:</b> {'Bot' if is_bot else 'User'}",
            f"• <b>Registered:</b> {reg_info.get('estimated_month', 'Unknown')} ({reg_info.get('relative_age', '')})",
            f"• <b>Data Center:</b> {dc_info.get('flag', '🌐')} {dc_info.get('name', 'DC Unknown')}",
            f"• <b>Status:</b> {badges_str}",
        ]
        if bio:
            text.append(f"• <b>Bio:</b> <i>{bio}</i>")
        return "\n".join(text)

    elif theme == "osint":
        links_str = ", ".join(osint_analysis.get("links", [])) or "None"
        emails_str = ", ".join(osint_analysis.get("emails", [])) or "None"
        mentions_str = ", ".join(osint_analysis.get("mentions", [])) or "None"

        text = [
            "🕵️ <b>SENTINEL // DEEP OSINT DOSSIER</b>",
            "═" * 32,
            f"🎯 <b>Target:</b> {full_name}",
            f"🆔 <b>Numeric ID:</b> <code>{uid}</code>",
            f"🏷️ <b>Username:</b> {uname_str}",
            f"🔗 <b>Permanent Link:</b> <a href=\"tg://user?id={uid}\">tg://user?id={uid}</a>",
            "",
            "📊 <b>INFRASTRUCTURE & LIFECYCLE</b>",
            f"• <b>Data Center:</b> {dc_info.get('flag', '🌐')} {dc_info.get('name', 'Unknown')} ({dc_info.get('location', 'Global')})",
            f"• <b>Server IP Node:</b> <code>{dc_info.get('ip', 'N/A')}</code>",
            f"• <b>Est. Registration:</b> <code>{reg_info.get('estimated_month', 'N/A')}</code>",
            f"• <b>Account Longevity:</b> {reg_info.get('relative_age', 'N/A')}",
            f"• <b>Confidence:</b> {reg_info.get('confidence', 'N/A')}",
            "",
            "🛡️ <b>SECURITY & RECON METRICS</b>",
            f"• <b>Badges:</b> {badges_str}",
            f"• <b>Script Detection:</b> <code>{osint_analysis.get('language_script', 'N/A')}</code>",
            f"• <b>Risk Rating:</b> <b>{osint_analysis.get('risk_rating', 'CLEAN')}</b> (Score: {osint_analysis.get('risk_score', 0)}/100)",
            f"• <b>Extracted Links:</b> {links_str}",
            f"• <b>Extracted Emails:</b> {emails_str}",
            f"• <b>Extracted Mentions:</b> {mentions_str}",
        ]
        if bio:
            text.extend(["", "📝 <b>BIOGRAPHY TEXT</b>", f"<blockquote>{bio}</blockquote>"])
        return "\n".join(text)

    else:
        # Default: Cyberpunk Neo
        text = [
            "⚡ <b>[SENTINEL // ENTITY DOSSIER]</b> ⚡",
            "──────────────────────────────",
            f"👤 <b>NAME:</b> <b>{full_name}</b>",
            f"🏷️ <b>HANDLE:</b> {uname_str}",
            f"🆔 <b>USER ID:</b> <code>{uid}</code>",
            f"🔰 <b>STATUS:</b> {badges_str}",
            "──────────────────────────────",
            "🛰️ <b>TELEGRAM CORE METRICS</b>",
            f"• <b>Data Center:</b> {dc_info.get('flag', '🌐')} <b>{dc_info.get('name', 'Cloud DC')}</b>",
            f"• <b>Region:</b> {dc_info.get('location', 'Global Distribution')}",
            f"• <b>Account Age:</b> <code>{reg_info.get('estimated_month', 'N/A')}</code> ({reg_info.get('relative_age', 'Unknown')})",
            f"• <b>Permanent Link:</b> <a href=\"tg://user?id={uid}\">Direct User Protocol</a>",
        ]
        if bio:
            text.extend([
                "──────────────────────────────",
                f"📝 <b>BIO:</b> <i>{bio}</i>"
            ])
        if osint_analysis.get("risk_rating") and "HIGH" in osint_analysis.get("risk_rating"):
            text.extend([
                "──────────────────────────────",
                f"⚠️ <b>THREAT ASSESSMENT:</b> <b>{osint_analysis['risk_rating']}</b>"
            ])
        return "\n".join(text)


def format_channel_report(data: Dict[str, Any], theme: str = "cyberpunk") -> str:
    """Formats channel OSINT and statistics report."""
    cid = data["id"]
    title = escape_html(data.get("title", ""))
    username = data.get("username")
    uname_str = f"@{username}" if username else "<i>Private / Invite Only</i>"
    members = data.get("members_count")
    members_str = f"<b>{members:,}</b>" if members is not None else "<i>Unavailable</i>"
    description = escape_html(data.get("description", ""))
    is_verified = data.get("is_verified", False)
    is_scam = data.get("is_scam", False)
    dc_info = data.get("dc_info", {})
    reg_info = data.get("reg_info", {})
    linked_chat_id = data.get("linked_chat_id")
    invite_link = data.get("invite_link")

    flags = []
    if is_verified:
        flags.append("🔷 <b>VERIFIED</b>")
    if is_scam:
        flags.append("🚨 <b>SCAM</b>")
    else:
        flags.append("🛡️ <b>SAFE</b>")
    flags_str = " | ".join(flags)

    text = [
        "📢 <b>[SENTINEL // BROADCAST CHANNEL]</b>",
        "──────────────────────────────",
        f"🏷️ <b>TITLE:</b> <b>{title}</b>",
        f"🆔 <b>CHANNEL ID:</b> <code>{cid}</code>",
        f"🔗 <b>PUBLIC LINK:</b> {uname_str}",
        f"👥 <b>SUBSCRIBERS:</b> {members_str}",
        f"🔰 <b>STATUS:</b> {flags_str}",
        "──────────────────────────────",
        "🛰️ <b>METRICS & INFRASTRUCTURE</b>",
        f"• <b>Creation Epoch:</b> <code>{reg_info.get('estimated_month', 'N/A')}</code> ({reg_info.get('relative_age', '')})",
        f"• <b>Data Center:</b> {dc_info.get('flag', '🌐')} <b>{dc_info.get('name', 'Cloud')}</b> ({dc_info.get('location', 'Global')})",
    ]
    if linked_chat_id:
        text.append(f"• <b>Discussion Group:</b> <code>{linked_chat_id}</code>")
    if invite_link:
        text.append(f"• <b>Invite Link:</b> <code>{invite_link}</code>")
    if description:
        text.extend([
            "──────────────────────────────",
            f"📝 <b>DESCRIPTION:</b>",
            f"<blockquote>{description}</blockquote>"
        ])

    return "\n".join(text)


def format_group_report(data: Dict[str, Any], theme: str = "cyberpunk") -> str:
    """Formats supergroup / community report."""
    gid = data["id"]
    title = escape_html(data.get("title", ""))
    username = data.get("username")
    uname_str = f"@{username}" if username else "<i>Private Group</i>"
    members = data.get("members_count")
    members_str = f"<b>{members:,}</b>" if members is not None else "<i>Hidden / Unavailable</i>"
    description = escape_html(data.get("description", ""))
    is_forum = data.get("is_forum", False)
    slowmode = data.get("slow_mode_delay", 0)
    dc_info = data.get("dc_info", {})
    reg_info = data.get("reg_info", {})

    text = [
        "👥 <b>[SENTINEL // COMMUNITY GROUP]</b>",
        "──────────────────────────────",
        f"🏷️ <b>GROUP TITLE:</b> <b>{title}</b>",
        f"🆔 <b>SUPERGROUP ID:</b> <code>{gid}</code>",
        f"🔗 <b>HANDLE:</b> {uname_str}",
        f"👥 <b>MEMBERS:</b> {members_str}",
        f"💬 <b>FORUM TOPICS:</b> {'✅ Enabled' if is_forum else '❌ Disabled'}",
        f"⏱️ <b>SLOWMODE DELAY:</b> {f'{slowmode}s' if slowmode else 'Off'}",
        "──────────────────────────────",
        "🛰️ <b>NETWORK INFRASTRUCTURE</b>",
        f"• <b>Est. Inception:</b> <code>{reg_info.get('estimated_month', 'N/A')}</code>",
        f"• <b>Data Center:</b> {dc_info.get('flag', '🌐')} <b>{dc_info.get('name', 'Cloud')}</b> ({dc_info.get('location', '')})",
    ]
    if description:
        text.extend([
            "──────────────────────────────",
            f"📝 <b>ABOUT:</b>",
            f"<blockquote>{description}</blockquote>"
        ])

    return "\n".join(text)


def format_forward_report(data: Dict[str, Any]) -> str:
    """Formats inspection report for forwarded messages."""
    origin_type = data.get("origin_type", "Unknown")
    date_str = data.get("date_str", "Unknown")
    sender_name = escape_html(data.get("sender_name", "Anonymous / Hidden"))
    sender_id = data.get("sender_id")
    sender_username = data.get("sender_username")
    uname_str = f"@{sender_username}" if sender_username else "<i>None</i>"
    chat_title = escape_html(data.get("chat_title", ""))
    chat_id = data.get("chat_id")
    msg_id = data.get("message_id")

    text = [
        "📨 <b>[FORWARD HEADER FORENSICS]</b>",
        "──────────────────────────────",
        f"📅 <b>ORIGINAL TIMESTAMP:</b> <code>{date_str}</code>",
        f"🔍 <b>ORIGIN TYPE:</b> <code>{origin_type.upper()}</code>",
    ]

    if sender_id:
        text.extend([
            f"👤 <b>ORIGINAL SENDER:</b> <b>{sender_name}</b>",
            f"🆔 <b>SENDER USER ID:</b> <code>{sender_id}</code>",
            f"🏷️ <b>SENDER USERNAME:</b> {uname_str}",
            f"🔗 <b>DIRECT PROTOCOL:</b> <a href=\"tg://user?id={sender_id}\">Open User Profile</a>",
        ])
    elif chat_id:
        text.extend([
            f"📢 <b>ORIGIN CHANNEL/CHAT:</b> <b>{chat_title}</b>",
            f"🆔 <b>ORIGIN CHAT ID:</b> <code>{chat_id}</code>",
        ])
        if msg_id:
            text.append(f"🔢 <b>ORIGINAL MESSAGE ID:</b> <code>{msg_id}</code>")
    else:
        text.extend([
            "⚠️ <b>SENDER PRIVACY ACTIVE:</b>",
            "<i>The sender has enabled 'Forwarded Messages Privacy'. Their numeric ID is hidden by Telegram, but original display name was preserved.</i>",
            f"👤 <b>DISPLAY NAME:</b> <b>{sender_name}</b>"
        ])

    return "\n".join(text)
