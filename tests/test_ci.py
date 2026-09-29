"""
Sentinel OSINT Bot - CI/CD Automated Test Suite
Designed for headless execution in GitHub Actions, Docker builds, and local development.
Does not require active internet connection or Telegram bot credentials.
"""
import pytest
import asyncio
import tempfile
import os
from pathlib import Path

from core.reg_date_estimator import estimate_registration_date
from core.dc_resolver import get_dc_info
from core.id_forensics import analyze_telegram_id, analyze_bot_token_forensics
from core.phone_analyzer import analyze_phone_number
from core.osint_analyzer import analyze_text_osint, validate_telegram_username
from core.directory_data import get_directory_stats, get_curated_communities, search_directory, get_category_items
from core.network_tools import calculate_hashes


def test_directory_catalog_integrity():
    """Verify curated catalog has 1,400+ valid entries across 32 categories."""
    stats = get_directory_stats()
    assert stats["total_communities"] >= 1400, "Catalog must have at least 1400 items"
    assert stats["total_categories"] == 32, "Catalog must span 32 categories"
    assert stats["channels_count"] > 500, "Must contain channels"
    assert stats["groups_count"] > 300, "Must contain supergroups"
    assert stats["bots_count"] > 200, "Must contain bots"

    communities = get_curated_communities()
    for item in communities[:100]:
        assert "username" in item, "Item must have username"
        assert "title" in item, "Item must have title"
        assert "category" in item, "Item must have category"
        assert item["type"] in ["channel", "group", "bot"], f"Invalid type {item['type']}"


def test_directory_search_and_pagination():
    """Test keyword filtering and category pagination."""
    python_items = search_directory("python")
    assert len(python_items) > 0, "Should find python communities"

    page_data = get_category_items("ai_ml", page=1, page_size=5)
    assert page_data["current_page"] == 1
    assert len(page_data["items"]) <= 5
    assert page_data["total_items"] > 0


def test_registration_age_regression():
    """Test chronological piecewise linear regression for historical and modern Telegram IDs."""
    early_user = estimate_registration_date(50_000_000)
    assert "2014" in early_user["estimated_month"]
    assert early_user["confidence"].startswith("±")

    modern_user = estimate_registration_date(7_500_000_000)
    assert "2024" in modern_user["estimated_month"]

    channel_reg = estimate_registration_date(-1001500000000)
    assert "2021" in channel_reg["estimated_month"] or "2022" in channel_reg["estimated_month"]


def test_dc_resolver():
    """Test Data Center resolver for official Telegram DCs."""
    dc2 = get_dc_info(2)
    assert dc2 is not None
    assert "Amsterdam" in dc2["location"] or "Netherlands" in dc2.get("country", "")
    assert dc2["name"] == "Venus (DC2)" or "Venus" in dc2["name"]

    dc4 = get_dc_info(4)
    assert dc4 is not None
    assert "Amsterdam" in dc4["location"]


def test_id_forensics():
    """Test 64-bit Telegram ID decomposition and bot token parser."""
    res_64bit = analyze_telegram_id(7_500_000_000)
    assert res_64bit["is_64bit"] is True
    assert res_64bit["bit_length"] >= 33
    assert "64-bit" in res_64bit["architecture"]

    token_res = analyze_bot_token_forensics("1234567890:ABCdefGHIjklMNOpqrsTUVwxyz123456789")
    assert token_res["is_valid_format"] is True
    assert token_res["bot_id"] == 1234567890

    bad_token = analyze_bot_token_forensics("invalid_token_string")
    assert bad_token["is_valid_format"] is False


def test_phone_analyzer():
    """Test phone OSINT, Fragment +888 detection, and international numbers."""
    frag = analyze_phone_number("+88801234567")
    assert frag["is_fragment_nft_number"] is True
    assert "TON NFT" in frag["country"]

    us_num = analyze_phone_number("+12025550123")
    assert us_num["is_fragment_nft_number"] is False
    assert us_num["dial_code"] == "+1"
    assert us_num["is_valid_length"] is True


def test_osint_risk_analyzer():
    """Test spam / phishing threat scoring."""
    clean_text = "Hello everyone, welcome to our open source project repository!"
    score_clean = analyze_text_osint(clean_text)
    assert score_clean["risk_score"] <= 30

    suspicious_text = "Free crypto giveaway! Visit https://t.me/example and contact ceo@example.com"
    score_suspicious = analyze_text_osint(suspicious_text)
    assert score_suspicious["risk_score"] >= 30
    assert len(score_suspicious["risk_triggers"]) > 0

    assert validate_telegram_username("durov")["is_valid_format"] is True
    assert validate_telegram_username("bad!name#")["is_valid_format"] is False
    assert validate_telegram_username("toolongusername123456789012345678901234567890")["is_valid_format"] is False


def test_hash_calculator():
    """Test cryptographic checksum generation."""
    hashes = calculate_hashes("Sentinel Intelligence")
    assert hashes["md5"] is not None
    assert hashes["sha256"] is not None
    assert len(hashes["sha256"]) == 64


@pytest.mark.asyncio
async def test_database_isolated():
    """Test SQLite database operations in an isolated environment."""
    import aiosqlite
    with tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        async with aiosqlite.connect(tmp_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    query_count INTEGER DEFAULT 0
                )
            """)
            await db.execute("INSERT INTO users (user_id, username, query_count) VALUES (?, ?, ?)", (999, "test_user", 5))
            await db.commit()

            async with db.execute("SELECT query_count FROM users WHERE user_id = 999") as cursor:
                row = await cursor.fetchone()
                assert row is not None
                assert row[0] == 5
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


@pytest.mark.asyncio
async def test_phone_to_telegram_resolution():
    """Test phone resolution, Fragment +888 detection, and vCard export."""
    from core.phone_resolver import resolve_phone_to_telegram
    res_888 = await resolve_phone_to_telegram("+88801234567")
    assert res_888["is_fragment_nft"] is True
    assert "tg://resolve?phone=" in res_888["tg_protocol"]
    assert "BEGIN:VCARD" in res_888["vcard_content"]
    assert res_888["dial_code"] == "+888"

    res_us = await resolve_phone_to_telegram("+12025550123")
    assert res_us["is_fragment_nft"] is False
    assert res_us["dial_code"] == "+1"
    assert "https://wa.me/" in res_us["wa_link"]

    # Indian phone number with telecom circle and UPI forensics
    res_in = await resolve_phone_to_telegram("+917492068998")
    assert res_in["country"] == "India"
    assert res_in["india_telecom"] is not None
    assert "Bihar & Jharkhand" in res_in["india_telecom"]["circle"]
    assert res_in["upi_data"] is not None
    assert res_in["upi_data"]["paytm"] == "7492068998@paytm"


@pytest.mark.asyncio
async def test_user_to_phone_exposure_audit():
    """Test username profile phone exposure and deanonymization assessment."""
    from core.phone_resolver import audit_user_phone_exposure
    audit = await audit_user_phone_exposure("telegram")
    assert audit["found"] is True
    assert "threat_score" in audit
    assert "recommendation" in audit


@pytest.mark.asyncio
async def test_keyboard_url_protocols_compliance():
    """Validate that all inline keyboard buttons adhere to Telegram Bot API protocol rules."""
    from core.phone_resolver import resolve_phone_to_telegram
    from aiogram.types import InlineKeyboardButton

    res = await resolve_phone_to_telegram("+917492068998")
    buttons = [
        InlineKeyboardButton(text="tg", url=res["tg_protocol"]),
        InlineKeyboardButton(text="web", url=res["tg_web"]),
        InlineKeyboardButton(text="wa", url=res["wa_link"]),
        InlineKeyboardButton(text="upi", callback_data=f"upi_reveal_{res['digits']}")
    ]

    for btn in buttons:
        if btn.url:
            assert btn.url.startswith(("https://", "http://", "tg://")), f"Invalid URL scheme in button: {btn.url}"
            assert not btn.url.startswith("upi://"), "Telegram Bot API rejects upi:// protocol in buttons!"


@pytest.mark.asyncio
async def test_cache_manager_ttl():
    """Test fast in-memory LRU & TTL cache subsystem."""
    from core.cache_manager import FastCache
    cache = FastCache(max_size=10, default_ttl=60)
    await cache.set("test_key", {"data": 123}, ttl=2)
    val = await cache.get("test_key")
    assert val is not None
    assert val["data"] == 123
    assert cache.hits == 1
    stats = cache.stats()
    assert stats["hits"] == 1


def test_search_operators_parser():
    """Test search operator parsing (min:10k, verified:true, type:channel)."""
    from core.pagination_manager import parse_search_operators
    clean, filters = parse_search_operators("python min:10k verified:true")
    assert clean == "python"
    assert filters["min_members"] == 10000
    assert filters["verified_only"] is True


def test_pagination_and_csv_generation():
    """Test session creation, pagination slicing, and CSV report export."""
    from core.pagination_manager import create_search_session, build_paginated_view, generate_search_csv
    fake_results = [
        {"title": f"Chan {i}", "username": f"chan_{i}", "type": "channel", "members_count": i * 1000, "is_verified": (i % 2 == 0)}
        for i in range(1, 15)
    ]
    sess_id = create_search_session(fake_results, "test", entity_type="channel", per_page=5)
    assert len(sess_id) == 8

    text, kb = build_paginated_view(sess_id, page=1)
    assert text is not None
    assert "Page 1 of 3" in text
    assert len(kb.inline_keyboard) > 0

    csv_data = generate_search_csv(sess_id)
    assert "Title,Username,Type" in csv_data
    assert "chan_1" in csv_data


@pytest.mark.asyncio
async def test_bot_safety_forensics():
    """Test bot safety analyzer and phishing risk heuristics."""
    from core.bot_safety_analyzer import audit_bot_safety
    res = await audit_bot_safety("botfather")
    assert res["found"] is True
    assert res["safety_score"] >= 75
    assert "verdict" in res


@pytest.mark.asyncio
async def test_channel_velocity_and_vsr():
    """Test Views-to-Subscriber Ratio and engagement velocity."""
    from core.channel_velocity import analyze_channel_velocity
    vel = await analyze_channel_velocity("telegram")
    assert vel["found"] is True
    assert "vsr_percent" in vel
    assert "err_percent" in vel
    assert "activity_grade" in vel


@pytest.mark.asyncio
async def test_link_security_and_invites():
    """Test Telegram private invite hash inspection and URL link unmasking."""
    from core.link_security import audit_telegram_link
    invite_res = await audit_telegram_link("https://t.me/+AbCdEfGhIjKlMnOp123456")
    assert invite_res["type"] == "telegram_invite"
    assert invite_res["invite_hash"] == "AbCdEfGhIjKlMnOp123456"
    assert "tg://join?invite=" in invite_res["tg_protocol"]

    web_res = await audit_telegram_link("https://telegram.org")
    assert web_res["type"] == "external_url"
    assert web_res["threat_level"] in ["LOW", "MEDIUM", "CRITICAL"]


def test_script_and_language_classifier():
    """Test Unicode script detection for international channels."""
    from core.language_detector import detect_scripts_in_text
    res_en = detect_scripts_in_text("Official Telegram News Channel")
    assert res_en["primary_script"] == "Latin"

    res_ru = detect_scripts_in_text("Новости Телеграм Канал")
    assert res_ru["primary_script"] == "Cyrillic"

    res_in = detect_scripts_in_text("टेलीग्राम समाचार चैनल")
    assert res_in["primary_script"] == "Devanagari"


@pytest.mark.asyncio
async def test_similar_community_recommender():
    """Test content and taxonomy-based channel recommender."""
    from core.similar_engine import find_similar_communities
    recs = await find_similar_communities("telegram", limit=4)
    assert len(recs["recommendations"]) > 0



