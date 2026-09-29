"""
Sentinel Telegram Link Security & Private Invite Forensics Engine.
Inspects Telegram private invite links (t.me/+hash), resolves shortener chains (bit.ly/tinyurl),
and detects phishing redirection vectors attempting to steal credentials.
"""
import re
import urllib.parse
import aiohttp
from typing import Dict, Any, List
from bs4 import BeautifulSoup


KNOWN_SUSPICIOUS_DOMAINS = [
    "telegram-login", "telegram-security", "free-telegram-premium",
    "ton-airdrop", "fragment-claim", "wallet-telegram", "telegram-gift",
    "telegram-verification", "t-me-login", "telegram-ton"
]

SHORTENER_DOMAINS = [
    "bit.ly", "tinyurl.com", "t.co", "cutt.ly", "is.gd", "rb.gy", "shorturl.at"
]


async def audit_telegram_link(url_input: str) -> Dict[str, Any]:
    """
    Analyzes Telegram invite links or general web links to assess safety and uncover destination.
    """
    raw_url = url_input.strip()
    if not raw_url.startswith(("http://", "https://", "tg://")):
        raw_url = "https://" + raw_url

    parsed = urllib.parse.urlparse(raw_url)
    netloc = parsed.netloc.lower()
    path = parsed.path

    # Case 1: Telegram Private Invite Link (t.me/+... or t.me/joinchat/...)
    if "t.me" in netloc or "telegram.me" in netloc:
        is_invite = False
        invite_hash = None

        if path.startswith("/+"):
            is_invite = True
            invite_hash = path[2:].split("/")[0].split("?")[0]
        elif path.startswith("/joinchat/"):
            is_invite = True
            invite_hash = path.replace("/joinchat/", "").split("/")[0].split("?")[0]

        if is_invite and invite_hash:
            # Analyze invite hash structure
            is_valid_format = len(invite_hash) >= 12 and re.match(r'^[a-zA-Z0-9_-]+$', invite_hash) is not None
            
            # Probe invite preview
            chat_title = None
            chat_members = None
            chat_desc = None
            is_revoked = False

            try:
                headers = {"User-Agent": "Mozilla/5.0"}
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=4)) as session:
                    async with session.get(f"https://t.me/+{invite_hash}", headers=headers) as resp:
                        if resp.status == 200:
                            html = await resp.text()
                            soup = BeautifulSoup(html, "html.parser")
                            title_el = soup.find("div", class_="tgme_page_title")
                            if title_el:
                                chat_title = title_el.text.strip()
                            extra_el = soup.find("div", class_="tgme_page_extra")
                            if extra_el:
                                chat_members = extra_el.text.strip()
                            desc_el = soup.find("div", class_="tgme_page_description")
                            if desc_el:
                                chat_desc = desc_el.text.strip()
                        else:
                            is_revoked = True
            except Exception:
                pass

            return {
                "type": "telegram_invite",
                "original_url": raw_url,
                "invite_hash": invite_hash,
                "is_valid_format": bool(is_valid_format),
                "tg_protocol": f"tg://join?invite={invite_hash}",
                "chat_title": chat_title or "Private Group or Channel",
                "chat_members": chat_members or "Undisclosed (Private)",
                "description": chat_desc or "Join link requires approval or active membership.",
                "is_active": chat_title is not None and not is_revoked,
                "verdict": "VALID TELEGRAM INVITE" if chat_title else "PRIVATE / REVOKED INVITE",
                "threat_level": "LOW"
            }

    # Case 2: External Link / URL Shortener Redirection Audit
    hops: List[str] = [raw_url]
    current_url = raw_url
    is_shortener = any(sd in netloc for sd in SHORTENER_DOMAINS)
    phishing_triggers = []

    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        timeout = aiohttp.ClientTimeout(total=6)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            for _ in range(5):  # Follow max 5 redirects
                async with session.get(current_url, headers=headers, allow_redirects=False) as resp:
                    if resp.status in [301, 302, 303, 307, 308] and "Location" in resp.headers:
                        next_url = resp.headers["Location"]
                        if not next_url.startswith("http"):
                            next_url = urllib.parse.urljoin(current_url, next_url)
                        hops.append(next_url)
                        current_url = next_url
                    else:
                        break
    except Exception:
        pass

    final_url = hops[-1]
    final_domain = urllib.parse.urlparse(final_url).netloc.lower()

    # Check for phishing domain names
    for bad in KNOWN_SUSPICIOUS_DOMAINS:
        if bad in final_domain:
            phishing_triggers.append(f"Domain contains deceptive Telegram phishing string '{bad}'")

    if phishing_triggers:
        verdict = "🚨 CRITICAL: PHISHING SITE DETECTED"
        threat_level = "CRITICAL"
    elif is_shortener and len(hops) > 1:
        verdict = "⚠️ SHORTENED LINK UNMASKED"
        threat_level = "MEDIUM"
    else:
        verdict = "✅ CANONICAL WEB LINK"
        threat_level = "LOW"

    return {
        "type": "external_url",
        "original_url": raw_url,
        "final_url": final_url,
        "final_domain": final_domain,
        "redirect_hops": len(hops) - 1,
        "hop_trail": hops,
        "is_shortener": is_shortener,
        "phishing_triggers": phishing_triggers,
        "verdict": verdict,
        "threat_level": threat_level
    }
