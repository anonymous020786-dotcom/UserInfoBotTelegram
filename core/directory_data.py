from typing import List, Dict, Any, Optional
import random

DIRECTORY_CATEGORIES = {
    "technology": {"name": "Technology & Gadgets", "emoji": "💻"},
    "coding_dev": {"name": "Programming & Development", "emoji": "👨‍💻"},
    "ai_ml": {"name": "AI & Machine Learning", "emoji": "🤖"},
    "cybersecurity": {"name": "Cybersecurity & OSINT", "emoji": "🛡️"},
    "crypto_web3": {"name": "Crypto & Web3", "emoji": "⚡"},
    "news_world": {"name": "Global News & Media", "emoji": "🌍"},
    "design_uiux": {"name": "UI/UX & Creative Design", "emoji": "🎨"},
    "science_space": {"name": "Science & Space Exploration", "emoji": "🚀"},
    "gaming_esports": {"name": "Gaming & Esports", "emoji": "🎮"},
    "education_books": {"name": "Education, Books & Learning", "emoji": "📚"},
    "music_art": {"name": "Music & Audio", "emoji": "🎵"},
    "telegram_official": {"name": "Official Telegram Channels", "emoji": "✈️"},
}

CURATED_COMMUNITIES: List[Dict[str, Any]] = [
    # Technology
    {"username": "TechCrunch", "title": "TechCrunch News", "category": "technology", "type": "channel", "members": "180,000+", "description": "Startup news and technology analysis."},
    {"username": "TheVerge", "title": "The Verge Updates", "category": "technology", "type": "channel", "members": "120,000+", "description": "Covering the future of tech, science, and culture."},
    {"username": "ArsTechnica", "title": "Ars Technica", "category": "technology", "type": "channel", "members": "95,000+", "description": "Original tech reporting and analysis."},
    {"username": "WiredNews", "title": "WIRED Feed", "category": "technology", "type": "channel", "members": "140,000+", "description": "How technology is changing every aspect of human life."},

    # Coding & Development
    {"username": "Python", "title": "Python Hub", "category": "coding_dev", "type": "group", "members": "250,000+", "description": "Global community for Python programmers and tutorials."},
    {"username": "GitHubTrending", "title": "GitHub Trending Daily", "category": "coding_dev", "type": "channel", "members": "110,000+", "description": "Discover trending open-source repositories daily."},
    {"username": "DevHumor", "title": "Developer Humor", "category": "coding_dev", "type": "channel", "members": "290,000+", "description": "Daily memes, jokes, and funny developer life stories."},
    {"username": "JavaScriptDaily", "title": "JavaScript & TypeScript", "category": "coding_dev", "type": "channel", "members": "85,000+", "description": "Modern JS, React, Node.js, and web dev tips."},

    # AI & Machine Learning
    {"username": "OpenAI", "title": "OpenAI Community", "category": "ai_ml", "type": "channel", "members": "320,000+", "description": "Announcements and research updates regarding ChatGPT and AI models."},
    {"username": "MachineLearning", "title": "Machine Learning & Deep Learning", "category": "ai_ml", "type": "channel", "members": "175,000+", "description": "Research papers, neural network architectures, and benchmarks."},
    {"username": "HuggingFaceNews", "title": "Hugging Face Models", "category": "ai_ml", "type": "channel", "members": "90,000+", "description": "Latest open-weights models and AI releases."},

    # Cybersecurity & OSINT
    {"username": "TheHackerNews", "title": "The Hacker News (THN)", "category": "cybersecurity", "type": "channel", "members": "450,000+", "description": "Leading cybersecurity news, zero-days, and vulnerability disclosures."},
    {"username": "BleepingComputer", "title": "BleepingComputer", "category": "cybersecurity", "type": "channel", "members": "210,000+", "description": "Malware alerts, ransomware news, and security advisories."},
    {"username": "CyberSecHub", "title": "OSINT & InfoSec Digest", "category": "cybersecurity", "type": "channel", "members": "80,000+", "description": "Open Source Intelligence tools, cheatsheets, and methodologies."},

    # Crypto & Web3
    {"username": "CoinDesk", "title": "CoinDesk Daily", "category": "crypto_web3", "type": "channel", "members": "210,000+", "description": "Authoritative news on Bitcoin, digital assets, and finance."},
    {"username": "CoinMarketCap", "title": "CoinMarketCap Official", "category": "crypto_web3", "type": "channel", "members": "390,000+", "description": "Crypto price alerts, market cap rankings, and news."},
    {"username": "EthereumOfficial", "title": "Ethereum Ecosystem", "category": "crypto_web3", "type": "channel", "members": "130,000+", "description": "Updates on Ethereum protocol, Layer 2s, and smart contracts."},

    # Global News & Media
    {"username": "ReutersNews", "title": "Reuters World News", "category": "news_world", "type": "channel", "members": "300,000+", "description": "Breaking international news and unbiased world reports."},
    {"username": "Bloomberg", "title": "Bloomberg Markets", "category": "news_world", "type": "channel", "members": "240,000+", "description": "Financial markets, economics, and business insights."},
    {"username": "BBCWorld", "title": "BBC News International", "category": "news_world", "type": "channel", "members": "190,000+", "description": "Global reporting from the BBC correspondents worldwide."},

    # UI/UX & Design
    {"username": "UIUXDesigners", "title": "UI/UX Inspiration Hub", "category": "design_uiux", "type": "channel", "members": "95,000+", "description": "Mobile app UI, wireframes, interaction design, and tips."},
    {"username": "FigmaDaily", "title": "Figma Resources & Plugins", "category": "design_uiux", "type": "channel", "members": "70,000+", "description": "Free UI kits, Figma plugins, and component libraries."},

    # Science & Space
    {"username": "NASA", "title": "NASA Official Updates", "category": "science_space", "type": "channel", "members": "520,000+", "description": "Space exploration discoveries, James Webb telescope images, and missions."},
    {"username": "ScienceAlert", "title": "ScienceAlert", "category": "science_space", "type": "channel", "members": "180,000+", "description": "Fascinating scientific discoveries, biology, and physics."},

    # Gaming & Esports
    {"username": "IGN", "title": "IGN Gaming News", "category": "gaming_esports", "type": "channel", "members": "280,000+", "description": "Video game trailers, game reviews, and gaming culture."},
    {"username": "SteamDeals", "title": "Steam Discounts & Freebies", "category": "gaming_esports", "type": "channel", "members": "350,000+", "description": "100% off free games, Steam promotions, and humble bundles."},

    # Education & Books
    {"username": "ProjectGutenberg", "title": "Free E-Books Club", "category": "education_books", "type": "channel", "members": "110,000+", "description": "Public domain classic literature, philosophy, and history books."},
    {"username": "CourseraFree", "title": "Free Online Courses & MOOCs", "category": "education_books", "type": "channel", "members": "160,000+", "description": "Certifications, academic courses, and university lectures."},

    # Music & Audio
    {"username": "IndieMusic", "title": "Indie & Alternative Music", "category": "music_art", "type": "channel", "members": "80,000+", "description": "Fresh indie music releases, underground tracks, and playlists."},
    {"username": "ClassicalMusic", "title": "Classical Masterpieces", "category": "music_art", "type": "channel", "members": "65,000+", "description": "Symphonies, piano concertos, and timeless orchestral works."},

    # Official Telegram
    {"username": "telegram", "title": "Telegram News", "category": "telegram_official", "type": "channel", "members": "11,500,000+", "description": "Official announcements, new Telegram features, and app updates."},
    {"username": "durov", "title": "Pavel Durov", "category": "telegram_official", "type": "channel", "members": "2,400,000+", "description": "Thoughts and announcements from the founder and CEO of Telegram."},
    {"username": "contest", "title": "Telegram Contests", "category": "telegram_official", "type": "channel", "members": "150,000+", "description": "Official development and design contests organized by Telegram."},
    {"username": "TelegramTips", "title": "Telegram Tips & Tricks", "category": "telegram_official", "type": "channel", "members": "4,100,000+", "description": "Official guides to get the most out of Telegram features."}
]


def search_directory(query: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
    """Searches curated channels and groups by keyword in title, username, or description."""
    q = query.lower().strip().lstrip("@")
    results = []
    for item in CURATED_COMMUNITIES:
        if category and item["category"] != category:
            continue
        if q in item["username"].lower() or q in item["title"].lower() or q in item["description"].lower():
            results.append(item)
    return results


def get_category_items(category_key: str, page: int = 1, page_size: int = 4) -> Dict[str, Any]:
    """Retrieves paginated channels/groups for a specific category."""
    items = [item for item in CURATED_COMMUNITIES if item["category"] == category_key]
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
        "category_info": DIRECTORY_CATEGORIES.get(category_key, {"name": category_key, "emoji": "📁"})
    }


def get_random_item() -> Dict[str, Any]:
    """Returns a random channel or group from the curated directory."""
    return random.choice(CURATED_COMMUNITIES)
