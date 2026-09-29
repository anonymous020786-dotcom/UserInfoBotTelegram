"""
Sentinel Related & Similar Community Recommendation Engine.
Matches channels, groups, and bots against the 1,472-community taxonomy
to discover high-relevance authentic communities in the same vertical.
"""
from typing import Dict, Any, List
from core.directory_data import get_curated_communities
from core.telegram_discovery import fetch_real_telegram_preview


async def find_similar_communities(target_identifier: str, limit: int = 6) -> Dict[str, Any]:
    """
    Recommends related authentic channels and groups matching the target's topic or vertical.
    """
    clean_target = target_identifier.strip().lstrip("@").lower()
    preview = await fetch_real_telegram_preview(clean_target)

    # Keywords from target
    title = preview.get("title", "") if preview else clean_target
    desc = preview.get("description", "") if preview else ""
    full_text = f"{clean_target} {title} {desc}".lower()

    # Match against catalog
    catalog = get_curated_communities()
    scored: List[tuple] = []

    # Detect category from target
    matched_cat = None
    for item in catalog:
        if item.get("username", "").lower() == clean_target:
            matched_cat = item.get("category")
            break

    # Score each community in catalog
    target_words = set([w for w in full_text.replace("_", " ").split() if len(w) >= 3])

    for item in catalog:
        u = item.get("username", "").lower()
        if u == clean_target:
            continue

        score = 0
        cat = item.get("category")
        if matched_cat and cat == matched_cat:
            score += 15

        item_text = f"{item.get('title', '')} {item.get('description', '')} {u}".lower()
        for w in target_words:
            if w in item_text:
                score += 5

        if score > 0:
            scored.append((score, item))

    # Sort by relevance score descending
    scored.sort(key=lambda x: x[0], reverse=True)
    recommended = [item for _, item in scored[:limit]]

    # If no strict keyword matches found, fallback to top communities from relevant vertical
    if not recommended:
        recommended = [it for it in catalog if it.get("username", "").lower() != clean_target][:limit]

    return {
        "target": clean_target,
        "title": title,
        "category": matched_cat or "General Topic",
        "recommendations": recommended
    }
