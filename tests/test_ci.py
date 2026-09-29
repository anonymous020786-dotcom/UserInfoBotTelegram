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


@pytest.mark.asyncio
async def test_user_to_phone_exposure_audit():
    """Test username profile phone exposure and deanonymization assessment."""
    from core.phone_resolver import audit_user_phone_exposure
    audit = await audit_user_phone_exposure("telegram")
    assert audit["found"] is True
    assert "threat_score" in audit
    assert "recommendation" in audit

