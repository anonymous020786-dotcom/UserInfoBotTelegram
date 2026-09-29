"""
Sentinel Content Language & Regional Audience Classifier.
Analyzes Unicode codepoints across channel titles and descriptions to identify
script composition (Latin, Cyrillic, Arabic, Devanagari, CJK) and target geography.
"""
from typing import Dict, Any
from core.telegram_discovery import fetch_real_telegram_preview


def detect_scripts_in_text(text: str) -> Dict[str, Any]:
    """Classifies unicode characters in text into major writing script families."""
    counts = {
        "Latin": 0,
        "Cyrillic": 0,
        "Arabic": 0,
        "Devanagari": 0,
        "CJK": 0,
        "Other": 0
    }
    total_letters = 0

    for ch in text:
        code = ord(ch)
        if (65 <= code <= 90) or (97 <= code <= 122) or (0x00C0 <= code <= 0x024F):
            counts["Latin"] += 1
            total_letters += 1
        elif (0x0400 <= code <= 0x04FF) or (0x0500 <= code <= 0x052F):
            counts["Cyrillic"] += 1
            total_letters += 1
        elif (0x0600 <= code <= 0x06FF) or (0x0750 <= code <= 0x077F) or (0x08A0 <= code <= 0x08FF):
            counts["Arabic"] += 1
            total_letters += 1
        elif 0x0900 <= code <= 0x097F:
            counts["Devanagari"] += 1
            total_letters += 1
        elif (0x4E00 <= code <= 0x9FFF) or (0x3040 <= code <= 0x30FF) or (0xAC00 <= code <= 0xD7AF):
            counts["CJK"] += 1
            total_letters += 1
        elif ch.isalnum():
            counts["Other"] += 1
            total_letters += 1

    if total_letters == 0:
        return {
            "primary_script": "Latin (Default)",
            "primary_region": "Global / English",
            "percentages": {"Latin": 100.0}
        }

    percentages = {}
    for s, count in counts.items():
        if count > 0:
            percentages[s] = round((count / total_letters) * 100, 1)

    # Sort descending
    sorted_scripts = sorted(percentages.items(), key=lambda x: x[1], reverse=True)
    primary = sorted_scripts[0][0]

    region_map = {
        "Latin": "🌐 Global / North America / Europe (English)",
        "Cyrillic": "🇷🇺 Eastern Europe / CIS (Russian / Ukrainian)",
        "Arabic": "🇸🇦 Middle East / North Africa / South Asia (Arabic / Persian)",
        "Devanagari": "🇮🇳 South Asia / India (Hindi / Marathi)",
        "CJK": "🇨🇳 East Asia (Chinese / Japanese / Korean)",
        "Other": "🌐 International Multi-Script"
    }

    return {
        "primary_script": primary,
        "primary_region": region_map.get(primary, "🌐 International"),
        "percentages": dict(sorted_scripts)
    }


async def analyze_channel_language(channel_handle: str) -> Dict[str, Any]:
    """Fetches channel bio/title and performs full linguistic breakdown."""
    clean_handle = channel_handle.strip().lstrip("@")
    preview = await fetch_real_telegram_preview(clean_handle)

    if not preview:
        return {
            "found": False,
            "handle": clean_handle,
            "error": f"Could not fetch profile for @{clean_handle}."
        }

    title = preview.get("title", "")
    desc = preview.get("description", "")
    combined = f"{title} {desc}"

    analysis = detect_scripts_in_text(combined)

    return {
        "found": True,
        "handle": clean_handle,
        "title": title,
        "primary_script": analysis["primary_script"],
        "primary_region": analysis["primary_region"],
        "percentages": analysis["percentages"]
    }
