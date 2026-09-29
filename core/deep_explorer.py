"""
Sentinel Deep Search & Multi-Vector Explorer Engine.
Executes unified cross-vector reconnaissance across:
1. Channels & Supergroups
2. Telegram Utility & AI Bots
3. Fragment TON NFT Marketplace (usernames & virtual numbers)
4. Domain & Web Asset Intelligence
5. Curated Community Directory (1,472 items across 32 topics)
"""
import asyncio
from typing import Dict, Any, List

from core.telegram_discovery import search_real_telegram_entities, fetch_real_telegram_preview
from core.bot_discovery import search_real_bots
from core.fragment_scraper import scrape_fragment_username
from core.directory_data import search_directory, get_directory_stats, CURATED_COMMUNITIES
from core.cache_manager import search_cache


async def execute_deep_search(query: str, bot=None) -> Dict[str, Any]:
    """
    Executes a comprehensive, multi-vector reconnaissance search across
    all Telegram ecosystems (channels, groups, bots, Fragment NFTs, and curated topics).
    """
    clean_q = query.strip().lstrip("@")
    cache_key = f"deepsearch:{clean_q.lower()}"
    cached = await search_cache.get(cache_key)
    if cached is not None:
        return cached

    # Concurrently launch 4 deep reconnaissance vectors
    async def get_channels_groups():
        return await search_real_telegram_entities(clean_q, limit=30, bot=bot)

    async def get_bots():
        return await search_real_bots(clean_q, limit=20)

    async def get_fragment():
        if len(clean_q) >= 4 and clean_q.isalnum():
            return await scrape_fragment_username(clean_q)
        return None

    async def get_curated():
        return search_directory(clean_q)

    chans_task = asyncio.create_task(get_channels_groups())
    bots_task = asyncio.create_task(get_bots())
    frag_task = asyncio.create_task(get_fragment())
    curated_task = asyncio.create_task(get_curated())

    entities_res, bots_res, frag_res, curated_res = await asyncio.gather(
        chans_task, bots_task, frag_task, curated_task, return_exceptions=True
    )

    entities = entities_res if isinstance(entities_res, list) else []
    bots = bots_res if isinstance(bots_res, list) else []
    frag = frag_res if isinstance(frag_res, dict) else None
    curated = curated_res if isinstance(curated_res, list) else []

    # Separate channels and groups
    channels = [e for e in entities if e.get("type") in ["channel", "broadcast"]]
    groups = [e for e in entities if e.get("type") in ["group", "supergroup"]]

    # Curated split
    for it in curated:
        itype = it.get("type", "channel")
        uname = it.get("username", "").lower()
        if itype == "channel" and not any(c.get("username", "").lower() == uname for c in channels):
            channels.append({
                "title": it.get("name", it.get("title", uname)),
                "username": it["username"],
                "type": "channel",
                "members_count": None,
                "extra": f"📁 {it.get('category', 'Curated')}",
                "description": it.get("desc", ""),
                "is_verified": False
            })
        elif itype in ["group", "supergroup"] and not any(g.get("username", "").lower() == uname for g in groups):
            groups.append({
                "title": it.get("name", it.get("title", uname)),
                "username": it["username"],
                "type": "group",
                "members_count": None,
                "extra": f"📁 {it.get('category', 'Curated')}",
                "description": it.get("desc", ""),
                "is_verified": False
            })

    # Total discovered entities
    total_found = len(channels) + len(groups) + len(bots)

    result = {
        "query": clean_q,
        "total_found": total_found,
        "channels": channels,
        "groups": groups,
        "bots": bots,
        "fragment": frag,
        "curated_matches_count": len(curated)
    }

    await search_cache.set(cache_key, result, ttl=300)
    return result


def get_explorer_categories() -> List[Dict[str, Any]]:
    """Returns directory statistics and category navigation anchors."""
    stats = get_directory_stats()
    return stats
