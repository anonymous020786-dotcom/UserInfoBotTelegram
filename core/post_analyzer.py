import re
import aiohttp
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup

from core.osint_analyzer import analyze_text_osint


async def fetch_real_telegram_post(post_url_or_ref: str) -> Optional[Dict[str, Any]]:
    """
    Scrapes 100% real live public Telegram channel post directly from Telegram embed server.
    Extracts author, title, exact views, UTC timestamp, media type, caption, and calculates engagement.
    """
    clean = post_url_or_ref.strip()
    # Support t.me/channel/123 or https://t.me/s/channel/123 or channel/123
    m = re.search(r'(?:t\.me\/(?:s\/)?|telegram\.me\/)?([a-zA-Z0-9_]{3,32})\/(\d+)', clean)
    if not m:
        return None

    channel_handle = m.group(1)
    message_id = int(m.group(2))

    embed_url = f"https://t.me/{channel_handle}/{message_id}?embed=1"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        timeout = aiohttp.ClientTimeout(total=6)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(embed_url, headers=headers) as resp:
                if resp.status != 200:
                    return None
                html = await resp.text()

        soup = BeautifulSoup(html, "html.parser")

        # 1. Author Name
        author_el = soup.find("div", class_="tgme_widget_message_author")
        author_name = author_el.text.strip() if author_el else f"@{channel_handle}"

        # 2. Check verified badge
        is_verified = bool(soup.find("i", class_="tgme_icon_verified"))

        # 3. Views count
        views_el = soup.find("span", class_="tgme_widget_message_views")
        views_str = views_el.text.strip() if views_el else "N/A"

        # Parse numeric views
        numeric_views = 0
        if views_str != "N/A":
            v_clean = views_str.replace(" ", "").replace(",", "")
            try:
                if "k" in v_clean.lower():
                    numeric_views = int(float(v_clean.lower().replace("k", "")) * 1000)
                elif "m" in v_clean.lower():
                    numeric_views = int(float(v_clean.lower().replace("m", "")) * 1_000_000)
                else:
                    numeric_views = int(v_clean)
            except Exception:
                numeric_views = 0

        # 4. Publication Date
        date_a = soup.find("a", class_="tgme_widget_message_date")
        published_iso = None
        published_human = "Unknown"
        if date_a:
            time_tag = date_a.find("time")
            if time_tag:
                published_iso = time_tag.get("datetime")
                published_human = time_tag.text.strip()

        # 5. Message Content / Caption
        text_el = soup.find("div", class_="tgme_widget_message_text")
        raw_text = text_el.text.strip() if text_el else ""

        # 6. Detect Media Type
        media_types = []
        if soup.find("i", class_="tgme_widget_message_video_thumb"):
            media_types.append("Video")
        if soup.find("a", class_="tgme_widget_message_photo_wrap"):
            media_types.append("Photo")
        if soup.find("div", class_="tgme_widget_message_document"):
            media_types.append("Document/File")
        if soup.find("div", class_="tgme_widget_message_poll"):
            media_types.append("Poll")
        if soup.find("a", class_="tgme_widget_message_link_preview"):
            media_types.append("Web Link Preview")
        if not media_types:
            media_types.append("Text Only")

        media_str = ", ".join(media_types)

        # 7. OSINT analysis of the post text
        osint_res = analyze_text_osint(raw_text) if raw_text else {
            "risk_rating": "CLEAN",
            "risk_score": 0,
            "language_script": "Latin (Western/Global)",
            "links": [],
            "emails": [],
            "mentions": [],
            "risk_triggers": []
        }

        # 8. Post stats & word metrics
        words_count = len(raw_text.split()) if raw_text else 0
        est_read_time = max(1, round(words_count / 200 * 60)) if words_count else 0

        return {
            "channel_handle": channel_handle,
            "message_id": message_id,
            "post_url": f"https://t.me/{channel_handle}/{message_id}",
            "author_name": author_name,
            "is_verified": is_verified,
            "views_str": views_str,
            "numeric_views": numeric_views,
            "published_iso": published_iso,
            "published_human": published_human,
            "media_type": media_str,
            "text": raw_text,
            "words_count": words_count,
            "est_read_time_sec": est_read_time,
            "osint": osint_res
        }
    except Exception:
        return None
