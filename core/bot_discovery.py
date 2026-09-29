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
    Discovers real Telegram bots matching a search query:
    1. Checks MTProto search index for bots.
    2. Searches live Web index for site:t.me/*bot.
    3. Matches curated bot database.
    4. Fetches live real metadata for discovered bots.
    """
    clean_q = query.strip().lower().lstrip("@")
    discovered_handles = set()

    # 1. Match curated database
    for b in CURATED_BOTS:
        if clean_q in b["username"].lower() or clean_q in b["name"].lower() or clean_q in b["category"].lower() or clean_q in b["desc"].lower():
            discovered_handles.add(b["username"])

    # 2. MTProto contacts search
    telethon_client = await get_telethon_client()
    if telethon_client:
        try:
            from telethon.tl.functions.contacts import SearchRequest
            res = await telethon_client(SearchRequest(q=f"{clean_q} bot", limit=limit * 2))
            for u in getattr(res, "users", []):
                if getattr(u, "bot", False) and getattr(u, "username", None):
                    discovered_handles.add(u.username)
        except Exception:
            pass

    # 3. Web search query: site:t.me/*bot {clean_q}
    try:
        search_data = urllib.parse.urlencode({"q": f"site:t.me/*bot {clean_q}"})
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }
        timeout = aiohttp.ClientTimeout(total=4)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post("https://html.duckduckgo.com/html/", data=search_data, headers=headers) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    matches = re.findall(r't\.me/([a-zA-Z0-9_]{3,32}bot)', html, re.IGNORECASE)
                    for m in matches:
                        discovered_handles.add(m)
    except Exception:
        pass

    # Fetch live previews
    results = []
    tasks = [fetch_real_telegram_preview(h) for h in list(discovered_handles)[:limit * 2]]
    previews = await asyncio.gather(*tasks, return_exceptions=True)

    for p in previews:
        if isinstance(p, dict) and p.get("title"):
            results.append(p)

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
