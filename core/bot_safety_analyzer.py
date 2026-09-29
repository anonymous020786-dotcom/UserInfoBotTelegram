"""
Sentinel Telegram Bot Safety & Phishing Vulnerability Scanner.
Audits bots for brand impersonation, seed phrase / OTP harvesting,
fake airdrop scams, token traps, and assigns an objective Security Score (0-100).
"""
import re
from typing import Dict, Any, List
from core.telegram_discovery import fetch_real_telegram_preview


PHISHING_KEYWORDS = [
    ("seed phrase", 30, "Prompts for cryptocurrency mnemonic / seed phrase"),
    ("12 words", 25, "Requests private 12-word wallet recovery words"),
    ("24 words", 25, "Requests private 24-word wallet recovery words"),
    ("private key", 30, "Solicits cryptographic private key access"),
    ("bank otp", 35, "Asks for one-time banking passwords (OTP)"),
    ("claim free ton", 20, "Suspicious high-reward giveaway / airdrop bait"),
    ("claim free usdt", 20, "Suspicious high-reward giveaway / airdrop bait"),
    ("login with phone", 25, "Attempts credential/session hijacking"),
    ("enter code from telegram", 35, "Session takeover via Telegram login code"),
    ("double your crypto", 30, "Classic doubling Ponzi/phishing scheme"),
    ("urgent: account suspended", 25, "Urgency bait impersonating Telegram security"),
    ("telegram support", 20, "Impersonates official Telegram customer service"),
]

IMPERSONATION_PATTERNS = [
    (r'(?:support|official|admin|security|verify|helpdesk)_?bot$', 25, "Uses deceptive administrative suffix in username"),
    (r'^(?:official|real|telegram)_', 20, "Uses deceptive authority prefix in username"),
    (r'(?:wallet|fragment|tonkeeper|binance|bybit)_?(?:bot|support)', 25, "Mimics popular crypto exchange or wallet services")
]


async def audit_bot_safety(bot_handle: str) -> Dict[str, Any]:
    """
    Performs forensic inspection of a Telegram bot's profile, description,
    and metadata to calculate a Bot Security Rating and Phishing Threat Score.
    """
    clean_handle = bot_handle.strip().lstrip("@")
    preview = await fetch_real_telegram_preview(clean_handle)

    if not preview:
        return {
            "found": False,
            "handle": clean_handle,
            "error": f"Could not fetch live Telegram profile for @{clean_handle}."
        }

    title = preview.get("title", "")
    desc = preview.get("description", "")
    is_verified = preview.get("is_verified", False)
    full_text = f"{title} {desc} {clean_handle}".lower()

    risk_points = 0
    triggers: List[Dict[str, str]] = []

    # 1. Phishing Keyword Detection
    for kw, weight, reason in PHISHING_KEYWORDS:
        if kw in full_text:
            risk_points += weight
            triggers.append({"type": "Phishing Keyword", "trigger": kw, "reason": reason})

    # 2. Impersonation Patterns
    for pattern, weight, reason in IMPERSONATION_PATTERNS:
        if re.search(pattern, clean_handle.lower()):
            if not is_verified:
                risk_points += weight
                triggers.append({"type": "Impersonation Risk", "trigger": clean_handle, "reason": reason})

    # 3. Official Verification Bonus
    if is_verified:
        risk_points = max(0, risk_points - 40)

    # 4. Compute Safety Score (100 is safest, 0 is most dangerous)
    safety_score = max(5, min(100, 100 - risk_points))

    # 5. Rating Tier
    if is_verified and safety_score >= 80:
        verdict = "VERIFIED SAFE"
        badge = "🛡️"
        color = "GREEN"
        recommendation = "Bot carries Telegram's official blue verification badge and shows zero phishing indicators."
    elif safety_score >= 75:
        verdict = "SAFE / CLEAN"
        badge = "✅"
        color = "GREEN"
        recommendation = "No suspicious credential harvesting or impersonation patterns identified."
    elif safety_score >= 45:
        verdict = "ELEVATED RISK / CAUTION"
        badge = "⚠️"
        color = "YELLOW"
        recommendation = "Bot uses administrative naming or high-risk keywords. Never share OTPs or recovery phrases."
    else:
        verdict = "CRITICAL / PHISHING SUSPECT"
        badge = "🚨"
        color = "RED"
        recommendation = "HIGH THREAT: Bot exhibits patterns typical of Telegram session theft or cryptocurrency drains."

    return {
        "found": True,
        "handle": clean_handle,
        "title": title,
        "is_verified": is_verified,
        "description": desc,
        "safety_score": safety_score,
        "threat_points": risk_points,
        "verdict": verdict,
        "badge": badge,
        "color": color,
        "triggers": triggers,
        "recommendation": recommendation,
        "photo_url": preview.get("photo_url")
    }
