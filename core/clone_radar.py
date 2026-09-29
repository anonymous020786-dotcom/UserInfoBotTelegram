"""
Sentinel Duplicate & Impersonator Clone Radar Engine.
Scans Telegram for lookalike channels, typosquats, and unauthorized
clones attempting to steal audience, run scams, or impersonate official brands.
"""
import asyncio
from typing import Dict, Any, List
from core.telegram_discovery import fetch_real_telegram_preview


async def scan_clone_radar(target_identifier: str) -> Dict[str, Any]:
    """
    Scans for spoofed, cloned, or typosquatted Telegram channels/groups.
    """
    clean = target_identifier.strip().lstrip("@").lower()
    base = clean.replace("_", "")

    # Permutation matrix for detecting clones & spoofed channels
    spoofs = [
        f"{clean}_official",
        f"{clean}official",
        f"official_{clean}",
        f"{clean}_channel",
        f"{clean}_news",
        f"{clean}_announcement",
        f"{clean}_alerts",
        f"{clean}_community",
        f"{clean}_group",
        f"{clean}_chat",
        f"{clean}_global",
        f"{clean}_support",
        f"{clean}_hub"
    ]

    # Add character substitution permutations if short enough
    if "o" in clean:
        spoofs.append(clean.replace("o", "0"))
    if "l" in clean:
        spoofs.append(clean.replace("l", "1"))

    # Filter duplicates and self
    candidates = list(dict.fromkeys([s for s in spoofs if s != clean and len(s) >= 4]))[:20]

    # Fetch live previews concurrently
    tasks = [fetch_real_telegram_preview(c) for c in candidates]
    previews = await asyncio.gather(*tasks, return_exceptions=True)

    detected_clones = []
    for prev in previews:
        if isinstance(prev, dict) and prev.get("title") and prev.get("username"):
            # Don't flag verified channels as malicious clones
            is_verified = prev.get("is_verified", False)
            uname = prev["username"]
            title = prev["title"]
            members = prev.get("members_count") or 0
            
            risk_tier = "CRITICAL IMPERSONATOR" if not is_verified and members > 1000 else "POTENTIAL SPOOF"
            detected_clones.append({
                "username": uname,
                "title": title,
                "members_count": members,
                "is_verified": is_verified,
                "type": prev.get("type", "channel"),
                "risk_tier": risk_tier,
                "link": f"https://t.me/{uname}"
            })

    # Sort by member count descending
    detected_clones.sort(key=lambda x: x["members_count"], reverse=True)

    return {
        "target": clean,
        "scanned_permutations": len(candidates),
        "clones_detected_count": len(detected_clones),
        "clones": detected_clones
    }
