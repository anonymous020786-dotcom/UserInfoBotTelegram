import re
import socket
import asyncio
import aiohttp
from typing import Dict, Any, Optional

SUSPICIOUS_TLDS = {
    "zip", "mov", "top", "xyz", "tk", "ml", "ga", "cf", "gq", 
    "work", "click", "loan", "cam", "fit", "buzz", "racing"
}

PHISHING_KEYWORDS = [
    "telegram", "telegrm", "fragment", "toncoin", "airdrop", 
    "giveaway", "free-crypto", "wallet-connect", "login-telegram",
    "verify-bot", "support-telegram", "recovery-account"
]


async def resolve_domain_or_ip(target: str) -> Dict[str, Any]:
    """
    Asynchronously resolves DNS, queries IP Geolocation and ASN, and audits phishing indicators.
    """
    clean = target.strip().lower()
    # Strip protocols and paths
    clean = re.sub(r'^https?:\/\/', '', clean)
    clean = clean.split('/')[0].split(':')[0].strip()

    is_ip = bool(re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', clean))

    ip_address = clean if is_ip else None
    domain_name = None if is_ip else clean

    # 1. Resolve DNS if it's a domain name
    if not is_ip:
        try:
            loop = asyncio.get_running_loop()
            addr_info = await loop.getaddrinfo(domain_name, None, family=socket.AF_INET)
            if addr_info:
                ip_address = addr_info[0][4][0]
        except Exception:
            ip_address = None

    # 2. Risk & Phishing Audit
    threat_signals = []
    risk_score = 0

    if domain_name:
        tld = domain_name.split('.')[-1] if '.' in domain_name else ""
        if tld in SUSPICIOUS_TLDS:
            threat_signals.append(f"High-abuse TLD (.{tld})")
            risk_score += 35

        for kw in PHISHING_KEYWORDS:
            if kw in domain_name and not domain_name.endswith("telegram.org") and not domain_name.endswith("fragment.com") and not domain_name.endswith("t.me"):
                threat_signals.append(f"Brand impersonation trigger ({kw})")
                risk_score += 45
                break

    if is_ip:
        threat_signals.append("Direct IP address used instead of branded domain name")
        risk_score += 25

    if risk_score >= 60:
        threat_level = "CRITICAL / PHISHING LIKELY"
    elif risk_score >= 30:
        threat_level = "SUSPICIOUS / ELEVATED RISK"
    else:
        threat_level = "LOW RISK / NOMINAL"

    # 3. Query IP Geolocation & ASN via ip-api
    geo_data = {
        "country": "Unknown",
        "country_code": "??",
        "city": "Unknown",
        "region": "Unknown",
        "isp": "Unknown",
        "org": "Unknown",
        "asn": "Unknown"
    }

    if ip_address:
        try:
            timeout = aiohttp.ClientTimeout(total=4)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                url = f"http://ip-api.com/json/{ip_address}?fields=status,country,countryCode,regionName,city,isp,org,as,query"
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("status") == "success":
                            geo_data["country"] = data.get("country", "Unknown")
                            geo_data["country_code"] = data.get("countryCode", "??")
                            geo_data["city"] = data.get("city", "Unknown")
                            geo_data["region"] = data.get("regionName", "Unknown")
                            geo_data["isp"] = data.get("isp", "Unknown")
                            geo_data["org"] = data.get("org", "")
                            geo_data["asn"] = data.get("as", "Unknown")
        except Exception:
            pass

    return {
        "target": target,
        "is_ip": is_ip,
        "domain": domain_name,
        "ip_address": ip_address,
        "risk_score": min(risk_score, 100),
        "threat_level": threat_level,
        "threat_signals": threat_signals,
        "geo": geo_data
    }
