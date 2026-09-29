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


def format_post_report(post: Dict[str, Any], channel_members: Optional[int] = None) -> str:
    """Formats forensic intelligence for a Telegram channel post."""
    author = escape_html(post.get("author_name", "Channel"))
    channel_handle = post.get("channel_handle", "")
    msg_id = post.get("message_id")
    views_str = post.get("views_str", "N/A")
    num_views = post.get("numeric_views", 0)
    pub_human = post.get("published_human", "Unknown")
    pub_iso = post.get("published_iso", "")
    media_type = post.get("media_type", "Text Only")
    text_content = escape_html(post.get("text", ""))
    words_count = post.get("words_count", 0)
    read_sec = post.get("est_read_time_sec", 1)
    osint_info = post.get("osint", {})

    verified_badge = " 🔷" if post.get("is_verified") else ""

    lines = [
        "📊 <b>[TELEGRAM POST FORENSICS & ENGAGEMENT]</b>",
        "──────────────────────────────",
        f"📢 <b>AUTHOR/CHANNEL:</b> <b>{author}</b>{verified_badge}",
        f"🏷️ <b>CHANNEL HANDLE:</b> @{channel_handle}",
        f"🔢 <b>MESSAGE ID:</b> <code>{msg_id}</code>",
        f"🔗 <b>DIRECT LINK:</b> <a href=\"{post.get('post_url')}\">View Original Post</a>",
        "──────────────────────────────",
        f"👁️ <b>TOTAL VIEWS:</b> <b>{views_str}</b>",
        f"📅 <b>PUBLISHED:</b> <code>{pub_human}</code>",
    ]
    if pub_iso:
        lines.append(f"⏱️ <b>UTC TIMESTAMP:</b> <code>{pub_iso}</code>")

    lines.extend([
        f"📁 <b>MEDIA TYPE:</b> <code>{media_type}</code>",
        f"📖 <b>READING TIME:</b> ~{read_sec} sec ({words_count} words)",
    ])

    if channel_members and channel_members > 0 and num_views > 0:
        engagement_rate = min(round((num_views / channel_members) * 100, 2), 1000.0)
        lines.append(f"📈 <b>ENGAGEMENT RATIO:</b> <b>{engagement_rate}%</b> (Views / {channel_members:,} Subs)")

    lines.extend([
        "──────────────────────────────",
        f"🛡️ <b>CONTENT AUDIT:</b> <b>{osint_info.get('risk_rating', 'CLEAN')}</b> (Threat: {osint_info.get('risk_score', 0)}/100)",
        f"🌐 <b>DETECTED SCRIPT:</b> <code>{osint_info.get('language_script', 'Latin')}</code>",
    ])

    links = osint_info.get("links", [])
    if links:
        lines.append(f"🔗 <b>LINKS DETECTED:</b> {', '.join(links[:4])}")

    mentions = osint_info.get("mentions", [])
    if mentions:
        lines.append(f"🏷️ <b>MENTIONS:</b> {', '.join(mentions[:6])}")

    if text_content:
        snippet = text_content[:280] + ("..." if len(text_content) > 280 else "")
        lines.extend([
            "──────────────────────────────",
            "📝 <b>POST CONTENT PREVIEW:</b>",
            f"<blockquote>{snippet}</blockquote>"
        ])

    return "\n".join(lines)


def format_fragment_report(data: Dict[str, Any]) -> str:
    """Formats live Fragment.com NFT marketplace audit."""
    uname = data.get("username", "")
    status = data.get("status", "Unknown")
    price_ton = data.get("price_ton")
    price_usd = data.get("price_usd_est")
    highest_bid = data.get("highest_bid")
    ends = data.get("auction_ends")
    frag_url = data.get("fragment_url", f"https://fragment.com/username/{uname}")

    lines = [
        f"💎 <b>[FRAGMENT NFT MARKETPLACE AUDIT: @{uname}]</b>",
        "──────────────────────────────",
        f"• <b>Marketplace Status:</b> <b>{status.upper()}</b>",
        f"• <b>Handle Length:</b> <code>{data.get('length', len(uname))} characters</code>",
    ]

    if price_ton:
        lines.append(f"• <b>Valuation / Price:</b> <b>{price_ton:,.0f} TON</b> (~${price_usd:,.2f} USD)")
    elif "price_ton_raw" in data:
        lines.append(f"• <b>Valuation:</b> {data['price_ton_raw']}")

    if highest_bid:
        lines.append(f"• <b>Current Bid:</b> <code>{highest_bid}</code>")

    if ends:
        lines.append(f"• <b>Auction Countdown:</b> ⏳ <code>{ends}</code>")

    lines.extend([
        "──────────────────────────────",
        f"🔗 <b>OFFICIAL LINK:</b> <a href=\"{frag_url}\">Open on Fragment.com</a>\n"
        "<i>Fragment is the official Telegram platform for trading collectible handles & numbers.</i>"
    ])
    return "\n".join(lines)


def format_comparison_report(e1: Dict[str, Any], e2: Dict[str, Any]) -> str:
    """Formats side-by-side comparison between two Telegram communities."""
    t1 = escape_html(e1.get("title", "Target 1"))
    t2 = escape_html(e2.get("title", "Target 2"))
    u1 = f"@{e1['username']}" if e1.get("username") else "N/A"
    u2 = f"@{e2['username']}" if e2.get("username") else "N/A"

    m1 = e1.get("members_count") or 0
    m2 = e2.get("members_count") or 0

    v1 = "🔷 Yes" if e1.get("is_verified") else "No"
    v2 = "🔷 Yes" if e2.get("is_verified") else "No"

    diff = abs(m1 - m2)
    leader = t1 if m1 >= m2 else t2

    lines = [
        "⚖️ <b>[COMMUNITY COMPARISON MATRIX]</b>",
        "──────────────────────────────",
        f"<b>Target A:</b> {t1} ({u1})",
        f"<b>Target B:</b> {t2} ({u2})",
        "──────────────────────────────",
        "📊 <b>MEMBERS / SUBSCRIBERS:</b>",
        f"• <b>{t1}:</b> {m1:,}",
        f"• <b>{t2}:</b> {m2:,}",
        f"• <b>Difference (Δ):</b> {diff:,} members",
        f"• <b>Leader:</b> 🏆 <b>{leader}</b>",
        "──────────────────────────────",
        "🛡️ <b>VERIFICATION & TRUST:</b>",
        f"• <b>{t1}:</b> {v1}",
        f"• <b>{t2}:</b> {v2}",
        "──────────────────────────────",
        "🌐 <b>INFRASTRUCTURE:</b>",
        f"• <b>{t1}:</b> DC{e1.get('dc_id', '?')}",
        f"• <b>{t2}:</b> DC{e2.get('dc_id', '?')}",
        "──────────────────────────────",
        f"💡 <i>Tip: Use /userinfo {u1} or /userinfo {u2} for individual full dossiers.</i>"
    ]
    return "\n".join(lines)


def format_domain_ip_report(data: Dict[str, Any]) -> str:
    """Formats DNS, IP Geolocation, ASN, and Phishing Domain audit."""
    target = escape_html(data.get("target", ""))
    ip = data.get("ip_address", "Could not resolve")
    geo = data.get("geo", {})
    score = data.get("risk_score", 0)
    level = data.get("threat_level", "UNKNOWN")
    signals = data.get("threat_signals", [])

    lines = [
        f"🌐 <b>[NETWORK & DOMAIN OSINT AUDIT: {target}]</b>",
        "──────────────────────────────",
        f"• <b>Resolved IP:</b> <code>{ip}</code>",
        f"• <b>Country / Location:</b> {geo.get('country', 'Unknown')} ({geo.get('city', 'Unknown')})",
        f"• <b>ISP Network:</b> <code>{geo.get('isp', 'Unknown')}</code>",
        f"• <b>Autonomous System (ASN):</b> <code>{geo.get('asn', 'Unknown')}</code>",
        "──────────────────────────────",
        f"🛡️ <b>THREAT LEVEL:</b> <b>{level}</b>",
        f"• <b>Phishing Score:</b> <code>{score}/100</code>",
    ]
    if signals:
        lines.append(f"⚠️ <b>Triggers:</b> {', '.join(signals)}")
    else:
        lines.append("✓ <b>Triggers:</b> No immediate phishing heuristics matched.")

    return "\n".join(lines)


def format_phone_report(data: Dict[str, Any]) -> str:
    """Formats international phone forensics & deep link routing."""
    fmt = data.get("formatted", "")
    country = data.get("country", "Unknown")
    flag = data.get("flag", "🌐")
    dial = data.get("dial_code", "")
    tz = data.get("timezone", "")
    is_nft = data.get("is_fragment_nft_number", False)

    lines = [
        "📱 <b>[PHONE NUMBER OSINT & ROUTING]</b>",
        "──────────────────────────────",
        f"• <b>Normalized (E.164):</b> <code>{fmt}</code>",
        f"• <b>Origin Country:</b> {flag} <b>{country}</b>",
        f"• <b>Dial Prefix:</b> <code>{dial}</code>",
        f"• <b>Timezone / Region:</b> <code>{tz}</code>",
    ]

    if is_nft:
        lines.extend([
            "──────────────────────────────",
            "💎 <b>ANONYMOUS NUMBER DETECTED:</b>",
            "<i>This is a decentralized Telegram Anonymous Number (+888) minted as an NFT on the TON Blockchain via Fragment.com. It is completely independent of telecom SIM cards.</i>"
        ])

    lines.extend([
        "──────────────────────────────",
        "🔗 <b>DIRECT PROTOCOL SHORTCUTS:</b>",
        f"• <b>Telegram Protocol:</b> <a href=\"{data.get('tg_protocol')}\">tg://resolve?phone=...</a>",
        f"• <b>Telegram Web Link:</b> <a href=\"{data.get('tg_web')}\">{data.get('tg_web')}</a>",
        f"• <b>WhatsApp Protocol:</b> <a href=\"{data.get('wa_link')}\">wa.me Link</a>",
        "──────────────────────────────",
        "🔒 <b>SECURITY ADVICE:</b>",
        "<i>To prevent unauthorized lookups, ensure your Telegram account privacy is set to: Settings > Privacy and Security > Phone Number > Nobody.</i>"
    ])
    return "\n".join(lines)


def format_id_forensics_report(data: Dict[str, Any]) -> str:
    """Formats 64-bit ID mathematics, architecture, and epoch breakdown."""
    raw = data.get("raw_id")
    peer = data.get("peer_type", "Unknown")
    arch = data.get("architecture", "Unknown")
    bits = data.get("bit_length", 0)
    hex_str = data.get("hex_representation", "")
    est_date = data.get("estimated_registration", "Unknown")
    rel_age = data.get("relative_age", "")
    underlying = data.get("underlying_channel_id")

    lines = [
        "🔢 <b>[64-BIT TELEGRAM ID ARCHITECTURE & FORENSICS]</b>",
        "──────────────────────────────",
        f"• <b>Decimal ID:</b> <code>{raw}</code>",
        f"• <b>Hexadecimal:</b> <code>{hex_str}</code>",
        f"• <b>Bit Depth:</b> <code>{bits} bits</code>",
        f"• <b>Peer Category:</b> <b>{peer}</b>",
        f"• <b>Telegram Architecture:</b> <code>{arch}</code>",
        "──────────────────────────────",
        f"⏳ <b>ESTIMATED EPOCH:</b> <b>{est_date}</b>",
        f"🕒 <b>ACCOUNT AGE:</b> {rel_age}",
    ]
    if underlying:
        lines.append(f"📢 <b>Underlying Channel ID:</b> <code>{underlying}</code> (stripped <code>-100</code> prefix)")

    return "\n".join(lines)

