import re
from typing import Dict, Any, Optional

DIAL_CODES = {
    "888": {"country": "Telegram Fragment Anonymous Numbers (TON NFT)", "flag": "💎", "iso": "TON", "timezone": "Decentralized Blockchain", "is_nft": True},
    "1": {"country": "United States / Canada", "flag": "🇺🇸 / 🇨🇦", "iso": "US/CA", "timezone": "UTC-4 to UTC-10"},
    "7": {"country": "Russia / Kazakhstan", "flag": "🇷🇺 / 🇰🇿", "iso": "RU/KZ", "timezone": "UTC+3 to UTC+12"},
    "20": {"country": "Egypt", "flag": "🇪🇬", "iso": "EG", "timezone": "UTC+2"},
    "27": {"country": "South Africa", "flag": "🇿🇦", "iso": "ZA", "timezone": "UTC+2"},
    "30": {"country": "Greece", "flag": "🇬🇷", "iso": "GR", "timezone": "UTC+2"},
    "31": {"country": "Netherlands", "flag": "🇳🇱", "iso": "NL", "timezone": "UTC+1"},
    "32": {"country": "Belgium", "flag": "🇧🇪", "iso": "BE", "timezone": "UTC+1"},
    "33": {"country": "France", "flag": "🇫🇷", "iso": "FR", "timezone": "UTC+1"},
    "34": {"country": "Spain", "flag": "🇪🇸", "iso": "ES", "timezone": "UTC+1"},
    "36": {"country": "Hungary", "flag": "🇭🇺", "iso": "HU", "timezone": "UTC+1"},
    "39": {"country": "Italy", "flag": "🇮🇹", "iso": "IT", "timezone": "UTC+1"},
    "40": {"country": "Romania", "flag": "🇷🇴", "iso": "RO", "timezone": "UTC+2"},
    "41": {"country": "Switzerland", "flag": "🇨🇭", "iso": "CH", "timezone": "UTC+1"},
    "44": {"country": "United Kingdom", "flag": "🇬🇧", "iso": "GB", "timezone": "UTC+0"},
    "45": {"country": "Denmark", "flag": "🇩🇰", "iso": "DK", "timezone": "UTC+1"},
    "46": {"country": "Sweden", "flag": "🇸🇪", "iso": "SE", "timezone": "UTC+1"},
    "47": {"country": "Norway", "flag": "🇳🇴", "iso": "NO", "timezone": "UTC+1"},
    "48": {"country": "Poland", "flag": "🇵🇱", "iso": "PL", "timezone": "UTC+1"},
    "49": {"country": "Germany", "flag": "🇩🇪", "iso": "DE", "timezone": "UTC+1"},
    "52": {"country": "Mexico", "flag": "🇲🇽", "iso": "MX", "timezone": "UTC-6"},
    "54": {"country": "Argentina", "flag": "🇦🇷", "iso": "AR", "timezone": "UTC-3"},
    "55": {"country": "Brazil", "flag": "🇧🇷", "iso": "BR", "timezone": "UTC-3"},
    "60": {"country": "Malaysia", "flag": "🇲🇾", "iso": "MY", "timezone": "UTC+8"},
    "61": {"country": "Australia", "flag": "🇦🇺", "iso": "AU", "timezone": "UTC+8 to UTC+11"},
    "62": {"country": "Indonesia", "flag": "🇮🇩", "iso": "ID", "timezone": "UTC+7 to UTC+9"},
    "63": {"country": "Philippines", "flag": "🇵🇭", "iso": "PH", "timezone": "UTC+8"},
    "65": {"country": "Singapore", "flag": "🇸🇬", "iso": "SG", "timezone": "UTC+8"},
    "66": {"country": "Thailand", "flag": "🇹🇭", "iso": "TH", "timezone": "UTC+7"},
    "81": {"country": "Japan", "flag": "🇯🇵", "iso": "JP", "timezone": "UTC+9"},
    "82": {"country": "South Korea", "flag": "🇰🇷", "iso": "KR", "timezone": "UTC+9"},
    "84": {"country": "Vietnam", "flag": "🇻🇳", "iso": "VN", "timezone": "UTC+7"},
    "86": {"country": "China", "flag": "🇨🇳", "iso": "CN", "timezone": "UTC+8"},
    "90": {"country": "Turkey", "flag": "🇹🇷", "iso": "TR", "timezone": "UTC+3"},
    "91": {"country": "India", "flag": "🇮🇳", "iso": "IN", "timezone": "UTC+5:30"},
    "92": {"country": "Pakistan", "flag": "🇵🇰", "iso": "PK", "timezone": "UTC+5"},
    "94": {"country": "Sri Lanka", "flag": "🇱🇰", "iso": "LK", "timezone": "UTC+5:30"},
    "98": {"country": "Iran", "flag": "🇮🇷", "iso": "IR", "timezone": "UTC+3:30"},
    "212": {"country": "Morocco", "flag": "🇲🇦", "iso": "MA", "timezone": "UTC+1"},
    "213": {"country": "Algeria", "flag": "🇩🇿", "iso": "DZ", "timezone": "UTC+1"},
    "216": {"country": "Tunisia", "flag": "🇹🇳", "iso": "TN", "timezone": "UTC+1"},
    "234": {"country": "Nigeria", "flag": "🇳🇬", "iso": "NG", "timezone": "UTC+1"},
    "254": {"country": "Kenya", "flag": "🇰🇪", "iso": "KE", "timezone": "UTC+3"},
    "351": {"country": "Portugal", "flag": "🇵🇹", "iso": "PT", "timezone": "UTC+0"},
    "370": {"country": "Lithuania", "flag": "🇱🇹", "iso": "LT", "timezone": "UTC+2"},
    "371": {"country": "Latvia", "flag": "🇱🇻", "iso": "LV", "timezone": "UTC+2"},
    "372": {"country": "Estonia", "flag": "🇪🇪", "iso": "EE", "timezone": "UTC+2"},
    "375": {"country": "Belarus", "flag": "🇧🇾", "iso": "BY", "timezone": "UTC+3"},
    "380": {"country": "Ukraine", "flag": "🇺🇦", "iso": "UA", "timezone": "UTC+2"},
    "880": {"country": "Bangladesh", "flag": "🇧🇩", "iso": "BD", "timezone": "UTC+6"},
    "966": {"country": "Saudi Arabia", "flag": "🇸🇦", "iso": "SA", "timezone": "UTC+3"},
    "971": {"country": "United Arab Emirates", "flag": "🇦🇪", "iso": "AE", "timezone": "UTC+4"},
    "972": {"country": "Israel", "flag": "🇮🇱", "iso": "IL", "timezone": "UTC+2"},
    "998": {"country": "Uzbekistan", "flag": "🇺🇿", "iso": "UZ", "timezone": "UTC+5"},
}


def analyze_phone_number(raw_phone: str) -> Dict[str, Any]:
    """
    Analyzes an international phone number, detects country, flag, timezone,
    identifies Fragment +888 anonymous numbers, and generates protocol links.
    """
    clean_digits = re.sub(r'[^\d]', '', raw_phone.strip())
    formatted = f"+{clean_digits}"

    matched_info = None
    dial_prefix = None

    # Check 3-digit prefixes, then 2-digit, then 1-digit
    for prefix_len in [3, 2, 1]:
        p = clean_digits[:prefix_len]
        if p in DIAL_CODES:
            matched_info = DIAL_CODES[p]
            dial_prefix = p
            break

    if not matched_info:
        country_name = "International / Unknown"
        flag = "🌐"
        iso = "??"
        tz = "Unknown"
        is_nft = False
    else:
        country_name = matched_info["country"]
        flag = matched_info["flag"]
        iso = matched_info["iso"]
        tz = matched_info["timezone"]
        is_nft = matched_info.get("is_nft", False)

    # Protocols
    tg_protocol_link = f"tg://resolve?phone={clean_digits}"
    tg_web_link = f"https://t.me/+{clean_digits}"
    wa_link = f"https://wa.me/{clean_digits}"

    is_valid_len = 7 <= len(clean_digits) <= 15

    return {
        "raw": raw_phone,
        "digits": clean_digits,
        "formatted": formatted,
        "is_valid_length": is_valid_len,
        "dial_code": f"+{dial_prefix}" if dial_prefix else "Unknown",
        "country": country_name,
        "flag": flag,
        "iso": iso,
        "timezone": tz,
        "is_fragment_nft_number": is_nft,
        "tg_protocol": tg_protocol_link,
        "tg_web": tg_web_link,
        "wa_link": wa_link
    }
