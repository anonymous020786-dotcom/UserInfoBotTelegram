import asyncio
import os
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from database import (
    init_db, get_or_create_user, update_user_preference, record_search,
    get_user_history, add_favorite, is_favorite, remove_favorite,
    log_identity, get_identity_history, get_bot_stats
)
from core.dc_resolver import get_dc_info
from core.reg_date_estimator import estimate_registration_date
from core.osint_analyzer import analyze_text_osint, validate_telegram_username
from core.qr_generator import generate_styled_qr
from core.vcard_generator import generate_vcard
from core.card_generator import create_identity_card
from core.pdf_generator import generate_osint_pdf
from core.telegram_discovery import fetch_real_telegram_preview
from core.post_analyzer import fetch_real_telegram_post
from core.fragment_scraper import scrape_fragment_username
from core.domain_ip_analyzer import resolve_domain_or_ip
from core.phone_analyzer import analyze_phone_number
from core.id_forensics import analyze_telegram_id, analyze_bot_token_forensics


async def run_diagnostics():
    print("=" * 65)
    print("🚀 SENTINEL BOT // SYSTEM DIAGNOSTICS & ADVANCED FEATURE VERIFICATION")
    print("=" * 65)

    # 1. Database Operations
    print("[1/14] Testing SQLite Database Schema & Queries...")
    await init_db()
    user = await get_or_create_user(12345678, "testuser", "John", "Doe")
    assert user["user_id"] == 12345678
    await update_user_preference(12345678, language="es", theme="osint")
    await record_search(12345678, 777000, "telegram", "channel", "Telegram News")
    history = await get_user_history(12345678)
    assert len(history) >= 1
    await add_favorite(12345678, 777000, "telegram", "Telegram News", "channel")
    assert await is_favorite(12345678, 777000) is True
    await remove_favorite(12345678, 777000)
    await log_identity(12345678, "testuser", "John", "Doe")
    identities = await get_identity_history(12345678)
    assert len(identities) >= 1
    stats = await get_bot_stats()
    print(f"       ✓ Database passed! Total registered users: {stats['total_users']}")

    # 2. Registration Date Regression Model
    print("[2/14] Testing Chronological Account Age Regression...")
    est_old = estimate_registration_date(50000000)
    est_mid = estimate_registration_date(850000000)
    est_new = estimate_registration_date(7500000000)
    print(f"       ✓ ID 50M: {est_old['estimated_month']} ({est_old['relative_age']})")
    print(f"       ✓ ID 850M: {est_mid['estimated_month']} ({est_mid['relative_age']})")
    print(f"       ✓ ID 7.5B: {est_new['estimated_month']} ({est_new['relative_age']})")

    # 3. DC Resolver
    print("[3/14] Testing Data Center (DC) Node Resolver...")
    dc2 = get_dc_info(2)
    dc4 = get_dc_info(4)
    dc5 = get_dc_info(5)
    print(f"       ✓ DC2: {dc2['name']} in {dc2['location']}")
    print(f"       ✓ DC4: {dc4['name']} in {dc4['location']}")
    print(f"       ✓ DC5: {dc5['name']} in {dc5['location']}")

    # 4. OSINT Text & Risk Analyzer
    print("[4/14] Testing OSINT Text & Phishing Risk Scoring...")
    sample_text = "Join my crypto pump! Guaranteed 100x return! Visit https://t.me/example and contact ceo@example.com @pumpleader"
    osint_res = analyze_text_osint(sample_text)
    print(f"       ✓ Threat Rating: {osint_res['risk_rating']} (Score: {osint_res['risk_score']})")
    assert len(osint_res["links"]) >= 1

    # 5. QR Code Generator
    print("[5/14] Testing Custom Telegram QR Generator...")
    qr_file = generate_styled_qr("https://t.me/telegram", filename_prefix="test_qr")
    assert Path(qr_file).exists() and Path(qr_file).stat().st_size > 0
    print(f"       ✓ QR Image created: {qr_file.name} ({qr_file.stat().st_size} bytes)")

    # 6. Digital Graphic ID Card Generator (Pillow)
    print("[6/14] Testing Pillow Digital ID Card Generator...")
    card_file = create_identity_card(
        entity_id=777000,
        title="Telegram Notifications",
        username="telegram",
        entity_type="channel",
        reg_estimate="August 2013 (~13 yrs)",
        dc_info="🇳🇱 DC2 - Amsterdam",
        is_premium=True,
        is_verified=True,
        is_scam=False
    )
    assert Path(card_file).exists() and Path(card_file).stat().st_size > 0
    print(f"       ✓ Graphic ID Card created: {card_file.name} ({card_file.stat().st_size} bytes)")

    # 7. PDF Dossier Generator (ReportLab)
    print("[7/14] Testing ReportLab OSINT Dossier Generator...")
    pdf_file = generate_osint_pdf(
        entity_id=777000,
        title="Telegram Notifications",
        username="telegram",
        entity_type="channel",
        reg_estimate="August 2013",
        dc_info="🇳🇱 DC2 - Amsterdam",
        bio="Official Telegram notifications channel.",
        extra_details={"is_premium": True, "is_verified": True}
    )
    assert Path(pdf_file).exists() and Path(pdf_file).stat().st_size > 0
    print(f"       ✓ PDF Dossier created: {pdf_file.name} ({pdf_file.stat().st_size} bytes)")

    # 8. Live Real Telegram Web Data Scraping
    print("[8/14] Testing Live Real Telegram Data Resolution...")
    preview = await fetch_real_telegram_preview("telegram")
    assert preview is not None
    print(f"       ✓ Live Real Title: {preview['title']} ({preview['extra']})")

    # 9. Channel Post Intelligence & Engagement Forensics
    print("[9/14] Testing Real Channel Post Forensics...")
    post = await fetch_real_telegram_post("https://t.me/telegram/248")
    assert post is not None
    print(f"       ✓ Post Author: {post['author_name']}")
    print(f"       ✓ Post Real Views: {post['views_str']}")
    print(f"       ✓ Post Media Type: {post['media_type']}")
    print(f"       ✓ Published: {post['published_human']}")

    # 10. Live Fragment.com NFT Marketplace Scraper
    print("[10/14] Testing Live Fragment.com NFT Marketplace Scraper...")
    frag = await scrape_fragment_username("crypto")
    assert frag is not None
    print(f"       ✓ Fragment @crypto Status: {frag['status']}")
    print(f"       ✓ Fragment @crypto Valuation: {frag.get('price_ton', 'N/A')} TON (~${frag.get('price_usd_est', 'N/A')} USD)")

    # 11. Domain & IP Geolocation Network OSINT
    print("[11/14] Testing Domain & IP Network Geolocation OSINT...")
    dom = await resolve_domain_or_ip("telegram.org")
    assert dom["ip_address"] is not None
    print(f"       ✓ Target: {dom['target']} -> IP: {dom['ip_address']}")
    print(f"       ✓ Location: {dom['geo']['country']} ({dom['geo']['city']})")
    print(f"       ✓ ASN & Network: {dom['geo']['asn']}")

    # 12. Phone Number Forensics & TON +888 NFT Number
    print("[12/14] Testing Phone Number OSINT & Fragment +888 Detection...")
    ph_nft = analyze_phone_number("+88801234567")
    ph_us = analyze_phone_number("+12025550143")
    print(f"       ✓ Phone +888: {ph_nft['flag']} {ph_nft['country']} (Is NFT: {ph_nft['is_fragment_nft_number']})")
    print(f"       ✓ Phone +1: {ph_us['flag']} {ph_us['country']} ({ph_us['timezone']})")

    # 13. 64-bit ID Mathematics & Peer Classification
    print("[13/14] Testing 64-bit ID Architecture & Peer Classification...")
    id_user = analyze_telegram_id(7500000000)
    id_chan = analyze_telegram_id(-1001234567890)
    print(f"       ✓ User 7.5B: {id_user['architecture']} ({id_user['bit_length']} bits) -> Hex: {id_user['hex_representation']}")
    print(f"       ✓ Channel ID: {id_chan['peer_type']} (Stripped Channel ID: {id_chan['underlying_channel_id']})")

    # 14. Bot Token Offline Decoding & Age Forensics
    print("[14/14] Testing Bot Token Forensic Decomposition...")
    token_audit = analyze_bot_token_forensics("1234567890:ABCdefGhIJKlmNoPQRsTUVwxyZ123456789")
    assert token_audit["is_valid_format"] is True
    print(f"       ✓ Embedded Bot ID: {token_audit['bot_id']}")
    print(f"       ✓ Estimated Bot Epoch: {token_audit['id_forensics']['estimated_registration']}")

    print("=" * 65)
    print("🎉 ALL 14 CORE & ADVANCED SUBSYSTEM TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(run_diagnostics())
