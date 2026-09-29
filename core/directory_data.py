import json
import random
from pathlib import Path
from typing import List, Dict, Any, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
CATALOG_PATH = BASE_DIR / "data" / "curated_catalog.json"

# Default fallback categories
DIRECTORY_CATEGORIES = {
    'ai_ml': {'name': 'AI & Machine Learning', 'emoji': '🤖'},
    'python_dev': {'name': 'Python Programming & Data', 'emoji': '🐍'},
    'javascript_web': {'name': 'JavaScript, TypeScript & Web', 'emoji': '🌐'},
    'systems_dev': {'name': 'C++, Rust, Go & Systems', 'emoji': '⚙️'},
    'devops_cloud': {'name': 'DevOps, Cloud & Linux', 'emoji': '☁️'},
    'mobile_dev': {'name': 'Mobile Dev: Android & iOS', 'emoji': '📱'},
    'cybersecurity': {'name': 'Cybersecurity & Exploits', 'emoji': '🛡️'},
    'osint_privacy': {'name': 'OSINT, Privacy & OpSec', 'emoji': '🕵️'},
    'crypto_bitcoin': {'name': 'Bitcoin & Web3 Assets', 'emoji': '⚡'},
    'defi_trading': {'name': 'DeFi, Trading & Analytics', 'emoji': '📈'},
    'global_news': {'name': 'Global News & Media', 'emoji': '🌍'},
    'business_finance': {'name': 'Markets, Economy & Stocks', 'emoji': '💼'},
    'science_space': {'name': 'Science & Space Exploration', 'emoji': '🚀'},
    'education_books': {'name': 'E-Books, Academic & History', 'emoji': '📚'},
    'design_uiux': {'name': 'UI/UX Design & 3D Art', 'emoji': '🎨'},
    'gaming_esports': {'name': 'Gaming, Steam & Consoles', 'emoji': '🎮'},
    'movies_series': {'name': 'Movies & Television Shows', 'emoji': '🎬'},
    'anime_manga': {'name': 'Anime & Manga Community', 'emoji': '⛩️'},
    'music_podcasts': {'name': 'Music, Audio & Playlists', 'emoji': '🎵'},
    'jobs_freelance': {'name': 'Tech Jobs & Remote Careers', 'emoji': '💼'},
    'hardware_gadgets': {'name': 'Hardware & PC Building', 'emoji': '💻'},
    'bots_ai': {'name': 'Top AI & LLM Bots', 'emoji': '🧠'},
    'bots_media': {'name': 'Media & Downloader Bots', 'emoji': '📥'},
    'bots_utility': {'name': 'Productivity Utility Bots', 'emoji': '🛠️'},
    'bots_moderation': {'name': 'Group Moderation Bots', 'emoji': '👮'},
    'bots_crypto': {'name': 'Crypto Wallet & P2P Bots', 'emoji': '💰'},
    'bots_security': {'name': 'Antivirus & Security Bots', 'emoji': '🔒'},
    'telegram_official': {'name': 'Official Telegram Channels', 'emoji': '✈️'},
    'regional_us': {'name': 'United States Communities', 'emoji': '🇺🇸'},
    'regional_in': {'name': 'India Tech & News', 'emoji': '🇮🇳'},
    'regional_eu': {'name': 'Europe & UK Communities', 'emoji': '🇪🇺'},
    'regional_latam': {'name': 'Latin America & Spanish', 'emoji': '🌎'}
}

# In-memory cached catalog
_LOADED_CATALOG: Optional[Dict[str, Any]] = None


def get_full_catalog() -> Dict[str, Any]:
    """Loads and caches the massive 1,400+ curated catalog."""
    global _LOADED_CATALOG
    if _LOADED_CATALOG is not None:
        return _LOADED_CATALOG

    if CATALOG_PATH.exists():
        try:
            with open(CATALOG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                _LOADED_CATALOG = data
                return _LOADED_CATALOG
        except Exception:
            pass

    # Basic fallback if catalog file is missing
    _LOADED_CATALOG = {
        "categories": DIRECTORY_CATEGORIES,
        "communities": [
            {"username": "telegram", "title": "Telegram News", "category": "telegram_official", "type": "channel", "members": "11,500,000+", "description": "Official updates from Telegram."},
            {"username": "Python", "title": "Python Hub", "category": "python_dev", "type": "group", "members": "310,000+", "description": "Global Python development forum."},
            {"username": "TechCrunch", "title": "TechCrunch", "category": "global_news", "type": "channel", "members": "180,000+", "description": "Technology startup journalism."}
        ]
    }
    return _LOADED_CATALOG


def get_curated_communities() -> List[Dict[str, Any]]:
    """Returns the complete list of 1,400+ communities and bots."""
    return get_full_catalog().get("communities", [])


# Alias for backward compatibility
CURATED_COMMUNITIES = get_curated_communities()


def search_directory(query: str, category: Optional[str] = None, entity_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Searches across the massive catalog of 1,400+ curated channels, groups, and bots:
    Supports filtering by keyword, category, and entity type (channel, group, bot).
    """
    q = query.lower().strip().lstrip("@")
    communities = get_curated_communities()
    results = []

    for item in communities:
        if category and item.get("category") != category:
            continue
        if entity_type and item.get("type") != entity_type:
            continue
        if not q or q in item.get("username", "").lower() or q in item.get("title", "").lower() or q in item.get("description", "").lower():
            results.append(item)

    return results


def get_category_items(category_key: str, page: int = 1, page_size: int = 4, entity_type: Optional[str] = None) -> Dict[str, Any]:
    """Retrieves paginated channels/groups/bots for a specific category."""
    communities = get_curated_communities()
    items = [
        item for item in communities 
        if item.get("category") == category_key and (not entity_type or item.get("type") == entity_type)
    ]
    
    total_items = len(items)
    total_pages = max(1, (total_items + page_size - 1) // page_size)
    current_page = max(1, min(page, total_pages))

    start_idx = (current_page - 1) * page_size
    page_items = items[start_idx : start_idx + page_size]

    return {
        "items": page_items,
        "current_page": current_page,
        "total_pages": total_pages,
        "total_items": total_items,
        "category_key": category_key,
        "category_info": DIRECTORY_CATEGORIES.get(category_key, {"name": category_key.title(), "emoji": "📁"})
    }


def get_random_community(category: Optional[str] = None, entity_type: Optional[str] = None) -> Dict[str, Any]:
    """Selects a random channel/group/bot from the 1,400+ catalog."""

    communities = get_curated_communities()
    candidates = communities

    if category:
        candidates = [c for c in candidates if c.get("category") == category]
    if entity_type:
        candidates = [c for c in candidates if c.get("type") == entity_type]

    if not candidates:
        candidates = communities

    return random.choice(candidates)


def get_directory_stats() -> Dict[str, Any]:
    """Returns total volume metrics for the catalog."""
    communities = get_curated_communities()
    channels_count = sum(1 for c in communities if c.get("type") == "channel")
    groups_count = sum(1 for c in communities if c.get("type") == "group")
    bots_count = sum(1 for c in communities if c.get("type") == "bot")

    return {
        "total_communities": len(communities),
        "total_categories": len(DIRECTORY_CATEGORIES),
        "channels_count": channels_count,
        "groups_count": groups_count,
        "bots_count": bots_count
    }


# Backward compatibility alias
get_random_item = get_random_community

