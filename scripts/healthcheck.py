#!/usr/bin/env python3
"""
Sentinel Telegram Bot - Container & Deployment Health Probe
Used by Docker HEALTHCHECK and CD deployment verification pipelines.
Exits 0 if all core systems, database, and catalog are operational; 1 otherwise.
"""
import sys
import os
import asyncio
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

async def check_health() -> bool:
    try:
        # 1. Verify Catalog Integrity
        catalog_path = BASE_DIR / "data" / "curated_catalog.json"
        if not catalog_path.exists():
            print(f"[HEALTHCHECK FAILED] Catalog file missing at {catalog_path}", file=sys.stderr)
            return False
        
        from core.directory_data import get_directory_stats
        stats = get_directory_stats()
        if stats["total_communities"] < 1000:
            print(f"[HEALTHCHECK FAILED] Catalog contains only {stats['total_communities']} items", file=sys.stderr)
            return False

        # 2. Verify Database Accessibility
        from config import DB_PATH
        from database import init_db
        import aiosqlite
        await init_db()
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT 1") as cursor:
                row = await cursor.fetchone()
                if not row or row[0] != 1:
                    print("[HEALTHCHECK FAILED] Database query check failed", file=sys.stderr)
                    return False

        # 3. Verify Core Module Imports
        from core.dc_resolver import get_dc_info
        from core.reg_date_estimator import estimate_registration_date
        from core.id_forensics import analyze_telegram_id
        from core.phone_analyzer import analyze_phone_number

        # Quick regression sanity check
        age_info = estimate_registration_date(7500000000)
        if not age_info or "estimated_month" not in age_info or age_info["estimated_month"] == "Unknown":
            print("[HEALTHCHECK FAILED] Age estimator sanity check failed", file=sys.stderr)
            return False

        print(f"[HEALTHCHECK OK] Sentinel Bot engine healthy. Catalog: {stats['total_communities']} items across {stats['total_categories']} categories.")
        return True

    except Exception as exc:
        print(f"[HEALTHCHECK ERROR] Unexpected error: {exc}", file=sys.stderr)
        return False

def main():
    healthy = asyncio.run(check_health())
    sys.exit(0 if healthy else 1)

if __name__ == "__main__":
    main()
