"""
Sentinel Public Group Security & Admin Hygiene Auditor.
Evaluates group protections, spam susceptibility, captcha gating indicators,
and produces a Security Grade (A+ to F) with admin hardening guidelines.
"""
from typing import Dict, Any, List
from core.telegram_discovery import fetch_real_telegram_preview


async def audit_group_security(group_handle: str) -> Dict[str, Any]:
    """
    Performs forensic hygiene audit on a Telegram public group or supergroup.
    """
    clean_handle = group_handle.strip().lstrip("@")
    preview = await fetch_real_telegram_preview(clean_handle)

    if not preview:
        return {
            "found": False,
            "handle": clean_handle,
            "error": f"Could not fetch live Telegram profile for @{clean_handle}."
        }

    title = preview.get("title", clean_handle)
    members = preview.get("members_count") or 0
    desc = preview.get("description", "") or ""
    is_verified = preview.get("is_verified", False)
    entity_type = preview.get("type", "group")

    score = 75
    checklist: List[Dict[str, Any]] = []

    # 1. Group Verification Badge
    if is_verified:
        score += 20
        checklist.append({"item": "Official Verification Badge", "status": "PASS", "note": "Group is cryptographically verified by Telegram."})
    else:
        checklist.append({"item": "Official Verification Badge", "status": "INFO", "note": "Unverified public group."})

    # 2. Impersonation & Scam Disclaimer in Bio
    desc_l = desc.lower()
    if "admin will never" in desc_l or "beware of scammers" in desc_l or "no dm" in desc_l:
        score += 10
        checklist.append({"item": "Anti-Scam Admin Disclaimer", "status": "PASS", "note": "Bio warns members that admins will not DM first."})
    else:
        score -= 10
        checklist.append({"item": "Anti-Scam Admin Disclaimer", "status": "WARN", "note": "Missing explicit warning about fake admin impostors."})

    # 3. Rules / Guidelines Link
    if "rules" in desc_l or "guidelines" in desc_l or "t.me/" in desc_l:
        score += 10
        checklist.append({"item": "Code of Conduct / Rules Link", "status": "PASS", "note": "Community standards or pinned rules referenced in description."})
    else:
        score -= 5
        checklist.append({"item": "Code of Conduct / Rules Link", "status": "WARN", "note": "No clear rules or moderation policy displayed in public bio."})

    # 4. Anti-Spam / Captcha Bot Reference
    if any(b in desc_l for b in ["bot", "captcha", "shield", "protect", "rose", "combot"]):
        score += 10
        checklist.append({"item": "Automated Moderation / Shield", "status": "PASS", "note": "Active bot gating or automated captcha moderation detected."})
    else:
        checklist.append({"item": "Automated Moderation / Shield", "status": "INFO", "note": "Ensure captcha bots (e.g. Shieldy / Rose) are active in group."})

    # 5. Group Scale / Flood Risk
    if members > 50000:
        checklist.append({"item": "Supergroup Scaling", "status": "ALERT", "note": f"Massive audience ({members:,} members). Slow mode recommended."})
    elif members > 5000:
        checklist.append({"item": "Supergroup Scaling", "status": "PASS", "note": f"Established community with {members:,} active members."})
    else:
        checklist.append({"item": "Supergroup Scaling", "status": "INFO", "note": f"Emerging group ({members:,} members)."})

    final_score = max(10, min(100, score))
    if final_score >= 90:
        grade = "A+"
        verdict = "EXCELLENT SECURITY HYGIENE"
    elif final_score >= 80:
        grade = "A"
        verdict = "ROBUST DEFENSES"
    elif final_score >= 65:
        grade = "B"
        verdict = "STANDARD PUBLIC GROUP"
    elif final_score >= 50:
        grade = "C"
        verdict = "MODERATE SPAM VULNERABILITY"
    else:
        grade = "F"
        verdict = "HIGH VULNERABILITY TO BOT RAIDS"

    return {
        "found": True,
        "handle": clean_handle,
        "title": title,
        "members": members,
        "is_verified": is_verified,
        "security_score": final_score,
        "grade": grade,
        "verdict": verdict,
        "checklist": checklist
    }
