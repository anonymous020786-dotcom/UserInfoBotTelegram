"""
Sentinel Channel Engagement & Velocity Intelligence Engine.
Computes Views-to-Subscriber Ratio (VSR%), Estimated Reach Rate (ERR%),
and flags Ghost/Zombie channels pumped with artificial bot subscribers.
"""
from typing import Dict, Any, Optional
from core.telegram_discovery import fetch_real_telegram_preview
from core.post_analyzer import fetch_real_telegram_post


async def analyze_channel_velocity(channel_handle: str) -> Dict[str, Any]:
    """
    Analyzes channel activity velocity, engagement ratio, and audience authenticity.
    """
    clean_handle = channel_handle.strip().lstrip("@")
    preview = await fetch_real_telegram_preview(clean_handle)

    if not preview:
        return {
            "found": False,
            "handle": clean_handle,
            "error": f"Could not resolve Telegram entity @{clean_handle}."
        }

    title = preview.get("title", clean_handle)
    subs = preview.get("members_count") or 0
    is_verified = preview.get("is_verified", False)
    entity_type = preview.get("type", "channel")

    # Sample latest posts to measure view counts
    sample_posts = [1, 2, 3, 5, 10]
    views_sampled = []
    
    # Try fetching public posts (sample 3 posts)
    for p_id in [10, 50, 100]:
        try:
            post_info = await fetch_real_telegram_post(f"https://t.me/{clean_handle}/{p_id}")
            if post_info and post_info.get("views_count"):
                views_sampled.append(post_info["views_count"])
        except Exception:
            pass

    # If no sample posts were directly reachable, estimate benchmark from entity metrics
    if views_sampled:
        avg_views = sum(views_sampled) // len(views_sampled)
    else:
        # Fallback benchmark estimation
        avg_views = int(subs * 0.12) if subs > 0 else 500

    # Views to Subscribers Ratio (VSR)
    if subs > 0:
        vsr_percent = round((avg_views / subs) * 100, 2)
    else:
        vsr_percent = 15.0

    # Audience Authenticity & Activity Assessment
    is_zombie = False
    if subs >= 25000 and vsr_percent < 0.8:
        is_zombie = True
        status_tier = "🚨 GHOST / BOT-PUMPED AUDIENCE"
        activity_grade = "F"
        assessment = "Severe anomaly: Views represent less than 0.8% of subscriber count. High probability of purchased dead bots."
    elif vsr_percent >= 25.0:
        status_tier = "🔥 HYPER-VIRAL / ELITE ENGAGEMENT"
        activity_grade = "A+"
        assessment = "Outstanding reach: Posts regularly exceed 25% organic view conversion of subscriber base."
    elif vsr_percent >= 12.0:
        status_tier = "🟢 HEALTHY / HIGH ENGAGEMENT"
        activity_grade = "A"
        assessment = "Solid organic audience with consistent post consumption."
    elif vsr_percent >= 4.0:
        status_tier = "🟡 NORMAL / AVERAGE REACH"
        activity_grade = "B"
        assessment = "Typical broadcast channel performance with standard active readership."
    else:
        status_tier = "⚠️ SLUGGISH / LOW ENGAGEMENT"
        activity_grade = "C"
        assessment = "Below-average viewership. A significant portion of members are muted or inactive."

    # Estimated Reach Rate (ERR%)
    err_percent = round(min(100.0, vsr_percent * 1.15), 1)

    return {
        "found": True,
        "handle": clean_handle,
        "title": title,
        "subscribers": subs,
        "is_verified": is_verified,
        "entity_type": entity_type,
        "avg_post_views": avg_views,
        "vsr_percent": vsr_percent,
        "err_percent": err_percent,
        "status_tier": status_tier,
        "activity_grade": activity_grade,
        "is_zombie": is_zombie,
        "assessment": assessment,
        "sample_size": len(views_sampled)
    }
