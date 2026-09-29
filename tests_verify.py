import asyncio
import os
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from database import (
    init_db, get_or_create_user, update_user_preference, record_search,
    get_user_history, add_favorite, is_favorite, remove_favorite,
    log_identity, get_identity_history, get_bot_stats,
    add_to_watchlist, get_user_watchlist, remove_from_watchlist, is_in_watchlist,
    export_user_data_json
)
from core.dc_resolver import get_dc_info
from core.reg_date_estimator import estimate_registration_date
from core.osint_analyzer import analyze_text_osint, validate_telegram_username
from core.qr_generator import generate_styled_qr
from core.card_generator import create_identity_card
from core.pdf_generator import generate_osint_pdf
from core.telegram_discovery import fetch_real_telegram_preview
from core.post_analyzer import fetch_real_telegram_post
from core.fragment_scraper import scrape_fragment_username
from core.domain_ip_analyzer import resolve_domain_or_ip
from core.phone_analyzer import analyze_phone_number
from core.id_forensics import analyze_telegram_id, analyze_bot_token_forensics
from core.bot_discovery import search_real_bots, detect_bot_clones, get_random_bot, CURATED_BOTS
from core.network_tools import (
    check_ssl_certificate, query_rdap_whois, calculate_hashes,
    decode_telegram_start_param, get_public_mtproto_proxies
)
from core.channel_intelligence import calculate_channel_health_score, get_country_channels
from core.directory_data import get_directory_stats, get_curated_communities, search_directory


async def run_diagnostics():
    print("=" * 70)
    print("🚀 SENTINEL BOT // SYSTEM DIAGNOSTICS & 27+ NEW ADVANCED FEATURES")
    print("=" * 70)

    # 1. Database Operations & Watchdog
    print("[1/18] Testing SQLite Database Schema & Watchdog System...")
    await init_db()
    user = await get_or_create_user(12345678, "testuser", "John", "Doe")
    assert user["user_id"] == 12345678
    await add_to_watchlist(12345678, "telegram", "channel", "Telegram News", 9400000)
    assert await is_in_watchlist(12345678, "telegram") is True
    watch = await get_user_watchlist(12345678)
    assert len(watch) >= 1
    await remove_from_watchlist(12345678, "telegram")
    assert await is_in_watchlist(12345678, "telegram") is False
    data_dump = await export_user_data_json(12345678)
    assert "export_timestamp" in data_dump
    print("       ✓ Database & Watchdog engine passed cleanly!")

    # 2. Registration Date Regression Model
    print("[2/18] Testing Chronological Account Age Regression...")
    est_old = estimate_registration_date(50000000)
    est_new = estimate_registration_date(7500000000)
    print(f"       ✓ ID 50M: {est_old['estimated_month']} ({est_old['relative_age']})")
    print(f"       ✓ ID 7.5B: {est_new['estimated_month']} ({est_new['relative_age']})")

    # 3. DC Resolver
    print("[3/18] Testing Data Center (DC) Node Resolver...")
    dc2 = get_dc_info(2)
    print(f"       ✓ DC2: {dc2['name']} in {dc2['location']}")

    # 4. OSINT Text & Phishing Risk Scoring
    print("[4/18] Testing OSINT Text & Phishing Risk Scoring...")
    sample_text = "Free crypto giveaway! Visit https://t.me/example and contact ceo@example.com"
    osint_res = analyze_text_osint(sample_text)
    print(f"       ✓ Threat Rating: {osint_res['risk_rating']} (Score: {osint_res['risk_score']})")

    # 5. Media & Export Generators (QR, ID Card, PDF)
    print("[5/18] Testing Styled QR, Pillow ID Card & ReportLab PDF Generators...")
    qr_file = generate_styled_qr("https://t.me/telegram", filename_prefix="diag_qr")
    assert Path(qr_file).exists()
    card_file = create_identity_card(777000, "Telegram News", "telegram", "channel", "Aug 2013", "DC2", True, True, False)
    assert Path(card_file).exists()
    pdf_file = generate_osint_pdf(777000, "Telegram News", "telegram", "channel", "Aug 2013", "DC2", "Official News", {})
    assert Path(pdf_file).exists()
    print("       ✓ All visual forensic export artifacts rendered successfully!")

    # 6. Live Telegram Web Data Resolution
    print("[6/18] Testing Live Real Telegram Data Resolution...")
    preview = await fetch_real_telegram_preview("telegram")
    assert preview is not None
    print(f"       ✓ Live Real Channel: {preview['title']} ({preview['extra']})")

    # 7. Channel Post Intelligence & Engagement Forensics
    print("[7/18] Testing Real Channel Post Forensics (/post)...")
    post = await fetch_real_telegram_post("https://t.me/telegram/248")
    assert post is not None
    print(f"       ✓ Real Post Views: {post['views_str']}, Author: {post['author_name']}, Media: {post['media_type']}")

    # 8. Live Fragment.com NFT Marketplace Scraper
    print("[8/18] Testing Live Fragment.com NFT Marketplace Scraper (/fragment)...")
    frag = await scrape_fragment_username("crypto")
    assert frag is not None
    print(f"       ✓ Fragment @crypto: Status={frag['status']}, Valuation={frag.get('price_ton')} TON")

    # 9. Domain & IP Geolocation Network OSINT
    print("[9/18] Testing Domain & IP Network Geolocation OSINT (/domain, /ip)...")
    dom = await resolve_domain_or_ip("telegram.org")
    assert dom["ip_address"] is not None
    print(f"       ✓ Target: {dom['target']} -> IP: {dom['ip_address']} ({dom['geo']['country']})")

    # 10. Phone Number Forensics & TON +888 Anonymous Number
    print("[10/18] Testing Phone Number OSINT (/phone)...")
    ph_nft = analyze_phone_number("+88801234567")
    assert ph_nft["is_fragment_nft_number"] is True
    print(f"       ✓ Phone +888: {ph_nft['flag']} {ph_nft['country']} (NFT: True)")

    # 11. 64-bit ID Forensics & Architecture
    print("[11/18] Testing 64-bit ID Architecture & Bit-Depth (/idmath)...")
    id_user = analyze_telegram_id(7500000000)
    assert id_user["is_64bit"] is True
    print(f"       ✓ User 7.5B: {id_user['architecture']} ({id_user['bit_length']} bits)")

    # 12. Bot Token Offline Decoding & Age Forensics
    print("[12/18] Testing Bot Token Forensic Decomposition (/token)...")
    token_audit = analyze_bot_token_forensics("1234567890:ABCdefGhIJKlmNoPQRsTUVwxyZ123456789")
    assert token_audit["bot_id"] == 1234567890
    print(f"       ✓ Embedded Bot ID: {token_audit['bot_id']}")

    # 13. Advanced Bot Finder Engine (/findbot)
    print("[13/18] Testing Advanced Bot Finder Engine (/findbot)...")
    bots = await search_real_bots("ai", limit=4)
    assert len(bots) >= 1
    print(f"       ✓ Found {len(bots)} live bots for query 'ai'. Example: @{bots[0]['username']}")

    # 14. Bot Squatting & Clone Hunter (/botsquat)
    print("[14/18] Testing Bot Squatting & Clone Hunter (/botsquat)...")
    clones = await detect_bot_clones("telegram")
    print(f"       ✓ Scanned permutations: detected {len(clones)} live clone candidates")

    # 15. Bot Roulette (/randombot)
    print("[15/19] Testing Bot Roulette (/randombot)...")
    rb = get_random_bot()
    assert rb["username"].lower().endswith("bot") or rb["username"].lower() in ["wallet", "botfather"]
    print(f"       ✓ Picked Random Bot: {rb['name']} (@{rb['username']}) - {rb['category']}")

    # 16. TLS/SSL Certificate Inspection (/ssl)
    print("[16/19] Testing TLS/SSL Certificate Audit (/ssl)...")
    ssl_info = await check_ssl_certificate("telegram.org")
    assert ssl_info["is_valid"] is True
    print(f"       ✓ SSL Issuer: {ssl_info['issuer']} (Expires: {ssl_info['expires_at']})")

    # 17. Authoritative RDAP / WHOIS Query (/whois)
    print("[17/19] Testing Authoritative RDAP / WHOIS Query (/whois)...")
    whois_info = await query_rdap_whois("telegram.org")
    print(f"       ✓ RDAP Status: {whois_info.get('success')}, Registrar: {whois_info.get('registrar')}")

    # 18. Channel Health Quality Score (/health) & Country Communities
    print("[18/19] Testing Channel Health Quality Score & Regional Directory...")
    health = calculate_channel_health_score(preview)
    assert health["score"] >= 70
    us_channels = get_country_channels("us")
    assert len(us_channels["channels"]) >= 3
    print(f"       ✓ Telegram News Health Score: {health['score']}/100 ({health['grade']})")
    print(f"       ✓ Regional US Directory: {us_channels['flag']} {len(us_channels['channels'])} top channels")

    # 19. Curated Directory Catalog (1,400+ Channels, Groups & Bots)
    print("[19/19] Testing Curated Directory Catalog (1,400+ communities & bots)...")
    stats = get_directory_stats()
    assert stats["total_communities"] >= 1400
    assert stats["total_categories"] == 32
    assert stats["channels_count"] > 500
    assert stats["groups_count"] > 300
    assert stats["bots_count"] > 200
    search_res = search_directory("crypto")
    assert len(search_res) > 20
    print(f"       ✓ Catalog Verified: {stats['total_communities']} communities across {stats['total_categories']} categories!")
    print(f"         (Channels: {stats['channels_count']} | Groups: {stats['groups_count']} | Bots: {stats['bots_count']})")
    print(f"       ✓ Query 'crypto' returned {len(search_res)} curated results.")

    # Clean temporary diagnostic artifacts
    for f in [qr_file, card_file, pdf_file]:
        try:
            Path(f).unlink(missing_ok=True)
        except Exception:
            pass

    print("=" * 70)
    print("🎉 ALL 19 CORE, BOT FINDER, DIRECTORY & ADVANCED SUBSYSTEMS PASSED WITH 100% SUCCESS!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_diagnostics())
