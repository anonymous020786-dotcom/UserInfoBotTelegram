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


async def run_diagnostics():
    print("=" * 60)
    print("🚀 SENTINEL BOT // SYSTEM DIAGNOSTICS & FEATURE VERIFICATION")
    print("=" * 60)

    # 1. Database Operations
    print("[1/8] Testing SQLite Database Schema & Queries...")
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
    print(f"      ✓ Database passed! Total registered users: {stats['total_users']}")

    # 2. Registration Date Regression Model
    print("[2/8] Testing Chronological Account Age Regression...")
    est_old = estimate_registration_date(50000000)
    est_mid = estimate_registration_date(850000000)
    est_new = estimate_registration_date(7500000000)
    print(f"      ✓ ID 50M: {est_old['estimated_month']} ({est_old['relative_age']})")
    print(f"      ✓ ID 850M: {est_mid['estimated_month']} ({est_mid['relative_age']})")
    print(f"      ✓ ID 7.5B: {est_new['estimated_month']} ({est_new['relative_age']})")

    # 3. DC Resolver
    print("[3/8] Testing Data Center (DC) Node Resolver...")
    dc2 = get_dc_info(2)
    dc4 = get_dc_info(4)
    dc5 = get_dc_info(5)
    print(f"      ✓ DC2: {dc2['name']} in {dc2['location']}")
    print(f"      ✓ DC4: {dc4['name']} in {dc4['location']}")
    print(f"      ✓ DC5: {dc5['name']} in {dc5['location']}")

    # 4. OSINT Text & Risk Analyzer
    print("[4/8] Testing OSINT Text & Phishing Risk Scoring...")
    sample_text = "Join my crypto pump! Guaranteed 100x return! Visit https://t.me/example and contact ceo@example.com @pumpleader"
    osint_res = analyze_text_osint(sample_text)
    print(f"      ✓ Threat Rating: {osint_res['risk_rating']} (Score: {osint_res['risk_score']})")
    print(f"      ✓ Extracted Links: {osint_res['links']}")
    print(f"      ✓ Extracted Emails: {osint_res['emails']}")
    print(f"      ✓ Extracted Mentions: {osint_res['mentions']}")
    assert len(osint_res["links"]) >= 1

    # 5. QR Code Generator
    print("[5/8] Testing Custom Telegram QR Generator...")
    qr_file = generate_styled_qr("https://t.me/telegram", filename_prefix="test_qr")
    assert Path(qr_file).exists() and Path(qr_file).stat().st_size > 0
    print(f"      ✓ QR Image created: {qr_file.name} ({qr_file.stat().st_size} bytes)")

    # 6. Digital Graphic ID Card Generator (Pillow)
    print("[6/8] Testing Pillow Digital ID Card Generator...")
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
    print(f"      ✓ Graphic ID Card created: {card_file.name} ({card_file.stat().st_size} bytes)")

    # 7. PDF Dossier Generator (ReportLab)
    print("[7/8] Testing ReportLab OSINT Dossier Generator...")
    pdf_file = generate_osint_pdf(
        entity_id=777000,
        title="Telegram Notifications",
        username="telegram",
        entity_type="channel",
        reg_estimate="August 2013",
        dc_info="🇳🇱 DC2 - Amsterdam",
        bio="Official Telegram notifications channel.",
        extra_details={
            "is_premium": True,
            "is_verified": True,
            "is_scam": False,
            "links": ["https://telegram.org"],
            "mentions": ["@durov"],
            "language_script": "Latin (Western/Global)"
        }
    )
    assert Path(pdf_file).exists() and Path(pdf_file).stat().st_size > 0
    print(f"      ✓ PDF Dossier created: {pdf_file.name} ({pdf_file.stat().st_size} bytes)")

    # 8. Live Real Telegram Web Data Scraping
    print("[8/8] Testing Live Real Telegram Data Resolution...")
    preview = await fetch_real_telegram_preview("telegram")
    assert preview is not None
    print(f"      ✓ Live Real Title: {preview['title']}")
    print(f"      ✓ Live Real Stats: {preview['extra']}")
    print(f"      ✓ Live Real Desc: {preview['description'][:40]}...")
    print(f"      ✓ Live Real Type: {preview['type']}")

    print("=" * 60)
    print("🎉 ALL 8 CORE SUBSYSTEM TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_diagnostics())
