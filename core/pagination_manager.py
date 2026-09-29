"""
Sentinel Search Pagination & Session Manager.
Manages deep search result sets, pagination navigation keyboards,
search operator filtering (min:, verified:, type:), and CSV exports.
"""
import uuid
import math
import time
from typing import Dict, Any, List, Optional, Tuple
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from ui.formatters import escape_html


# In-memory session store: session_id -> {results, query, entity_type, timestamp, verified_only}
_SESSIONS: Dict[str, Dict[str, Any]] = {}
SESSION_TTL = 1800  # 30 minutes


def parse_search_operators(raw_query: str) -> Tuple[str, Dict[str, Any]]:
    """
    Parses advanced search operators from user query string:
    - min:1000 or min:50k (minimum subscriber count)
    - verified:true or is:verified (only verified channels/bots)
    - type:channel or type:group or type:bot
    """
    tokens = raw_query.split()
    clean_tokens = []
    filters = {
        "min_members": None,
        "verified_only": False,
        "type_filter": None
    }

    for tok in tokens:
        lower_tok = tok.lower()
        if lower_tok.startswith("min:"):
            val_str = lower_tok[4:]
            try:
                if val_str.endswith("k"):
                    filters["min_members"] = int(float(val_str[:-1]) * 1000)
                elif val_str.endswith("m"):
                    filters["min_members"] = int(float(val_str[:-1]) * 1_000_000)
                else:
                    filters["min_members"] = int(val_str)
            except Exception:
                pass
        elif lower_tok in ["verified:true", "is:verified", "badge:verified"]:
            filters["verified_only"] = True
        elif lower_tok.startswith("type:"):
            t = lower_tok[5:]
            if t in ["channel", "group", "bot"]:
                filters["type_filter"] = t
        else:
            clean_tokens.append(tok)

    clean_query = " ".join(clean_tokens).strip() or raw_query.strip()
    return clean_query, filters


def create_search_session(
    results: List[Dict[str, Any]],
    query: str,
    entity_type: str = "channel",
    per_page: int = 5
) -> str:
    """Stores search results in session cache and returns unique 8-character session ID."""
    clean_expired_sessions()
    sess_id = uuid.uuid4().hex[:8]
    _SESSIONS[sess_id] = {
        "results": results,
        "query": query,
        "entity_type": entity_type,
        "per_page": per_page,
        "verified_only": False,
        "created_at": time.time()
    }
    return sess_id


def get_search_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves session if present and valid."""
    sess = _SESSIONS.get(session_id)
    if not sess:
        return None
    if time.time() - sess["created_at"] > SESSION_TTL:
        del _SESSIONS[session_id]
        return None
    return sess


def clean_expired_sessions():
    """Removes sessions older than TTL."""
    now = time.time()
    expired = [k for k, v in _SESSIONS.items() if now - v["created_at"] > SESSION_TTL]
    for k in expired:
        del _SESSIONS[k]


def build_paginated_view(
    session_id: str,
    page: int = 1
) -> Tuple[Optional[str], Optional[InlineKeyboardMarkup]]:
    """
    Renders the HTML text and inline navigation keyboard for the specified page.
    Returns (None, None) if session expired.
    """
    sess = get_search_session(session_id)
    if not sess:
        return None, None

    all_results = sess["results"]
    if sess.get("verified_only"):
        items = [r for r in all_results if r.get("is_verified")]
    else:
        items = all_results

    total_items = len(items)
    if total_items == 0:
        empty_text = (
            f"❌ <b>No results found for '{escape_html(sess['query'])}'</b> with active filters.\n\n"
            f"<i>Tap below to disable filters or search with another term.</i>"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Reset Filter (Show All)", callback_data=f"page_reset:{session_id}")],
            [InlineKeyboardButton(text="🏠 Home Menu", callback_data="nav_home")]
        ])
        return empty_text, kb

    per_page = sess["per_page"]
    total_pages = max(1, math.ceil(total_items / per_page))
    page = max(1, min(page, total_pages))

    start_idx = (page - 1) * per_page
    end_idx = min(start_idx + per_page, total_items)
    page_items = items[start_idx:end_idx]

    ent_type = sess["entity_type"]
    emoji_map = {
        "channel": "📢",
        "group": "👥",
        "bot": "🤖",
        "global": "🌐"
    }
    emoji = emoji_map.get(ent_type, "🔍")

    title_type = ent_type.upper() + "S" if not ent_type.endswith("s") else ent_type.upper()
    lines = [
        f"{emoji} <b>[{title_type} DISCOVERED: '{escape_html(sess['query'])}']</b>",
        f"<i>Page {page} of {total_pages} • Total: {total_items} candidates</i>",
        "──────────────────────────────"
    ]

    kb_rows = []

    for idx, it in enumerate(page_items, start=start_idx + 1):
        uname = it.get("username", "")
        title = escape_html(it.get("title", uname))
        extra = it.get("extra", "")
        desc = it.get("description", "")
        verified = " 🔷" if it.get("is_verified") else ""

        members_cnt = it.get("members_count")
        if members_cnt:
            members_label = f"👥 {members_cnt:,} subscribers/members"
        elif extra:
            members_label = extra
        else:
            members_label = "🌐 Public Telegram Entity"

        lines.append(f"<b>{idx}. {title}</b>{verified}")
        lines.append(f"   • Handle: @{uname}")
        lines.append(f"   • Metrics: <i>{members_label}</i>")
        if desc:
            snippet = escape_html(desc[:90].strip()) + ("..." if len(desc) > 90 else "")
            lines.append(f"   • Bio: <i>{snippet}</i>")
        lines.append("")

        # Action button row for this item
        if ent_type == "bot":
            kb_rows.append([
                InlineKeyboardButton(text=f"🤖 Open @{uname}", url=f"https://t.me/{uname}"),
                InlineKeyboardButton(text="🛡️ Safety Audit", callback_data=f"run_botsafety_{uname}")
            ])
        else:
            kb_rows.append([
                InlineKeyboardButton(text=f"🔍 Inspect @{uname}", callback_data=f"query_chat_{uname}"),
                InlineKeyboardButton(text="📈 Analytics", callback_data=f"run_velocity_{uname}")
            ])

    # Navigation Row: [◀️ Prev] [Page X/Y] [Next ▶️]
    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton(text="◀️ Prev", callback_data=f"page:{session_id}:{page-1}"))
    else:
        nav_row.append(InlineKeyboardButton(text="•", callback_data="noop"))

    nav_row.append(InlineKeyboardButton(text=f"📄 {page} / {total_pages}", callback_data="noop"))

    if page < total_pages:
        nav_row.append(InlineKeyboardButton(text="Next ▶️", callback_data=f"page:{session_id}:{page+1}"))
    else:
        nav_row.append(InlineKeyboardButton(text="•", callback_data="noop"))

    kb_rows.append(nav_row)

    # First / Last Jump Row if more than 2 pages
    if total_pages > 2:
        jump_row = []
        if page > 2:
            jump_row.append(InlineKeyboardButton(text="⏮️ First Page", callback_data=f"page:{session_id}:1"))
        if page < total_pages - 1:
            jump_row.append(InlineKeyboardButton(text="⏭️ Last Page", callback_data=f"page:{session_id}:{total_pages}"))
        if jump_row:
            kb_rows.append(jump_row)

    # Utility Action Row: Export CSV, Toggle Verified Filter, Home
    ver_text = "🔷 All Results" if sess.get("verified_only") else "🔷 Verified Only"
    kb_rows.append([
        InlineKeyboardButton(text="📥 Export CSV", callback_data=f"export_csv_{session_id}"),
        InlineKeyboardButton(text=ver_text, callback_data=f"toggle_ver_{session_id}:{page}")
    ])
    kb_rows.append([
        InlineKeyboardButton(text="🏠 Home Dashboard", callback_data="nav_home")
    ])

    return "\n".join(lines), InlineKeyboardMarkup(inline_keyboard=kb_rows)


def generate_search_csv(session_id: str) -> Optional[str]:
    """Generates structured CSV content string for all results in session."""
    sess = get_search_session(session_id)
    if not sess:
        return None

    results = sess["results"]
    lines = ["Index,Title,Username,Type,Members,Verified,Telegram_Link,Description"]
    for idx, r in enumerate(results, 1):
        title = r.get("title", "").replace('"', '""')
        uname = r.get("username", "")
        ent_type = r.get("type", "unknown")
        members = r.get("members_count") or ""
        ver = "Yes" if r.get("is_verified") else "No"
        link = f"https://t.me/{uname}"
        desc = r.get("description", "").replace("\n", " ").replace('"', '""')
        lines.append(f'{idx},"{title}","@{uname}",{ent_type},{members},{ver},{link},"{desc}"')

    return "\n".join(lines)
