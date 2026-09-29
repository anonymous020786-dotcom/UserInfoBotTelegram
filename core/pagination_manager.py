"""
Sentinel Search Pagination, Filtering & Advanced Sorting Engine.
Supports:
1. Multi-mode Sorting: Most Members, Fewest Members, Name A-Z, Verified First, Relevance
2. Multi-tier Filtering: Mega (>100k), Large (10k-100k), Medium (1k-10k), Starter (<1k)
3. Type Filtering: Channels (📢), Groups (👥), Bots (🤖)
4. Interactive Filter & Sorting Control Center UI
5. Search operator parsing (min:10k, verified:true, type:channel, sort:subs)
6. Instant CSV data export
"""
import uuid
import math
import time
from typing import Dict, Any, List, Optional, Tuple
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from ui.formatters import escape_html


# In-memory session store: session_id -> {results, query, entity_type, sort_by, size_tier, type_filter, verified_only, timestamp}
_SESSIONS: Dict[str, Dict[str, Any]] = {}
SESSION_TTL = 1800  # 30 minutes

SORT_LABELS = {
    "relevance": "🎯 Relevance",
    "subs_desc": "👥 Most Members",
    "subs_asc": "📉 Fewest Members",
    "name_asc": "🔤 Name (A-Z)",
    "name_desc": "🔤 Name (Z-A)",
    "verified_first": "🔷 Verified First"
}

SIZE_LABELS = {
    "all": "All Sizes",
    "mega": "👑 Mega (>100k)",
    "large": "🏢 Large (10k-100k)",
    "medium": "🌱 Medium (1k-10k)",
    "starter": "🐣 Starter (<1k)"
}


def parse_search_operators(raw_query: str) -> Tuple[str, Dict[str, Any]]:
    """
    Parses advanced search operators from user query string:
    - min:1000 or min:50k (minimum subscriber count)
    - verified:true or is:verified (only verified channels/bots)
    - type:channel or type:group or type:bot
    - sort:subs or sort:name or sort:verified
    """
    tokens = raw_query.split()
    clean_tokens = []
    filters = {
        "min_members": None,
        "verified_only": False,
        "type_filter": "all",
        "sort_by": "relevance",
        "size_tier": "all"
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
        elif lower_tok.startswith("sort:"):
            s = lower_tok[5:]
            if s in ["subs", "members", "size"]:
                filters["sort_by"] = "subs_desc"
            elif s in ["name", "alpha", "az"]:
                filters["sort_by"] = "name_asc"
            elif s in ["verified", "badge"]:
                filters["sort_by"] = "verified_first"
        else:
            clean_tokens.append(tok)

    clean_query = " ".join(clean_tokens).strip() or raw_query.strip()
    return clean_query, filters


def create_search_session(
    results: List[Dict[str, Any]],
    query: str,
    entity_type: str = "channel",
    per_page: int = 5,
    initial_filters: Optional[Dict[str, Any]] = None
) -> str:
    """Stores search results in session cache with active filters and returns unique session ID."""
    clean_expired_sessions()
    sess_id = uuid.uuid4().hex[:8]

    sort_by = "relevance"
    verified_only = False
    size_tier = "all"
    type_filter = "all"

    if initial_filters:
        sort_by = initial_filters.get("sort_by", "relevance")
        verified_only = initial_filters.get("verified_only", False)
        type_filter = initial_filters.get("type_filter", "all")
        if initial_filters.get("min_members"):
            mm = initial_filters["min_members"]
            if mm >= 100000:
                size_tier = "mega"
            elif mm >= 10000:
                size_tier = "large"
            elif mm >= 1000:
                size_tier = "medium"

    _SESSIONS[sess_id] = {
        "results": results,
        "query": query,
        "entity_type": entity_type,
        "per_page": per_page,
        "verified_only": verified_only,
        "sort_by": sort_by,
        "size_tier": size_tier,
        "type_filter": type_filter,
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


def apply_filters_and_sorting(sess: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Applies active filters and sorting rules to results."""
    items = list(sess["results"])

    # 1. Verification filter
    if sess.get("verified_only"):
        items = [r for r in items if r.get("is_verified")]

    # 2. Type filter
    t_filt = sess.get("type_filter", "all")
    if t_filt != "all":
        if t_filt == "group":
            items = [r for r in items if r.get("type") in ["group", "supergroup"]]
        elif t_filt == "channel":
            items = [r for r in items if r.get("type") in ["channel", "broadcast"]]
        elif t_filt == "bot":
            items = [r for r in items if r.get("type") in ["bot", "user"] or r.get("username", "").lower().endswith("bot")]

    # 3. Size Tier filter
    size_tier = sess.get("size_tier", "all")
    if size_tier == "mega":
        items = [r for r in items if (r.get("members_count") or 0) >= 100_000]
    elif size_tier == "large":
        items = [r for r in items if 10_000 <= (r.get("members_count") or 0) < 100_000]
    elif size_tier == "medium":
        items = [r for r in items if 1_000 <= (r.get("members_count") or 0) < 10_000]
    elif size_tier == "starter":
        items = [r for r in items if (r.get("members_count") or 0) < 1_000]

    # 4. Sorting
    sort_by = sess.get("sort_by", "relevance")
    if sort_by == "subs_desc":
        items.sort(key=lambda x: (x.get("members_count") or 0), reverse=True)
    elif sort_by == "subs_asc":
        items.sort(key=lambda x: (x.get("members_count") or 0))
    elif sort_by == "name_asc":
        items.sort(key=lambda x: x.get("title", x.get("username", "")).lower())
    elif sort_by == "name_desc":
        items.sort(key=lambda x: x.get("title", x.get("username", "")).lower(), reverse=True)
    elif sort_by == "verified_first":
        items.sort(key=lambda x: (1 if x.get("is_verified") else 0, x.get("members_count") or 0), reverse=True)

    return items


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

    items = apply_filters_and_sorting(sess)
    total_items = len(items)

    sort_label = SORT_LABELS.get(sess.get("sort_by", "relevance"), "Relevance")

    # Count active filters
    active_filters = []
    if sess.get("verified_only"):
        active_filters.append("Verified 🔷")
    if sess.get("size_tier", "all") != "all":
        active_filters.append(SIZE_LABELS.get(sess["size_tier"], sess["size_tier"]))
    if sess.get("type_filter", "all") != "all":
        active_filters.append(sess["type_filter"].title())

    filter_summary = f" • Filters: {', '.join(active_filters)}" if active_filters else ""

    if total_items == 0:
        empty_text = (
            f"❌ <b>No results found for '{escape_html(sess['query'])}'</b> with current filter settings.\n\n"
            f"• <b>Active Filter:</b> {', '.join(active_filters) if active_filters else 'None'}\n"
            f"• <b>Sort:</b> {sort_label}\n\n"
            f"<i>Tap below to reset all filters and view full candidate catalog:</i>"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Reset All Filters", callback_data=f"filter_reset:{session_id}")],
            [InlineKeyboardButton(text="⚙️ Adjust Filters", callback_data=f"open_filters:{session_id}:{page}")],
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
        f"<b>Sort:</b> <code>{sort_label}</code>{filter_summary}",
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
            snippet = escape_html(desc[:80].strip()) + ("..." if len(desc) > 80 else "")
            lines.append(f"   • Bio: <i>{snippet}</i>")
        lines.append("")

        # Action buttons
        if ent_type == "bot":
            kb_rows.append([
                InlineKeyboardButton(text=f"🤖 Open @{uname}", url=f"https://t.me/{uname}"),
                InlineKeyboardButton(text="🛡️ Safety Audit", callback_data=f"run_botsafety_{uname}")
            ])
        else:
            kb_rows.append([
                InlineKeyboardButton(text=f"🔍 Inspect @{uname}", callback_data=f"query_chat_{uname}"),
                InlineKeyboardButton(text="📈 Velocity", callback_data=f"run_velocity_{uname}")
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

    # Filter & Sort Control Bar
    filter_count_tag = f" ({len(active_filters)})" if active_filters else ""
    kb_rows.append([
        InlineKeyboardButton(text="🔄 Sort / Filter Controls" + filter_count_tag, callback_data=f"open_filters:{session_id}:{page}"),
        InlineKeyboardButton(text="📥 Export CSV", callback_data=f"export_csv_{session_id}")
    ])
    kb_rows.append([
        InlineKeyboardButton(text="🏠 Home Dashboard", callback_data="nav_home")
    ])

    return "\n".join(lines), InlineKeyboardMarkup(inline_keyboard=kb_rows)


def build_filter_controls_view(session_id: str, return_page: int = 1) -> Tuple[str, InlineKeyboardMarkup]:
    """
    Renders an interactive Control Center to toggle sorting algorithms,
    audience size brackets, entity types, and official verification badges.
    """
    sess = get_search_session(session_id)
    if not sess:
        return "⚠️ Session expired. Please search again.", InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 Home", callback_data="nav_home")]])

    cur_sort = sess.get("sort_by", "relevance")
    cur_size = sess.get("size_tier", "all")
    cur_type = sess.get("type_filter", "all")
    is_ver = sess.get("verified_only", False)

    total_candidates = len(sess["results"])
    filtered_candidates = len(apply_filters_and_sorting(sess))

    text = (
        f"⚙️ <b>[SEARCH CONTROLS: SORTING & ADVANCED FILTERS]</b>\n"
        f"Target Query: '<b>{escape_html(sess['query'])}</b>'\n"
        f"Showing: <b>{filtered_candidates}</b> of <b>{total_candidates}</b> candidates\n"
        "──────────────────────────────\n"
        f"• <b>Active Sorting:</b> <code>{SORT_LABELS.get(cur_sort, cur_sort)}</code>\n"
        f"• <b>Size Tier:</b> <code>{SIZE_LABELS.get(cur_size, cur_size)}</code>\n"
        f"• <b>Entity Type:</b> <code>{cur_type.title()}</code>\n"
        f"• <b>Verification:</b> <code>{'🔷 Verified Only' if is_ver else 'All (Verified & Unverified)'}</code>\n"
        "──────────────────────────────\n"
        "<i>Tap any control below to update in real-time:</i>"
    )

    kb = [
        # 1. Sorting Methods
        [
            InlineKeyboardButton(text="👥 Most Members" + (" ✓" if cur_sort == "subs_desc" else ""), callback_data=f"set_sort:{session_id}:subs_desc"),
            InlineKeyboardButton(text="📉 Least Members" + (" ✓" if cur_sort == "subs_asc" else ""), callback_data=f"set_sort:{session_id}:subs_asc")
        ],
        [
            InlineKeyboardButton(text="🔤 Name (A-Z)" + (" ✓" if cur_sort == "name_asc" else ""), callback_data=f"set_sort:{session_id}:name_asc"),
            InlineKeyboardButton(text="🔷 Verified First" + (" ✓" if cur_sort == "verified_first" else ""), callback_data=f"set_sort:{session_id}:verified_first")
        ],
        # 2. Audience Size Tiers
        [
            InlineKeyboardButton(text="👑 Mega >100k" + (" ✓" if cur_size == "mega" else ""), callback_data=f"set_size:{session_id}:mega"),
            InlineKeyboardButton(text="🏢 10k-100k" + (" ✓" if cur_size == "large" else ""), callback_data=f"set_size:{session_id}:large"),
            InlineKeyboardButton(text="🌱 1k-10k" + (" ✓" if cur_size == "medium" else ""), callback_data=f"set_size:{session_id}:medium")
        ],
        # 3. Type Filters & Verification Toggle
        [
            InlineKeyboardButton(text="📢 Channels" + (" ✓" if cur_type == "channel" else ""), callback_data=f"set_type:{session_id}:channel"),
            InlineKeyboardButton(text="👥 Groups" + (" ✓" if cur_type == "group" else ""), callback_data=f"set_type:{session_id}:group"),
            InlineKeyboardButton(text="🤖 Bots" + (" ✓" if cur_type == "bot" else ""), callback_data=f"set_type:{session_id}:bot")
        ],
        [
            InlineKeyboardButton(text="🔷 Only Verified" + (" [ON]" if is_ver else " [OFF]"), callback_data=f"toggle_ver_btn:{session_id}")
        ],
        # 4. Actions
        [
            InlineKeyboardButton(text="◀️ Apply & Back to Results", callback_data=f"page:{session_id}:1"),
            InlineKeyboardButton(text="🔄 Reset All Filters", callback_data=f"filter_reset:{session_id}")
        ]
    ]

    return text, InlineKeyboardMarkup(inline_keyboard=kb)


def generate_search_csv(session_id: str) -> Optional[str]:
    """Generates structured CSV content string for all results in session."""
    sess = get_search_session(session_id)
    if not sess:
        return None

    results = apply_filters_and_sorting(sess)
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
