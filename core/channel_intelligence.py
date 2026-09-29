from typing import Dict, Any, List, Optional

COUNTRY_COMMUNITIES = {
    "us": {"country": "United States", "flag": "🇺🇸", "channels": ["nytimes", "washingtonpost", "cnn", "techcrunch", "theverge"]},
    "uk": {"country": "United Kingdom", "flag": "🇬🇧", "channels": ["bbcnews", "guardian", "reuters", "thetimes"]},
    "in": {"country": "India", "flag": "🇮🇳", "channels": ["ndtv", "indiatoday", "timesofindia", "thehindu", "isro"]},
    "de": {"country": "Germany", "flag": "🇩🇪", "channels": ["tagesschau", "spiegel", "zeit", "heise"]},
    "es": {"country": "Spain", "flag": "🇪🇸", "channels": ["elpais", "elmundo", "marca"]},
    "fr": {"country": "France", "flag": "🇫🇷", "channels": ["lemonde", "lefigaro", "france24"]},
    "br": {"country": "Brazil", "flag": "🇧🇷", "channels": ["g1", "folha", "estadao"]},
    "ae": {"country": "United Arab Emirates", "flag": "🇦🇪", "channels": ["gulfnews", "khaleejtimes", "thenationalnews"]}
}


def calculate_channel_health_score(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes a comprehensive 100-point Channel Health & Quality Score:
    Evaluates audience size, description density, verification, safety flags, and media.
    """
    score = 0
    breakdown = []

    # 1. Safety flags check (instant penalty)
    if data.get("is_scam") or data.get("is_fake"):
        score -= 50
        breakdown.append("🚨 Flagged by Telegram as Scam/Fake (-50 pts)")
    else:
        score += 20
        breakdown.append("✓ Clean safety record & No fraud warnings (+20 pts)")

    # 2. Official verified status
    if data.get("is_verified"):
        score += 25
        breakdown.append("🔷 Official Telegram Verified Checkmark (+25 pts)")

    # 3. Audience Size
    members = data.get("members_count") or 0
    if members >= 1_000_000:
        score += 25
        breakdown.append(f"📈 Mega-scale audience ({members:,} members) (+25 pts)")
    elif members >= 100_000:
        score += 20
        breakdown.append(f"📈 Large established audience ({members:,} members) (+20 pts)")
    elif members >= 10_000:
        score += 15
        breakdown.append(f"📈 Moderate audience ({members:,} members) (+15 pts)")
    elif members >= 1_000:
        score += 10
        breakdown.append(f"📈 Growing audience ({members:,} members) (+10 pts)")
    elif members > 0:
        score += 5
        breakdown.append(f"📈 Early-stage audience ({members:,} members) (+5 pts)")

    # 4. Profile & Metadata Quality
    if data.get("username"):
        score += 10
        breakdown.append(f"🏷️ Public handle @{data['username']} configured (+10 pts)")

    desc = data.get("description") or data.get("bio") or ""
    if len(desc) >= 50:
        score += 10
        breakdown.append("📝 Comprehensive public description (+10 pts)")
    elif len(desc) > 0:
        score += 5
        breakdown.append("📝 Basic description present (+5 pts)")
    else:
        breakdown.append("⚠️ Missing channel description (0 pts)")

    if data.get("photo_url") or data.get("has_photo"):
        score += 10
        breakdown.append("🖼️ Custom branded avatar configured (+10 pts)")

    final_score = max(0, min(100, score))

    if final_score >= 85:
        grade = "A+ (Elite Quality & Trust)"
    elif final_score >= 70:
        grade = "A (High Quality Channel)"
    elif final_score >= 50:
        grade = "B (Standard Community)"
    elif final_score >= 30:
        grade = "C (Low Activity / Unverified)"
    else:
        grade = "F (High Risk / Suspicious)"

    return {
        "score": final_score,
        "grade": grade,
        "breakdown": breakdown
    }


def get_country_channels(country_code: str) -> Optional[Dict[str, Any]]:
    """Retrieves national channel recommendations for a country code."""
    code = country_code.strip().lower()
    return COUNTRY_COMMUNITIES.get(code)
