"""
Sentinel Telegram OSINT - Phone to User & Username to Phone Intelligence Engine
Provides comprehensive phone number forensics, Fragment +888 NFT virtual number scraping,
direct client protocol links, vCard generation, and Telegram MTProto privacy boundary analysis.
"""
import re
from typing import Dict, Any, Optional, List
from pathlib import Path

from core.phone_analyzer import analyze_phone_number
from core.fragment_scraper import scrape_fragment_phone_number, scrape_fragment_username
from core.telegram_discovery import resolve_full_entity


def resolve_india_telecom(digits: str) -> Optional[Dict[str, str]]:
    """Resolves Telecom Circle / State and Carrier for Indian mobile numbers."""
    if not ((digits.startswith("91") and len(digits) == 12) or (len(digits) == 10 and digits[0] in "6789")):
        return None
    d10 = digits[-10:]
    p2 = d10[:2]
    p4 = d10[:4]
    p5 = d10[:5]

    circle = "India National Mobile"
    operator = "GSM / 4G-5G VoLTE"

    if p4 in ["7488", "7489", "7490", "7491", "7492", "7493", "7494"]:
        circle = "Bihar & Jharkhand"
        operator = "Bharti Airtel / Reliance Jio"
    elif p4.startswith("749"):
        circle = "Bihar & Jharkhand"
        operator = "Bharti Airtel / Reliance Jio"
    elif p2 in ["98", "99", "97", "96", "95", "94", "93", "92", "91", "90"]:
        if p4.startswith("981") or p4.startswith("987") or p4.startswith("991"):
            circle = "Delhi NCR / Punjab / North"
        elif p4.startswith("982") or p4.startswith("989"):
            circle = "Mumbai / Maharashtra / Gujarat"
        elif p4.startswith("984") or p4.startswith("944"):
            circle = "Karnataka / Tamil Nadu / South"
        elif p4.startswith("983") or p4.startswith("943"):
            circle = "Kolkata / West Bengal / East"

    return {
        "circle": circle,
        "operator": operator,
        "series": p5,
        "national_format": f"0{d10[:5]} {d10[5:]}",
        "e164_spaced": f"+91 {d10[:5]} {d10[5:]}"
    }


def get_upi_vectors(digits: str) -> Optional[Dict[str, Any]]:
    """Generates NPCI UPI Virtual Payment Addresses for Indian mobile numbers."""
    if not ((digits.startswith("91") and len(digits) == 12) or (len(digits) == 10 and digits[0] in "6789")):
        return None
    d10 = digits[-10:]
    return {
        "phonepe": f"{d10}@ybl",
        "paytm": f"{d10}@paytm",
        "google_pay": f"{d10}@oksbi",
        "bhim": f"{d10}@upi",
        "upi_link": f"upi://pay?pa={d10}@paytm&pn=VerifyTargetName&cu=INR"
    }


async def resolve_phone_to_telegram(phone_input: str) -> Dict[str, Any]:
    """
    Performs multi-layered Telegram forensics on an international phone number:
    1. Geographic, carrier code, timezone, and flag analysis.
    2. Indian Telecom Circle and Telecom Operator series allocation.
    3. UPI Virtual Payment Address (VPA) financial OSINT vectors.
    4. Fragment +888 Anonymous Virtual Number scraping (TON NFT status, price, owner).
    5. Telegram direct client protocol links (tg://resolve?phone= and https://t.me/+).
    6. RFC vCard generation for native iOS/Android mutual contact synchronization.
    7. Telegram MTProto cryptographic privacy boundary assessment.
    """
    base_info = analyze_phone_number(phone_input)
    clean_digits = base_info["digits"]
    is_fragment_888 = clean_digits.startswith("888")

    fragment_data = None
    if is_fragment_888:
        fragment_data = await scrape_fragment_phone_number(clean_digits)

    # India Telecom & UPI Resolution
    india_telecom = resolve_india_telecom(clean_digits)
    upi_data = get_upi_vectors(clean_digits)

    # Generate RFC 2426 vCard for 1-tap mobile contact sync
    vcard_content = (
        "BEGIN:VCARD\r\n"
        "VERSION:3.0\r\n"
        f"FN:Sentinel Target {clean_digits}\r\n"
        f"TEL;TYPE=CELL:+{clean_digits}\r\n"
        "NOTE:Exported by Sentinel OSINT Bot for Telegram Contact Sync\r\n"
        "END:VCARD\r\n"
    )

    # MTProto Privacy Assessment
    privacy_info = {
        "bot_api_restriction": "Telegram Bot API intentionally restricts bot tokens from querying random address books to prevent mass harvesting.",
        "mtproto_hash_method": "MTProto uses salted SHA-256 phone hashing inside InputPhoneContact structures.",
        "resolution_method": "Direct Client-Side Contact Sync via tg:// protocol or imported vCard."
    }

    return {
        "raw": phone_input,
        "digits": clean_digits,
        "formatted": f"+{clean_digits}",
        "country": base_info["country"],
        "flag": base_info["flag"],
        "dial_code": base_info["dial_code"],
        "timezone": base_info["timezone"],
        "is_valid_length": base_info["is_valid_length"],
        "is_fragment_nft": is_fragment_888,
        "fragment_data": fragment_data,
        "india_telecom": india_telecom,
        "upi_data": upi_data,
        "tg_protocol": f"tg://resolve?phone={clean_digits}",
        "tg_web": f"https://t.me/+{clean_digits}",
        "wa_link": f"https://wa.me/{clean_digits}",
        "vcard_content": vcard_content,
        "privacy_analysis": privacy_info
    }


async def audit_user_phone_exposure(identifier: str, bot=None) -> Dict[str, Any]:
    """
    Performs forensic audit on a Telegram User or Channel profile to detect phone exposure:
    1. Resolves full live entity metadata from Telegram.
    2. Deep scans biography and public descriptions for cleartext phone patterns.
    3. Checks for direct WhatsApp, Viber, or Tel protocol links in profile text.
    4. Evaluates Fragment NFT username collectible status.
    5. Calculates Deanonymization Risk Score (Clean vs Leaked).
    """
    clean_handle = identifier.strip().lstrip("@")
    entity_data = await resolve_full_entity(clean_handle, bot=bot)

    if not entity_data:
        return {
            "identifier": clean_handle,
            "found": False,
            "error": "Could not resolve entity on Telegram."
        }

    bio = entity_data.get("description", "") or entity_data.get("extra", "") or ""
    
    # 1. Regex search for exposed international and local phone numbers in bio
    phone_pattern = re.compile(r'(?:\+?\d{1,4}[-.\s]?(?:\(?\d{2,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{3,4})')
    candidate_numbers = phone_pattern.findall(bio)
    
    valid_extracted_phones = []
    for num in candidate_numbers:
        digits_only = re.sub(r'[^\d]', '', num)
        if 7 <= len(digits_only) <= 15:
            valid_extracted_phones.append(f"+{digits_only}")

    # 2. Check for WhatsApp / Call links
    has_wa_link = "wa.me" in bio or "whatsapp.com" in bio
    has_tel_link = "tel:" in bio

    # 3. Check Fragment username status
    fragment_info = await scrape_fragment_username(clean_handle)

    # 4. Risk scoring
    if valid_extracted_phones or has_wa_link:
        threat_score = 85
        rating = "CRITICAL / CLEAR TEXT PHONE EXPOSURE"
        recommendation = "Target has publicly published a cleartext phone number or WhatsApp link in bio."
    else:
        threat_score = 10
        rating = "SECURE / PROTECTED BY TELEGRAM PRIVACY"
        recommendation = "Target's phone number is encrypted and hidden by Telegram's server-side privacy boundary."

    return {
        "identifier": clean_handle,
        "found": True,
        "entity": entity_data,
        "extracted_phones": list(set(valid_extracted_phones)),
        "has_wa_link": has_wa_link,
        "has_tel_link": has_tel_link,
        "fragment_info": fragment_info,
        "threat_score": threat_score,
        "rating": rating,
        "recommendation": recommendation
    }
