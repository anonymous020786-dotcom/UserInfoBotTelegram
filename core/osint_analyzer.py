import re
from typing import Dict, Any, List


URL_REGEX = re.compile(r'https?://[^\s<>"]+|www\.[^\s<>"]+')
EMAIL_REGEX = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
MENTION_REGEX = re.compile(r'@[a-zA-Z0-9_]{3,32}')
USERNAME_REGEX = re.compile(r'^[a-zA-Z0-9_]{5,32}$')

SUSPICIOUS_KEYWORDS = [
    "guaranteed profit", "free crypto", "invest now", "double your money", 
    "binary option", "100x return", "carding", "bank logs", "whatsapp hack",
    "dm for pump", "giveaway claim", "free btc", "free eth", "airdrop claim"
]


def analyze_text_osint(text: str) -> Dict[str, Any]:
    """
    Performs comprehensive OSINT analysis on biography or chat descriptions.
    """
    if not text:
        return {
            "links": [],
            "emails": [],
            "mentions": [],
            "language_script": "None / Empty",
            "risk_score": 0,
            "risk_rating": "Clean",
            "risk_triggers": []
        }

    links = URL_REGEX.findall(text)
    emails = EMAIL_REGEX.findall(text)
    mentions = MENTION_REGEX.findall(text)

    # Detect scripts
    scripts = []
    if re.search(r'[\u0400-\u04FF]', text):
        scripts.append("Cyrillic (RU/UA/KZ)")
    if re.search(r'[\u0600-\u06FF]', text):
        scripts.append("Arabic / Perso-Arabic")
    if re.search(r'[\u0900-\u097F]', text):
        scripts.append("Devanagari (Hindi/Sanskrit)")
    if re.search(r'[\u4E00-\u9FFF\u3040-\u30FF\uAC00-\uD7AF]', text):
        scripts.append("East Asian (CJK)")
    if re.search(r'[a-zA-Z]', text):
        scripts.append("Latin (Western/Global)")

    detected_script = " / ".join(scripts) if scripts else "Symbols / Emoji Only"

    # Suspicious keywords heuristic
    lower_text = text.lower()
    matched_triggers = [kw for kw in SUSPICIOUS_KEYWORDS if kw in lower_text]
    
    risk_score = min(100, len(matched_triggers) * 35)
    if risk_score >= 70:
        risk_rating = "HIGH RISK (Scam/Phishing signals)"
    elif risk_score >= 35:
        risk_rating = "MODERATE (Commercial / Promotional)"
    else:
        risk_rating = "LOW / CLEAN"

    return {
        "links": list(set(links)),
        "emails": list(set(emails)),
        "mentions": list(set(mentions)),
        "language_script": detected_script,
        "risk_score": risk_score,
        "risk_rating": risk_rating,
        "risk_triggers": matched_triggers
    }


def validate_telegram_username(username: str) -> Dict[str, Any]:
    """
    Validates if a username matches Telegram conventions and checks if it qualifies as Fragment NFT.
    """
    clean_uname = username.lstrip("@").strip()
    is_valid = bool(USERNAME_REGEX.match(clean_uname))
    is_short = 1 <= len(clean_uname) < 5
    is_collectible_candidate = is_short or (clean_uname.isdigit() and len(clean_uname) in [8, 9, 10])

    return {
        "clean_username": clean_uname,
        "is_valid_format": is_valid or is_short,
        "length": len(clean_uname),
        "is_fragment_candidate": is_collectible_candidate,
        "fragment_url": f"https://fragment.com/username/{clean_uname}" if is_collectible_candidate or is_valid else None
    }
