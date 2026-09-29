import re
import urllib.parse
import asyncio
import aiohttp
import random
from typing import List, Dict, Any, Optional

from core.telethon_engine import get_telethon_client
from core.telegram_discovery import fetch_real_telegram_preview

CURATED_BOTS = [
    # AI & Assistants
    {"username": "ChatGPT_Telegram_Bot", "name": "ChatGPT AI Assistant", "category": "AI & Language", "desc": "Conversational AI and reasoning bot powered by LLMs."},
    {"username": "midjourney_free_bot", "name": "Midjourney Image Generator", "category": "AI & Creative", "desc": "Generates AI artwork and prompts in chat."},
    {"username": "ClaudeAiTelegramBot", "name": "Claude AI Companion", "category": "AI & Language", "desc": "Anthropic Claude reasoning and code assistant."},
    
    # Utilities & Downloaders
    {"username": "vkmusic_bot", "name": "VK Music Bot", "category": "Media & Audio", "desc": "Global music search and audio downloader."},
    {"username": "SpotifySaveBot", "name": "Spotify Downloader Bot", "category": "Media & Audio", "desc": "Downloads tracks, albums, and playlists from Spotify."},
    {"username": "SaveAsBot", "name": "Instagram & TikTok Saver", "category": "Downloader", "desc": "Downloads reels, stories, and videos from social platforms."},
    {"username": "uploadbot", "name": "URL File Uploader", "category": "Utility", "desc": "Uploads web files directly to Telegram cloud storage."},
    {"username": "GmailBot", "name": "Official Gmail Bot", "category": "Productivity", "desc": "Receive and reply to Gmail emails directly inside Telegram."},
    
    # OSINT & Security
    {"username": "DrWebBot", "name": "Dr.Web Antivirus Scanner", "category": "Security", "desc": "Scans files and links for malware, trojans, and virus threats."},
    {"username": "VirusTotalBot", "name": "VirusTotal Community Bot", "category": "Security", "desc": "Audits URLs and hashes against 70+ antivirus engines."},
    {"username": "TGStat_Bot", "name": "TGStat Channel Analytics", "category": "Analytics", "desc": "Channel analytics, reach, views, and subscriber dynamics."},
    {"username": "Combot", "name": "Combot Community Manager", "category": "Group Moderation", "desc": "Group moderation, analytics, anti-spam, and XP system."},
    {"username": "MissRose_bot", "name": "Rose Moderation Bot", "category": "Group Moderation", "desc": "The most widely used group management and filter bot."},
    
    # Developer & Crypto
    {"username": "GithubBot", "name": "Official GitHub Bot", "category": "Developer Tools", "desc": "Subscribes to repository commits, issues, and pull requests."},
    {"username": "wallet", "name": "Telegram Wallet", "category": "Crypto & Finance", "desc": "Official TON and USDT crypto wallet inside Telegram."},
    {"username": "CryptoBot", "name": "Crypto Bot Exchange", "category": "Crypto & Finance", "desc": "P2P crypto exchange, invoices, and payment gateway."},
    {"username": "BotFather", "name": "BotFather (Official)", "category": "Core / Official", "desc": "The official Telegram bot to create and manage all Telegram bots."}
]

BOT_CATEGORIES = {
    "ai": {"name": "AI & Machine Learning", "emoji": "🧠"},
    "media": {"name": "Media & Downloaders", "emoji": "📥"},
    "moderation": {"name": "Group & Moderation", "emoji": "🛡️"},
    "security": {"name": "Security & Antivirus", "emoji": "🔒"},
    "crypto": {"name": "Crypto & Payments", "emoji": "💰"},
    "developer": {"name": "Developer & Productivity", "emoji": "💻"}
}


async def search_real_bots(query: str, limit: int = 8) -> List[Dict[str, Any]]:
    """
    Discovers real, functional Telegram bots matching any search query:
    1. Searches massive local catalog (276 curated bots).
    2. Probes high-probability bot handle permutations directly on Telegram.
    3. Queries live Telegram public indexes (Lyzem Telegram Engine).
    4. Fetches 100% real live metadata and subscriber counts directly from Telegram.
    """
    clean_q = query.strip().lower().lstrip("@")
    base = clean_q.rstrip("bot").rstrip("_")
    if not base:
        base = clean_q

    discovered_handles = set()

    # 1. Search massive curated catalog
    from core.directory_data import get_curated_communities
    all_comms = get_curated_communities()
    for item in all_comms:
        if item.get("type") == "bot":
            uname = item.get("username", "").lower()
            title = item.get("title", "").lower()
            desc = item.get("description", "").lower()
            if base in uname or base in title or base in desc or clean_q in uname or clean_q in title:
                discovered_handles.add(item["username"])

    # Match static CURATED_BOTS list
    for b in CURATED_BOTS:
        if base in b["username"].lower() or base in b["name"].lower() or base in b["category"].lower() or base in b["desc"].lower():
            discovered_handles.add(b["username"])

    # 2. Smart Bot Permutations (Direct Telegram Probing)
    perm_candidates = [
        f"{base}bot",
        f"{base}_bot",
        f"{base}s_bot",
        f"{base}_official_bot",
        f"official_{base}_bot",
        f"{base}_the_bot",
        f"{base}_z_bot",
        f"{base}_org_bot",
        f"{base}_downloader_bot",
        f"{base}_search_bot",
        f"{base}_video_bot",
        f"{base}_chat_bot",
        f"{base}_ai_bot",
        f"{base}ai_bot",
        f"{base}_channel_bot",
        f"{base}_link_bot",
        f"{base}_app_bot"
    ]
    if clean_q.endswith("bot") or len(clean_q) >= 4:
        perm_candidates.insert(0, clean_q)

    for p in perm_candidates:
        if len(p) >= 4:
            discovered_handles.add(p)

    # 3. Live Public Telegram Index Search (Lyzem Engine)
    try:
        lyzem_url = f"https://lyzem.com/search?q={urllib.parse.quote(clean_q)}+bot"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"}
        timeout = aiohttp.ClientTimeout(total=4)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(lyzem_url, headers=headers) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    matches = re.findall(r't\.me/([a-zA-Z0-9_]{3,32})', html, re.IGNORECASE)
                    for m in matches:
                        m_lower = m.lower()
                        if m_lower.endswith("bot") and "lyzem" not in m_lower:
                            discovered_handles.add(m)
    except Exception:
        pass

    # 4. Concurrently fetch real, live Telegram previews
    candidate_list = list(discovered_handles)[:30]
    tasks = [fetch_real_telegram_preview(h) for h in candidate_list]
    previews = await asyncio.gather(*tasks, return_exceptions=True)

    results = []
    seen_unames = set()
    for p in previews:
        if isinstance(p, dict) and p.get("title") and p.get("username"):
            uname_l = p["username"].lower()
            if uname_l in seen_unames:
                continue
            # Ensure it is a bot (ends in 'bot' or official verified bot)
            if uname_l.endswith("bot") or uname_l in ["wallet", "botfather"] or p.get("type") in ["bot", "user"]:
                # Relevant check
                if base in uname_l or base in p["title"].lower() or clean_q in uname_l or clean_q in p["title"].lower():
                    seen_unames.add(uname_l)
                    results.append(p)

    # If no strict keyword matches, fallback to all valid discovered bots
    if not results:
        for p in previews:
            if isinstance(p, dict) and p.get("title") and p.get("username"):
                uname_l = p["username"].lower()
                if uname_l not in seen_unames and (uname_l.endswith("bot") or uname_l in ["wallet", "botfather"]):
                    seen_unames.add(uname_l)
                    results.append(p)

    # Sort results: exact keyword matches first, then verified, then title length
    def bot_sort(x):
        u = x.get("username", "").lower()
        exact = 2 if u == clean_q or u == f"{base}bot" or u == f"{base}_bot" else 1
        ver = 1 if x.get("is_verified") else 0
        return (exact, ver)

    results.sort(key=bot_sort, reverse=True)
    return results[:limit]


async def detect_bot_clones(brand_name: str) -> List[Dict[str, Any]]:
    """
    Generates common phishing, clone, and typo-squatting bot permutations
    for a brand/project and checks if active bots exist on Telegram.
    """
    clean = re.sub(r'[^a-zA-Z0-9_]', '', brand_name.strip().lower().rstrip("bot"))
    permutations = [
        f"{clean}_bot",
        f"{clean}bot",
        f"{clean}_official_bot",
        f"official_{clean}_bot",
        f"{clean}_support_bot",
        f"{clean}_help_bot",
        f"real_{clean}_bot",
        f"{clean}_airdrop_bot",
        f"{clean}_claim_bot"
    ]

    tasks = [fetch_real_telegram_preview(p) for p in permutations]
    previews = await asyncio.gather(*tasks, return_exceptions=True)

    found = []
    for p in previews:
        if isinstance(p, dict) and p.get("title"):
            # Tag with clone analysis
            p["is_verified"] = p.get("is_verified", False)
            found.append(p)

    return found


def get_random_bot() -> Dict[str, Any]:
    """Returns a random high-quality bot from the curated catalog."""
    return random.choice(CURATED_BOTS)
